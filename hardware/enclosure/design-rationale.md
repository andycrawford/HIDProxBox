# HIDProxBox Enclosure Design Rationale — DVI-38

Two form factors: enhanced desktop slab and compact handheld.

---

## Desktop v2 (`enclosure_desktop_v2.scad`)

**Goal:** Iterate the DVI-35 Option A slab with ergonomic, visual, and assembly improvements while preserving full hardware and mounting compatibility.

### Changes from v1

| Feature | v1 (DVI-35) | v2 (DVI-38) | Rationale |
|---|---|---|---|
| Top profile | Flat, 32 mm | 3° tilt — 24 mm front, 32 mm rear | Wedge profile puts the display at a natural upward-facing angle for desk use; reduces perceived bulk |
| Ventilation | Right side only, 5 plain slots | Both sides, 10 paired slots | Pi 4 under load can reach 70–80 °C; adding the left side roughly doubles airflow cross-section |
| Underside | Plain floor | 4× Ø12 mm rubber-foot recesses | Flat plastic slides on smooth desks; recesses locate stick-on rubber feet precisely |
| Lid | Smooth flat | Shallow logo-plate recess (45 × 14 mm) | Provides a registration pocket for a printed or cut vinyl logo badge; removable without damaging paint |
| Interior | No cable management | Clip boss near USB-C power port | Prevents the USB-C cable from pulling the power connector loose during port switching |
| Front panel | No separator | Shallow label groove between display zone and button zone | Visual cue separating the status display from the input-select controls |

### What stayed the same

- 175 × 90 mm footprint — existing mounts/brackets fit without change
- Back panel port centres (USB-A output ×4, keyboard input, USB-C power)
- Front panel display opening (73 × 22 mm), button positions, LED positions
- M3 heat-set inserts, M3 × 10 mm lid screws (×4)
- Two-piece (bottom shell + flat lid) FDM design, zero supports

### Tilt geometry note

The tilt is implemented as a hull between a 24 mm front cross-section and a 32 mm rear cross-section. The lid top surface is flat; the underside follows the tilt so the lid sits flush on the tilted rim. Boss heights vary front-to-rear to keep boss tops level with the split plane. This approach avoids non-manifold geometry and prints cleanly without supports.

---

## Handheld (`enclosure_handheld.scad`)

**Goal:** A pocket-sized 2-computer variant for field use, battery-adjacent power, and one-handed operation.

### Design decisions

#### Form factor: 120 × 62 × 22 mm candy-bar

- Pi Zero 2W (65 × 30 mm) is the smallest Pi with adequate compute and built-in BT/WiFi
- 2-computer variant keeps the footprint to 2× CH552T boards (~40 × 15 mm each)
- 22 mm height accommodates the board stack + cables with a 2.5 mm floor and 2 mm lid
- 120 mm length fits a normal adult hand without being longer than a phone

#### Port placement: bottom-exit

All USB ports (keyboard input + 2× output) exit through the bottom edge rather than a rear face. Rationale:
- Handheld use means cables must exit downward (toward a desk/bag) — rear-exit cables create awkward slack when held
- Keeps the front face clean (display + buttons only) and the sides unobstructed for grip
- USB-C power enters the right side (thumb-side for right-hand grip) so the power cable does not interfere with the left-hand-grippable left side

#### Grip ridges

Three triangular ridges on each long side (left/right walls). These add 0.8 mm of protrusion and prevent the device from slipping when held. The triangular cross-section is self-cleaning (no debris traps) and adds minimal material.

#### 1.3" OLED display (34 × 14 mm opening)

The 1.3" SH1106/SSD1306 OLED is the smallest display that can show two lines of legible text for active-computer status. The display opening is positioned left-of-centre to leave room for two select buttons on the right of the same face.

#### M2.5 fasteners

M3 bosses are too large for a 62 × 120 mm shell at 2 mm walls. M2.5 heat-set inserts (OD ~4 mm) fit a 3.8 mm outer boss with 1 mm wall margin. Boss height is 15 mm — sufficient for a 4.5 mm insert pocket plus clamping depth.

#### Corner radius: 4 mm

Larger than desktop v2 (2.5 mm) because handheld ergonomics benefit from a more rounded profile; sharp corners are uncomfortable to grip. 4 mm is the practical maximum that still leaves flat wall area for the vent slots and port cutouts.

### Hardware assumptions (verify with Systems Developer before STL export)

| Component | Assumed dimension | Source |
|---|---|---|
| Pi Zero 2W PCB | 65 × 30 mm | Raspberry Pi datasheet |
| CH552T breakout board | ~40 × 15 mm | Manufacturer listing |
| 1.3" OLED module | 36 × 16 mm module; 34 × 14 mm active | Typical AliExpress/Adafruit SH1106 |
| 12 mm tactile button cap | Ø12 mm, 9 mm travel | Standard momentary push-button |

If the actual CH552T board is taller (some variants are 20 mm wide), interior height may need to increase from 22 to 26 mm, increasing weight by ~15 g.

---

## Files

| File | Description |
|---|---|
| `enclosure_desktop_v2.scad` | Enhanced desktop — parametric OpenSCAD |
| `enclosure_handheld.scad` | Handheld — parametric OpenSCAD |
| `enclosure.scad` | Original Option A (DVI-35) — preserved for reference |
| `print_notes.md` | Print settings, orientation, and BOM for all variants |
| `generate_stl.py` | STL export script (update PARTS list to include new files) |
