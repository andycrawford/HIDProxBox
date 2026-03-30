"""
gpio_watcher.py — Physical button watcher with short/long press detection

Monitors all buttons defined in config.BUTTON_MAP.  Each button supports:
  • Short press  (< LONG_PRESS_S):  fires "short" action
  • Long press   (≥ LONG_PRESS_S):  fires "long"  action

All buttons are active-low (press pulls pin to GND via momentary switch;
internal pull-up keeps pin HIGH at rest).

Button layout (BCM pins, from config.py)
─────────────────────────────────────────
  Pin  4  — Computer 1  (short & long)
  Pin 17  — Computer 2  (short & long)
  Pin 27  — Computer 3  (short & long)
  Pin 22  — Computer 4  (short & long)
  Pin  5  — BT keyboard  short=toggle USB↔BT input   long=pair BT keyboard
  Pin  6  — BT output    short=toggle USB↔BT output   long=pair Pi to computer

LED feedback
─────────────
  GPIOWatcher subscribes to Router.set_on_state_change() so it can
  update the indicator LEDs immediately whenever routing state changes.

Long-press approach
────────────────────
  We use RPi.GPIO BOTH-edge detection.
  FALLING  → record press_start time for that pin.
  RISING   → compute duration; dispatch short or long action.
"""

import logging
import time
import threading
from typing import Dict, Optional

import config

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────

