/* ══════════════════════════════════════════════════════════════════════
   HIDProxBox Enclosure — Handheld / Portable  (rev 2)
   Parametric OpenSCAD model · DVI-38 · constrained by DVI-39

   Redesigned to meet DVI-39 hardware constraint spec:
     • Footprint  : 90 × 50 mm  (≤ 90 × 50 mm target)
     • SBC        : Raspberry Pi Zero 2 W (65 × 30 mm)
     • MCUs       : 4× CH552T on 10 mm standoffs stacked above Pi
     • Buttons    : 4× computer select (12 mm caps) + 2× mode
     • LEDs       : 4× status (3 mm dia), one per select button
     • Ports      : 4× USB-A output + 1× USB-A keyboard input (back panel)
                    1× USB-C charging / power (right side)
     • Battery    : placeholder void for slim LiPo TBD
                    (chemistry / capacity unresolved — see DVI-39 §11)
     • Display    : omitted (optional per spec; footprint precludes it)

   OVERALL DIMENSIONS: 90 × 50 × 30 mm

   TWO-PIECE FDM DESIGN
     Bottom shell : floor face down, open top up (no supports needed)
     Top cap      : outer face down, flip 180° in slicer

   FASTENERS: 4× M2.5 heat-set inserts + 4× M2.5 × 8 mm pan-head screws

   Grip ridges run along the left and right long sides (3 per side).
   ══════════════════════════════════════════════════════════════════════ */

/* ── OUTER SHELL ────────────────────────────────────────────────────── */
W  = 90;    // exterior width   (X) — landscape
D  = 50;    // exterior depth   (Y)
H  = 30;    // exterior height  (Z)
CR = 4.0;   // XY corner radius

/* ── WALL THICKNESS ────────────────────────────────────────────────── */
WS = 2.0;
WB = 2.5;
WT = 2.0;

/* ── LID / SPLIT ───────────────────────────────────────────────────── */
LID_STEP_H  = 1.2;
LID_TOTAL_H = WT + LID_STEP_H;   // 3.2 mm
BOT_H       = H - WT;            // 28.0 mm

/* ── ALIGNMENT RIB ─────────────────────────────────────────────────── */
RIB_T   = 0.8;
RIB_H   = 0.7;
FIT_GAP = 0.15;

/* ── M2.5 FASTENERS ────────────────────────────────────────────────── */
SCREW_R      = 1.4;    // M2.5 clearance
INSERT_R     = 1.75;   // M2.5 heat-set insert pocket
INSERT_DEPTH = 4.5;
BOSS_R       = 3.8;
BOSS_H       = 20.0;   // from floor to top of boss (clamped well below lid)
BOSS_INSET   = WS + BOSS_R + 1.0;   // = 6.8 mm from outer edge

/* ── FRONT FACE (Y=0)
   Layout (X from left, Z from floor):

   Z=24 ○    ○    ○    ○       ← 4× status LEDs (3 mm dia), one per computer
   Z=16 ●    ●         ●    ●  ← 4× select buttons (12 mm), pairs C1+C2 / C3+C4
   Z= 8           ▬ ▬          ← 2× mode buttons, centred in inter-group gap

   Groups are separated by a 22 mm gap (X = 34 … 56 mm) to give a visual
   cue distinguishing the two pairs.  Mode buttons sit in that gap at Z = 8.
   ──────────────────────────────────────────────────────────────────── */
// 12 mm diameter select buttons (smaller than desktop 16 mm — handheld ergonomics)
BTN_R   = 6.0;
BTN_ZC  = WB + 13.5;   // = 16.0 mm from floor
BTN_XC  = [12.0, 28.0, 62.0, 78.0];
// Group 1 right edge: 28+6=34; Group 2 left edge: 62-6=56 → 22 mm gap

// 3 mm status LEDs (one per button, tangent above — "space allows" threshold per DVI-39)
LED_R   = 1.5;
LED_ZC  = WB + 21.5;   // = 24.0 mm from floor (tangent: 24-1.5=22.5 > BTN top 22)
LED_XC  = BTN_XC;      // directly above respective select button

// 2× mode buttons — centred in the 22 mm inter-group gap
MODE_W  = 9.0;    // slightly narrower than desktop to fit gap
MODE_H  = 4.0;
MODE_ZC = WB + 5.5;    // = 8.0 mm from floor (tangent below select buttons)
MODE_XC = [40.0, 50.0];
// Mode btn1 X-span: [35.5, 44.5], mode btn2: [45.5, 54.5]
// Clearance from select groups: 34→35.5 (1.5 mm) and 54.5→56 (1.5 mm) ✓

