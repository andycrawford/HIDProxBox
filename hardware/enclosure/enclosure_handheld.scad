/* ══════════════════════════════════════════════════════════════════════
   HIDProxBox Enclosure — Handheld / Portable
   Parametric OpenSCAD model · DVI-38

   Compact candy-bar form factor for a 2-computer variant of HIDProxBox.
   Designed around:
     • Raspberry Pi Zero 2W (65 × 30 mm) — the smallest Pi with WiFi/BT
     • 2× CH552T USB-serial boards (~40 × 15 mm each)
     • 1.3" OLED display module (34 × 14 mm active area; module ~36 × 16 mm)
     • 4× tactile select buttons (12 mm caps)
     • 2× status LEDs (3 mm)
     • 1× mode button (12 × 6 mm)
     • 1× USB-A input (keyboard)
     • 2× USB-A output (2 computers)
     • 1× USB-C power in (right side)

   OVERALL DIMENSIONS
     120 × 62 × 22 mm — fits comfortably in one hand

   TWO-PIECE FDM DESIGN
     Bottom shell : floor face down, open top up (no supports needed)
     Top cap      : outer face down, flip 180° in slicer

   FASTENERS: 4× M2.5 heat-set inserts + M2.5 × 8 mm pan-head screws

   Grip ridges run along the left and right long sides for ergonomics.
   ══════════════════════════════════════════════════════════════════════ */

/* ── OUTER SHELL ────────────────────────────────────────────────────── */
W  = 120;   // exterior width   (X) — landscape
D  = 62;    // exterior depth   (Y)
H  = 22;    // exterior height  (Z)
CR = 4.0;   // corner radius (XY plane)

/* ── WALL THICKNESS ────────────────────────────────────────────────── */
WS = 2.0;
WB = 2.5;
WT = 2.0;

/* ── LID / SPLIT ───────────────────────────────────────────────────── */
LID_STEP_H  = 1.2;
LID_TOTAL_H = WT + LID_STEP_H;   // 3.2 mm
BOT_H       = H - WT;            // 20.0 mm

/* ── ALIGNMENT RIB ─────────────────────────────────────────────────── */
RIB_T   = 0.8;
RIB_H   = 0.7;
FIT_GAP = 0.15;

/* ── M2.5 FASTENERS ────────────────────────────────────────────────── */
SCREW_R      = 1.4;    // M2.5 clearance
INSERT_R     = 1.75;   // M2.5 heat-set insert pocket radius
INSERT_DEPTH = 4.5;
BOSS_R       = 3.8;
BOSS_H       = 15.0;   // from floor to top of boss (below lid step)
BOSS_INSET   = WS + BOSS_R + 1.0;   // = 6.8 mm

/* ── FRONT FACE (Y=0) — display + buttons + LEDs ───────────────────── */
// Display: 1.3" OLED, opening 34 × 14 mm, centred left-of-midpoint
DISP_W  = 34.0;
DISP_H  = 14.0;
DISP_XC = 28.0;         // centre X of display (from left outer edge)
DISP_ZC = H / 2 + 0.5;  // roughly vertically centred
DISP_CHAMFER = 1.0;

// 2 select buttons — right of display, 12 mm caps
BTN_R  = 6.0;
BTN_ZC = H / 2;
BTN_XC = [72.0, 88.0];

// 2 status LEDs — 3 mm diameter, above display
LED_R  = 1.5;
LED_ZC = DISP_ZC + DISP_H/2 + 4.0;  // 4 mm above display top
LED_XC = [DISP_XC - 10.0, DISP_XC + 10.0];

// 1 mode button — small, below display
MODE_W  = 12.0;
MODE_H  = 6.0;
MODE_XC = DISP_XC;
MODE_ZC = DISP_ZC - DISP_H/2 - 5.0;

/* ── BOTTOM FACE (Z=0, cut from below) — USB ports ─────────────────── */
// Ports face downward through the shell bottom so cables exit below the device.
// USB-A dims: 12.5 × 4.5 mm cutout; USB-C: 9.0 × 3.5 mm
USBA_W  = 12.5;
USBA_H  = 4.5;
// 1 keyboard input + 2 output ports, evenly distributed across width
USB_ZC  = H / 2;  // centred vertically in shell (for back-edge ports)
// For handheld, the ports exit the BOTTOM edge to keep the front face clean.
// Bottom-edge cutout: through the floor into the interior.
USB_INPUT_XC  = W / 2;          // keyboard input, centred
USB_OUT_XC    = [W/2 - 22, W/2 + 22];   // two output ports

/* ── RIGHT SIDE — USB-C power ───────────────────────────────────────── */
USBC_W  = 9.0;
USBC_H  = 3.5;
USBC_ZC = H / 2;  // vertically centred
USBC_YC = D / 2;  // front-to-back centred

/* ── GRIP RIDGES (left + right sides) ──────────────────────────────── */
// Three triangular ridges per side, running full Z height of shell
GRIP_W = 1.5;   // ridge base width
GRIP_H = 0.8;   // ridge protrusion from side wall
GRIP_N = 3;
GRIP_Y0 = D * 0.30;   // first ridge Y
GRIP_PITCH = D * 0.18;

/* ── VENTILATION (left side) ───────────────────────────────────────── */
VENT_W  = 1.2;
VENT_L  = 20.0;
VENT_N  = 4;
VENT_ZC0    = WB + 8.0;
VENT_PITCH  = 3.5;
VENT_YC     = D / 2;

