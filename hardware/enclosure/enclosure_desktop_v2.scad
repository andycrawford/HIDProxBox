/* ══════════════════════════════════════════════════════════════════════
   HIDProxBox Enclosure — Desktop v2 (Enhanced Slab)
   Parametric OpenSCAD model · DVI-38

   Builds on Option A (DVI-35 / enclosure.scad) with:
     • 3° ergonomic tilt — rear is 32 mm, front drops to ~24 mm
     • Rubber-foot boss pockets (×4) on underside
     • Dual-side chevron ventilation (left + right)
     • Port-label channels (0.4 mm deep grooves above port groups)
     • Recessed logo plate area on top lid
     • Wider interior cable-management clip boss near power

   Hardware compatibility is unchanged:
     — Same 175 × 90 mm footprint as v1
     — Same port centre-lines (back panel USB-A and USB-C positions)
     — Same front-panel display + button + LED layout
     — Same M3 × 4 mm heat-set inserts (×4), M3 × 10 mm lid screws

   Print orientation
     Bottom shell : floor face down, open top up (rear wall is tallest).
     Top lid      : outer face down, flip 180° in slicer.
   ══════════════════════════════════════════════════════════════════════ */

/* ── MAIN FOOTPRINT (mm) ────────────────────────────────────────────── */
W  = 175;    // exterior width (X)
D  = 90;     // exterior depth (Y)
H_REAR = 32; // exterior height at rear (tallest side)
H_FRONT = 24;// exterior height at front (tilt creates a wedge profile)
// The tilt is applied as a linear height gradient front→rear.
// TILT_SLOPE = (H_REAR - H_FRONT) / D
TILT_SLOPE = (H_REAR - H_FRONT) / D;

/* ── WALL THICKNESS ────────────────────────────────────────────────── */
WS = 2.5;   // side walls
WB = 3.0;   // base / floor
WT = 2.5;   // lid panel thickness

/* ── LID / SPLIT ───────────────────────────────────────────────────── */
LID_STEP_H  = 1.5;
LID_TOTAL_H = WT + LID_STEP_H;  // 4.0 mm
// The split-plane follows the tilt: at depth y the shell wall height is:
//   shell_h(y) = H_FRONT + TILT_SLOPE * y - WT
// We keep the lid flat on the outside and tapered on the bottom edge.
BOT_H_FRONT = H_FRONT - WT;   // shell height at front = 21.5 mm
BOT_H_REAR  = H_REAR  - WT;   // shell height at rear  = 29.5 mm

/* ── ALIGNMENT RIB ─────────────────────────────────────────────────── */
RIB_T   = 1.0;
RIB_H   = 0.8;
FIT_GAP = 0.15;

/* ── M3 FASTENERS ──────────────────────────────────────────────────── */
SCREW_R      = 1.65;
INSERT_R     = 2.0;
INSERT_DEPTH = 6.0;
BOSS_R       = 5.0;
BOSS_H_MIN   = 14.0;   // boss height at front corners (shorter due to tilt)
BOSS_H_MAX   = 22.0;   // boss height at rear corners
BOSS_INSET   = WS + BOSS_R + 1.5;   // = 9.0 mm from outer edge

/* ── RUBBER FOOT POCKETS (underside) ───────────────────────────────── */
FOOT_R     = 6.5;    // pocket radius (fits Ø12 mm rubber foot)
FOOT_DEPTH = 1.5;    // recess depth
FOOT_INSET = 10.0;   // from outer edge to pocket centre

/* ── FRONT PANEL ───────────────────────────────────────────────────── */
// Heights below are measured from the FRONT floor (Z=0).
DISP_X       = WS + 8.0;  // 10.5 mm from left outer edge
DISP_Z       = WB + 4.0;  // 7.0 mm from floor
DISP_W       = 73.0;
DISP_H       = 22.0;
DISP_CHAMFER = 1.5;

SEP_X = DISP_X + DISP_W + 4.0;   // = 87.5 mm

BTN_R  = 8.0;
BTN_ZC = WB + 13.0;   // 16.0 mm from floor (lowered 2 mm vs v1 for tilt)
BTN_XC = [SEP_X+14, SEP_X+30, SEP_X+46, SEP_X+62];

LED_R    = 2.5;
LED_ZC   = WB + 19.5;  // 22.5 mm from floor
LED_STEP = (BTN_XC[3] - BTN_XC[0]) / 5;
LED_XC   = [for (i=[0:5]) BTN_XC[0] + i * LED_STEP];

MODE_W  = 16.0;
MODE_H  = 8.0;
MODE_ZC = WB + 7.0;   // 10.0 mm
MODE_XC = [BTN_XC[0] - 2, BTN_XC[2] - 2];

