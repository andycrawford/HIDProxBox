# HIDProxBox

A 4-port Bluetooth/USB HID KVM proxy built on a Raspberry Pi and four CH552T microcontrollers. HIDProxBox sits between your input devices (a physical USB keyboard or a Bluetooth keyboard) and up to four computers, letting you switch between hosts instantly with a button press — no software installation required on any of the target computers.

---

## What It Does

- **Switch between 4 computers** with dedicated selector buttons — all computers stay USB-connected at all times
- **Accept input from a physical USB keyboard** plugged into the Pi, or from **any Bluetooth keyboard**
- **Toggle keyboard input source** (USB ↔ BT) with a single button
- **Output via USB** (the Pi talks to each computer through an individual CH552T HID device) **or via Bluetooth** (the Pi presents itself as a wireless keyboard directly to the selected computer)
- **Hold a button to pair** — one hold gesture pairs an upstream BT keyboard; another pairs the Pi itself as a BT keyboard to the active computer
- **LED feedback** — six indicator LEDs show which computer is active, which input source is live, and which output mode is in use

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi                             │
│                                                                 │
│  ┌────────────┐   ┌───────────┐   ┌──────────────────────────┐ │
│  │ usb_kbd.py │   │bt_listener│   │      gpio_watcher.py     │ │
│  │ (evdev)    │   │   .py     │   │ 4× computer select btns  │ │
│  │ USB kbd in │   │ BT kbd in │   │ BT-input btn (s/l press) │ │
│  └─────┬──────┘   └─────┬─────┘   │ BT-output btn(s/l press)│ │
│        │  source="usb"  │  source="bt"   └──────┬───────────┘ │
│        └────────────────┴────────────────────────┤             │
│                                                   ▼             │
│                              ┌────────────────────────────┐    │
│                              │         router.py          │    │
│                              │  active_computer : 1–4     │    │
│                              │  input_mode : usb | bt     │    │
│                              │  output_mode: usb | bt     │    │
│                              └──────────┬─────────────────┘    │
│                                         │                       │
│                    ┌────────────────────┴──────────────────┐   │
│                    ▼  output_mode=usb                       ▼   │
│          ┌─────────────────┐                  ┌─────────────────┐│
│          │  hid_writer.py  │                  │  bt_output.py   ││
│          │ 4× serial ports │                  │ Pi as BT HID    ││
│          └──┬──┬──┬──┬─────┘                  │ keyboard device ││
│             │  │  │  │                         └────────┬────────┘│
└─────────────┼──┼──┼──┼──────────────────────────────────┼────────┘
              │  │  │  │  /dev/ttyUSB0–3                   │ Bluetooth
       ┌──────┘  │  │  └──────┐                            │
       ▼         ▼  ▼         ▼                            ▼
  ┌────────┐ ┌──────┐ ┌──────┐ ┌────────┐        (selected computer)
  │CH552T 1│ │  #2  │ │  #3  │ │CH552T 4│
  │USB HID │ │      │ │      │ │USB HID │
  └───┬────┘ └──┬───┘ └──┬───┘ └───┬────┘
      │         │         │         │  USB cables (always plugged in)
      ▼         ▼         ▼         ▼
  Computer1  Computer2  Computer3  Computer4
