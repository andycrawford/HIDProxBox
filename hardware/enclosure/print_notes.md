# HIDProxBox Enclosure — Print Notes

Three variants across two tickets (DVI-35 original · DVI-38 enhanced):

| Variant | File | Footprint | Ticket |
|---|---|---|---|
| Desktop original | `enclosure.scad` | 175 × 90 × 32 mm | DVI-35 |
| Desktop v2 (enhanced) | `enclosure_desktop_v2.scad` | 175 × 90 × 22–32 mm (tilt) | DVI-38 |
| Handheld | `enclosure_handheld.scad` | 90 × 50 × 30 mm | DVI-38 |

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

## Handheld (`enclosure_handheld.scad`) — rev 2

Redesigned per DVI-39 hardware constraint spec.  See `design-rationale.md` for full change log.

### Parts

| File | Description | Print orientation |
|---|---|---|
| `stl/handheld_bottom.stl` | Shell with grip ridges, back-panel ports, left-side vents | Floor face down |
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

- Port placement: 4× USB-A output + 1× USB-A input exit the back panel; USB-C power/charge enters the right side.
- Grip ridges: three triangular ridges per long side — do not fill or remove them.
- No display opening (display omitted at this form factor — see DVI-39 §11).
- Battery void: enable `SHOW_BATTERY_VOID = true` in the SCAD before printing to verify battery fit. Actual battery cutout TBD once DVI-39 battery spec is confirmed.

### Assembly

1. Heat-set 4× M2.5 inserts into corner bosses (4.5 mm deep pockets, boss height 20 mm).
2. Install Pi Zero 2W on 3 mm standoffs above the 2.5 mm floor.
3. Install 4× CH552T boards on 10 mm standoffs above the Pi.
4. Route USB cables to back panel before seating top cap.
5. Install battery once spec confirmed (void located beside Pi Zero 2W footprint).
6. Seat top cap; fasten with 4× M2.5 × 8 mm pan-head screws.

### Hardware BOM (handheld)

| Qty | Part |
|---|---|
| 4 | M2.5 × OD4 × 3 mm heat-set inserts |
| 4 | M2.5 × 8 mm pan-head machine screws |
| 4 | 12 mm momentary push-button caps (select, one per computer) |
| 2 | 9 × 4 mm momentary push-button (mode) |
| 4 | 3 mm LED (status, one per computer) |
| 1 | LiPo battery — chemistry/capacity TBD (DVI-39 §8) |

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
