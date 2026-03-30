"""
bt_output.py — Pi as Bluetooth HID keyboard/mouse device

When output_mode is "bluetooth", HID reports are sent over Bluetooth
to the selected computer rather than via the CH552T USB cable.

How it works
────────────
  The Pi registers itself as a Bluetooth HID device (keyboard + mouse)
  using BlueZ.  Each computer that wants wireless input first pairs with
  the Pi (once), then reconnects automatically when the Pi is available.

  Per-computer pairing data (MAC addresses) is stored in
  BT_OUTPUT_PAIRS_FILE so reconnects survive reboots.

Pairing procedure (triggered by long-press of BT-output button)
────────────────────────────────────────────────────────────────
  1. BTOutput.pair_to_computer(slot) is called.
  2. Pi becomes BT-discoverable and BT-pairable for BT_PAIRING_TIMEOUT s.
  3. User opens Bluetooth settings on the target computer and selects
     "HIDProxBox" from the device list.
  4. Pairing completes; the computer's MAC is stored for slot N.
  5. Pi connects on L2CAP PSM 0x11 (control) and 0x13 (interrupt).

Reconnect (automatic, on computer select switch)
────────────────────────────────────────────────
  When select_computer(n) is called with output_mode == "bluetooth",
  BTOutput.connect_to_computer(slot) attempts an outgoing L2CAP
  connection to the stored MAC.

Dependencies
────────────
  apt install python3-dbus python3-gi bluetooth bluez
  pip install pybluez --break-system-packages
"""

import json
import logging
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

import config

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HID Report descriptor  (keyboard + mouse, same as gadget_setup.sh)
# Used to build the SDP record.
# ─────────────────────────────────────────────────────────────────────────────

_KBD_REPORT_DESC = bytes([
    0x05, 0x01, 0x09, 0x06, 0xa1, 0x01,
    0x05, 0x07, 0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 0x25, 0x01,
    0x75, 0x01, 0x95, 0x08, 0x81, 0x02,
    0x95, 0x01, 0x75, 0x08, 0x81, 0x03,
    0x95, 0x05, 0x75, 0x01, 0x05, 0x08, 0x19, 0x01, 0x29, 0x05,
    0x91, 0x02, 0x95, 0x01, 0x75, 0x03, 0x91, 0x03,
    0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x25, 0x65,
    0x05, 0x07, 0x19, 0x00, 0x29, 0x65, 0x81, 0x00, 0xc0,
])

_MOUSE_REPORT_DESC = bytes([
    0x05, 0x01, 0x09, 0x02, 0xa1, 0x01,
    0x09, 0x01, 0xa1, 0x00,
    0x05, 0x09, 0x19, 0x01, 0x29, 0x03, 0x15, 0x00, 0x25, 0x01,
    0x95, 0x03, 0x75, 0x01, 0x81, 0x02,
    0x95, 0x01, 0x75, 0x05, 0x81, 0x03,
    0x05, 0x01, 0x09, 0x30, 0x09, 0x31, 0x09, 0x38,
    0x15, 0x81, 0x25, 0x7f, 0x75, 0x08, 0x95, 0x03, 0x81, 0x06,
    0xc0, 0xc0,
])

_COMBINED_DESC = _KBD_REPORT_DESC + _MOUSE_REPORT_DESC


# ─────────────────────────────────────────────────────────────────────────────