/* ── BACK PANEL — 4× USB-A output + 1× USB-A keyboard input ─────────── */
// All ports centred at H/2 = 15 mm (mid-height of 30 mm shell)
USBA_PORT_ZC = H / 2;   // = 15.0 mm
USBA_W       = 12.5;
USBA_H       = 4.5;
USBA_PITCH   = 15.0;    // 15 mm pitch (vs. 18 mm desktop — 90 mm back panel)
// C1–C4 output port centres
USBA_XC = [for (i=[0:3]) WS + 8.0 + i * USBA_PITCH];
         // = [10.0, 25.0, 40.0, 55.0]
KBD_XC  = USBA_XC[3] + USBA_PITCH;   // keyboard input  (= 70.0 mm)
// Keyboard right edge: 70+6.25=76.25 < 88 mm (interior right) ✓

/* ── RIGHT SIDE — USB-C charging / power ────────────────────────────── */
USBC_W  = 9.0;
USBC_H  = 3.5;
USBC_ZC = H / 2;   // = 15.0 mm
USBC_YC = D / 2;   // = 25.0 mm front-to-back

/* ── BATTERY PLACEHOLDER ────────────────────────────────────────────── */
// Chemistry and capacity TBD (DVI-39 §11 §8).  Uncomment when spec is confirmed.
// A representative slim LiPo (e.g. 401660 ~150 mAh, or 503450 ~800 mAh)
// can fit in the interior beside the Pi Zero 2W footprint (65 × 30 mm)
// or in a second layer above the CH552T stack.  Set to true to preview the void.
SHOW_BATTERY_VOID  = false;
BAT_W  = 18.0;   // placeholder width  (X)
BAT_D  = 38.0;   // placeholder depth  (Y)
BAT_H  =  7.0;   // placeholder height (Z) — sits on floor
BAT_X  = W - WS - BAT_W - 1.0;   // right side of interior
BAT_Y  = WS + 4.0;

/* ── GRIP RIDGES (left + right long sides) ───────────────────────────── */
GRIP_W  = 1.5;   // ridge base width (Y)
GRIP_H  = 0.8;   // ridge protrusion (X outward)
GRIP_N  = 3;
GRIP_Y0    = D * 0.25;
GRIP_PITCH = D * 0.22;

/* ── VENTILATION (left side wall) ────────────────────────────────────── */
VENT_W  = 1.2;
VENT_L  = 20.0;
VENT_N  = 4;
VENT_ZC0    = WB + 8.0;   // = 10.5 mm from floor
VENT_PITCH  = 4.0;
VENT_YC     = D / 2;

$fn = 48;

/* ══════════════════════════════════════════════════════════════════════
   HELPERS
   ══════════════════════════════════════════════════════════════════════ */

module rounded_rect(w, d, h, r) {
    hull() {
        for (x = [r, w-r]) for (y = [r, d-r])
            translate([x, y, 0]) cylinder(r=r, h=h);
    }
}

module m25_boss(h) {
    difference() {
        cylinder(r=BOSS_R, h=h);
        translate([0, 0, h - INSERT_DEPTH])
            cylinder(r=INSERT_R, h=INSERT_DEPTH + 0.1);
    }
}

module m25_hole(h) {
    cylinder(r=SCREW_R, h=h + 0.2);
}

boss_corners = [
    [BOSS_INSET,   BOSS_INSET  ],
    [W-BOSS_INSET, BOSS_INSET  ],
    [BOSS_INSET,   D-BOSS_INSET],
    [W-BOSS_INSET, D-BOSS_INSET]
];

// Y-direction cylinder cutter (front / back wall)
module y_cyl_cutter(r, xc, zc, y_start, len) {
    translate([xc, y_start, zc])
        rotate([90, 0, 0])
            cylinder(r=r, h=len);
}

// Y-direction rect cutter
module y_rect_cutter(w, h, xc, zc, y_start, len) {
    translate([xc - w/2, y_start, zc - h/2])
        cube([w, len, h]);
}

/* ── Front face cutouts ─────────────────────────────────────────────── */
module front_cutouts() {
    y0  = -1;
    len = WS + 2;

    // 4 select buttons (two groups of 2 — see layout comment above)
    for (bx = BTN_XC)
        y_cyl_cutter(BTN_R, bx, BTN_ZC, y0, len);

    // 4 status LEDs (3 mm, one above each select button)
    for (lx = LED_XC)
        y_cyl_cutter(LED_R, lx, LED_ZC, y0, len);

    // 2 mode buttons (rounded rect, centred in inter-group gap)
    for (mx = MODE_XC)
        translate([mx - MODE_W/2 + MODE_H/2, y0, MODE_ZC - MODE_H/2])
            hull() {
                rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
                translate([MODE_W - MODE_H, 0, 0])
                    rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
            }
}

/* ── Back face cutouts ──────────────────────────────────────────────── */
module back_cutouts() {
    y0  = D - WS - 1;
    len = WS + 2;
    zc  = USBA_PORT_ZC;

