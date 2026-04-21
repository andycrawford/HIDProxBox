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

## Handheld (`enclosure_handheld.scad`) — rev 2

**Goal:** Redesigned to comply with the DVI-39 hardware constraint spec (received 2026-04-21).
Previous rev (120 × 62 × 22 mm, 2-computer) was too large and under-specified.

### Changes from rev 1

| Feature | Rev 1 (DVI-38 initial) | Rev 2 (DVI-39 constrained) | Rationale |
|---|---|---|---|
| Footprint | 120 × 62 mm | **90 × 50 mm** | DVI-39 specifies ≤ 90 × 50 mm target |
| Height | 22 mm | **30 mm** | Extra depth needed for 4× CH552T stack + battery headroom |
| Computer support | 2 (2× CH552T) | **4** (4× CH552T) | DVI-39 §1 — system requires 4 output computers |
| Select buttons | 2× | **4×** (two paired groups) | DVI-39 §11 — minimum 4× select |
| Status LEDs | 2× (3 mm) | **4×** (3 mm, one per computer) | Per spec: "same as desktop if space allows" |
| USB-A outputs | 2 (bottom-exit) | **4 (back panel)** | 4 outputs + 1 input = 5 ports; back-exit is cleaner for 5 cables |
| Battery | None | **Placeholder void** (TBD) | DVI-39 §8 / §11 — required; chemistry/capacity unresolved |
| Display | 1.3" OLED | **Omitted** | No space at 90 × 50 mm; spec marks it optional at this form factor |

### Design decisions

#### Form factor: 90 × 50 × 30 mm

- Meets the ≤ 90 × 50 mm footprint target from DVI-39 exactly at the boundary
- 30 mm height (vs. 22 mm rev 1) provides interior clearance for Pi Zero 2W + 4× CH552T on 10 mm standoffs + battery void: floor (2.5 mm) + Pi standoffs (~8 mm) + CH552T stack (~13 mm above Pi) = ~23.5 mm stack, plus lid (2 mm) = 25.5 mm → 30 mm shell gives 4.5 mm headroom for cables
- Pi Zero 2W (65 × 30 mm) fits within 86 × 46 mm interior pocket

#### Button layout: paired groups

4 select buttons are split into two visual groups of 2 (computers 1+2 on left, 3+4 on right) with a 22 mm inter-group gap on the front face. The 2 mode buttons are centred in that gap at a lower Z height. This mirrors the logical pairing used on the desktop and makes one-thumb selection easier.

#### Port placement: back-panel exit

5 USB-A ports (4 outputs + 1 input) exit the back panel. Rationale:
- 5 cables via the bottom edge creates cable-management chaos; back-panel grouping is cleaner
- USB-C power remains on the right side (unchanged from rev 1) for one-handed power-on access

#### Battery placeholder

DVI-39 §11 defers battery chemistry and capacity to a future decision. The shell reserves interior space beside the Pi for a slim LiPo (placeholder: 18 × 38 × 7 mm). Enable `SHOW_BATTERY_VOID = true` in the SCAD to visualise the reserved volume. Final cutout geometry and PCB/connector routing TBD once the battery spec is confirmed.

#### M2.5 fasteners (retained)

M3 bosses are too large for a 50 × 90 mm shell at 2 mm walls. M2.5 heat-set inserts (OD ~4 mm) fit a 3.8 mm outer boss with 1 mm wall margin. Boss height increased to 20 mm (from 15 mm) to match the taller 30 mm shell.

#### Corner radius: 4 mm (retained)

Handheld ergonomics benefit from a more rounded profile than the desktop's 2.5 mm. 4 mm is the practical maximum that still leaves flat wall area for vent slots and port cutouts.

### Hardware assumptions per DVI-39 spec

| Component | Spec dimension | DVI-39 ref |
|---|---|---|
| Raspberry Pi Zero 2 W | 65 × 30 mm | §11 |
| CH552T breakout board | ~40 × 15 mm (4× required) | §1 |
| Select button cap | 12 mm dia (handheld; spec unspecified) | §11 |
| Battery | TBD — chemistry/capacity unresolved | §8 / §11 |
| Display | Omitted (optional per spec) | §11 |

---

## Files

| File | Description |
|---|---|
| `enclosure_desktop_v2.scad` | Enhanced desktop — parametric OpenSCAD |
| `enclosure_handheld.scad` | Handheld — parametric OpenSCAD |
| `enclosure.scad` | Original Option A (DVI-35) — preserved for reference |
| `print_notes.md` | Print settings, orientation, and BOM for all variants |
| `generate_stl.py` | STL export script (update PARTS list to include new files) |
