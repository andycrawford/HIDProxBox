"""
HIDProxBox — Central configuration
Edit this file to match your hardware before running.
"""

from typing import Dict, List, Optional

# ── USB Gadget (optional legacy path — gadget_setup.sh) ──────────────────────
GADGET_NAME         = "hidproxbox"
GADGET_VENDOR_ID    = "0x1d6b"
GADGET_PRODUCT_ID   = "0x0104"
GADGET_MANUFACTURER = "VoyageTech"
GADGET_PRODUCT      = "HIDProxBox"
GADGET_SERIAL       = "HIDPX001"

HID_KEYBOARD_DEV    = "/dev/hidg0"
HID_MOUSE_DEV       = "/dev/hidg1"

# ── 4-Computer CH552T Serial Ports ───────────────────────────────────────────
# Each computer gets its own CH552T plugged into that computer's USB port.
# The Pi talks to all four CH552Ts over four USB-serial adapters.
#
# Wiring summary:
#   Pi /dev/ttyUSB0  TX/RX  ──►  CH552T #1  USB ──►  Computer 1
#   Pi /dev/ttyUSB1  TX/RX  ──►  CH552T #2  USB ──►  Computer 2
#   Pi /dev/ttyUSB2  TX/RX  ──►  CH552T #3  USB ──►  Computer 3
#   Pi /dev/ttyUSB3  TX/RX  ──►  CH552T #4  USB ──►  Computer 4

COMPUTERS: Dict[int, str] = {
    1: "/dev/ttyUSB0",
    2: "/dev/ttyUSB1",
    3: "/dev/ttyUSB2",
    4: "/dev/ttyUSB3",
}

SERIAL_BAUD         = 115200
SERIAL_TIMEOUT      = 0.1

# CH552T framing constants
CH552_FRAME_SOF     = 0xAA
CH552_TYPE_KBD      = 0x01
CH552_TYPE_MOUSE    = 0x02
CH552_TYPE_CONSUMER = 0x03
CH552_TYPE_SET_ACTIVE = 0x10   # payload: 0x01=active (LED on), 0x00=inactive
CH552_TYPE_RESET    = 0xFF

# ── Physical USB Keyboard Input ───────────────────────────────────────────────
# Set to "" to auto-detect the first keyboard in /dev/input/by-id/
# or set to a specific evdev path, e.g. "/dev/input/event2"
USB_KBD_DEVICE      = ""
USB_KBD_AUTO_DETECT = True

# ── Bluetooth — Keyboard Input (Pi as BT host) ────────────────────────────────
BT_INPUT_ENABLED    = True
BT_SCAN_TIMEOUT     = 10
BT_DEVICE_MAC       = ""        # lock to a specific keyboard MAC; "" = any
BT_AUTO_RECONNECT   = True
BT_RECONNECT_DELAY  = 5
BT_ADAPTER          = "hci0"
BT_HID_CONTROL_PSM  = 0x11
BT_HID_INTERRUPT_PSM = 0x13

# ── Bluetooth — Output (Pi as BT HID keyboard device) ────────────────────────
# When output_mode == "bluetooth", the Pi acts as a wireless keyboard
# to the selected computer.  Paired computer MACs are stored in this file
# so reconnect works across reboots.
BT_OUTPUT_ENABLED   = True
BT_OUTPUT_PAIRS_FILE = "/var/lib/hidproxbox/bt_output_pairs.json"
BT_OUTPUT_DEVICE_NAME = "HIDProxBox"
BT_PAIRING_TIMEOUT  = 60        # seconds discoverable while waiting to pair

# ── GPIO ─────────────────────────────────────────────────────────────────────
GPIO_ENABLED        = True
LONG_PRESS_S        = 1.5       # seconds held to trigger long-press action
GPIO_BOUNCE_MS      = 50

# Button map: BCM pin → { "short": action_name, "long": action_name }
# Actions are interpreted by GPIOWatcher and dispatched to the Router.
#
#   select_computer_N      — make computer N the active output target
#   input_bt               — switch keyboard input source to Bluetooth
#   input_usb              — switch keyboard input source to USB
#   pair_bt_keyboard       — enter BT pairing mode for the upstream keyboard
#   output_bt              — switch output for active computer to Bluetooth
#   output_usb             — switch output back to USB (CH552T)
#   pair_bt_output         — enter BT pairing mode (Pi as keyboard to computer)

BUTTON_MAP: Dict[int, Dict[str, str]] = {
    # ── Computer select ───────────────────────────────────────────────────────
    4:  {"short": "select_computer_1", "long": "select_computer_1"},
    17: {"short": "select_computer_2", "long": "select_computer_2"},
    27: {"short": "select_computer_3", "long": "select_computer_3"},
    22: {"short": "select_computer_4", "long": "select_computer_4"},

    # ── Keyboard input source ─────────────────────────────────────────────────
    # Short press: toggle USB ↔ BT keyboard input
    # Long press : enter BT pairing mode for the keyboard
    5:  {"short": "toggle_input",      "long": "pair_bt_keyboard"},

    # ── Computer output mode ──────────────────────────────────────────────────
    # Short press: toggle USB ↔ BT output for active computer
    # Long press : pair Pi as BT keyboard to active computer
    6:  {"short": "toggle_output",     "long": "pair_bt_output"},
}

# ── LED Pins (BCM numbering, optional — leave empty dict to disable) ──────────
# Active-high: HIGH = LED on.
LED_PINS: Dict[str, int] = {
    "computer_1": 12,
    "computer_2": 16,
    "computer_3": 20,
    "computer_4": 21,
    "input_bt":   24,   # lit when BT keyboard is the active input
    "output_bt":  25,   # lit when BT is the active output mode
}

# ── HID Macros (still supported via GPIO buttons if needed) ──────────────────
# Modifier bits: Ctrl=0x01, Shift=0x02, Alt=0x04, GUI=0x08
MACROS: Dict[str, List[bytes]] = {
    "macro_copy":        [bytes([0x01, 0x00, 0x06, 0, 0, 0, 0, 0])],
    "macro_paste":       [bytes([0x01, 0x00, 0x19, 0, 0, 0, 0, 0])],
    "macro_undo":        [bytes([0x01, 0x00, 0x1d, 0, 0, 0, 0, 0])],
    "macro_save":        [bytes([0x01, 0x00, 0x16, 0, 0, 0, 0, 0])],
    "macro_lock_screen": [bytes([0x08, 0x00, 0x0f, 0, 0, 0, 0, 0])],
    "macro_screenshot":  [bytes([0x00, 0x00, 0x46, 0, 0, 0, 0, 0])],
}

MACRO_KEY_HOLD_S    = 0.050
MACRO_KEY_GAP_S     = 0.020

# ── Report Queue ──────────────────────────────────────────────────────────────
REPORT_QUEUE_SIZE   = 256

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL           = "INFO"
LOG_FILE            = "/var/log/hidproxbox.log"
LOG_MAX_BYTES       = 5 * 1024 * 1024
LOG_BACKUP_COUNT    = 3
LOG_TO_CONSOLE      = True

# ── Daemon ────────────────────────────────────────────────────────────────────
PID_FILE            = "/var/run/hidproxbox.pid"
WATCHDOG_INTERVAL_S = 2.0