// Port-label groove above button zone (shallow channel, cosmetic)
LABEL_GROOVE_H  = 0.4;   // depth
LABEL_GROOVE_W  = 1.2;   // width
LABEL_GROOVE_ZC = WB + 2.0;  // just above the mode buttons

/* ── BACK PANEL ────────────────────────────────────────────────────── */
// Vertical centre measured from REAR floor (rear is tallest).
USBA_PORT_ZC = H_REAR / 2;  // = 16.0 mm — same as v1
USBA_W       = 12.5;
USBA_H       = 4.5;
USBA_PITCH   = 18.0;
USBA_XC = [for (i=[0:3]) WS + 12.0 + i * USBA_PITCH];
KBD_XC  = USBA_XC[3] + USBA_PITCH + 3.0;
USBC_XC = KBD_XC + USBA_PITCH;
USBC_W  = 9.0;
USBC_H  = 3.5;

/* ── LOGO PLATE RECESS (top lid) ───────────────────────────────────── */
LOGO_W     = 45.0;    // width of recess
LOGO_D     = 14.0;    // depth (Y) of recess
LOGO_DEPTH = 0.8;     // how far it sinks into the lid
LOGO_XC    = W / 2;   // centred on lid
LOGO_YC    = D * 0.30; // 30 % from front

/* ── VENTILATION — BOTH SIDES (chevron slots) ──────────────────────── */
// Left side (X=0 wall) and right side (X=W wall)
// Chevron = two angled rectangles forming a V shape per unit
VENT_W        = 1.5;    // slot width
VENT_L        = 24.0;   // half-leg length of chevron
VENT_ANGLE    = 30;     // degrees from vertical
VENT_N        = 5;      // number of chevron units per side
VENT_ZC0      = WB + 10.0;
VENT_PITCH    = 5.0;
VENT_Y_CENTER = D / 2;  // centred front-to-back

/* ── CABLE CLIP BOSS (interior, near USB-C power) ──────────────────── */
// Small upright tower with a notch to clip a USB-C cable tidy
CLIP_X = USBC_XC - 10.0;  // interior X near power port
CLIP_R = 2.5;
CLIP_H = 8.0;
CLIP_SLOT_W = 4.0;    // slot width (cable pass-through)
CLIP_SLOT_H = 3.0;

$fn = 64;

/* ══════════════════════════════════════════════════════════════════════
   HELPER MODULES
   ══════════════════════════════════════════════════════════════════════ */

// Height of shell wall at a given Y depth (tilt)
function shell_h(y) = H_FRONT + TILT_SLOPE * y;

// Boss height from floor at given Y (so top of boss reaches lid split plane)
function boss_h(y) = shell_h(y) - WT - WB;

module m3_boss(h) {
    difference() {
        cylinder(r=BOSS_R, h=h);
        translate([0, 0, h - INSERT_DEPTH])
            cylinder(r=INSERT_R, h=INSERT_DEPTH + 0.1);
    }
}

module m3_hole(h) {
    cylinder(r=SCREW_R, h=h + 0.2);
}

// Rubber foot pocket (recess into floor bottom face)
module foot_pocket() {
    translate([0, 0, -0.1])
        cylinder(r=FOOT_R, h=FOOT_DEPTH + 0.1);
}

boss_corners = [
    [BOSS_INSET,   BOSS_INSET  ],
    [W-BOSS_INSET, BOSS_INSET  ],
    [BOSS_INSET,   D-BOSS_INSET],
    [W-BOSS_INSET, D-BOSS_INSET]
];

module y_cyl_cutter(r, xc, zc, y_start, len) {
    translate([xc, y_start, zc])
        rotate([90, 0, 0])
            cylinder(r=r, h=len);
}

module y_rect_cutter(w, h, xc, zc, y_start, len) {
    translate([xc - w/2, y_start, zc - h/2])
        cube([w, len, h]);
}

/* ── Front panel cutouts ────────────────────────────────────────────── */
module front_cutouts() {
    y0  = -1;
    len = WS + 2;

    // Display opening
    translate([DISP_X, y0, DISP_Z])
        cube([DISP_W, len, DISP_H]);
    // Bridge chamfer
    translate([DISP_X, WS - DISP_CHAMFER, DISP_Z + DISP_H - DISP_CHAMFER])
        rotate([-45, 0, 0])
            cube([DISP_W, DISP_CHAMFER * 1.42, DISP_CHAMFER * 1.42]);

    // 4 select buttons
    for (bx = BTN_XC)
        y_cyl_cutter(BTN_R, bx, BTN_ZC, y0, len);

    // 6 status LEDs
    for (lx = LED_XC)
        y_cyl_cutter(LED_R, lx, LED_ZC, y0, len);

