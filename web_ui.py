"""
web_ui.py — Lightweight HTTP server for HIDProxBox control

Exposes:
  GET  /              → HTML control panel
  GET  /api/status    → JSON {active_computer, input_mode, output_mode}
  POST /api/computer/<n>       → select computer n (1–4)
  POST /api/input/toggle       → toggle input mode
  POST /api/output/toggle      → toggle output mode
  POST /api/paste              → JSON {"text":"…"} → send as keystrokes

Runs in a daemon thread started by daemon.py.
No third-party dependencies — uses only stdlib http.server.
"""

import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

import config
from router import Router

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# HID keycode map — US ANSI layout
# ─────────────────────────────────────────────────────────────────────────────
# Maps printable characters to (hid_keycode, modifier_byte).
# modifier 0x02 = Left Shift.  Only US ANSI layout is supported.
# Reference: USB HID Usage Tables 1.21, §10 Keyboard/Keypad page.
#
# Used by Router.type_text() to build 8-byte keyboard reports:
#   [modifier, 0x00, keycode, 0x00, 0x00, 0x00, 0x00, 0x00]
# Each character requires a key-down report followed by a key-up report
# (all zeros) to register as a single keystroke.
CHAR_MAP: dict[str, tuple[int, int]] = {
    # ── lowercase letters ────────────────────────────────────────────────────
    'a': (0x04, 0), 'b': (0x05, 0), 'c': (0x06, 0), 'd': (0x07, 0),
    'e': (0x08, 0), 'f': (0x09, 0), 'g': (0x0A, 0), 'h': (0x0B, 0),
    'i': (0x0C, 0), 'j': (0x0D, 0), 'k': (0x0E, 0), 'l': (0x0F, 0),
    'm': (0x10, 0), 'n': (0x11, 0), 'o': (0x12, 0), 'p': (0x13, 0),
    'q': (0x14, 0), 'r': (0x15, 0), 's': (0x16, 0), 't': (0x17, 0),
    'u': (0x18, 0), 'v': (0x19, 0), 'w': (0x1A, 0), 'x': (0x1B, 0),
    'y': (0x1C, 0), 'z': (0x1D, 0),
    # ── uppercase letters (Left Shift) ───────────────────────────────────────
    'A': (0x04, 0x02), 'B': (0x05, 0x02), 'C': (0x06, 0x02), 'D': (0x07, 0x02),
    'E': (0x08, 0x02), 'F': (0x09, 0x02), 'G': (0x0A, 0x02), 'H': (0x0B, 0x02),
    'I': (0x0C, 0x02), 'J': (0x0D, 0x02), 'K': (0x0E, 0x02), 'L': (0x0F, 0x02),
    'M': (0x10, 0x02), 'N': (0x11, 0x02), 'O': (0x12, 0x02), 'P': (0x13, 0x02),
    'Q': (0x14, 0x02), 'R': (0x15, 0x02), 'S': (0x16, 0x02), 'T': (0x17, 0x02),
    'U': (0x18, 0x02), 'V': (0x19, 0x02), 'W': (0x1A, 0x02), 'X': (0x1B, 0x02),
    'Y': (0x1C, 0x02), 'Z': (0x1D, 0x02),
    # ── digits ───────────────────────────────────────────────────────────────
    '1': (0x1E, 0), '2': (0x1F, 0), '3': (0x20, 0), '4': (0x21, 0),
    '5': (0x22, 0), '6': (0x23, 0), '7': (0x24, 0), '8': (0x25, 0),
    '9': (0x26, 0), '0': (0x27, 0),
    # ── shifted digits ───────────────────────────────────────────────────────
    '!': (0x1E, 0x02), '@': (0x1F, 0x02), '#': (0x20, 0x02), '$': (0x21, 0x02),
    '%': (0x22, 0x02), '^': (0x23, 0x02), '&': (0x24, 0x02), '*': (0x25, 0x02),
    '(': (0x26, 0x02), ')': (0x27, 0x02),
    # ── whitespace / control ─────────────────────────────────────────────────
    '\n': (0x28, 0), '\t': (0x2B, 0), ' ': (0x2C, 0),
    # ── punctuation (unshifted) ──────────────────────────────────────────────
    '-': (0x2D, 0), '=': (0x2E, 0), '[': (0x2F, 0), ']': (0x30, 0),
    '\\': (0x31, 0), ';': (0x33, 0), "'": (0x34, 0), '`': (0x35, 0),
    ',': (0x36, 0), '.': (0x37, 0), '/': (0x38, 0),
    # ── punctuation (shifted) ────────────────────────────────────────────────
    '_': (0x2D, 0x02), '+': (0x2E, 0x02), '{': (0x2F, 0x02), '}': (0x30, 0x02),
    '|': (0x31, 0x02), ':': (0x33, 0x02), '"': (0x34, 0x02), '~': (0x35, 0x02),
    '<': (0x36, 0x02), '>': (0x37, 0x02), '?': (0x38, 0x02),
}

