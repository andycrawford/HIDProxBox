#!/usr/bin/env python3
"""
HIDProxBox Enclosure STL Generator — DVI-35
Converts parametric spec to printable STLs using manifold3d + numpy-stl.

Usage:
    python3 generate_stl.py

Output:
    stl/enclosure_bottom.stl   — main tray (print floor-down)
    stl/enclosure_top_lid.stl  — flat cover  (print face-down, flip in slicer)

Requirements:
    pip3 install manifold3d numpy-stl
"""

import numpy as np
from pathlib import Path
from manifold3d import Manifold
from stl import mesh as stl_mesh

# ── PARAMETERS ──────────────────────────────────────────────────────────────

W  = 175.0   # exterior width   (mm)
D  = 90.0    # exterior depth   (mm)
H  = 32.0    # exterior height  (mm)

WS = 2.5     # side wall thickness
WB = 3.0     # base / floor thickness
WT = 2.5     # top lid flat thickness

LID_STEP_H  = 1.5               # step depth below lid flat face
LID_TOTAL_H = WT + LID_STEP_H   # = 4.0 mm  (printed height of lid)
BOT_H       = H - WT            # = 29.5 mm (bottom shell outer wall height)

RIB_T   = 1.0    # alignment rib wall thickness
RIB_H   = 0.8    # alignment rib protrusion height
FIT_GAP = 0.15   # fit clearance for lid step

BOSS_R       = 5.0
SCREW_R      = 1.65    # M3 clearance through-hole
INSERT_R     = 2.0     # M3 heat-set insert pocket
INSERT_DEPTH = 6.0
BOSS_H       = 18.0
BOSS_INSET   = WS + BOSS_R + 1.5   # = 9.0 mm from outer edge

# Front panel
DISP_X = WS + 8.0     # display left edge from outer left  (= 10.5)
DISP_Z = WB + 4.0     # display bottom from floor           (= 7.0)
DISP_W = 73.0
DISP_H = 22.0

SEP_X = DISP_X + DISP_W + 4.0    # separator X  (= 87.5)

BTN_R  = 8.0
BTN_ZC = WB + 15.0   # select-button centre Z  (= 18.0)
BTN_XC = [SEP_X + 14, SEP_X + 30, SEP_X + 46, SEP_X + 62]
         # = [101.5, 117.5, 133.5, 149.5]

LED_R  = 2.5
LED_ZC = WB + 22.0   # LED centre Z  (= 25.0)
LED_XC = [BTN_XC[0] + i * (BTN_XC[3]-BTN_XC[0])/5 for i in range(6)]

MODE_W  = 16.0
MODE_H  = 8.0
MODE_ZC = WB + 8.0   # mode-button centre Z  (= 11.0)
MODE_XC = [BTN_XC[0] - 2, BTN_XC[2] - 2]

# Back panel — all ports centred at H/2 = 16.0 mm
USBA_PORT_ZC = H / 2   # = 16.0
USBA_W = 12.5
USBA_H = 4.5
USBA_PITCH = 18.0
USBA_XC = [WS + 12.0 + i * USBA_PITCH for i in range(4)]
          # = [14.5, 32.5, 50.5, 68.5]
KBD_XC  = USBA_XC[-1] + USBA_PITCH + 3.0   # = 89.5
USBC_XC = KBD_XC + USBA_PITCH              # = 107.5
USBC_W  = 9.0
USBC_H  = 3.5

# Ventilation slots (right-side wall)
VENT_W     = 1.5
VENT_L     = 28.0
VENT_N     = 5
VENT_ZC0   = WB + 12.0   # = 15.0
VENT_PITCH = 5.0

SEGS = 48   # cylinder segments for smooth curves

BOSS_CORNERS = [
    (BOSS_INSET,     BOSS_INSET    ),
    (W - BOSS_INSET, BOSS_INSET    ),
    (BOSS_INSET,     D - BOSS_INSET),
    (W - BOSS_INSET, D - BOSS_INSET),
]