$fn = 48;

/* ══════════════════════════════════════════════════════════════════════
   HELPERS
   ══════════════════════════════════════════════════════════════════════ */

// Rounded rectangle in XY plane, height h (for 2D-extruded shapes)
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

// Y-direction cylinder cutter (front wall)
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

// X-direction rect cutter (right side wall)
module x_rect_cutter(w, h, yc, zc, x_start, len) {
    translate([x_start, yc - w/2, zc - h/2])
        cube([len, w, h]);
}

/* ── Front face cutouts ─────────────────────────────────────────────── */
module front_cutouts() {
    y0  = -1;
    len = WS + 2;

    // OLED display opening
    translate([DISP_XC - DISP_W/2, y0, DISP_ZC - DISP_H/2])
        cube([DISP_W, len, DISP_H]);

    // Bridge chamfer on display top interior edge
    translate([DISP_XC - DISP_W/2, WS - DISP_CHAMFER,
               DISP_ZC + DISP_H/2 - DISP_CHAMFER])
        rotate([-45, 0, 0])
            cube([DISP_W, DISP_CHAMFER*1.42, DISP_CHAMFER*1.42]);

    // 2 select buttons
    for (bx = BTN_XC)
        y_cyl_cutter(BTN_R, bx, BTN_ZC, y0, len);

    // 2 status LEDs
    for (lx = LED_XC)
        y_cyl_cutter(LED_R, lx, LED_ZC, y0, len);

    // Mode button (rounded rect)
    translate([MODE_XC - MODE_W/2 + MODE_H/2, y0, MODE_ZC - MODE_H/2])
        hull() {
            rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
            translate([MODE_W - MODE_H, 0, 0])
                rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
        }
}

/* ── Bottom-edge USB port cutouts ───────────────────────────────────── */
// Ports emerge from bottom edge — cutouts through the floor into interior
module bottom_port_cutouts() {
    z0  = -1;
    len = WB + 2;

    // USB-A input (keyboard) — centred
    translate([USB_INPUT_XC - USBA_W/2, D/2 - USBA_H/2, z0])
        cube([USBA_W, USBA_H, len]);

    // 2× USB-A outputs — offset left and right
    for (ox = USB_OUT_XC)
        translate([ox - USBA_W/2, D/2 - USBA_H/2, z0])
            cube([USBA_W, USBA_H, len]);
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

/* ── Left-side ventilation slots ───────────────────────────────────── */
module left_vent_slots() {
    x0  = -1;
    len = WS + 2;
    for (i = [0 : VENT_N-1]) {
        zc = VENT_ZC0 + i * VENT_PITCH;
        translate([x0, VENT_YC - VENT_L/2, zc - VENT_W/2])
            cube([len, VENT_L, VENT_W]);
    }
}

/* ── Grip ridge (single, triangular cross-section) ──────────────────── */
// Runs full Z height on the outer side wall surface.
module grip_ridge(x_base, side) {
    // Triangular prism: extends GRIP_H outward, GRIP_W wide at base
    sign = (side == "right") ? 1 : -1;
    translate([x_base, 0, 0])
        rotate([90, 0, 0])
            linear_extrude(height=D)
                polygon([[0,0],[GRIP_W,0],[GRIP_W/2, sign*GRIP_H]]);
}

/* ══════════════════════════════════════════════════════════════════════
   BOTTOM SHELL
   ══════════════════════════════════════════════════════════════════════ */
module bottom_shell() {
    difference() {
        union() {
            // Outer rounded-rect body
            rounded_rect(W, D, BOT_H, CR);

            // Grip ridges (left side: X=0, right side: X=W)
            // Left ridges (pointing inward negative X — flush to wall face,
            // actually raised outward, so they add to exterior at X < 0 side)
            // We add them as bumps on the outer surface.
            for (i = [0 : GRIP_N-1]) {
                ypos = GRIP_Y0 + i * GRIP_PITCH;
                // Right side ridges
                translate([W, ypos, 0])
                    rotate([0, 0, 0])
                        linear_extrude(height=BOT_H)
                            polygon([[0,0],[0,GRIP_W],[GRIP_H,GRIP_W/2]]);
                // Left side ridges
                translate([0, ypos, 0])
                    rotate([0, 0, 0])
                        linear_extrude(height=BOT_H)
                            polygon([[0,0],[0,GRIP_W],[-GRIP_H,GRIP_W/2]]);
            }
        }

        // Interior pocket
        translate([WS, WS, WB])
            rounded_rect(W-2*WS, D-2*WS, BOT_H-WB+0.1, max(0.1, CR-WS));

        // Cutouts
        front_cutouts();
        bottom_port_cutouts();
        right_usbc_cutout();
        left_vent_slots();
    }

    // Corner bosses
    translate([0, 0, WB])
        for (c = boss_corners)
            translate([c[0], c[1], 0])
                m25_boss(BOSS_H - WB);

    // Alignment rib at top rim
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

            // Step rebate
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

        // Screw through-holes
        translate([0, 0, -LID_STEP_H-0.1])
            for (c = boss_corners)
                translate([c[0], c[1], 0])
                    m25_hole(LID_TOTAL_H);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   RENDER CONTROL
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