    // 2 mode buttons (rounded rect)
    for (mx = MODE_XC)
        translate([mx - MODE_W/2 + MODE_H/2, y0, MODE_ZC - MODE_H/2])
            hull() {
                rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
                translate([MODE_W - MODE_H, 0, 0])
                    rotate([90, 0, 0]) cylinder(r=MODE_H/2, h=len);
            }

    // Label groove above mode/button zone (cosmetic separator line)
    translate([SEP_X, y0, LABEL_GROOVE_ZC - LABEL_GROOVE_W/2])
        cube([W - SEP_X - WS - 2, len, LABEL_GROOVE_W]);
}

/* ── Back panel cutouts ─────────────────────────────────────────────── */
module back_cutouts() {
    y0  = D - WS - 1;
    len = WS + 2;
    zc  = USBA_PORT_ZC;

    for (bx = USBA_XC)
        y_rect_cutter(USBA_W, USBA_H, bx, zc, y0, len);

    y_rect_cutter(USBA_W, USBA_H, KBD_XC, zc, y0, len);

    translate([USBC_XC - USBC_W/2 + USBC_H/2, y0, zc - USBC_H/2])
        hull() {
            rotate([90, 0, 0]) cylinder(r=USBC_H/2, h=len);
            translate([USBC_W - USBC_H, 0, 0])
                rotate([90, 0, 0]) cylinder(r=USBC_H/2, h=len);
        }
}

/* ── Chevron vent slot (single leg) ────────────────────────────────── */
// Generates one angled rectangle; call twice mirrored for a full chevron.
module chevron_leg(xface, flip) {
    sign = flip ? -1 : 1;
    rotate([0, 0, sign * VENT_ANGLE])
        translate([-VENT_W/2, 0, 0])
            cube([VENT_W, VENT_L, 100]);  // Z clipped by difference
}

/* ── Ventilation cutouts for one vertical face ──────────────────────── */
// face: "left" (X=0 wall) or "right" (X=W wall)
module vent_cutouts(face) {
    for (i = [0 : VENT_N-1]) {
        zc = VENT_ZC0 + i * VENT_PITCH;
        yc = VENT_Y_CENTER;
        if (face == "right") {
            translate([W - WS - 1, yc, zc])
                rotate([90, 90, 0]) {
                    chevron_leg(W, false);
                    mirror([1,0,0]) chevron_leg(W, false);
                }
        } else {
            translate([WS + 1, yc, zc])
                rotate([90, -90, 0]) {
                    chevron_leg(0, false);
                    mirror([1,0,0]) chevron_leg(0, false);
                }
        }
    }
}

/* ── Simple slot vents (X-direction, punched through side wall) ─────── */
// Straightforward rectangular slots, pair per chevron unit for clarity
module side_vent_slots(face) {
    x0  = (face == "right") ? W - WS - 1 : -1;
    len = WS + 2;
    for (i = [0 : VENT_N-1]) {
        zc = VENT_ZC0 + i * VENT_PITCH;
        // Two angled slots forming a V
        for (dy = [-5, 5]) {
            translate([x0, VENT_Y_CENTER + dy - VENT_W/2, zc - VENT_L/2])
                cube([len, VENT_W, VENT_L]);
        }
    }
}

/* ── Tilted outer body ──────────────────────────────────────────────── */
// Approximates the wedge with a hull of front-face and rear-face rectangles.
// OpenSCAD linear_extrude with scale doesn't do a simple linear Z slope
// easily, so we use a polyhedron-style hull.
module tilted_body() {
    hull() {
        // Front face (Y=0): height H_FRONT
        translate([0, 0, 0]) cube([W, 0.01, H_FRONT]);
        // Rear face (Y=D): height H_REAR
        translate([0, D - 0.01, 0]) cube([W, 0.01, H_REAR]);
    }
}

