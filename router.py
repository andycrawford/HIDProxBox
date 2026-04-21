"""
router.py — Central routing / state machine

Maintains the three key state variables:
  active_computer  (1–4)   which computer receives HID output
  input_mode       usb|bt  which keyboard is the active input source
  output_mode      usb|bt  how reports reach the active computer

All input sources (USB keyboard, BT keyboard, GPIO macros) push
(source, ReportType, bytes) tuples to Router.report_queue.

The Router's dispatch thread filters by input_mode and forwards to
either the USB sink (HIDWriter) or the BT sink (BTOutput).

State change callbacks let gpio_watcher.py update LEDs instantly.
"""

import enum
import logging
import queue
import threading
from typing import Callable, Optional

import config

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────

class InputMode(str, enum.Enum):
    USB       = "usb"
    BLUETOOTH = "bluetooth"


class OutputMode(str, enum.Enum):
    USB       = "usb"
    BLUETOOTH = "bluetooth"


# Source labels used by input threads when pushing to report_queue
SOURCE_USB = "usb"
SOURCE_BT  = "bluetooth"
SOURCE_GPIO = "gpio"    # GPIO macros always pass through regardless of input_mode


# ─────────────────────────────────────────────────────────────────────────────

class Router(threading.Thread):
    """
    Drains report_queue and routes reports to the correct output sink
    based on the current state (active_computer, input_mode, output_mode).

    Sinks are set after construction:
      router.set_usb_sink(callable(computer_id, report_type, data))
      router.set_bt_sink(callable(report_type, data))
    """

    def __init__(self) -> None:
        super().__init__(name="router", daemon=True)
        self._lock  = threading.Lock()
        self._stop  = threading.Event()

        # ── mutable state (always access under _lock) ─────────────────────────
        self._active_computer : int        = 1
        self._input_mode      : InputMode  = InputMode.USB
        self._output_mode     : OutputMode = OutputMode.USB

        # ── shared queue all input sources push into ──────────────────────────
        self.report_queue: queue.Queue = queue.Queue(maxsize=config.REPORT_QUEUE_SIZE)

        # ── output sinks (set from daemon.py after construction) ──────────────
        self._usb_sink: Optional[Callable] = None   # (computer_id, rtype, data)
        self._bt_sink : Optional[Callable] = None   # (rtype, data)

        # ── state-change callback (used by GPIOWatcher to update LEDs) ────────
        self._on_state_change: Optional[Callable] = None

    # ── sink wiring ───────────────────────────────────────────────────────────

    def set_usb_sink(self, sink: Callable) -> None:
        """sink(computer_id: int, report_type: ReportType, data: bytes)"""
        self._usb_sink = sink

    def set_bt_sink(self, sink: Callable) -> None:
        """sink(report_type: ReportType, data: bytes)"""
        self._bt_sink = sink

    def set_on_state_change(self, cb: Callable) -> None:
        """cb(active_computer, input_mode, output_mode) — called on any state change."""
        self._on_state_change = cb

    # ── state accessors ───────────────────────────────────────────────────────

    @property
    def active_computer(self) -> int:
        with self._lock:
            return self._active_computer

    @property
    def input_mode(self) -> InputMode:
        with self._lock:
            return self._input_mode

    @property
    def output_mode(self) -> OutputMode:
        with self._lock:
            return self._output_mode

    # ── state mutators ────────────────────────────────────────────────────────

    def select_computer(self, n: int) -> None:
        """Switch active output target to computer n (1–4)."""
        if n not in config.COMPUTERS:
            log.warning("select_computer: invalid computer id %d", n)
            return
        with self._lock:
            if self._active_computer == n:
                return
            old = self._active_computer
            self._active_computer = n
        log.info("Active computer: %d → %d", old, n)
        self._notify()

    def set_input_mode(self, mode: InputMode) -> None:
        """Switch active keyboard input source."""
        with self._lock:
            if self._input_mode == mode:
                return
            self._input_mode = mode
        log.info("Input mode: %s", mode.value)
        self._notify()

    def toggle_input(self) -> None:
        with self._lock:
            new = InputMode.BLUETOOTH if self._input_mode == InputMode.USB else InputMode.USB
            self._input_mode = new
        log.info("Input mode toggled → %s", new.value)
        self._notify()

    def set_output_mode(self, mode: OutputMode) -> None:
        """Switch output delivery method for the active computer."""
        with self._lock:
            if self._output_mode == mode:
                return
            self._output_mode = mode
        log.info("Output mode: %s", mode.value)
        self._notify()

    def toggle_output(self) -> None:
        with self._lock:
            new = OutputMode.BLUETOOTH if self._output_mode == OutputMode.USB else OutputMode.USB
            self._output_mode = new
        log.info("Output mode toggled → %s", new.value)
        self._notify()

    def snapshot(self) -> tuple:
        """Return (active_computer, input_mode, output_mode) atomically."""
        with self._lock:
            return (self._active_computer, self._input_mode, self._output_mode)

    # ── dispatch loop ─────────────────────────────────────────────────────────

    def run(self) -> None:
        log.info("Router dispatch loop started.")
        while not self._stop.is_set():
            try:
                source, report_type, data = self.report_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self._dispatch(source, report_type, data)
            except Exception as exc:
                log.error("Router dispatch error: %s", exc)
            finally:
                self.report_queue.task_done()

    def stop(self) -> None:
        self._stop.set()
        self.join(timeout=3)

    # ── internal dispatch ─────────────────────────────────────────────────────

    def _dispatch(self, source: str, report_type, data: bytes) -> None:
        with self._lock:
            computer  = self._active_computer
            inp_mode  = self._input_mode
            out_mode  = self._output_mode

        # GPIO macros bypass the input_mode filter (always pass through)
        if source == SOURCE_BT  and inp_mode != InputMode.BLUETOOTH:
            return
        if source == SOURCE_USB and inp_mode != InputMode.USB:
            return

        if out_mode == OutputMode.USB:
            if self._usb_sink:
                self._usb_sink(computer, report_type, data)
        else:
            if self._bt_sink:
                self._bt_sink(report_type, data)

    # ── notification ──────────────────────────────────────────────────────────

    def _notify(self) -> None:
        if self._on_state_change:
            try:
                self._on_state_change(*self.snapshot())
            except Exception as exc:
                log.warning("State-change callback error: %s", exc)