class BTOutput(threading.Thread):
    """
    Manages the Pi's role as a BT HID keyboard/mouse device.

    Public interface used by daemon.py / router.py:
      start()                      — start listener thread
      stop()                       — stop cleanly
      send(report_type, data)      — called by Router when output_mode == bt
      pair_to_computer(slot)       — enter pairing mode, associate with slot
      connect_to_computer(slot)    — outgoing connect to stored MAC for slot
    """

    _PSM_CTRL = 0x11   # HID Control channel
    _PSM_INTR = 0x13   # HID Interrupt channel (reports go here)
    _HID_INPUT_REPORT = 0xA1   # HIDP header for INPUT reports (device→host)

    def __init__(self) -> None:
        super().__init__(name="bt-output", daemon=True)
        self._stop      = threading.Event()

        # slot → (ctrl_socket, intr_socket)
        self._connections: Dict[int, tuple] = {}
        self._conn_lock  = threading.Lock()

        # slot → paired computer MAC address
        self._pairs: Dict[int, str] = {}
        self._active_slot: int = 1

        # Listener sockets (accept incoming connections from computers)
        self._ctrl_server: Optional[socket.socket] = None
        self._intr_server: Optional[socket.socket] = None

        self._pairing_event = threading.Event()
        self._pairing_slot  = 0

        self._load_pairs()

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if not config.BT_OUTPUT_ENABLED:
            log.info("BTOutput disabled in config.")
            return
        try:
            import bluetooth  # noqa
        except ImportError:
            log.warning("pybluez not installed — BT output disabled.")
            return

        self._setup_sdp()
        self._open_server_sockets()
        super().start()
        log.info("BTOutput started; listening for incoming HID connections.")

    def stop(self) -> None:
        self._stop.set()
        self._close_all()
        self.join(timeout=5)
        log.info("BTOutput stopped.")

    # ── main loop: accept incoming connections from computers ─────────────────

    def run(self) -> None:
        if not self._ctrl_server:
            return

        self._ctrl_server.settimeout(1.0)
        self._intr_server.settimeout(1.0)

        while not self._stop.is_set():
            # Accept control channel
            try:
                ctrl_sock, addr = self._ctrl_server.accept()
            except (socket.timeout, OSError):
                continue

            mac = addr[0]
            log.info("BTOutput: control channel connected from %s", mac)

            # Accept interrupt channel (should arrive quickly after control)
            try:
                self._intr_server.settimeout(5.0)
                intr_sock, _ = self._intr_server.accept()
            except (socket.timeout, OSError) as exc:
                log.warning("BTOutput: interrupt channel not received: %s", exc)
                ctrl_sock.close()
                continue
            finally:
                self._intr_server.settimeout(1.0)

            log.info("BTOutput: HID connection established from %s", mac)
            slot = self._mac_to_slot(mac)

            with self._conn_lock:
                # Close any existing connection for this slot
                if slot in self._connections:
                    self._close_slot(slot)
                self._connections[slot] = (ctrl_sock, intr_sock)

    # ── report sending ────────────────────────────────────────────────────────

    def send(self, report_type, data: bytes) -> None:
        """Called by Router to deliver a HID report over Bluetooth."""
        with self._conn_lock:
            pair = self._connections.get(self._active_slot)
        if pair is None:
            return  # no BT connection for this slot; silently drop

        _, intr_sock = pair
        # HIDP INPUT report: prepend 0xA1 header
        packet = bytes([self._HID_INPUT_REPORT]) + data
        try:
            intr_sock.send(packet)
        except OSError as exc:
            log.warning("BTOutput: send error on slot %d: %s", self._active_slot, exc)
            with self._conn_lock:
                self._close_slot(self._active_slot)

    def set_active_slot(self, slot: int) -> None:
        """Called when the user switches active computer."""
        self._active_slot = slot
        # Try to reconnect if we have a stored MAC but no live socket
        if slot not in self._connections and slot in self._pairs:
            threading.Thread(
                target=self._outgoing_connect,
                args=(slot,),
                daemon=True,
                name=f"bt-out-connect-{slot}",
            ).start()

    # ── pairing ───────────────────────────────────────────────────────────────

    def pair_to_computer(self, slot: int) -> None:
        """
        Make the Pi discoverable and pairable.  The user pairs the target
        computer to "HIDProxBox" from the computer's BT settings.
        Any incoming connection during the pairing window is assigned to slot.
        """
        log.info("BTOutput: entering pairing mode for slot %d (%ds window)…",
                 slot, config.BT_PAIRING_TIMEOUT)
        self._pairing_slot = slot

        # Set adapter name and make discoverable
        self._bt_ctl("system-alias", config.BT_OUTPUT_DEVICE_NAME)
        self._bt_ctl("discoverable", "on")
        self._bt_ctl("pairable", "on")

        # Flash LED (if configured) — non-blocking
        threading.Thread(target=self._blink_pairing_led, daemon=True).start()

        # Wait for pairing window; next accepted connection is associated with slot
        time.sleep(config.BT_PAIRING_TIMEOUT)

        self._bt_ctl("discoverable", "off")
        self._bt_ctl("pairable", "off")
        log.info("BTOutput: pairing window closed for slot %d.", slot)

    def connect_to_computer(self, slot: int) -> None:
        """Attempt outgoing connection to the stored MAC for slot."""
        threading.Thread(
            target=self._outgoing_connect,
            args=(slot,),
            daemon=True,
            name=f"bt-out-connect-{slot}",
        ).start()

    # ── internal: outgoing L2CAP connect ─────────────────────────────────────

    def _outgoing_connect(self, slot: int) -> None:
        mac = self._pairs.get(slot)
        if not mac:
            log.debug("BTOutput: no stored MAC for slot %d.", slot)
            return

        log.info("BTOutput: connecting to computer slot %d (%s)…", slot, mac)
        try:
            import bluetooth
            ctrl_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            ctrl_sock.connect((mac, self._PSM_CTRL))

            intr_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            intr_sock.connect((mac, self._PSM_INTR))

            with self._conn_lock:
                if slot in self._connections:
                    self._close_slot(slot)
                self._connections[slot] = (ctrl_sock, intr_sock)

            log.info("BTOutput: connected to slot %d (%s).", slot, mac)
        except Exception as exc:
            log.warning("BTOutput: outgoing connect to slot %d failed: %s", slot, exc)

    # ── SDP & server socket setup ─────────────────────────────────────────────

    def _setup_sdp(self) -> None:
        """Register an SDP record for the HID profile."""
        # Build HID descriptor list as hex string for sdptool
        desc_hex = _COMBINED_DESC.hex()

        # Use sdptool to add the HID service record
        # (Full SDP XML is the cleanest approach; here we use the built-in HID template)
        try:
            result = subprocess.run(
                ["sdptool", "add", "--handle=0x00010001", "HID"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                log.info("BTOutput: SDP HID record registered.")
            else:
                log.warning("BTOutput: sdptool add failed: %s", result.stderr.strip())
        except FileNotFoundError:
            log.warning("BTOutput: sdptool not found — SDP record not registered. "
                        "Install with: apt install bluez")
        except Exception as exc:
            log.warning("BTOutput: SDP setup error: %s", exc)

        # Set the device class to HID keyboard (0x000540)
        try:
            subprocess.run(
                ["hciconfig", config.BT_ADAPTER, "class", "0x000540"],
                check=False, capture_output=True, timeout=3,
            )
        except Exception:
            pass

    def _open_server_sockets(self) -> None:
        try:
            import bluetooth
            self._ctrl_server = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self._ctrl_server.bind(("", self._PSM_CTRL))
            self._ctrl_server.listen(4)

            self._intr_server = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self._intr_server.bind(("", self._PSM_INTR))
            self._intr_server.listen(4)

            log.info("BTOutput: L2CAP servers listening on PSM 0x11 and 0x13.")
        except Exception as exc:
            log.error("BTOutput: cannot open L2CAP server sockets: %s", exc)
            self._ctrl_server = None
            self._intr_server = None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _mac_to_slot(self, mac: str) -> int:
        """Return the slot associated with mac; if new, use the pairing slot."""
        for slot, stored_mac in self._pairs.items():
            if stored_mac.lower() == mac.lower():
                return slot
        # New connection during pairing window
        slot = self._pairing_slot or self._active_slot
        self._pairs[slot] = mac
        self._save_pairs()
        log.info("BTOutput: stored pairing slot %d → %s", slot, mac)
        return slot

    def _close_slot(self, slot: int) -> None:
        pair = self._connections.pop(slot, None)
        if pair:
            for s in pair:
                try:
                    s.close()
                except Exception:
                    pass

    def _close_all(self) -> None:
        with self._conn_lock:
            for slot in list(self._connections):
                self._close_slot(slot)
        for s in (self._ctrl_server, self._intr_server):
            if s:
                try:
                    s.close()
                except Exception:
                    pass

    def _bt_ctl(self, *args: str) -> None:
        """Run a bluetoothctl command."""
        try:
            subprocess.run(
                ["bluetoothctl", *args],
                check=False, capture_output=True, timeout=5,
            )
        except Exception as exc:
            log.warning("BTOutput: bluetoothctl %s failed: %s", " ".join(args), exc)

    def _blink_pairing_led(self) -> None:
        """Blink the BT-output LED during pairing window."""
        pin = config.LED_PINS.get("output_bt")
        if pin is None:
            return
        try:
            import RPi.GPIO as GPIO
            deadline = time.monotonic() + config.BT_PAIRING_TIMEOUT
            while time.monotonic() < deadline and not self._stop.is_set():
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.25)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.25)
        except Exception:
            pass

    # ── pair persistence ──────────────────────────────────────────────────────

    def _load_pairs(self) -> None:
        path = Path(config.BT_OUTPUT_PAIRS_FILE)
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                self._pairs = {int(k): v for k, v in raw.items()}
                log.info("BTOutput: loaded %d stored pairing(s).", len(self._pairs))
            except Exception as exc:
                log.warning("BTOutput: cannot load pairs file: %s", exc)

    def _save_pairs(self) -> None:
        path = Path(config.BT_OUTPUT_PAIRS_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps({str(k): v for k, v in self._pairs.items()}, indent=2))
        except Exception as exc:
            log.warning("BTOutput: cannot save pairs file: %s", exc)