# Safety limit: reject requests longer than this to avoid locking up the HID pipeline.
PASTE_TEXT_LIMIT = 2000

# ─────────────────────────────────────────────────────────────────────────────
# Embedded HTML frontend
# ─────────────────────────────────────────────────────────────────────────────

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HIDProxBox</title>
<style>
  :root {
    --bg: #1a1a2e; --card: #16213e; --accent: #0f3460;
    --active: #e94560; --text: #eaeaea; --muted: #888;
    --radius: 10px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--text);
    font-family: system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column;
    align-items: center; padding: 24px 16px;
  }
  h1 { font-size: 1.5rem; margin-bottom: 6px; letter-spacing: 1px; }
  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 28px; }
  .card {
    background: var(--card); border-radius: var(--radius);
    padding: 20px; width: 100%; max-width: 420px; margin-bottom: 16px;
  }
  .card h2 { font-size: 0.75rem; text-transform: uppercase;
    letter-spacing: 1px; color: var(--muted); margin-bottom: 14px; }
  .computers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .btn {
    background: var(--accent); border: 2px solid transparent;
    color: var(--text); border-radius: var(--radius);
    padding: 14px 8px; font-size: 1rem; font-weight: 600;
    cursor: pointer; transition: background 0.15s, border-color 0.15s;
    width: 100%;
  }
  .btn:hover { filter: brightness(1.2); }
  .btn.active { background: var(--active); border-color: #fff4; }
  .btn.wide { width: 100%; padding: 14px; margin-top: 10px; font-size: 0.95rem; }
  .modes { display: flex; gap: 10px; }
  .modes .btn { flex: 1; }
  .status-line {
    display: flex; justify-content: space-between;
    font-size: 0.8rem; color: var(--muted); margin-top: 16px;
  }
  #dot { display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: #4caf50; margin-right: 6px; }
  #dot.stale { background: #f44336; }
  .paste-area {
    width: 100%; background: var(--accent); color: var(--text);
    border: 1px solid #ffffff22; border-radius: var(--radius);
    padding: 10px; font-size: 0.9rem; font-family: monospace;
    resize: vertical; outline: none; margin-bottom: 0;
  }
  .paste-area:focus { border-color: #ffffff55; }
  #paste-status { font-size: 0.8rem; margin-top: 8px; min-height: 1.2em; color: var(--muted); }
</style>
</head>
<body>
<h1>HIDProxBox</h1>
<p class="subtitle">KVM Control Panel</p>

<div class="card">
  <h2>Active Computer</h2>
  <div class="computers">
    <button class="btn" id="c1" onclick="selectComputer(1)">1</button>
    <button class="btn" id="c2" onclick="selectComputer(2)">2</button>
    <button class="btn" id="c3" onclick="selectComputer(3)">3</button>
    <button class="btn" id="c4" onclick="selectComputer(4)">4</button>
  </div>
</div>

<div class="card">
  <h2>Input Mode</h2>
  <div class="modes">
    <button class="btn" id="input-usb">USB</button>
    <button class="btn" id="input-bt">Bluetooth</button>
  </div>
  <button class="btn wide" onclick="toggleInput()">Toggle Input</button>
</div>

<div class="card">
  <h2>Output Mode</h2>
  <div class="modes">
    <button class="btn" id="output-usb">USB</button>
    <button class="btn" id="output-bt">Bluetooth</button>
  </div>
  <button class="btn wide" onclick="toggleOutput()">Toggle Output</button>
</div>

<div class="card">
  <h2>Paste Text</h2>
  <textarea class="paste-area" id="paste-input" rows="4"
    placeholder="Paste text here to send as keystrokes to the active computer…"></textarea>
  <button class="btn wide" id="paste-btn" onclick="sendPaste()">Send as Keystrokes</button>
  <div id="paste-status"></div>
</div>

<div class="status-line">
  <span><span id="dot"></span><span id="conn">connecting…</span></span>
  <span id="ts"></span>
</div>

<script>
let lastOk = Date.now();

function apiFetch(path, method='GET') {
  return fetch(path, { method }).then(r => r.json());
}

function selectComputer(n) {
  apiFetch('/api/computer/' + n, 'POST').then(applyState);
}
function toggleInput()  { apiFetch('/api/input/toggle',  'POST').then(applyState); }
function toggleOutput() { apiFetch('/api/output/toggle', 'POST').then(applyState); }

function applyState(s) {
  lastOk = Date.now();
  document.getElementById('dot').className = '';
  document.getElementById('conn').textContent = 'connected';
  document.getElementById('ts').textContent = new Date().toLocaleTimeString();

  [1,2,3,4].forEach(n => {
    document.getElementById('c'+n).className =
      'btn' + (n === s.active_computer ? ' active' : '');
  });

  const inBt = s.input_mode === 'bluetooth';
  document.getElementById('input-usb').className = 'btn' + (inBt ? '' : ' active');
  document.getElementById('input-bt').className  = 'btn' + (inBt ? ' active' : '');

  const outBt = s.output_mode === 'bluetooth';
  document.getElementById('output-usb').className = 'btn' + (outBt ? '' : ' active');
  document.getElementById('output-bt').className  = 'btn' + (outBt ? ' active' : '');
}

function poll() {
  apiFetch('/api/status').then(applyState).catch(() => {
    if (Date.now() - lastOk > 3000) {
      document.getElementById('dot').className = 'stale';
      document.getElementById('conn').textContent = 'disconnected';
    }
  });
}

function sendPaste() {
  const text = document.getElementById('paste-input').value;
  if (!text) return;
  const btn = document.getElementById('paste-btn');
  const status = document.getElementById('paste-status');
  btn.disabled = true;
  btn.textContent = 'Sending\u2026';
  status.textContent = '';
  status.style.color = 'var(--muted)';
  fetch('/api/paste', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text}),
  })
    .then(r => r.json())
    .then(d => {
      if (d.error) {
        status.textContent = '\u2717 ' + d.error;
        status.style.color = 'var(--active)';
      } else {
        const skipped = d.skipped ? ` (${d.skipped} char${d.skipped !== 1 ? 's' : ''} skipped)` : '';
        status.textContent = `\u2713 Sent ${d.sent} char${d.sent !== 1 ? 's' : ''}` + skipped;
        status.style.color = '#4caf50';
      }
    })
    .catch(() => {
      status.textContent = '\u2717 Request failed';
      status.style.color = 'var(--active)';
    })
    .finally(() => {
      btn.disabled = false;
      btn.textContent = 'Send as Keystrokes';
    });
}

