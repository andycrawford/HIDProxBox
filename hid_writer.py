"""
hid_writer.py — Multi-computer USB HID output sink

Manages four serial connections, one per CH552T (one per computer).
Acts as the "usb" output sink for the Router:

  router.set_usb_sink(writer.write)
  writer.write(computer_id, report_type, data)

When the active computer switches, hid_writer also sends a
TYPE_SET_ACTIVE command to each CH552T so their "active" indicator
LEDs reflect the current selection.

Report format accepted
──────────────────────
  Keyboard : 8 bytes — [modifier, 0x00, key1..key6]
  Mouse    : 4 bytes — [buttons, X (int8), Y (int8), wheel (int8)]
  Consumer : 2 bytes — [usage_lo, usage_hi]

CH552T frame format  (same protocol as before)
───────────────────
  [0xAA] [TYPE] [LEN] [DATA ...] [XOR checksum]
"""

import logging
import os
import threading
import time
from typing import Dict, Optional

import serial

import config

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────

class ReportType:
    KEYBOARD = "keyboard"
    MOUSE    = "mouse"
    CONSUMER = "consumer"


NULL_KEYBOARD = bytes(8)
NULL_MOUSE    = bytes(4)
NULL_CONSUMER = bytes(2)


# ─────────────────────────────────────────────────────────────────────────────

def _ch552_frame(type_byte: int, data: bytes) -> bytes:
    """Build a framed, checksummed packet for the CH552T."""
    length = len(data)
    chk = type_byte ^ length
    for b in data:
        chk ^= b
    return bytes([config.CH552_FRAME_SOF, type_byte, length]) + data + bytes([chk])


# ─────────────────────────────────────────────────────────────────────────────

class _ComputerLink:
    """One serial connection to one CH552T."""

    def __init__(self, computer_id: int, port: str) -> None:
        self.computer_id = computer_id
        self.port        = port
        self._lock       = threading.Lock()
        self._serial: Optional[serial.Serial] = None
        self._open()

    def _open(self) -> None:
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=config.SERIAL_BAUD,
                timeout=config.SERIAL_TIMEOUT,
            )
            log.info("CH552T #%d open: %s", self.computer_id, self.port)
        except serial.SerialException as exc:
            log.warning("CH552T #%d cannot open %s: %s", self.computer_id, self.port, exc)
            self._serial = None

    def send_frame(self, type_byte: int, data: bytes) -> bool:
        """Send a framed packet; returns True on success."""
        frame = _ch552_frame(type_byte, data)
        with self._lock:
            if self._serial is None or not self._serial.is_open:
                self._open()
            if self._serial is None:
                return False
            try:
                self._serial.write(frame)
                return True
            except serial.SerialException as exc:
                log.warning("CH552T #%d write error: %s — will reopen.", self.computer_id, exc)
                try:
                    self._serial.close()
                except Exception:
                    pass
                self._serial = None
                return False

    def send_report(self, report_type: str, data: bytes) -> bool:
        type_map = {
            ReportType.KEYBOARD: config.CH552_TYPE_KBD,
            ReportType.MOUSE:    config.CH552_TYPE_MOUSE,
            ReportType.CONSUMER: config.CH552_TYPE_CONSUMER,
        }
        type_byte = type_map.get(report_type)
        if type_byte is None:
            return False
        return self.send_frame(type_byte, data)

    def set_active_led(self, active: bool) -> None:
        """Tell the CH552T whether this computer is the currently selected one."""
        self.send_frame(config.CH552_TYPE_SET_ACTIVE, bytes([0x01 if active else 0x00]))

    def close(self) -> None:
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except Exception:
                    pass


# ─────────────────────────────────────────────────────────────────────────────

class HIDWriter:
    """
    USB HID sink — routes a report to the specified computer's CH552T.

    This is NOT a thread itself; it is called from the Router's dispatch
    thread via the usb_sink callback.
    """

    def __init__(self) -> None:
        self._links: Dict[int, _ComputerLink] = {}
        self._active_computer = 1

    def open(self) -> None:
        """Open serial connections to all CH552Ts."""
        for computer_id, port in config.COMPUTERS.items():
            self._links[computer_id] = _ComputerLink(computer_id, port)

        # Mark initial active computer on all CH552T LEDs
        self._update_active_leds(self._active_computer)
        log.info("HIDWriter: %d computer link(s) initialised.", len(self._links))

    def close(self) -> None:
        for link in self._links.values():
            link.close()
        log.info("HIDWriter closed.")

    # ── router sink callback ──────────────────────────────────────────────────

    def write(self, computer_id: int, report_type: str, data: bytes) -> None:
        """
        Called by Router.  Route 'data' to computer_id's CH552T.
        Also fires _update_active_leds if the active computer changed.
        """
        if computer_id != self._active_computer:
            self._active_computer = computer_id
            self._update_active_leds(computer_id)

        link = self._links.get(computer_id)
        if link:
            link.send_report(report_type, data)
        else:
            log.warning("HIDWriter: no link for computer %d", computer_id)

    # ── convenience wrappers (used by daemon for macro injection) ─────────────

    def send_macro(self, computer_id: int, macro_name: str) -> None:
        steps = config.MACROS.get(macro_name)
        if not steps:
            log.warning("HIDWriter: unknown macro '%s'", macro_name)
            return
        for step in steps:
            self.write(computer_id, ReportType.KEYBOARD, step)
            time.sleep(config.MACRO_KEY_HOLD_S)
            self.write(computer_id, ReportType.KEYBOARD, NULL_KEYBOARD)
            time.sleep(config.MACRO_KEY_GAP_S)

    # ── LED sync ──────────────────────────────────────────────────────────────

    def _update_active_leds(self, active_id: int) -> None:
        """Send SET_ACTIVE to all CH552Ts to sync their indicator LEDs."""
        for cid, link in self._links.items():
            link.set_active_led(cid == active_id)