# ── GEOMETRY HELPERS ─────────────────────────────────────────────────────────

def box(w, d, h):
    """Axis-aligned box with corner at origin."""
    return Manifold.cube([w, d, h])

def cyl_z(r, h, segs=SEGS):
    """Cylinder along +Z from z=0."""
    return Manifold.cylinder(height=h, radius_low=r, circular_segments=segs)

def cyl_y(r, y0, length, xc, zc, segs=SEGS):
    """Cylinder along +Y starting at y0, centred at (xc, _, zc)."""
    c = Manifold.cylinder(height=length, radius_low=r, circular_segments=segs)
    # rotate Z→Y: rotate +90° around X
    c = c.rotate([90, 0, 0])     # now along Y; spans y=0..length, centred x,z at 0
    # after rotation cylinder goes from y=0..length at xc,zc=0
    return c.translate([xc, y0, zc])

def rect_y(w, h, y0, length, xc, zc):
    """Box cutter through a wall in the Y direction.
    w: opening width (X), h: opening height (Z).
    """
    return box(w, length, h).translate([xc - w/2, y0, zc - h/2])

def rounded_rect_y(rw, rh, y0, length, xc, zc, segs=SEGS):
    """Rounded-rectangle (stadium) cutter through Y-direction wall.
    rw: total width, rh: total height (= 2*radius for pill shape).
    """
    r = rh / 2
    straight = rw - rh   # straight section length
    # Build in XZ plane, extrude in Y via hull trick:
    # Two cylinders separated in X, unioned (= stadium / discorectangle)
    c1 = cyl_y(r, y0, length, xc - straight/2, zc, segs)
    c2 = cyl_y(r, y0, length, xc + straight/2, zc, segs)
    return c1 + c2


def m3_boss(h):
    """Solid boss with insert pocket (from top)."""
    outer = cyl_z(BOSS_R, h)
    pocket = cyl_z(INSERT_R, INSERT_DEPTH + 0.1).translate(
        [0, 0, h - INSERT_DEPTH])
    return outer - pocket

def m3_through_hole(h):
    return cyl_z(SCREW_R, h + 0.2)

# ── BOTTOM SHELL ─────────────────────────────────────────────────────────────

def make_bottom_shell():
    print("  Building bottom shell outer body…")
    body = box(W, D, BOT_H)

    # Interior pocket (open top)
    pocket = box(W - 2*WS, D - 2*WS, BOT_H - WB + 0.1).translate([WS, WS, WB])
    body = body - pocket

    # ── Front face cutouts (Y=0 wall, thickness WS) ──────────────────────
    print("  Cutting front face…")
    y0   = -1.0
    wlen = WS + 2.0  # cutter depth (through-wall + 1 mm each side)

    # Display opening
    disp = box(DISP_W, wlen, DISP_H).translate([DISP_X, y0, DISP_Z])
    body = body - disp

    # Select buttons (4×)
    for bx in BTN_XC:
        body = body - cyl_y(BTN_R, y0, wlen, bx, BTN_ZC)

    # Status LEDs (6×)
    for lx in LED_XC:
        body = body - cyl_y(LED_R, y0, wlen, lx, LED_ZC)

    # Mode buttons (2× rounded rect)
    for mx in MODE_XC:
        body = body - rounded_rect_y(MODE_W, MODE_H, y0, wlen, mx, MODE_ZC)

    # ── Back face cutouts (Y=D wall) ─────────────────────────────────────
    print("  Cutting back face…")
    y0b  = D - WS - 1.0
    wlen = WS + 2.0

    # USB-A output × 4
    for bx in USBA_XC:
        body = body - rect_y(USBA_W, USBA_H, y0b, wlen, bx, USBA_PORT_ZC)

    # USB-A keyboard input
    body = body - rect_y(USBA_W, USBA_H, y0b, wlen, KBD_XC, USBA_PORT_ZC)

    # USB-C power (rounded rect)
    body = body - rounded_rect_y(USBC_W, USBC_H, y0b, wlen, USBC_XC, USBA_PORT_ZC)

    # ── Ventilation slots (X=W right-side wall) ──────────────────────────
    print("  Cutting vent slots…")
    x0v  = W - WS - 1.0
    for i in range(VENT_N):
        zc = VENT_ZC0 + i * VENT_PITCH
        slot = box(WS + 2.0, VENT_L, VENT_W).translate(
            [x0v, D/2 - VENT_L/2, zc - VENT_W/2])
        body = body - slot

    # ── Corner bosses ────────────────────────────────────────────────────
    print("  Adding corner bosses…")
    for bx, by in BOSS_CORNERS:
        b = m3_boss(BOSS_H).translate([bx, by, WB])
        body = body + b

    # ── Alignment rib on top rim ─────────────────────────────────────────
    rib_outer = box(W - 2*WS,        D - 2*WS,        RIB_H)
    rib_inner = box(W - 2*WS - 2*RIB_T, D - 2*WS - 2*RIB_T, RIB_H + 0.1) \
                    .translate([RIB_T, RIB_T, 0])
    rib = (rib_outer - rib_inner).translate([WS, WS, BOT_H - RIB_H])
    body = body + rib

    return body


