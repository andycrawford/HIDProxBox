/* ══════════════════════════════════════════════════════════════════════
   HIDProxBox Enclosure — Option A: Compact Slab
   Parametric OpenSCAD model · DVI-35
   Source concept: DVI-33 / branding/enclosure-a-slab.svg (commit a8979bd)

   Two-piece FDM design: bottom shell (tray) + top lid
   ── Print orientation ──────────────────────────────────────────────
   Bottom shell : floor face down, open top up.  No supports needed
                  except possible bridging for display opening (72 mm);
                  enable slicer bridging detection or add 45° chamfer
                  (already included as DISP_CHAMFER).
   Top lid      : flip 180° in slicer (outer face down, step facing up).
                  Fully flat — zero supports.
   ══════════════════════════════════════════════════════════════════════ */

/* ── MAIN DIMENSIONS (mm) ──────────────────────────────────────────── */
W  = 175;   // exterior width
D  = 90;    // exterior depth
H  = 32;    // exterior height (assembled)

/* ── WALL THICKNESS ────────────────────────────────────────────────── */
WS = 2.5;   // sides
WB = 3.0;   // base / floor
WT = 2.5;   // flat lid thickness

/* ── LID / SPLIT ───────────────────────────────────────────────────── */
LID_STEP_H  = 1.5;               // step depth below lid flat
LID_TOTAL_H = WT + LID_STEP_H;  // = 4.0 mm (printed height)
BOT_H       = H - WT;            // = 29.5 mm (bottom shell wall height)

/* ── ALIGNMENT RIB (top rim of bottom shell) ───────────────────────── */
RIB_T   = 1.0;   // rib wall thickness
RIB_H   = 0.8;   // rib protrusion above rim
FIT_GAP = 0.15;  // clearance between rib and lid groove

/* ── M3 FASTENERS ──────────────────────────────────────────────────── */
SCREW_R      = 1.65;  // M3 clearance (through-hole radius)
INSERT_R     = 2.0;   // M3 heat-set insert pocket radius
INSERT_DEPTH = 6.0;   // insert pocket depth from top of boss
BOSS_R       = 5.0;   // boss outer radius
BOSS_H       = 18.0;  // boss height from floor
BOSS_INSET   = WS + BOSS_R + 1.5;  // = 9.0 mm from outer edge

/* ── FRONT PANEL ───────────────────────────────────────────────────── */
// 3.5" display opening
DISP_X       = WS + 8.0;  // left edge from outer left (= 10.5 mm)
DISP_Z       = WB + 4.0;  // bottom from floor          (= 7.0 mm)
DISP_W       = 73.0;       // opening width
DISP_H       = 22.0;       // opening height
DISP_CHAMFER = 1.5;        // 45° chamfer on top interior edge (bridge aid)

// Right-section separator groove X position
SEP_X = DISP_X + DISP_W + 4.0;  // = 87.5 mm from left outer edge

// 4 select buttons — 16 mm diameter round caps, centered
BTN_R  = 8.0;
BTN_ZC = WB + 15.0;  // centre Z from floor  (= 18.0 mm)
BTN_XC = [SEP_X+14, SEP_X+30, SEP_X+46, SEP_X+62];  // [101.5, 117.5, 133.5, 149.5]

// 6 status LEDs — 5 mm diameter holes
LED_R  = 2.5;
LED_ZC = WB + 22.0;  // centre Z  (= 25.0 mm)
// Evenly spaced over button span, 6 holes
LED_STEP = (BTN_XC[3] - BTN_XC[0]) / 5;
LED_XC   = [for (i=[0:5]) BTN_XC[0] + i * LED_STEP];

// 2 mode buttons — 16 × 8 mm rounded rectangles
MODE_W  = 16.0;
MODE_H  = 8.0;
MODE_ZC = WB + 8.0;  // centre Z  (= 11.0 mm)
MODE_XC = [BTN_XC[0] - 2, BTN_XC[2] - 2];