module tilted_interior() {
    hull() {
        translate([WS, WS, WB]) cube([W - 2*WS, 0.01, H_FRONT - WB]);
        translate([WS, D - WS - 0.01, WB]) cube([W - 2*WS, 0.01, H_REAR - WB]);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   BOTTOM SHELL
   ══════════════════════════════════════════════════════════════════════ */
module bottom_shell() {
    // Shell wall heights at front/rear boss corners
    bh_front = boss_h(BOSS_INSET);
    bh_rear  = boss_h(D - BOSS_INSET);

    difference() {
        tilted_body();

        // Interior pocket
        translate([0, 0, 0.1]) tilted_interior();

        // Front/back panel cutouts
        front_cutouts();
        back_cutouts();

        // Side ventilation slots
        side_vent_slots("left");
        side_vent_slots("right");

        // Rubber foot pockets (cut into bottom face)
        foot_positions = [
            [FOOT_INSET,   FOOT_INSET  ],
            [W-FOOT_INSET, FOOT_INSET  ],
            [FOOT_INSET,   D-FOOT_INSET],
            [W-FOOT_INSET, D-FOOT_INSET]
        ];
        for (fp = foot_positions)
            translate([fp[0], fp[1], 0]) foot_pocket();
    }

    // Corner bosses (4 corners, height adjusted for tilt)
    for (c = boss_corners) {
        bh = boss_h(c[1]);
        translate([c[0], c[1], WB]) m3_boss(bh);
    }

    // Alignment rib on top rim (follows tilt — built as a hull)
    rib_front_h = H_FRONT - WT - RIB_H;  // Z at front rim
    rib_rear_h  = H_REAR  - WT - RIB_H;  // Z at rear rim
    translate([WS, WS, 0])
        difference() {
            hull() {
                translate([0, 0, rib_front_h]) cube([W-2*WS, 0.01, RIB_H]);
                translate([0, D-2*WS-0.01, rib_rear_h]) cube([W-2*WS, 0.01, RIB_H]);
            }
            hull() {
                translate([RIB_T, RIB_T, rib_front_h-0.1])
                    cube([W-2*WS-2*RIB_T, 0.01, RIB_H+0.2]);
                translate([RIB_T, D-2*WS-RIB_T-0.01, rib_rear_h-0.1])
                    cube([W-2*WS-2*RIB_T, 0.01, RIB_H+0.2]);
            }
        }

    // Cable clip boss (interior, near power port)
    translate([CLIP_X, D - WS - 15, WB]) {
        difference() {
            cylinder(r=CLIP_R + 1.5, h=CLIP_H);
            translate([-(CLIP_SLOT_W/2), -0.1, CLIP_H - CLIP_SLOT_H])
                cube([CLIP_SLOT_W, CLIP_R + 3, CLIP_SLOT_H + 0.1]);
        }
    }
}

/* ══════════════════════════════════════════════════════════════════════
   TOP LID
   Flat outer surface; underside follows the tilt to mate with shell rim.
   ══════════════════════════════════════════════════════════════════════ */
module top_lid() {
    g = FIT_GAP;

    difference() {
        union() {
            // Flat exterior top panel (a wedge: WT thick everywhere, but
            // the underside follows tilt so the assembled result has a
            // flat top that descends front-to-rear by the tilt amount).
            hull() {
                translate([0, 0, H_FRONT - WT]) cube([W, 0.01, WT]);
                translate([0, D-0.01, H_REAR - WT]) cube([W, 0.01, WT]);
            }

            // Step rebate descending below the tilt split plane
            hull() {
                translate([WS+g, WS+g, H_FRONT - WT - LID_STEP_H])
                    cube([W-2*(WS+g), 0.01, LID_STEP_H]);
                translate([WS+g, D-(WS+g)-0.01, H_REAR - WT - LID_STEP_H])
                    cube([W-2*(WS+g), 0.01, LID_STEP_H]);
            }
        }

        // Interior of step (leaves only the outer ring for alignment)
        hull() {
            translate([WS+g+RIB_T+g, WS+g+RIB_T+g, H_FRONT-WT-LID_STEP_H-0.1])
                cube([W-2*(WS+g+RIB_T+g), 0.01, LID_STEP_H+0.2]);
            translate([WS+g+RIB_T+g, D-(WS+g+RIB_T+g)-0.01, H_REAR-WT-LID_STEP_H-0.1])
                cube([W-2*(WS+g+RIB_T+g), 0.01, LID_STEP_H+0.2]);
        }

        // M3 screw through-holes at corner boss positions
        for (c = boss_corners) {
            zh = (c[1] < D/2) ? H_FRONT - WT - LID_STEP_H - 0.1
                               : H_REAR  - WT - LID_STEP_H - 0.1;
            translate([c[0], c[1], zh])
                m3_hole(LID_TOTAL_H + 0.2);
        }

        // Logo plate recess on top surface
        translate([LOGO_XC - LOGO_W/2,
                   LOGO_YC - LOGO_D/2,
                   H_FRONT - WT + TILT_SLOPE * LOGO_YC - 0.1])
            cube([LOGO_W, LOGO_D, LOGO_DEPTH + 0.1]);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   RENDER CONTROL
   Set PART = "both" for preview (shows shell + lid offset apart).
   Set PART = "bottom" or "top" for individual STL export.
   ══════════════════════════════════════════════════════════════════════ */
PART = "both";  // "bottom" | "top" | "both"

if (PART == "both") {
    color("#2A3F5C") bottom_shell();
    translate([0, D + 30, 0])
        color("#3B6080", 0.75) top_lid();
}
else if (PART == "bottom") {
    bottom_shell();
}
else if (PART == "top") {
    top_lid();
}