poll();
setInterval(poll, 1000);
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Request handler
# ─────────────────────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    """HTTP handler; router reference injected via server.router."""

    # Silence default access logging — daemon.py owns the log
    def log_message(self, fmt, *args):  # noqa: N802
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Optional[dict]:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return None
        try:
            raw = self.rfile.read(length)
            return json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return None

    def _state_json(self) -> dict:
        router: Router = self.server.router
        computer, inp, out = router.snapshot()
        return {
            "active_computer": computer,
            "input_mode": inp.value,
            "output_mode": out.value,
        }

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send_html(_HTML)
        elif self.path == "/api/status":
            self._send_json(self._state_json())
        else:
            self.send_error(404)

    def do_POST(self):  # noqa: N802
        router: Router = self.server.router
        path = self.path.rstrip("/")

        m = re.fullmatch(r"/api/computer/([1-4])", path)
        if m:
            router.select_computer(int(m.group(1)))
            self._send_json(self._state_json())
            return

        if path == "/api/input/toggle":
            router.toggle_input()
            self._send_json(self._state_json())
            return

        if path == "/api/output/toggle":
            router.toggle_output()
            self._send_json(self._state_json())
            return

        if path == "/api/paste":
            body = self._read_json_body()
            if body is None or "text" not in body:
                self._send_json({"error": "JSON body with 'text' field required"}, 400)
                return
            text = str(body["text"])
            if len(text) > PASTE_TEXT_LIMIT:
                self._send_json(
                    {"error": f"text too long (max {PASTE_TEXT_LIMIT} chars)"}, 400
                )
                return
            # Router.type_text(text: str) -> dict {"sent": int, "skipped": int}
            # Uses CHAR_MAP from this module to build key-down/key-up HID reports
            # and dispatches them to the active computer's output sink.
            # Returns {"error": str} if no computer is active.
            result = router.type_text(text)
            self._send_json(result)
            return

        self.send_error(404)


# ─────────────────────────────────────────────────────────────────────────────
# Server wrapper
# ─────────────────────────────────────────────────────────────────────────────

class _RouterHTTPServer(HTTPServer):
    """HTTPServer subclass that carries a Router reference for handlers."""
    router: Optional[Router] = None


class WebUIServer:
    """
    Lightweight HTTP control panel.

    Start with .start(), stop with .stop().
    The server runs on config.WEB_UI_HOST : config.WEB_UI_PORT.
    """

    def __init__(self, router: Router) -> None:
        self._router = router
        self._server: Optional[_RouterHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        try:
            srv = _RouterHTTPServer((config.WEB_UI_HOST, config.WEB_UI_PORT), _Handler)
            srv.router = self._router
            self._server = srv
        except OSError as exc:
            log.warning("WebUIServer: cannot bind %s:%d — %s",
                        config.WEB_UI_HOST, config.WEB_UI_PORT, exc)
            return

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="web-ui",
            daemon=True,
        )
        self._thread.start()
        log.info("WebUI listening on http://%s:%d/", config.WEB_UI_HOST, config.WEB_UI_PORT)

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        log.info("WebUIServer stopped.")
