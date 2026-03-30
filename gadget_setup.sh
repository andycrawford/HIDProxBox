#!/usr/bin/env bash
# gadget_setup.sh — Configure Linux USB gadget (HID keyboard + mouse)
#
# Creates two HID interfaces via ConfigFS:
#   /dev/hidg0  →  Boot-compatible keyboard  (8-byte reports)
#   /dev/hidg1  →  3-button + wheel mouse    (4-byte reports)
#
# Prerequisites:
#   1. Add to /boot/config.txt:
#        dtoverlay=dwc2
#        enable_uart=1
#   2. Add to /etc/modules:
#        dwc2
#        libcomposite
#   3. Run as root (e.g. via rc.local or a systemd unit).
#
# Usage:
#   sudo ./gadget_setup.sh [up|down]
#
# Tested on: Raspberry Pi Zero 2W / Pi 4 (Raspberry Pi OS Bookworm)

set -euo pipefail

GADGET_DIR="/sys/kernel/config/usb_gadget/hidproxbox"
UDC_SYSFS="/sys/class/udc"

ACTION="${1:-up}"

# ─────────────────────────────────────────────────────────────────────────────
# HID Report Descriptors (binary, written via printf)
# ─────────────────────────────────────────────────────────────────────────────

# Keyboard descriptor — boot-compatible, 6KRO, 8 LEDs
# Yields an 8-byte input report:
#   byte 0: modifier keys  byte 1: reserved  bytes 2-7: keycodes
KBD_DESC=$(printf \
  '\x05\x01'  `# Usage Page (Generic Desktop)` \
  '\x09\x06'  `# Usage (Keyboard)` \
  '\xa1\x01'  `# Collection (Application)` \
  '\x05\x07'  `#   Usage Page (Keyboard/Keypad)` \
  '\x19\xe0'  `#   Usage Minimum (Left Ctrl)` \
  '\x29\xe7'  `#   Usage Maximum (Right GUI)` \
  '\x15\x00'  `#   Logical Minimum (0)` \
  '\x25\x01'  `#   Logical Maximum (1)` \
  '\x75\x01'  `#   Report Size (1)` \
  '\x95\x08'  `#   Report Count (8)` \
  '\x81\x02'  `#   Input (Data, Variable, Absolute) — modifier byte` \
  '\x95\x01'  `#   Report Count (1)` \
  '\x75\x08'  `#   Report Size (8)` \
  '\x81\x03'  `#   Input (Const) — reserved byte` \
  '\x95\x05'  `#   Report Count (5)` \
  '\x75\x01'  `#   Report Size (1)` \
  '\x05\x08'  `#   Usage Page (LEDs)` \
  '\x19\x01'  `#   Usage Minimum (Num Lock)` \
  '\x29\x05'  `#   Usage Maximum (Kana)` \
  '\x91\x02'  `#   Output (Data, Variable, Absolute) — LED byte` \
  '\x95\x01'  `#   Report Count (1)` \
  '\x75\x03'  `#   Report Size (3)` \
  '\x91\x03'  `#   Output (Const) — LED padding` \
  '\x95\x06'  `#   Report Count (6)` \
  '\x75\x08'  `#   Report Size (8)` \
  '\x15\x00'  `#   Logical Minimum (0)` \
  '\x25\x65'  `#   Logical Maximum (101)` \
  '\x05\x07'  `#   Usage Page (Keyboard/Keypad)` \
  '\x19\x00'  `#   Usage Minimum (0)` \
  '\x29\x65'  `#   Usage Maximum (101)` \
  '\x81\x00'  `#   Input (Data, Array) — 6 keycodes` \
  '\xc0'      `# End Collection`
)

# Mouse descriptor — 3 buttons + relative XY + scroll wheel
# Yields a 4-byte input report:
#   byte 0: buttons[2:0] + padding[7:3]
#   byte 1: X  (-127..+127)
#   byte 2: Y  (-127..+127)
#   byte 3: W  (-127..+127, wheel)
MOUSE_DESC=$(printf \
  '\x05\x01'  `# Usage Page (Generic Desktop)` \
  '\x09\x02'  `# Usage (Mouse)` \
  '\xa1\x01'  `# Collection (Application)` \
  '\x09\x01'  `#   Usage (Pointer)` \
  '\xa1\x00'  `#   Collection (Physical)` \
  '\x05\x09'  `#     Usage Page (Button)` \
  '\x19\x01'  `#     Usage Minimum (Button 1 – left)` \
  '\x29\x03'  `#     Usage Maximum (Button 3 – middle)` \
  '\x15\x00'  `#     Logical Minimum (0)` \
  '\x25\x01'  `#     Logical Maximum (1)` \
  '\x95\x03'  `#     Report Count (3)` \
  '\x75\x01'  `#     Report Size (1)` \
  '\x81\x02'  `#     Input (Data, Variable, Absolute)` \
  '\x95\x01'  `#     Report Count (1)` \
  '\x75\x05'  `#     Report Size (5)` \
  '\x81\x03'  `#     Input (Const) — padding` \
  '\x05\x01'  `#     Usage Page (Generic Desktop)` \
  '\x09\x30'  `#     Usage (X)` \
  '\x09\x31'  `#     Usage (Y)` \
  '\x09\x38'  `#     Usage (Wheel)` \
  '\x15\x81'  `#     Logical Minimum (-127)` \
  '\x25\x7f'  `#     Logical Maximum (127)` \
  '\x75\x08'  `#     Report Size (8)` \
  '\x95\x03'  `#     Report Count (3)` \
  '\x81\x06'  `#     Input (Data, Variable, Relative)` \
  '\xc0'      `#   End Collection` \
  '\xc0'      `# End Collection`
)

