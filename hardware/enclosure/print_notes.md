# HIDProxBox Enclosure — Print Notes

Option A: Compact Slab · 175 × 90 × 32 mm · DVI-35

## Files

| File | Description | Print orientation |
|------|-------------|-------------------|
| `stl/enclosure_bottom.stl` | Main tray (all walls + cutouts) | Floor face down, open top up |
| `stl/enclosure_top_lid.stl` | Flat cover | **Flip 180° in slicer** — outer face down, step faces up during print |

## Recommended Print Settings

| Setting | Value |
|---------|-------|
| Material | PLA or PETG |
| Layer height | 0.20 mm |
| Perimeters / walls | 3 |
| Infill | 20 % grid |
| Print speed | 40–60 mm/s |
| Estimated time | 5–7 hr total (both parts) |
| Supports | **None required** (see note below) |

## Display Opening Bridge

The display opening on the front face is 73 mm wide.  This span requires
bridging.  Two options:

- **Preferred:** Enable bridging detection in your slicer (Bambu/Orca/PrusaSlicer
  all handle this automatically at ≤ 60 mm/s bridge speed).  The top interior
  edge already has a 1.5 mm × 45° chamfer in the SCAD model to support the bridge.
- **Fallback:** Add a single horizontal support bar across the top of the display
  opening in the slicer; snap it off after printing.

All other openings (USB ports ≤ 12.5 mm, button holes ≤ 16 mm diameter,
LED holes 5 mm) bridge cleanly without settings changes.

## Assembly

1. Heat-set 4 × M3 inserts into the corner bosses in the bottom shell
   (18 mm deep boss, insert pocket is 6 mm from top).
2. Install internals:
   - Raspberry Pi horizontal on standoffs on the 3 mm floor
   - CH552T USB-serial boards stacked on 10 mm standoffs
   - Route cables to front (display, buttons, LEDs) and back (USB ports)
3. Seat the top lid — the step rebate registers on the alignment rib.
4. Fasten with 4 × M3 × 8 mm pan-head screws through the lid.

## Hardware BOM (fasteners)

| Qty | Part |
|-----|------|
| 4 | M3 × 4 mm heat-set inserts (e.g. M3 × OD5 × 4 mm) |
| 4 | M3 × 8 mm pan-head machine screws |

## Regenerating STLs

If you edit `enclosure.scad` (parametric OpenSCAD) or `generate_stl.py`
(Python/manifold3d generator), re-run:

```bash
cd hardware/enclosure
python3 generate_stl.py
```

Requires: `pip3 install manifold3d numpy-stl`

To preview or modify interactively, open `enclosure.scad` in OpenSCAD and set
`PART = "both"` / `"bottom"` / `"top"` at the bottom of the file.
