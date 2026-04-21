# HIDProxBox Enclosure — Print Notes

Three variants across two tickets (DVI-35 original · DVI-38 enhanced):

| Variant | File | Footprint | Ticket |
|---|---|---|---|
| Desktop original | `enclosure.scad` | 175 × 90 × 32 mm | DVI-35 |
| Desktop v2 (enhanced) | `enclosure_desktop_v2.scad` | 175 × 90 × 22–32 mm (tilt) | DVI-38 |
| Handheld | `enclosure_handheld.scad` | 120 × 62 × 22 mm | DVI-38 |

See `design-rationale.md` for the motivation behind v2 changes and handheld design decisions.

---

## Desktop v2 (`enclosure_desktop_v2.scad`)

### Parts

| File | Description | Print orientation |
|---|---|---|
| `stl/desktop_v2_bottom.stl` | Shell with tilted walls, vent slots both sides | Floor face down, open top up |
| `stl/desktop_v2_lid.stl` | Wedge-profile flat lid with logo recess | **Flip 180°** — outer face down, step faces up |

### Print settings

| Setting | Value |
|---|---|
| Material | PLA or PETG |
| Layer height | 0.20 mm |
| Perimeters / walls | 3 |
| Infill | 20 % grid |
| Supports | **None required** |
| Print speed | 40–60 mm/s |
| Estimated time | 5–7 hr total |

### Notes

- Front-face display opening (73 mm) requires slicer bridging detection or a 45° chamfer bridge (already included). No manual supports needed.
- The tilted shell has a 24 mm front / 32 mm rear height. Orient the rear face toward the back of the build plate so the rear wall is tallest.
- Stick Ø12 mm rubber feet into the four floor recesses (1.5 mm deep) before assembling.
- Logo badge: the 45 × 14 mm recess on the lid accepts a laser-cut or printed acrylic badge; secure with thin double-sided tape.

### Assembly

1. Heat-set 4× M3 inserts into corner bosses (6 mm deep pockets, 18 mm boss at rear, ~14 mm at front).
2. Install Raspberry Pi on standoffs on the 3 mm floor; route cables to front (display, buttons, LEDs) and back (USB ports).
3. Seat lid — step rebate registers on alignment rib.
4. Fasten with 4× M3 × 10 mm pan-head screws (lid step adds ~1.5 mm; M3 × 8 mm from v1 may be too short).

### Hardware BOM (desktop v2)

| Qty | Part |
|---|---|
| 4 | M3 × 4 mm OD5 heat-set inserts |
| 4 | M3 × 10 mm pan-head machine screws |
| 4 | Ø12 mm self-adhesive rubber feet |
| 1 | Logo badge, 45 × 14 mm (optional) |

---

## Handheld (`enclosure_handheld.scad`)

### Parts

| File | Description | Print orientation |
|---|---|---|
| `stl/handheld_bottom.stl` | Shell with grip ridges, ports on bottom + right | Floor face down |
| `stl/handheld_top.stl` | Flat cap | **Flip 180°** — outer face down |

### Print settings

| Setting | Value |
|---|---|
| Material | PETG preferred (more flexible, less brittle for handheld) |
| Layer height | 0.15 mm (finer detail for grip ridges) |
| Perimeters / walls | 4 (handheld sees more flexing) |
| Infill | 25 % gyroid |
| Supports | **None required** |
| Print speed | 35–45 mm/s |
| Estimated time | 3–4 hr total |

### Notes

- Port placement: USB ports exit the bottom edge; USB-C power enters the right side. Orient accordingly in the slicer.
- Grip ridges: the three triangular ridges per side are part of the shell body — do not fill or remove them.
- Display opening is 34 × 14 mm (1.3" OLED SH1106 or SSD1306). Module PCB is ~36 × 16 mm and sits inside on hot-glue standoffs.
- 2-computer variant only (2× CH552T + 2× USB-A output + 1× USB-A input).

### Assembly

1. Heat-set 4× M2.5 inserts into corner bosses (4.5 mm deep, boss height 15 mm).
2. Install Pi Zero 2W + 2× CH552T boards on 2.5 mm floor. Both boards fit within 120 × 62 mm interior with ~4 mm clearance per side.
3. Route USB cables through bottom cutouts before seating PCBs.
4. Thread OLED ribbon cable through display opening; secure module with hot glue.
5. Seat top cap; fasten with 4× M2.5 × 8 mm pan-head screws.

### Hardware BOM (handheld)

| Qty | Part |
|---|---|
| 4 | M2.5 × 3 mm OD4 heat-set inserts |
| 4 | M2.5 × 8 mm pan-head machine screws |
| 1 | 1.3" OLED module (SH1106 or SSD1306, 128×64) |
| 2 | 12 mm momentary push-button caps (select) |
| 1 | 12 × 6 mm momentary push-button (mode) |
| 2 | 3 mm LED (status) |

---

## Generating STLs

### Desktop original (Python/manifold3d)

```bash
cd hardware/enclosure
python3 generate_stl.py
# Outputs: stl/enclosure_bottom.stl, stl/enclosure_top_lid.stl
```

Requires: `pip3 install manifold3d numpy-stl`

### Desktop v2 and Handheld (OpenSCAD CLI)

```bash
cd hardware/enclosure

# Desktop v2 bottom
openscad -D 'PART="bottom"' -o stl/desktop_v2_bottom.stl enclosure_desktop_v2.scad

# Desktop v2 lid
openscad -D 'PART="top"' -o stl/desktop_v2_lid.stl enclosure_desktop_v2.scad

# Handheld bottom
openscad -D 'PART="bottom"' -o stl/handheld_bottom.stl enclosure_handheld.scad

# Handheld top
openscad -D 'PART="top"' -o stl/handheld_top.stl enclosure_handheld.scad
```

Requires: OpenSCAD 2021.01 or later (`brew install openscad` on macOS).

### Interactive preview

Open any `.scad` file in OpenSCAD and set `PART = "both"` to see the assembled view.
Use `PART = "bottom"` or `PART = "top"` before exporting STLs.