# ─────────────────────────────────────────────────────────────────────────────
bring_up() {
    echo "[gadget_setup] Bringing up HID gadget..."

    modprobe libcomposite

    if [[ -d "$GADGET_DIR" ]]; then
        echo "[gadget_setup] Gadget directory already exists; tearing down first."
        bring_down
    fi

    mkdir -p "$GADGET_DIR"
    pushd "$GADGET_DIR" > /dev/null

    # ── USB device descriptors ────────────────────────────────────────────────
    echo 0x1d6b > idVendor          # Linux Foundation
    echo 0x0104 > idProduct
    echo 0x0100 > bcdDevice         # device version 1.0
    echo 0x0200 > bcdUSB            # USB 2.0
    echo 0xEF   > bDeviceClass      # Miscellaneous
    echo 0x02   > bDeviceSubClass   # Common Class
    echo 0x01   > bDeviceProtocol   # Interface Association Descriptor

    # ── String descriptors ────────────────────────────────────────────────────
    mkdir -p strings/0x409
    echo "HIDPX001"   > strings/0x409/serialnumber
    echo "VoyageTech" > strings/0x409/manufacturer
    echo "HIDProxBox" > strings/0x409/product

    # ── Configuration ─────────────────────────────────────────────────────────
    mkdir -p configs/c.1/strings/0x409
    echo "HID Proxy"  > configs/c.1/strings/0x409/configuration
    echo 250          > configs/c.1/MaxPower     # 250 mA
    echo 0x80         > configs/c.1/bmAttributes # bus-powered, no remote wakeup

    # ── Function: Keyboard ────────────────────────────────────────────────────
    mkdir -p functions/hid.usb0
    echo 1  > functions/hid.usb0/protocol      # keyboard
    echo 1  > functions/hid.usb0/subclass      # boot interface
    echo 8  > functions/hid.usb0/report_length
    printf "%s" "$KBD_DESC" > functions/hid.usb0/report_desc
    ln -s "$(pwd)/functions/hid.usb0" configs/c.1/hid.usb0

    # ── Function: Mouse ───────────────────────────────────────────────────────
    mkdir -p functions/hid.usb1
    echo 2  > functions/hid.usb1/protocol      # mouse
    echo 0  > functions/hid.usb1/subclass
    echo 4  > functions/hid.usb1/report_length
    printf "%s" "$MOUSE_DESC" > functions/hid.usb1/report_desc
    ln -s "$(pwd)/functions/hid.usb1" configs/c.1/hid.usb1

    # ── Bind to UDC ───────────────────────────────────────────────────────────
    UDC=$(ls "$UDC_SYSFS" 2>/dev/null | head -1)
    if [[ -z "${UDC:-}" ]]; then
        echo "[gadget_setup] ERROR: No UDC found. Is dwc2 loaded and USB cable connected?" >&2
        popd > /dev/null
        bring_down
        exit 1
    fi
    echo "$UDC" > UDC

    popd > /dev/null

    # Verify devices appeared
    sleep 0.5
    for dev in /dev/hidg0 /dev/hidg1; do
        if [[ -c "$dev" ]]; then
            echo "[gadget_setup] ✓  $dev ready"
        else
            echo "[gadget_setup] ✗  $dev NOT found" >&2
        fi
    done
    echo "[gadget_setup] Gadget bound to UDC: $UDC"
}

# ─────────────────────────────────────────────────────────────────────────────
bring_down() {
    echo "[gadget_setup] Tearing down HID gadget..."

    [[ ! -d "$GADGET_DIR" ]] && { echo "[gadget_setup] Nothing to tear down."; return; }

    pushd "$GADGET_DIR" > /dev/null

    # Unbind UDC
    echo "" > UDC 2>/dev/null || true

    # Remove config symlinks
    rm -f configs/c.1/hid.usb0 configs/c.1/hid.usb1 2>/dev/null || true

    # Remove config strings + config
    rmdir configs/c.1/strings/0x409 2>/dev/null || true
    rmdir configs/c.1               2>/dev/null || true

    # Remove functions
    rmdir functions/hid.usb0 2>/dev/null || true
    rmdir functions/hid.usb1 2>/dev/null || true

    # Remove gadget strings
    rmdir strings/0x409 2>/dev/null || true

    popd > /dev/null
    rmdir "$GADGET_DIR" 2>/dev/null || true

    echo "[gadget_setup] Done."
}

# ─────────────────────────────────────────────────────────────────────────────
case "$ACTION" in
    up)   bring_up   ;;
    down) bring_down ;;
    *)
        echo "Usage: $0 [up|down]" >&2
        exit 1
        ;;
esac