/* ── BACK PANEL ────────────────────────────────────────────────────── */
// All ports centred at H/2 = 16 mm (within BOT_H = 29.5 mm)
USBA_PORT_ZC = H / 2;  // = 16.0 mm
USBA_W       = 12.5;
USBA_H       = 4.5;
USBA_PITCH   = 18.0;
// C1–C4 output port centres
USBA_XC = [for (i=[0:3]) WS + 12.0 + i * USBA_PITCH];  // [14.5, 32.5, 50.5, 68.5]
KBD_XC  = USBA_XC[3] + USBA_PITCH + 3.0;  // keyboard input  (= 89.5 mm)
USBC_XC = KBD_XC + USBA_PITCH;            // USB-C power     (= 107.5 mm)
USBC_W  = 9.0;
USBC_H  = 3.5;

/* ── VENTILATION (right side) ──────────────────────────────────────── */
VENT_W       = 1.5;
VENT_L       = 28.0;
VENT_N       = 5;
VENT_ZC0     = WB + 12.0;  // first slot centre Z  (= 15.0 mm)
VENT_PITCH   = 5.0;

$fn = 64;

/* ══════════════════════════════════════════════════════════════════════
   HELPER MODULES
   ══════════════════════════════════════════════════════════════════════ */

// M3 boss with heat-set insert pocket (insert from top)
module m3_boss(h) {
    difference() {
        cylinder(r=BOSS_R, h=h);
        translate([0, 0, h - INSERT_DEPTH])
            cylinder(r=INSERT_R, h=INSERT_DEPTH + 0.1);
    }
}

// M3 screw through-hole
module m3_hole(h) {
    cylinder(r=SCREW_R, h=h + 0.2);
}

// Boss corner positions [x, y]
boss_corners = [
    [BOSS_INSET,     BOSS_INSET    ],
    [W-BOSS_INSET,   BOSS_INSET    ],
    [BOSS_INSET,     D-BOSS_INSET  ],
    [W-BOSS_INSET,   D-BOSS_INSET  ]
];

// Iterate corners
module at_corners() {
    for (c = boss_corners)
        translate([c[0], c[1], 0])
            children();
}

// Y-direction cylinder cutter (penetrates front or back wall)
// y_start: start Y of cut, len: length through wall (WS+2 for clean cuts)
// xc, zc: centre of hole
module y_cyl_cutter(r, xc, zc, y_start, len) {
    translate([xc, y_start, zc])
        rotate([90, 0, 0])
            cylinder(r=r, h=len);
}

// Rectangular wall cutter (front/back face, Y direction)
module y_rect_cutter(w, h, xc, zc, y_start, len) {
    translate([xc - w/2, y_start, zc - h/2])
        cube([w, len, h]);
}

/* ── Front panel cutouts ────────────────────────────────────────────── */
module front_cutouts() {
    y0 = -1;
    len = WS + 2;

    // Display opening
    translate([DISP_X, y0, DISP_Z])
        cube([DISP_W, len, DISP_H]);

    // 45° chamfer on top interior edge of display opening (bridge aid)
    translate([DISP_X, WS - DISP_CHAMFER, DISP_Z + DISP_H - DISP_CHAMFER])
        rotate([-45, 0, 0])
            cube([DISP_W, DISP_CHAMFER * 1.42, DISP_CHAMFER * 1.42]);

    // 4 select button holes
    for (bx = BTN_XC)
        y_cyl_cutter(BTN_R, bx, BTN_ZC, y0, len);

    // 6 status LED holes
    for (lx = LED_XC)
        y_cyl_cutter(LED_R, lx, LED_ZC, y0, len);

    // 2 mode buttons (rounded rect via hull)
    for (mx = MODE_XC)
        translate([mx - MODE_W/2 + MODE_H/2, y0, MODE_ZC - MODE_H/2])
            hull() {
                translate([0, 0, 0])
                    rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
                translate([MODE_W - MODE_H, 0, 0])
                    rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
            }
}

/* ── Back panel cutouts ─────────────────────────────────────────────── */
module back_cutouts() {
    y0 = D - WS - 1;
    len = WS + 2;
    zc = USBA_PORT_ZC;