```

### File Overview

| File | Role |
|------|------|
| `config.py` | Single source of truth — serial ports, GPIO pins, button actions, LED pins, BT settings |
| `router.py` | Central state machine; drains the shared report queue and dispatches to the right output sink |
| `usb_kbd.py` | Reads a physical USB keyboard via evdev; converts Linux key events to 8-byte HID reports |
| `bt_listener.py` | Bluetooth HID host — receives HID reports from a paired BT keyboard |
| `bt_output.py` | Bluetooth HID device — makes the Pi appear as a wireless keyboard to computers |
| `hid_writer.py` | USB output sink — manages four CH552T serial connections, routes reports to the active one |
| `gpio_watcher.py` | Button input with short/long press detection; drives all six indicator LEDs |
| `daemon.py` | Entry point — wires all subsystems, installs signal handlers, runs the health watchdog |
| `gadget_setup.sh` | Optional: configures Linux USB gadget mode (keyboard + mouse on /dev/hidg0/1) |
| `firmware/ch552t_hid_proxy/ch552t_hid_proxy.ino` | Arduino sketch for each CH552T unit |

---

## Hardware Bill of Materials

| Qty | Item | Notes |
|-----|------|-------|
| 1 | Raspberry Pi Zero 2W **or** Pi 4 | Pi 4 preferred — multiple hardware UARTs, more USB ports |
| 4 | CH552T microcontroller (breakout or bare chip) | [Available on AliExpress / LCSC](https://lcsc.com/search?q=CH552T) |
| 4 | USB-A to USB-C (or USB-B) cable | One per computer |
| 4 | USB-serial adapter (CP2102 / CH340) | One per CH552T; provides /dev/ttyUSB0–3 |
| 6 | Momentary push-buttons (SPST NO) | Active-low; any 6mm tactile switch |
| 6 | LEDs + 220 Ω resistors | Indicator LEDs |
| 1 | 3.3 V power supply | CH552T is a 3.3 V part |
| — | 22 Ω resistors (x8) | USB D+/D− series resistors on CH552T (2 per unit) |
| — | Enclosure of your choice | |

---

## Wiring

### GPIO Buttons (active-low — press pulls pin to GND)

Each button connects between a BCM GPIO pin and GND. The Pi's internal pull-up holds the pin HIGH at rest.

| BCM Pin | Button Function | Short Press | Long Press |
|---------|-----------------|-------------|------------|
| 4 | Computer 1 | Select computer 1 | Select computer 1 |
| 17 | Computer 2 | Select computer 2 | Select computer 2 |
| 27 | Computer 3 | Select computer 3 | Select computer 3 |
| 22 | Computer 4 | Select computer 4 | Select computer 4 |
| 5 | BT keyboard | Toggle USB ↔ BT input | Pair BT keyboard to Pi |
| 6 | BT output | Toggle USB ↔ BT output | Pair Pi as BT keyboard to active computer |

### GPIO LEDs (active-high — HIGH = on)

Each LED connects from a BCM pin through a 220 Ω resistor to the LED anode, with the cathode to GND.

| BCM Pin | Indicator |
|---------|-----------|
| 12 | Computer 1 active |
| 16 | Computer 2 active |
| 20 | Computer 3 active |
| 21 | Computer 4 active |
| 24 | BT keyboard input active |
| 25 | BT output mode active |

### CH552T Units (one per computer)

Each CH552T unit needs four connections to the Pi and two to its target computer.

```
Pi /dev/ttyUSB0 TX ──────── CH552T #1 P3.0 (RXD1)
Pi /dev/ttyUSB0 RX ──────── CH552T #1 P3.1 (TXD1)
Pi GND ─────────────────── CH552T #1 GND
Pi 3.3V ────────────────── CH552T #1 VCC

CH552T #1 USB D+ ──22Ω──── Computer 1 USB D+
CH552T #1 USB D− ──22Ω──── Computer 1 USB D−
CH552T #1 GND ─────────── Computer 1 USB GND
CH552T #1 VBUS ──────────── Computer 1 USB VBUS (5V, used for detection only)

CH552T #1 P3.4 ──220Ω──LED── GND   (active LED: lit when this computer is selected)
CH552T #1 P1.4 ──220Ω──LED── GND   (status LED: blinks on each received HID frame)
```

Repeat the same wiring for CH552T units #2, #3, and #4, substituting `/dev/ttyUSB1`, `/dev/ttyUSB2`, and `/dev/ttyUSB3`.

> **Note:** CH552T is a 3.3 V part. The Raspberry Pi's GPIO UART pins are already 3.3 V, so no level shifter is needed. Do not connect a 5 V UART directly.

### Physical USB Keyboard (optional)

Plug directly into any USB-A port on the Pi. The `usb_kbd.py` module auto-detects the first keyboard-capable device in `/dev/input/`. To lock it to a specific device, set `USB_KBD_DEVICE` in `config.py`.

---

## Software Installation

### 1. Prepare the Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dbus bluez bluetooth

# Install Python dependencies
pip3 install evdev pyserial pybluez --break-system-packages
```

### 2. Enable required kernel modules

Add to `/boot/config.txt` (or `/boot/firmware/config.txt` on newer Pi OS):

```ini
# Enable USB gadget mode (optional — for legacy gadget output)
dtoverlay=dwc2
enable_uart=1
```

Add to `/etc/modules`:

```
dwc2
libcomposite
```

### 3. Clone and install HIDProxBox

```bash
git clone https://github.com/andycrawford/HIDProxBox.git /opt/hidproxbox
cd /opt/hidproxbox
chmod +x gadget_setup.sh
```

### 4. Flash the CH552T firmware

Each CH552T unit runs the same firmware. Flash each one using the Arduino IDE with the ch55xduino board package installed.

**Board manager URL** (add in Arduino IDE → Preferences):
```
https://raw.githubusercontent.com/DeqingSun/ch55xduino/master/package_ch55xduino_mcs51_index.json
```

**Board settings:**