class GPIOWatcher(threading.Thread):

    def __init__(self, router) -> None:
        """
        router : router.Router instance
        """
        super().__init__(name="gpio-watcher", daemon=True)
        self._router     = router
        self._stop       = threading.Event()
        self._gpio       = None
        self._press_time : Dict[int, float] = {}   # pin → press start monotonic time
        self._press_lock = threading.Lock()

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if not config.GPIO_ENABLED:
            log.info("GPIOWatcher disabled in config.")
            return
        try:
            import RPi.GPIO as GPIO
            self._gpio = GPIO
        except (ImportError, RuntimeError) as exc:
            log.warning("RPi.GPIO unavailable: %s — GPIO watcher disabled.", exc)
            return

        self._setup_gpio()

        # Subscribe to state changes so we can update LEDs
        self._router.set_on_state_change(self._on_state_change)

        super().start()
        log.info("GPIOWatcher started; %d button(s) active.", len(config.BUTTON_MAP))

        # Initial LED state
        self._on_state_change(*self._router.snapshot())

    def stop(self) -> None:
        self._stop.set()
        self.join(timeout=3)
        if self._gpio:
            try:
                self._gpio.cleanup()
            except Exception:
                pass
        log.info("GPIOWatcher stopped.")

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        # Callbacks fire in RPi.GPIO's internal thread.
        # This thread just keeps the watcher alive and handles long-press
        # timeouts (fires the long-press action while button is still held).
        while not self._stop.is_set():
            now = time.monotonic()
            with self._press_lock:
                for pin, start_t in list(self._press_time.items()):
                    held = now - start_t
                    if held >= config.LONG_PRESS_S:
                        # Fire long press now (don't wait for release) and
                        # remove from tracking so we don't fire again.
                        del self._press_time[pin]
                        threading.Thread(
                            target=self._fire_action,
                            args=(pin, "long"),
                            daemon=True,
                        ).start()
            time.sleep(0.05)   # 50 ms poll

    # ── GPIO setup ────────────────────────────────────────────────────────────

    def _setup_gpio(self) -> None:
        GPIO = self._gpio
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # ── Button pins ───────────────────────────────────────────────────────
        for pin in config.BUTTON_MAP:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            def _make_cb(p):
                def _cb(channel):
                    self._button_event(p)
                return _cb

            GPIO.add_event_detect(
                pin,
                GPIO.BOTH,
                callback=_make_cb(pin),
                bouncetime=config.GPIO_BOUNCE_MS,
            )
            log.debug("GPIO button pin %d registered.", pin)

        # ── LED pins ──────────────────────────────────────────────────────────
        for name, pin in config.LED_PINS.items():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            log.debug("GPIO LED '%s' on pin %d.", name, pin)

    # ── edge callback (fires in RPi.GPIO thread) ──────────────────────────────

    def _button_event(self, pin: int) -> None:
        GPIO = self._gpio
        level = GPIO.input(pin)   # 0 = pressed (LOW), 1 = released (HIGH)

        if level == 0:
            # Button pressed — record time
            with self._press_lock:
                self._press_time[pin] = time.monotonic()
        else:
            # Button released — check if we already fired (long press)
            with self._press_lock:
                start_t = self._press_time.pop(pin, None)

            if start_t is None:
                return   # already fired as long press

            duration = time.monotonic() - start_t
            action_type = "long" if duration >= config.LONG_PRESS_S else "short"
            threading.Thread(
                target=self._fire_action,
                args=(pin, action_type),
                daemon=True,
            ).start()

    # ── action dispatch ───────────────────────────────────────────────────────

    def _fire_action(self, pin: int, press_type: str) -> None:
        btn_cfg = config.BUTTON_MAP.get(pin)
        if not btn_cfg:
            return
        action = btn_cfg.get(press_type)
        if not action:
            return

        log.info("Button pin %d %s-press → action '%s'", pin, press_type, action)

        r = self._router

        # ── computer select ───────────────────────────────────────────────────
        if action.startswith("select_computer_"):
            slot = int(action[-1])
            r.select_computer(slot)

        elif action == "toggle_input":
            r.toggle_input()

        elif action == "input_usb":
            from router import InputMode
            r.set_input_mode(InputMode.USB)

        elif action == "input_bt":
            from router import InputMode
            r.set_input_mode(InputMode.BLUETOOTH)

        elif action == "toggle_output":
            r.toggle_output()
            # If switching to BT, ensure connection for active computer
            from router import OutputMode
            if r.output_mode == OutputMode.BLUETOOTH:
                self._trigger_bt_connect(r.active_computer)

        elif action == "output_usb":
            from router import OutputMode
            r.set_output_mode(OutputMode.USB)

        elif action == "output_bt":
            from router import OutputMode
            r.set_output_mode(OutputMode.BLUETOOTH)
            self._trigger_bt_connect(r.active_computer)

        elif action == "pair_bt_keyboard":
            self._trigger_bt_input_pair()

        elif action == "pair_bt_output":
            self._trigger_bt_output_pair(r.active_computer)

        else:
            log.warning("Unknown GPIO action: '%s'", action)

    # ── BT operation triggers ─────────────────────────────────────────────────

    def _trigger_bt_input_pair(self) -> None:
        """Start BT keyboard (input) pairing in a background thread."""
        from bt_listener import BTListener
        bt = getattr(self._router, "_bt_listener", None)
        if bt:
            log.info("GPIOWatcher: requesting BT keyboard pairing scan.")
            threading.Thread(target=bt.scan_and_pair, daemon=True).start()
        else:
            log.warning("GPIOWatcher: no BTListener reference for pairing.")

    def _trigger_bt_output_pair(self, slot: int) -> None:
        """Start BT output pairing (Pi as keyboard) for computer slot."""
        bt_out = getattr(self._router, "_bt_output", None)
        if bt_out:
            log.info("GPIOWatcher: starting BT output pairing for slot %d.", slot)
            threading.Thread(
                target=bt_out.pair_to_computer,
                args=(slot,),
                daemon=True,
            ).start()
        else:
            log.warning("GPIOWatcher: no BTOutput reference for pairing.")

    def _trigger_bt_connect(self, slot: int) -> None:
        bt_out = getattr(self._router, "_bt_output", None)
        if bt_out:
            bt_out.set_active_slot(slot)

    # ── LED update ────────────────────────────────────────────────────────────

    def _on_state_change(self, active_computer: int, input_mode, output_mode) -> None:
        """Called by Router whenever state changes — update all indicator LEDs."""
        if not self._gpio:
            return

        GPIO = self._gpio
        from router import InputMode, OutputMode

        try:
            # Computer select LEDs
            for slot in range(1, 5):
                pin = config.LED_PINS.get(f"computer_{slot}")
                if pin is not None:
                    GPIO.output(pin, GPIO.HIGH if slot == active_computer else GPIO.LOW)

            # Input mode LED
            pin_in = config.LED_PINS.get("input_bt")
            if pin_in is not None:
                GPIO.output(pin_in, GPIO.HIGH if input_mode == InputMode.BLUETOOTH else GPIO.LOW)

            # Output mode LED
            pin_out = config.LED_PINS.get("output_bt")
            if pin_out is not None:
                GPIO.output(pin_out, GPIO.HIGH if output_mode == OutputMode.BLUETOOTH else GPIO.LOW)

        except Exception as exc:
            log.warning("GPIOWatcher: LED update error: %s", exc)
