/**
 * ch552t_hid_proxy.ino
 * HIDProxBox — CH552T secondary USB HID output  (one unit per computer)
 *
 * Each CH552T is permanently plugged into one computer's USB port.
 * The Raspberry Pi sends framed command packets over UART1 and the
 * CH552T translates them into USB HID reports on the host side.
 *
 * Additionally, the Pi can command the CH552T to show whether its
 * computer is currently the "active" (selected) one via an LED.
 *
 * ── Frame Format (Pi → CH552T via UART1) ─────────────────────────────────
 *
 *   [0xAA] [TYPE] [LEN] [DATA ...LEN bytes...] [CHECKSUM]
 *
 *   TYPE   LEN   Description
 *   ────   ───   ──────────────────────────────────────────────────────────
 *   0x01    8    Keyboard report: [modifier, 0, key1..key6]
 *   0x02    4    Mouse report:    [buttons, X (int8), Y (int8), W (int8)]
 *   0x03    2    Consumer report: [usage_lo, usage_hi]
 *   0x10    1    Set-active LED:  0x01=active (LED on), 0x00=inactive (off)
 *   0xFE    0    Ping (no-op — wakes UART)
 *   0xFF    0    Reset: release all keys, clear mouse buttons
 *
 *   CHECKSUM = XOR of TYPE ^ LEN ^ DATA[0] ^ ... ^ DATA[N-1]
 *
 * ── LED Behaviour ─────────────────────────────────────────────────────────
 *
 *   ACTIVE_LED  (P3.4, active-low):
 *     • Solid ON  — this computer is the currently selected KVM target.
 *     • Solid OFF — standby (another computer is selected).
 *     • Fast blink (during RX) — data is being forwarded to this computer.
 *
 *   STATUS_LED  (P1.4, active-low, optional):
 *     • Short blink on every valid received frame.
 *     • Rapid blink on checksum error (bad frame).
 *
 * ── Board Setup in Arduino IDE ────────────────────────────────────────────
 *
 *   Board manager URL:
 *     https://raw.githubusercontent.com/DeqingSun/ch55xduino/master/
 *     package_ch55xduino_mcs51_index.json
 *
 *   Tools → Board          : CH55x boards → CH552
 *   Tools → Clock Source   : 16 MHz (internal)
 *   Tools → Upload Method  : USB (bootloader)
 *   Tools → USB Settings   : USER CODE w/ 148B USB ram
 *
 * ── Wiring (per CH552T unit) ──────────────────────────────────────────────
 *
 *   CH552T P3.0 (RXD1) ─── Pi /dev/ttyUSBx TX    (3.3 V — no level shift)
 *   CH552T P3.1 (TXD1) ─── Pi /dev/ttyUSBx RX
 *   CH552T GND         ─── Pi GND
 *   CH552T USB D+/D−   ─── Computer USB port  (22 Ω series resistors)
 *   CH552T VCC (3.3 V) ─── 3.3 V supply
 *   Active LED         ─── P3.4 → 220 Ω → LED → GND  (active-low)
 *   Status LED         ─── P1.4 → 220 Ω → LED → GND  (active-low, optional)
 */

#include <USBHIDKeyboard.h>
#include <USBHIDMouse.h>

// ── Pin definitions ──────────────────────────────────────────────────────────
#define ACTIVE_LED_PIN   34    // P3.4  active-low — "this computer is selected"
#define STATUS_LED_PIN   14    // P1.4  active-low — frame-received blink (optional)

// ── Protocol constants ───────────────────────────────────────────────────────
#define FRAME_SOF         0xAA
#define TYPE_KEYBOARD     0x01
#define TYPE_MOUSE        0x02
#define TYPE_CONSUMER     0x03
#define TYPE_SET_ACTIVE   0x10
#define TYPE_PING         0xFE
#define TYPE_RESET        0xFF

#define MAX_PAYLOAD       16
#define UART_BAUD         115200

// ── Frame parser state machine ───────────────────────────────────────────────
typedef enum {
    WAIT_SOF,
    WAIT_TYPE,
    WAIT_LEN,
    WAIT_DATA,
    WAIT_CHECKSUM
} ParserState;

static ParserState  s_state   = WAIT_SOF;
static uint8_t      s_type    = 0;
static uint8_t      s_len     = 0;
static uint8_t      s_buf[MAX_PAYLOAD];
static uint8_t      s_idx     = 0;
static uint8_t      s_chk_acc = 0;

// ── Runtime state ────────────────────────────────────────────────────────────
static bool         s_active  = false;   // is this the selected computer?

