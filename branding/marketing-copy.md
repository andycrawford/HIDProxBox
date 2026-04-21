# HIDProxBox — Marketing Copy

---

## Tagline

> **One keyboard. Four computers. Zero software on the targets.**

*Alternate short form (social / card preview):*
> Your keyboard, everywhere — one button press at a time.

---

## Elevator Pitch

HIDProxBox is an open-source Raspberry Pi KVM proxy that routes a single keyboard and mouse to up to four computers simultaneously. Each target sees a genuine USB or Bluetooth HID device — no drivers, no agents, no software to install on anything you want to control. Press a button (or tap the web panel from your phone) and your keystrokes instantly follow.

It accepts input from a wired USB keyboard or any Bluetooth keyboard, and it can deliver that input over USB — through four dedicated CH552T microcontrollers, one per computer — or wirelessly over Bluetooth. Mix and match: type over USB to one machine, switch, and beam keystrokes wirelessly to a laptop across the room.

---

## Feature Highlights

- **4-port instant switching** — dedicated selector buttons with LED confirmation; every computer stays USB-connected at all times, with zero warm-up delay when you switch.
- **Wired or wireless input** — accept keystrokes from a physical USB keyboard *or* any Bluetooth keyboard; toggle the active source with a single button press, or long-press to pair a new wireless keyboard on the fly.
- **USB and Bluetooth output** — relay input via dedicated CH552T HID devices over USB *or* turn the Pi itself into a Bluetooth keyboard for cable-free control; per-computer output mode persists across reboots.
- **Browser-based control panel** — a built-in web UI at `http://<pi-ip>:8080` lets you switch computers and toggle input/output modes from any phone, tablet, or browser on your network, no app required.
- **Optional touchscreen display** — a local tkinter GUI (`display.py`) runs on any Pi-compatible touchscreen for at-a-glance tally lights and one-tap switching, with a built-in ZSA Keymapp launcher for ZSA keyboard users.
- **Programmable HID macros** — map keystroke sequences (lock screen, screenshot, Ctrl+C/V, custom combos) to button short- or long-press actions via a plain Python config file.
- **Nothing to install on target computers** — each CH552T enumerates as a standard USB HID keyboard and mouse; the Pi's Bluetooth output appears as a standard wireless keyboard. Your computers never know it is a proxy.
- **Fully open-source and hackable** — Python daemon with a clean producer-consumer architecture; add new input sources or output sinks in a few lines of code.

---

## Use-Case Scenarios

### The Multi-Machine Developer

You have a beefy workstation on the left, a work laptop docked to the right, and a headless server sitting in the rack underneath. You want a single ergonomic keyboard across all three — no USB unplugging, no KVM lag, no extra software on the laptop you don't own. HIDProxBox sits in the middle: press button 1 for the workstation, button 2 for the laptop (Bluetooth, so it's still on the docking station's USB ports), and hold a button to SSH macros straight into the server. Every switch is instant, every machine thinks it has a dedicated keyboard.

### The Clean-Desk Home Office

Your personal Mac sits beside your company-issued Windows PC. You've tried software KVMs — they break after updates, they need admin rights, and your company's IT policy won't allow them. HIDProxBox is purely hardware from the target computers' perspective. Both machines are always plugged in, always ready. One physical button (or a tap on the web panel from your phone) hands input from one to the other. Toggle Bluetooth output and your Mac never needs a USB cable at all.

### The Maker Workbench

You're building and flashing firmware across a Pi, an STM32 discovery board, and an x86 test machine — all headless, all needing occasional keyboard input for setup and logs. HIDProxBox lives on a shelf, wired into all three. Pair your Bluetooth mechanical keyboard as the input source so there's no cable to knock loose. Add a couple of macro buttons to automate your most-used debug commands. Connect the optional touchscreen to the front of your project enclosure for a clean, self-contained control panel. Build it once, reuse it forever.

---

## Marketing One-Pager

> *Suitable for GitHub project description, Hackaday project page, Reddit r/raspberry_pi, or Hacker News Show HN.*

---

### HIDProxBox

**One keyboard. Four computers. Zero software on the targets.**

HIDProxBox is a DIY Raspberry Pi KVM proxy that routes keyboard and mouse input to up to four computers over USB or Bluetooth — no drivers, no agents, nothing to install on the machines you control.

#### How it works

A Python daemon on the Pi sits at the centre of a thread-based producer-consumer pipeline. Input arrives from a wired USB keyboard (via Linux evdev) or any Bluetooth keyboard. The daemon's Router dispatches each HID report to the active computer through one of four CH552T microcontrollers (one per computer, each presenting as a standard USB HID device) or via Bluetooth if you prefer wireless output.

Switch targets with a physical button, a tap on the built-in web control panel (`http://<pi-ip>:8080`), or the optional local touchscreen GUI. LED indicators confirm the active computer and input/output modes at a glance.

#### Key capabilities

| Feature | Detail |
|---------|--------|
| Computers supported | Up to 4 |
| Input sources | USB keyboard (evdev) or Bluetooth HID |
| Output paths | USB via CH552T HID devices or Bluetooth (Pi as BT keyboard) |
| Control | Physical buttons, web browser, or optional touchscreen |
| Pairing | Long-press to pair a BT keyboard in; long-press to pair Pi out |
| Macros | Configurable HID keystroke sequences on button actions |
| Config | Single `config.py` — ports, GPIO pins, macros, timeouts |
| Footprint | Runs on Raspberry Pi Zero 2W or Pi 4 |

#### Why HIDProxBox?

Commercial KVMs only switch USB cables. Software KVMs require agents on every machine. HIDProxBox is the middle path: real hardware-level HID switching, open-source firmware, and a clean Python codebase you can extend in an afternoon.

- **No target software** — works with air-gapped machines, locked-down corporate laptops, and everything in between.
- **Dual input** — wired and wireless keyboard support in the same box; toggle with one button.
- **Dual output** — switch between USB and Bluetooth output per computer, with pairing state persisted across reboots.
- **Web + physical control** — switch from your phone when you're not at your desk.
- **Hackable by design** — add a new input source (foot pedal? stream deck?) in a few dozen lines of Python. New output sink? Same pattern.

#### Bill of materials (approx.)

| Item | Qty | Approx. cost |
|------|-----|-------------|
| Raspberry Pi Zero 2W or Pi 4 | 1 | $15–$55 |
| CH552T microcontrollers | 4 | < $1 each |
| USB-serial adapters (CP2102/CH340) | 4 | ~$1–$2 each |
| Tactile buttons + LEDs + resistors | — | < $5 |
| Optional Pi touchscreen (3.5–7″) | 1 | $15–$30 |

Total hardware cost: **under $100** for a full 4-port build.

#### Get started

```bash
git clone https://github.com/andycrawford/HIDProxBox.git /opt/hidproxbox
pip3 install evdev pyserial pybluez --break-system-packages
sudo python3 /opt/hidproxbox/daemon.py --foreground
```

Flash the same Arduino sketch to each CH552T, wire the buttons and LEDs to GPIO, and you're switching computers in an afternoon.

**License:** MIT — build it, fork it, sell it, improve it.

---

*HIDProxBox is an open-source project. Contributions, issues, and hardware build logs are welcome.*