# ── TOP LID ──────────────────────────────────────────────────────────────────

def make_top_lid():
    print("  Building top lid…")
    g = FIT_GAP

    # Flat outer plate
    plate = box(W, D, WT)

    # Step rebate (solid frame, extends below plate into shell)
    step_outer_w = W - 2*(WS + g)
    step_outer_d = D - 2*(WS + g)
    step_inner_w = W - 2*(WS + g + RIB_T + g)
    step_inner_d = D - 2*(WS + g + RIB_T + g)

    step_outer = box(step_outer_w, step_outer_d, LID_STEP_H) \
                     .translate([WS + g, WS + g, -LID_STEP_H])
    step_inner = box(step_inner_w, step_inner_d, LID_STEP_H + 0.1) \
                     .translate([WS + g + RIB_T + g, WS + g + RIB_T + g, -LID_STEP_H - 0.05])
    step = step_outer - step_inner

    lid = plate + step

    # M3 screw through-holes
    for bx, by in BOSS_CORNERS:
        hole = m3_through_hole(LID_TOTAL_H).translate(
            [bx, by, -LID_STEP_H - 0.1])
        lid = lid - hole

    return lid


# ── STL EXPORT ───────────────────────────────────────────────────────────────

def manifold_to_stl(m: Manifold, path: Path):
    """Export manifold mesh to binary STL via numpy-stl."""
    mesh_data = m.to_mesh()
    verts = mesh_data.vert_properties   # (N, 3)
    tris  = mesh_data.tri_verts         # (T, 3) int indices

    obj = stl_mesh.Mesh(np.zeros(len(tris), dtype=stl_mesh.Mesh.dtype))
    for i, tri in enumerate(tris):
        for j in range(3):
            obj.vectors[i][j] = verts[tri[j]]
    obj.save(str(path))
    kb = path.stat().st_size // 1024
    print(f"  ✓  {path.name}  ({len(tris):,} triangles, {kb} KB)")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    out = Path(__file__).parent / "stl"
    out.mkdir(exist_ok=True)

    print("HIDProxBox Enclosure STL Generator")
    print(f"Output: {out.resolve()}")
    print()

    print("── Bottom shell ─────────────────────────")
    bottom = make_bottom_shell()
    print(f"  mesh: {bottom.num_vert()} verts, {bottom.num_tri()} tris")
    manifold_to_stl(bottom, out / "enclosure_bottom.stl")
    print()

    print("── Top lid ──────────────────────────────")
    lid = make_top_lid()
    print(f"  mesh: {lid.num_vert()} verts, {lid.num_tri()} tris")
    manifold_to_stl(lid, out / "enclosure_top_lid.stl")
    print()

    print("Done.  See hardware/enclosure/print_notes.md for slicer settings.")


if __name__ == "__main__":
    main()
