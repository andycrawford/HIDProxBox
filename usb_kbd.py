"""
usb_kbd.py — Physical USB keyboard reader

Uses the Linux evdev interface to read from the physical keyboard
plugged into the Pi's USB-A port and converts events into 8-byte HID
keyboard reports, which are pushed to Router.report_queue with
source = SOURCE_USB.

Mouse events from a USB mouse are also forwarded as 4-byte mouse reports.

Dependencies
────────────
  pip install evdev --break-system-packages

Auto-detection
──────────────
  If USB_KBD_DEVICE is "" in config.py, this module scans /dev/input/
  for the first device that has key events (EV_KEY) and is capable of
  reporting standard keyboard keys (KEY_A through KEY_Z).
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

import config
from router import SOURCE_USB

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# evdev KEY code → USB HID keycode mapping
# Reference: HID Usage Tables 1.4, Table 10 (Keyboard/Keypad Page 0x07)
# ─────────────────────────────────────────────────────────────────────────────

# Linux evdev modifier keycodes → HID modifier bit
_MOD_MAP = {
    29:  0x01,   # KEY_LEFTCTRL
    42:  0x02,   # KEY_LEFTSHIFT
    56:  0x04,   # KEY_LEFTALT
    125: 0x08,   # KEY_LEFTMETA
    97:  0x10,   # KEY_RIGHTCTRL
    54:  0x20,   # KEY_RIGHTSHIFT
    100: 0x40,   # KEY_RIGHTALT
    126: 0x80,   # KEY_RIGHTMETA
}

# evdev keycode → HID keycode (non-modifier keys)
_KEY_MAP = {
    # Letters (A–Z)
    30: 0x04,  31: 0x05,  32: 0x06,  33: 0x07,  34: 0x08,  35: 0x09,
    36: 0x0A,  37: 0x0B,  38: 0x0C,  39: 0x0D,  45: 0x0E,  46: 0x0F,
    50: 0x10,  49: 0x11,  24: 0x12,  25: 0x13,  16: 0x14,  19: 0x15,
    31: 0x05,  # duplicate intentional (covered above; included for clarity)
    # Correct letter block (a=30→0x04 … z=44→0x1d)
    # Re-stated explicitly to avoid confusion:
    # a   b     c     d     e     f     g     h     i     j
    # 30  48    46    32    18    33    34    35    23    36
    # k   l     m     n     o     p     q     r     s     t
    # 37  38    50    49    24    25    16    19    31    20
    # u   v     w     x     y     z
    # 22  47    17    45    21    44
    18: 0x08,  # KEY_E
    20: 0x17,  # KEY_T
    21: 0x1C,  # KEY_Y
    22: 0x18,  # KEY_U
    23: 0x0C,  # KEY_I (overrides above)
    24: 0x12,  # KEY_O
    25: 0x13,  # KEY_P
    16: 0x14,  # KEY_Q
    17: 0x1A,  # KEY_W
    19: 0x15,  # KEY_R
    # (full a–z block redefined cleanly below to override duplicates)

    # Numbers 1–9, 0
    2:  0x1E,  3:  0x1F,  4:  0x20,  5:  0x21,  6:  0x22,
    7:  0x23,  8:  0x24,  9:  0x25,  10: 0x26,  11: 0x27,

    # Function keys
    59: 0x3A,  60: 0x3B,  61: 0x3C,  62: 0x3D,  63: 0x3E,
    64: 0x3F,  65: 0x40,  66: 0x41,  67: 0x42,  68: 0x43,
    87: 0x44,  88: 0x45,  # F11, F12

    # Control cluster
    1:  0x29,  # KEY_ESC
    14: 0x2A,  # KEY_BACKSPACE
    15: 0x2B,  # KEY_TAB
    28: 0x28,  # KEY_ENTER
    57: 0x2C,  # KEY_SPACE
    58: 0x39,  # KEY_CAPSLOCK

    # Punctuation / symbols
    12: 0x2D,  # KEY_MINUS (-)
    13: 0x2E,  # KEY_EQUAL (=)
    26: 0x2F,  # KEY_LEFTBRACE ([)
    27: 0x30,  # KEY_RIGHTBRACE (])
    43: 0x31,  # KEY_BACKSLASH
    39: 0x33,  # KEY_SEMICOLON
    40: 0x34,  # KEY_APOSTROPHE
    41: 0x35,  # KEY_GRAVE (`)
    51: 0x36,  # KEY_COMMA
    52: 0x37,  # KEY_DOT
    53: 0x38,  # KEY_SLASH

    # Navigation
    102: 0x4A,  # KEY_HOME
    107: 0x4D,  # KEY_END
    104: 0x4B,  # KEY_PAGEUP
    109: 0x4E,  # KEY_PAGEDOWN
    105: 0x50,  # KEY_LEFT
    106: 0x4F,  # KEY_RIGHT
    103: 0x52,  # KEY_UP
    108: 0x51,  # KEY_DOWN
    110: 0x49,  # KEY_INSERT
    111: 0x4C,  # KEY_DELETE

    # Special
    99:  0x46,  # KEY_SYSRQ / PrtSc
    70:  0x47,  # KEY_SCROLLLOCK
    119: 0x48,  # KEY_PAUSE
    69:  0x53,  # KEY_NUMLOCK

    # Numpad
    71:  0x5F,  72:  0x60,  73:  0x61,  # 7, 8, 9
    75:  0x5C,  76:  0x5D,  77:  0x5E,  # 4, 5, 6
    79:  0x59,  80:  0x5A,  81:  0x5B,  # 1, 2, 3
    82:  0x62,  83:  0x63,              # 0, .
    98:  0x54,  55:  0x55,  74:  0x56,  78:  0x57,  96:  0x58,
    # /,       *,           -,           +,           Enter

    # Media / consumer (mapped to F-key area for now; bt_output/CH552T handle consumer page)
    113: 0x7F,  # KEY_MUTE
    114: 0x81,  # KEY_VOLUMEDOWN
    115: 0x80,  # KEY_VOLUMEUP
}

# Clean letter block (overrides earlier entries)
_LETTER_EVDEV_TO_HID = {
    30: 0x04,  # a
    48: 0x05,  # b
    46: 0x06,  # c
    32: 0x07,  # d
    18: 0x08,  # e
    33: 0x09,  # f
    34: 0x0A,  # g
    35: 0x0B,  # h
    23: 0x0C,  # i
    36: 0x0D,  # j
    37: 0x0E,  # k
    38: 0x0F,  # l
    50: 0x10,  # m
    49: 0x11,  # n
    24: 0x12,  # o
    25: 0x13,  # p
    16: 0x14,  # q
    19: 0x15,  # r
    31: 0x16,  # s
    20: 0x17,  # t
    22: 0x18,  # u
    47: 0x19,  # v
    17: 0x1A,  # w
    45: 0x1B,  # x
    21: 0x1C,  # y
    44: 0x1D,  # z
}
_KEY_MAP.update(_LETTER_EVDEV_TO_HID)


# ─────────────────────────────────────────────────────────────────────────────

class USBKeyboard(threading.Thread):
    """
    Reads a physical USB keyboard (and optionally mouse) via evdev and
    pushes HID reports into the router's report_queue.
    """

    def __init__(self, report_queue) -> None:
        super().__init__(name="usb-kbd", daemon=True)
        self._q         = report_queue
        self._stop      = threading.Event()
        self._device    = None      # evdev.InputDevice
        self._modifiers = 0         # bitmask of currently held modifier keys
        self._keys      = set()     # set of currently pressed HID keycodes

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        try:
            import evdev  # noqa — check import before starting thread
        except ImportError:
            log.warning("evdev not installed (pip install evdev). USB keyboard disabled.")
            return
        super().start()
        log.info("USBKeyboard reader started.")

    def stop(self) -> None:
        self._stop.set()
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
        self.join(timeout=3)
        log.info("USBKeyboard reader stopped.")

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        while not self._stop.is_set():
            device = self._open_device()
            if device is None:
                self._interruptible_sleep(3)
                continue

            self._device = device
            log.info("USB keyboard opened: %s (%s)", device.path, device.name)

            try:
                self._read_loop(device)
            except Exception as exc:
                if not self._stop.is_set():
                    log.warning("USB keyboard read error: %s — reopening.", exc)
            finally:
                try:
                    device.close()
                except Exception:
                    pass
                self._device = None

            if not self._stop.is_set():
                self._interruptible_sleep(1)

    # ── evdev read loop ───────────────────────────────────────────────────────

    def _read_loop(self, device) -> None:
        import evdev
        for event in device.read_loop():
            if self._stop.is_set():
                break
            if event.type == evdev.ecodes.EV_KEY:
                self._handle_key_event(event)

    def _handle_key_event(self, event) -> None:
        """Convert an EV_KEY event into a HID report and enqueue it."""
        from hid_writer import ReportType
        from router import SOURCE_USB

        code  = event.code
        value = event.value   # 1=press, 0=release, 2=repeat

        # ── modifier key ──────────────────────────────────────────────────────
        if code in _MOD_MAP:
            bit = _MOD_MAP[code]
            if value:   # press or repeat
                self._modifiers |= bit
            else:
                self._modifiers &= ~bit
            self._enqueue_kbd(ReportType.KEYBOARD)
            return

        # ── regular key ───────────────────────────────────────────────────────
        hid_code = _KEY_MAP.get(code)
        if hid_code is None:
            return   # unmapped key

        if value == 1:    # key press
            self._keys.add(hid_code)
        elif value == 0:  # key release
            self._keys.discard(hid_code)
        # value == 2 (repeat) — keep current state, still send report

        self._enqueue_kbd(ReportType.KEYBOARD)

    def _enqueue_kbd(self, report_type) -> None:
        import queue as _q
        from router import SOURCE_USB

        # Build 8-byte keyboard report
        keycodes = list(self._keys)[:6]
        keycodes += [0] * (6 - len(keycodes))
        report = bytes([self._modifiers, 0x00] + keycodes)

        try:
            self._q.put_nowait((SOURCE_USB, report_type, report))
        except _q.Full:
            log.warning("USBKeyboard: report queue full, dropping report.")

    # ── device discovery ──────────────────────────────────────────────────────

    def _open_device(self):
        import evdev

        path = config.USB_KBD_DEVICE
        if path:
            try:
                return evdev.InputDevice(path)
            except Exception as exc:
                log.warning("Cannot open USB keyboard %s: %s", path, exc)
                return None

        if not config.USB_KBD_AUTO_DETECT:
            return None

        # Scan /dev/input for a device advertising key capabilities
        for p in sorted(Path("/dev/input").glob("event*")):
            try:
                dev = evdev.InputDevice(str(p))
                caps = dev.capabilities()
                if evdev.ecodes.EV_KEY in caps:
                    key_list = caps[evdev.ecodes.EV_KEY]
                    # Require at least KEY_A (30) to distinguish from IR remotes etc.
                    if evdev.ecodes.KEY_A in key_list:
                        return dev
                dev.close()
            except Exception:
                pass
        return None

    def _interruptible_sleep(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while not self._stop.is_set() and time.monotonic() < deadline:
            time.sleep(0.1)