    // 4× USB-A output (C1–C4)
    for (bx = USBA_XC)
        y_rect_cutter(USBA_W, USBA_H, bx, zc, y0, len);

    // USB-A keyboard input
    y_rect_cutter(USBA_W, USBA_H, KBD_XC, zc, y0, len);
}

/* ── Right-side USB-C cutout ────────────────────────────────────────── */
module right_usbc_cutout() {
    x0  = W - WS - 1;
    len = WS + 2;
    translate([x0, USBC_YC - USBC_W/2 + USBC_H/2, USBC_ZC - USBC_H/2])
        hull() {
            rotate([0, 90, 0]) cylinder(r=USBC_H/2, h=len);
            translate([0, USBC_W - USBC_H, 0])
                rotate([0, 90, 0]) cylinder(r=USBC_H/2, h=len);
        }
}

/* ── Left-side ventilation slots ────────────────────────────────────── */
module left_vent_slots() {
    x0  = -1;
    len = WS + 2;
    for (i = [0 : VENT_N-1]) {
        zc = VENT_ZC0 + i * VENT_PITCH;
        translate([x0, VENT_YC - VENT_L/2, zc - VENT_W/2])
            cube([len, VENT_L, VENT_W]);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   BOTTOM SHELL
   ══════════════════════════════════════════════════════════════════════ */
module bottom_shell() {
    difference() {
        union() {
            // Outer rounded-rect body
            rounded_rect(W, D, BOT_H, CR);

            // Grip ridges — added as XY-plane triangular prisms on outer walls
            for (i = [0 : GRIP_N-1]) {
                ypos = GRIP_Y0 + i * GRIP_PITCH;
                // Right side (X = W face)
                translate([W, ypos, 0])
                    linear_extrude(height=BOT_H)
                        polygon([[0,0],[0,GRIP_W],[GRIP_H,GRIP_W/2]]);
                // Left side (X = 0 face)
                translate([0, ypos, 0])
                    linear_extrude(height=BOT_H)
                        polygon([[0,0],[0,GRIP_W],[-GRIP_H,GRIP_W/2]]);
            }
        }

        // Interior pocket
        translate([WS, WS, WB])
            rounded_rect(W-2*WS, D-2*WS, BOT_H-WB+0.1, max(0.1, CR-WS));

        // Face cutouts
        front_cutouts();
        back_cutouts();
        right_usbc_cutout();
        left_vent_slots();

        // Battery placeholder void (enable with SHOW_BATTERY_VOID = true)
        if (SHOW_BATTERY_VOID)
            translate([BAT_X, BAT_Y, WB])
                cube([BAT_W, BAT_D, BAT_H]);
    }

    // Corner bosses
    translate([0, 0, WB])
        for (c = boss_corners)
            translate([c[0], c[1], 0])
                m25_boss(BOSS_H - WB);

    // Alignment rib on top rim
    translate([WS, WS, BOT_H - RIB_H])
        difference() {
            cube([W-2*WS, D-2*WS, RIB_H]);
            translate([RIB_T, RIB_T, -0.1])
                cube([W-2*WS-2*RIB_T, D-2*WS-2*RIB_T, RIB_H+0.2]);
        }
}

/* ══════════════════════════════════════════════════════════════════════
   TOP CAP
   ══════════════════════════════════════════════════════════════════════ */
module top_cap() {
    g = FIT_GAP;

    difference() {
        union() {
            // Flat top panel
            rounded_rect(W, D, WT, CR);

            // Step rebate (descends into shell, mates with alignment rib)
            translate([WS+g, WS+g, -LID_STEP_H])
                difference() {
                    cube([W-2*(WS+g), D-2*(WS+g), LID_STEP_H]);
                    translate([RIB_T+g, RIB_T+g, -0.1])
                        cube([
                            W-2*(WS+g+RIB_T+g),
                            D-2*(WS+g+RIB_T+g),
                            LID_STEP_H+0.2
                        ]);
                }
        }

        // M2.5 screw through-holes at corner boss positions
        translate([0, 0, -LID_STEP_H-0.1])
            for (c = boss_corners)
                translate([c[0], c[1], 0])
                    m25_hole(LID_TOTAL_H);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   RENDER CONTROL
   Set PART = "both" for interactive preview.
   Set PART = "bottom" or "top" for STL export.
   ══════════════════════════════════════════════════════════════════════ */
PART = "both";  // "bottom" | "top" | "both"

if (PART == "both") {
    color("#1A2E40") bottom_shell();
    translate([0, D + 20, LID_TOTAL_H])
        rotate([180, 0, 0])
            color("#2A4F6E", 0.75) top_cap();
}
else if (PART == "bottom") {
    bottom_shell();
}
else if (PART == "top") {
    top_cap();
}
