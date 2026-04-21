"""
daemon.py — HIDProxBox main daemon

Wires all subsystems together:

  Router          — central state machine + dispatch queue consumer
  HIDWriter       — 4× CH552T USB output (one per computer)
  BTOutput        — Pi as BT keyboard device (output to computers)
  BTListener      — BT keyboard input (upstream keyboard → Pi)
  USBKeyboard     — physical USB keyboard input via evdev
  GPIOWatcher     — buttons + LEDs

Data flow:
  USBKeyboard  ──┐
  BTListener   ──┼──► Router.report_queue ──► Router dispatch ──► HIDWriter  (USB out)
  GPIO macros  ──┘                                             └──► BTOutput  (BT out)

Usage
─────
  sudo python3 daemon.py [--foreground]

Systemd unit (example)
──────────────────────
  [Unit]
  Description=HIDProxBox
  After=network.target bluetooth.target

  [Service]
  Type=simple
  ExecStartPre=/usr/bin/bash /opt/hidproxbox/gadget_setup.sh up
  ExecStart=/usr/bin/python3 /opt/hidproxbox/daemon.py --foreground
  ExecStopPost=/usr/bin/bash /opt/hidproxbox/gadget_setup.sh down
  Restart=on-failure
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
"""

import argparse
import logging
import logging.handlers
import os
import signal
import sys
import threading
import time

import config
from router import Router, InputMode, OutputMode, SOURCE_GPIO
from hid_writer import HIDWriter, ReportType
from gpio_watcher import GPIOWatcher
from bt_listener import BTListener
from bt_output import BTOutput
from usb_kbd import USBKeyboard


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

def _setup_logging(foreground: bool) -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)-16s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        fh = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError as exc:
        print(f"[daemon] WARNING: cannot open log file: {exc}", file=sys.stderr)

    if foreground or config.LOG_TO_CONSOLE:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        root.addHandler(sh)


# ─────────────────────────────────────────────────────────────────────────────
# PID file
# ─────────────────────────────────────────────────────────────────────────────

def _write_pid() -> None:
    try:
        with open(config.PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except OSError as exc:
        logging.getLogger(__name__).warning("Cannot write PID file: %s", exc)


def _remove_pid() -> None:
    try:
        os.remove(config.PID_FILE)
    except OSError:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Daemon
# ─────────────────────────────────────────────────────────────────────────────

class HIDProxDaemon:

    def __init__(self) -> None:
        self._log        = logging.getLogger("daemon")
        self._stop_event = threading.Event()

        # ── Core components ───────────────────────────────────────────────────
        self._router  = Router()
        self._writer  = HIDWriter()
        self._bt_out  = BTOutput()
        self._bt_in   = BTListener(self._router.report_queue)
        self._usb_kbd = USBKeyboard(self._router.report_queue)
        self._gpio    = GPIOWatcher(self._router)

        # Attach back-references so GPIOWatcher can trigger pairing operations
        self._router._bt_listener = self._bt_in
        self._router._bt_output   = self._bt_out

    # ── entry point ───────────────────────────────────────────────────────────

    def run(self) -> int:
        self._log.info("=" * 64)
        self._log.info("HIDProxBox starting  (pid %d)", os.getpid())
        self._log.info("  Computers : %s", list(config.COMPUTERS.keys()))
        self._log.info("  Buttons   : %d configured", len(config.BUTTON_MAP))
        self._log.info("  LEDs      : %d configured", len(config.LED_PINS))
        self._log.info("=" * 64)

        _write_pid()
        self._install_signals()
        self._start_all()

        code = self._watchdog_loop()

        self._stop_all()
        _remove_pid()
        self._log.info("HIDProxBox exited (code %d).", code)
        return code

    # ── signal handling ───────────────────────────────────────────────────────

    def _install_signals(self) -> None:
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_signal)
        signal.signal(signal.SIGHUP, lambda *_: self._log.info("SIGHUP — reload not implemented."))

    def _handle_signal(self, signum: int, _frame) -> None:
        self._log.info("Signal %s received — shutting down.", signal.Signals(signum).name)
        self._stop_event.set()

    # ── startup ───────────────────────────────────────────────────────────────

    def _start_all(self) -> None:
        # 1. Open CH552T serial ports
        self._log.info("Opening CH552T serial links…")
        self._writer.open()

        # 2. Wire Router sinks
        self._router.set_usb_sink(self._writer.write)
        self._router.set_bt_sink(self._bt_out.send)

        # 3. Hook Router state changes → BTOutput slot tracking
        _orig_notify = self._router._notify

        def _notify_with_bt(*args, **kwargs):
            _orig_notify(*args, **kwargs)
            computer, _, out_mode = self._router.snapshot()
            if out_mode == OutputMode.BLUETOOTH:
                self._bt_out.set_active_slot(computer)

        self._router._notify = _notify_with_bt

        # 4. Start threads (order: router first, then sources, then GPIO)
        self._log.info("Starting Router…")
        self._router.start()

        self._log.info("Starting BTOutput…")
        self._bt_out.start()

        self._log.info("Starting BTListener (keyboard input)…")
        self._bt_in.start()

        self._log.info("Starting USBKeyboard…")
        self._usb_kbd.start()

        self._log.info("Starting GPIOWatcher…")
        self._gpio.start()

        self._log.info("All subsystems started.")

    # ── shutdown ──────────────────────────────────────────────────────────────

    def _stop_all(self) -> None:
        self._log.info("Stopping subsystems…")
        self._gpio.stop()
        self._usb_kbd.stop()
        self._bt_in.stop()
        self._bt_out.stop()
        self._router.stop()
        self._writer.close()
        self._log.info("All subsystems stopped.")

    # ── watchdog loop ─────────────────────────────────────────────────────────

    def _watchdog_loop(self) -> int:
        self._log.info("Watchdog running (%.1fs interval).", config.WATCHDOG_INTERVAL_S)

        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=config.WATCHDOG_INTERVAL_S)
            if self._stop_event.is_set():
                break

            # Router is critical — restart if dead
            if not self._router.is_alive():
                self._log.error("Router thread died — restarting.")
                try:
                    self._router = Router()
                    self._router.set_usb_sink(self._writer.write)
                    self._router.set_bt_sink(self._bt_out.send)
                    self._router.start()
                    # Re-wire GPIO
                    self._gpio._router = self._router
                    self._router.set_on_state_change(self._gpio._on_state_change)
                except Exception as exc:
                    self._log.critical("Cannot restart Router: %s", exc)
                    return 1

            # Log a brief status line every 60 s
            if int(time.monotonic()) % 60 == 0:
                computer, inp, out = self._router.snapshot()
                self._log.debug(
                    "Status: computer=%d  input=%s  output=%s  queue=%d",
                    computer, inp.value, out.value,
                    self._router.report_queue.qsize(),
                )

        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="HIDProxBox daemon")
    parser.add_argument(
        "--foreground", "-f",
        action="store_true",
        help="Log to stderr and skip log-file rotation (useful with systemd).",
    )
    args = parser.parse_args()
    _setup_logging(foreground=args.foreground)
    sys.exit(HIDProxDaemon().run())


if __name__ == "__main__":
    main()