| Setting | Value |
|---------|-------|
| Board | CH55x boards → CH552 |
| Clock Source | 16 MHz (internal) |
| Upload Method | USB (bootloader) |
| USB Settings | USER CODE w/ 148B USB ram |

Open `firmware/ch552t_hid_proxy/ch552t_hid_proxy.ino` and upload to each unit. All four units use the same firmware — they are distinguished only by which serial port and computer they are physically connected to.

**To enter bootloader mode on a bare CH552T:** hold the BOOT pin (P3.6) LOW while applying power, then release.

### 5. Configure

Edit `/opt/hidproxbox/config.py` to match your hardware:

```python
# Serial ports for each CH552T (check dmesg or ls /dev/ttyUSB* after plugging in)
COMPUTERS = {
    1: "/dev/ttyUSB0",
    2: "/dev/ttyUSB1",
    3: "/dev/ttyUSB2",
    4: "/dev/ttyUSB3",
}

# To lock to a specific BT keyboard, set its MAC address:
BT_DEVICE_MAC = "AA:BB:CC:DD:EE:FF"   # or "" to accept any

# Long-press threshold (seconds)
LONG_PRESS_S = 1.5
```

### 6. Set up systemd service

```bash
sudo cp /opt/hidproxbox/hidproxbox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hidproxbox
sudo systemctl start hidproxbox
```

Example `/etc/systemd/system/hidproxbox.service`:

```ini
[Unit]
Description=HIDProxBox KVM Daemon
After=network.target bluetooth.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/hidproxbox/daemon.py --foreground
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Check that it started cleanly:

```bash
sudo systemctl status hidproxbox
sudo journalctl -u hidproxbox -f
```

---

## Operation

### Switching computers

Press the button for the target computer (pins 4 / 17 / 27 / 22). The corresponding LED on the Pi lights up, and the CH552T for the newly selected computer lights its own active LED. All other CH552T active LEDs go dark.

### Switching keyboard input source

| Action | Result |
|--------|--------|
| Short press pin 5 | Toggles between USB keyboard and Bluetooth keyboard as the active input. The BT-input LED (pin 24) lights when BT is active. |
| Long press pin 5 | Puts the Pi into BT discovery mode for `BT_SCAN_TIMEOUT` seconds. Put your Bluetooth keyboard into pairing mode during this window. |

### Switching computer output mode

| Action | Result |
|--------|--------|
| Short press pin 6 | Toggles output for the active computer between USB (via CH552T) and Bluetooth. The BT-output LED (pin 25) lights when BT is active. |
| Long press pin 6 | Puts the Pi into BT discoverable/pairable mode for `BT_PAIRING_TIMEOUT` seconds. On the target computer, open Bluetooth settings, find **HIDProxBox**, and complete the pairing. The computer's MAC is stored and associated with the currently selected computer slot. Subsequent output-mode switches to BT will reconnect automatically. |

### Pairing summary

| Goal | Steps |
|------|-------|
| Pair a BT keyboard as input | Select the input source button → **hold** pin 5 → put keyboard into pairing mode |
| Use BT keyboard as input | **Short press** pin 5 (toggles to BT input mode) |
| Pair Pi as BT keyboard to a computer | Select the computer (pins 4/17/27/22) → **hold** pin 6 → pair from the computer's BT settings |
| Switch that computer to BT output | **Short press** pin 6 (toggles to BT output mode) |
| Switch back to USB output | **Short press** pin 6 again |

---

## Logs

```bash
# Live log tail
sudo tail -f /var/log/hidproxbox.log

# Or via journalctl if running as a systemd service
sudo journalctl -u hidproxbox -f
```

---

## Project Structure

```
HIDProxBox/
├── config.py                          # All hardware and behaviour settings
├── router.py                          # Central state machine + report dispatch
├── daemon.py                          # Entry point, wires all subsystems
├── hid_writer.py                      # USB output: 4× CH552T serial sink
├── bt_listener.py                     # BT input: Pi as BT HID host
├── bt_output.py                       # BT output: Pi as BT HID keyboard device
├── usb_kbd.py                         # USB input: evdev keyboard reader
├── gpio_watcher.py                    # Button handling + LED feedback
├── gadget_setup.sh                    # (Optional) Linux USB gadget setup
└── firmware/
    └── ch552t_hid_proxy/
        └── ch552t_hid_proxy.ino       # CH552T Arduino firmware (same for all 4)
```

---

## Contributing

Issues and pull requests are welcome. When adding new features, keep the source/sink separation in `router.py` clean — new input sources push `(source, ReportType, bytes)` tuples to `router.report_queue`, and new output sinks register via `router.set_usb_sink()` or `router.set_bt_sink()`.

---

## License

MIT
