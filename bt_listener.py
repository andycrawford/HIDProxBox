"""
bt_listener.py — Bluetooth HID host listener

Connects to a Bluetooth HID device (keyboard, mouse, or combo) and
forwards raw HID input reports to the shared queue so HIDWriter can
re-inject them through the USB gadget.

Protocol overview
─────────────────
  Classic BT HID uses L2CAP on two PSM channels:
    0x11  — Control  (commands / handshake, not usually needed for passthrough)
    0x13  — Interrupt (input reports arrive here)

  Each packet on the interrupt channel is:
    [0xA1] [report_id_or_data ...] for INPUT reports (device → host)

  We strip the 0xA1 lead byte and pass the remainder to HIDWriter,
  auto-detecting keyboard vs mouse by payload length:
    8 bytes  → keyboard report
    4 bytes  → mouse report
    other    → logged and dropped (extend _classify() for your device)

Dependencies
────────────
  Kernel: bluetooth, hidp, l2cap  (usually loaded by default on Raspberry Pi OS)
  Python: pip install pybluez --break-system-packages
          (or 'bluetooth' package from apt: python3-bluetooth)

  BlueZ must be running:  sudo systemctl start bluetooth
  The Pi's BT adapter must be powered:  bluetoothctl power on

Pairing
───────
  Pair the BT device once with bluetoothctl (or the Desktop GUI).
  Then set BT_DEVICE_MAC in config.py to lock onto that device,
  or leave it empty to connect to the first BT HID device found in
  the local BlueZ device cache.
"""

import logging
import queue
import socket
import threading
import time
from typing import Optional

import config

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────

class BTListener(threading.Thread):
    """
    Maintains a persistent L2CAP connection to a BT HID device and
    puts decoded HID reports into the shared queue.
    """

    _HID_INTERRUPT_PSM = config.BT_HID_INTERRUPT_PSM  # 0x13
    _HID_INPUT_PREFIX  = 0xA1                          # report type: INPUT

    def __init__(self, report_queue: queue.Queue):
        super().__init__(name="bt-listener", daemon=True)
        self._q          = report_queue
        self._stop       = threading.Event()
        self._sock       : Optional[socket.socket] = None
        self._device_mac : str = config.BT_DEVICE_MAC
        self._bluetooth  = None  # module, imported lazily

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if not config.BT_ENABLED:
            log.info("BTListener disabled in config; not starting.")
            return

        try:
            import bluetooth
            self._bluetooth = bluetooth
        except ImportError:
            log.warning(
                "pybluez not installed (pip install pybluez). "
                "BTListener disabled."
            )
            return

        super().start()
        log.info("BTListener started.")

    def stop(self) -> None:
        self._stop.set()
        self._disconnect()
        self.join(timeout=5)
        log.info("BTListener stopped.")

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        while not self._stop.is_set():
            mac = self._resolve_device()
            if not mac:
                log.info("BTListener: no BT HID device found; will retry in %ds.", config.BT_SCAN_TIMEOUT)
                self._interruptible_sleep(config.BT_SCAN_TIMEOUT)
                continue

            log.info("BTListener: connecting to %s", mac)
            if not self._connect(mac):
                self._interruptible_sleep(config.BT_RECONNECT_DELAY)
                continue

            log.info("BTListener: connected to %s — forwarding HID reports.", mac)
            self._receive_loop()

            if self._stop.is_set():
                break

            if config.BT_AUTO_RECONNECT:
                log.info("BTListener: disconnected; reconnecting in %ds.", config.BT_RECONNECT_DELAY)
                self._interruptible_sleep(config.BT_RECONNECT_DELAY)
            else:
                log.info("BTListener: disconnected; auto-reconnect disabled.")
                break

    # ── device discovery ──────────────────────────────────────────────────────

    def _resolve_device(self) -> Optional[str]:
        """
        Return the MAC address to connect to.

        If BT_DEVICE_MAC is set, return it directly (no scan needed).
        Otherwise query BlueZ for paired/known devices and look for one
        advertising the HID service class (0x2500).
        """
        if self._device_mac:
            return self._device_mac

        bt = self._bluetooth
        log.debug("BTListener: scanning for BT HID devices...")
        try:
            devices = bt.discover_devices(
                duration=config.BT_SCAN_TIMEOUT,
                lookup_names=True,
                lookup_class=True,
            )
        except Exception as exc:
            log.warning("BT scan failed: %s", exc)
            return None

        HID_CLASS_MASK  = 0x000500   # Major device class: Peripheral
        HID_CLASS_KBD   = 0x000540
        HID_CLASS_MOUSE = 0x000580
        HID_CLASS_COMBO = 0x0005C0

        for addr, name, dev_class in devices:
            major = dev_class & 0x001F00
            if major == HID_CLASS_MASK >> 8:  # Peripheral
                log.info("BTListener: found HID device '%s' at %s (class 0x%06X)", name, addr, dev_class)
                return addr

        log.debug("BTListener: no HID device found in scan.")
        return None

    # ── L2CAP connection ──────────────────────────────────────────────────────

    def _connect(self, mac: str) -> bool:
        bt = self._bluetooth
        try:
            sock = bt.BluetoothSocket(bt.L2CAP)
            sock.settimeout(10)
            sock.connect((mac, self._HID_INTERRUPT_PSM))
            sock.settimeout(None)   # back to blocking for recv
            self._sock = sock
            return True
        except (bt.BluetoothError, OSError) as exc:
            log.warning("BTListener: connect to %s failed: %s", mac, exc)
            self._sock = None
            return False

    def _disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    # ── receive loop ──────────────────────────────────────────────────────────

    def _receive_loop(self) -> None:
        """
        Read raw L2CAP packets from the HID interrupt channel,
        strip the report-type header byte, classify, and enqueue.
        """
        while not self._stop.is_set():
            try:
                data = self._sock.recv(64)
            except (OSError, Exception) as exc:
                if not self._stop.is_set():
                    log.info("BTListener: recv error: %s", exc)
                break

            if not data:
                break

            # Strip the HIDP header byte (0xA1 = INPUT, 0xA2 = OUTPUT …)
            if data[0] == self._HID_INPUT_PREFIX:
                payload = data[1:]
            else:
                # Occasionally we get handshake / feature packets; skip them.
                log.debug("BTListener: unexpected header byte 0x%02X — skipped", data[0])
                continue

            report_type = self._classify(payload)
            if report_type is None:
                log.debug("BTListener: unclassified payload len=%d — dropped", len(payload))
                continue

            try:
                self._q.put_nowait((report_type, payload))
            except queue.Full:
                log.warning("BTListener: HID queue full; dropping report.")

    # ── report classification ─────────────────────────────────────────────────

    @staticmethod
    def _classify(payload: bytes):
        """
        Infer ReportType from payload length.

        Override this if your device uses report IDs or a different layout.
        """
        from hid_writer import ReportType

        n = len(payload)
        if n == 8:
            return ReportType.KEYBOARD
        if n == 4:
            return ReportType.MOUSE
        # Some combo devices prepend a 1-byte report ID
        if n == 9:
            return ReportType.KEYBOARD   # strip report_id upstream if needed
        if n == 5:
            return ReportType.MOUSE
        return None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep in small increments so we can react to _stop quickly."""
        deadline = time.monotonic() + seconds
        while not self._stop.is_set() and time.monotonic() < deadline:
            time.sleep(0.1)