    // 4× USB-A output (C1–C4)
    for (bx = USBA_XC)
        y_rect_cutter(USBA_W, USBA_H, bx, zc, y0, len);

    // USB-A keyboard input
    y_rect_cutter(USBA_W, USBA_H, KBD_XC, zc, y0, len);

    // USB-C power (rounded rect)
    translate([USBC_XC - USBC_W/2 + USBC_H/2, y0, zc - USBC_H/2])
        hull() {
            rotate([90, 0, 0]) cylinder(r=USBC_H/2, h=len);
            translate([USBC_W - USBC_H, 0, 0])
                rotate([90, 0, 0]) cylinder(r=USBC_H/2, h=len);
        }
}

/* ── Right-side ventilation slots ───────────────────────────────────── */
module vent_slots() {
    for (i = [0 : VENT_N-1]) {
        zc = VENT_ZC0 + i * VENT_PITCH;
        translate([W - WS - 1, D/2 - VENT_L/2, zc - VENT_W/2])
            cube([WS + 2, VENT_L, VENT_W]);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   BOTTOM SHELL (main tray)
   Print: floor face down (Z=0 on build plate), open top facing up.
   ══════════════════════════════════════════════════════════════════════ */
module bottom_shell() {
    difference() {
        // Outer body
        cube([W, D, BOT_H]);

        // Interior pocket — open at top
        translate([WS, WS, WB])
            cube([W - 2*WS, D - 2*WS, BOT_H - WB + 0.1]);

        // Panel cutouts
        front_cutouts();
        back_cutouts();
        vent_slots();
    }

    // Corner bosses (added, not subtracted)
    translate([0, 0, WB])
        at_corners()
            m3_boss(BOSS_H);

    // Alignment rib on top rim (mates with lid step groove)
    translate([WS, WS, BOT_H - RIB_H])
        difference() {
            cube([W - 2*WS, D - 2*WS, RIB_H]);
            translate([RIB_T, RIB_T, -0.1])
                cube([W - 2*WS - 2*RIB_T, D - 2*WS - 2*RIB_T, RIB_H + 0.2]);
        }
}

/* ══════════════════════════════════════════════════════════════════════
   TOP LID (flat cover)
   Print: outer face down (flip 180° in slicer — step faces up during print).
   ══════════════════════════════════════════════════════════════════════ */
module top_lid() {
    g = FIT_GAP;

    difference() {
        union() {
            // Flat top panel
            cube([W, D, WT]);

            // Step rebate (descends below plate into shell for alignment)
            translate([WS + g, WS + g, -LID_STEP_H])
                difference() {
                    cube([W - 2*(WS+g), D - 2*(WS+g), LID_STEP_H]);
                    // Groove in step that mates with alignment rib
                    translate([RIB_T + g, RIB_T + g, -0.1])
                        cube([
                            W - 2*(WS + g + RIB_T + g),
                            D - 2*(WS + g + RIB_T + g),
                            LID_STEP_H + 0.2
                        ]);
                }
        }

        // M3 screw through-holes
        translate([0, 0, -LID_STEP_H - 0.1])
            at_corners()
                m3_hole(LID_TOTAL_H);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   RENDER CONTROL
   ── For preview ──────────────────────────────────────────────────────
   Set PART = "both"
   ── For STL export (OpenSCAD CLI or File > Export > STL) ─────────────
   Set PART = "bottom" → export enclosure_bottom.stl
   Set PART = "top"    → export enclosure_top_lid.stl
   ══════════════════════════════════════════════════════════════════════ */
PART = "both";  // "bottom" | "top" | "both"

if (PART == "both") {
    color("#2A3F5C") bottom_shell();
    translate([0, D + 25, LID_TOTAL_H])
        rotate([180, 0, 0])
            color("#3B6080", 0.75) top_lid();
}
else if (PART == "bottom") {
    bottom_shell();
}
else if (PART == "top") {
    top_lid();
}