// ── USB HID objects ──────────────────────────────────────────────────────────
USBHIDKeyboard_ Keyboard;
USBHIDMouse_    Mouse;

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
    pinMode(ACTIVE_LED_PIN, OUTPUT);
    digitalWrite(ACTIVE_LED_PIN, HIGH);   // off (active-low)

    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, HIGH);

    Serial1.begin(UART_BAUD);
    delay(500);   // let host enumerate

    // Three quick blinks = ready
    for (int i = 0; i < 3; i++) {
        led_active(true);  delay(80);
        led_active(false); delay(80);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
void loop() {
    while (Serial1.available() > 0) {
        process_byte((uint8_t)Serial1.read());
    }
    delay(1);
}

// ─────────────────────────────────────────────────────────────────────────────
// Frame parser
// ─────────────────────────────────────────────────────────────────────────────
static void process_byte(uint8_t b) {
    switch (s_state) {

        case WAIT_SOF:
            if (b == FRAME_SOF) s_state = WAIT_TYPE;
            break;

        case WAIT_TYPE:
            s_type    = b;
            s_chk_acc = b;
            s_state   = WAIT_LEN;
            break;

        case WAIT_LEN:
            s_len     = b;
            s_chk_acc ^= b;
            s_idx     = 0;
            if      (s_len == 0)           s_state = WAIT_CHECKSUM;
            else if (s_len > MAX_PAYLOAD)  s_state = WAIT_SOF;   // oversize — resync
            else                           s_state = WAIT_DATA;
            break;

        case WAIT_DATA:
            s_buf[s_idx++] = b;
            s_chk_acc ^= b;
            if (s_idx >= s_len) s_state = WAIT_CHECKSUM;
            break;

        case WAIT_CHECKSUM:
            if (b == s_chk_acc) {
                dispatch_frame();
                blink_status();          // brief blink on valid frame
            } else {
                blink_error();           // rapid blink on checksum failure
            }
            s_state = WAIT_SOF;
            break;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Frame dispatcher
// ─────────────────────────────────────────────────────────────────────────────
static void dispatch_frame() {
    switch (s_type) {

        case TYPE_KEYBOARD:
            if (s_len == 8) send_keyboard_report(s_buf);
            break;

        case TYPE_MOUSE:
            if (s_len == 4) send_mouse_report(s_buf);
            break;

        case TYPE_CONSUMER:
            if (s_len == 2) send_consumer_report(s_buf);
            break;

        case TYPE_SET_ACTIVE:
            // s_buf[0]: 0x01 = this computer is now selected, 0x00 = deselected
            if (s_len == 1) {
                s_active = (s_buf[0] == 0x01);
                led_active(s_active);
            }
            break;

        case TYPE_RESET:
            Keyboard.releaseAll();
            Mouse.release(MOUSE_LEFT | MOUSE_RIGHT | MOUSE_MIDDLE);
            break;

        case TYPE_PING:
            // No-op
            break;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// HID report senders
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Keyboard — 8-byte boot-compatible report
 *   buf[0] modifier  buf[1] reserved  buf[2..7] keycodes
 */
static void send_keyboard_report(const uint8_t *buf) {
    Keyboard.sendReport(buf[0], (uint8_t *)(buf + 2), 6);
}

/**
 * Mouse — 4-byte relative report
 *   buf[0] buttons  buf[1] X  buf[2] Y  buf[3] wheel  (all signed int8)
 */
static void send_mouse_report(const uint8_t *buf) {
    int8_t dx    = (int8_t)buf[1];
    int8_t dy    = (int8_t)buf[2];
    int8_t wheel = (int8_t)buf[3];
    uint8_t btns  = buf[0];

    if (btns & 0x01) Mouse.press(MOUSE_LEFT);   else Mouse.release(MOUSE_LEFT);
    if (btns & 0x02) Mouse.press(MOUSE_RIGHT);  else Mouse.release(MOUSE_RIGHT);
    if (btns & 0x04) Mouse.press(MOUSE_MIDDLE); else Mouse.release(MOUSE_MIDDLE);

    if (dx || dy || wheel) Mouse.move(dx, dy, wheel);
}

/**
 * Consumer (multimedia) — 2-byte usage ID, little-endian
 *   e.g. [0xE9, 0x00] = Volume Up
 */
static void send_consumer_report(const uint8_t *buf) {
    uint16_t usage = (uint16_t)buf[0] | ((uint16_t)buf[1] << 8);
#if defined(USBHID_CONSUMER_SUPPORTED)
    Keyboard.consumerPress(usage);
    delay(20);
    Keyboard.consumerRelease();
#else
    (void)usage;
#endif
}

// ─────────────────────────────────────────────────────────────────────────────
// LED helpers
// ─────────────────────────────────────────────────────────────────────────────

static void led_active(bool on) {
    // Active-low: LOW = LED on
    digitalWrite(ACTIVE_LED_PIN, on ? LOW : HIGH);
}

static void blink_status() {
    // Single short blink on status LED (won't block loop for long)
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(12);
    digitalWrite(STATUS_LED_PIN, HIGH);
}

static void blink_error() {
    // Two rapid blinks to signal checksum error
    for (int i = 0; i < 2; i++) {
        digitalWrite(STATUS_LED_PIN, LOW);  delay(60);
        digitalWrite(STATUS_LED_PIN, HIGH); delay(60);
    }
}
