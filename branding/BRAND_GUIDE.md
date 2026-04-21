# HIDProxBox Brand Style Guide

> Version 1.0 · April 2026

---

## Brand Essence

**HIDProxBox** is a hardware-first open-source project. The visual identity reflects its core values: precision, transparency, and technical craftsmanship. The aesthetic draws from embedded-systems culture — circuit boards, terminal interfaces, and clean engineering — without veering into clichéd "hacker" imagery.

**Tagline:** *One keyboard. Four computers. Zero software on the targets.*

---

## Logo

### Files

| File | Use case |
|---|---|
| `branding/icon.svg` | Favicon, app icon, avatar (64×64 base, scalable) |
| `branding/logo-dark.svg` | Dark backgrounds, GitHub README header, dark mode UI |
| `branding/logo-light.svg` | Light backgrounds, print, light mode UI |
| `branding/social-preview.svg` | GitHub repository social preview (1280×640) |
| `branding/readme-banner.svg` | README header banner (1280×200) |

### Icon mark

The icon depicts the HIDProxBox proxy concept directly:
- **Cyan dot + line (left):** A single keyboard/mouse input source
- **Dark rounded box (center):** The HIDProxBox hardware, styled as an IC package with corner pads
- **Blue dot (center inside):** The routing/switching node
- **Blue lines + dots (right):** Four target computers

The IC-package corner pads and internal bus give the icon a deliberate circuit-board character at any scale.

### Wordmark

The wordmark uses three typographic segments in three brand colors:

```
HID     Prox    Box
cyan    white   blue
```

- **HID** — `#22D3EE` (Cyan 400) — identifies the Human Interface Device protocol
- **Prox** — `#F1F5F9` (Slate 50) — the proxy/switching core
- **Box** — `#3B82F6` (Blue 500) — the hardware box

On light backgrounds, use the light-variant colors: `#0891B2` / `#0F172A` / `#2563EB`.

### Clear space

Maintain a minimum clear space of **0.5× the icon height** on all sides. Never crowd the logo against other elements.

### Don't

- Don't recolor individual wordmark segments arbitrarily
- Don't stretch or distort the icon
- Don't place the dark logo on a dark background (use the light variant instead)
- Don't apply drop shadows or glows to the logo
- Don't use the wordmark alone without the icon in primary applications

---

## Color Palette

### Primary colors

| Name | Hex | RGB | Use |
|---|---|---|---|
| **Midnight** | `#090D1A` | 9, 13, 26 | Page/card background (dark) |
| **Navy** | `#0F172A` | 15, 23, 42 | Surface background (dark) |
| **Slate** | `#1E293B` | 30, 41, 59 | Card/box fill, icon body |

### Accent colors

| Name | Hex | RGB | Use |
|---|---|---|---|
| **Cyan** | `#22D3EE` | 34, 211, 238 | Input indicator, "HID" wordmark, active state |
| **Electric Blue** | `#3B82F6` | 59, 130, 246 | Output/computer connections, "Box" wordmark, primary CTA |

### Text colors

| Name | Hex | RGB | Use |
|---|---|---|---|
| **White** | `#F1F5F9` | 241, 245, 249 | Primary text on dark |
| **Muted** | `#94A3B8` | 148, 163, 184 | Secondary/body text on dark |
| **Dim** | `#475569` | 71, 85, 105 | Tertiary/caption text on dark |
| **Border** | `#334155` | 51, 65, 85 | Dividers, card borders |

### Light-mode accent colors

When rendering on white or light-grey backgrounds, use these slightly darker variants to preserve contrast:

| Dark variant | Light variant |
|---|---|
| `#22D3EE` Cyan | `#0891B2` Cyan 600 |
| `#3B82F6` Blue | `#2563EB` Blue 600 |

### Color roles summary

- **Cyan** = input / source / active selection
- **Blue** = output / destination / interactive
- **White** = content / data
- **Dark navy/slate** = structure / background / hardware

---

## Typography

### Wordmark / Code / Data

```
Font:   JetBrains Mono, Fira Code, Courier New, monospace
Weight: 700 (Bold)
Usage:  Logo wordmark, code samples, hex values, terminal output
```

### UI / Body / Marketing

```
Font:   Inter, system-ui, -apple-system, sans-serif
Weight: 400 (Regular) / 600 (Semi-bold) / 700 (Bold)
Usage:  Taglines, feature descriptions, badge labels, README prose
```

### Type scale

| Role | Size | Weight | Color |
|---|---|---|---|
| Hero title | 80–90px | 700 | white (three-color split) |
| Section heading | 48–56px | 700 | white |
| Subheading | 28–32px | 600 | Muted |
| Body | 16–18px | 400 | Muted |
| Caption / badge | 12–14px | 600 | Dim |
| Code | 14–16px | 400–700 | Cyan or white |

---

## Iconography & Visual Language

- Use **monoline** icon style (1.5–2px strokes) to match the logo's circuit-trace aesthetic
- Prefer **rounded linecaps** and **rounded joins**
- Use **dots at endpoints** to signify connections (circuit-pad visual language)
- Use **dashed lines** sparingly to indicate non-active or potential connections
- Avoid filled blob icons; prefer outline-on-dark

---

## Background Patterns

The brand uses a **dot-grid background pattern** for large surfaces (social cards, banners):

```
Pattern:  40×40px repeating tile
Element:  1px circle at center
Color:    #1E2D45 (slightly lighter than Midnight)
Opacity:  70–90%
```

Circuit trace accents (thin lines that make 90° turns with junction dots) may be added to backgrounds for texture, using the same `#1E2D45` color at low opacity. Keep them subtle — they should read as texture, not content.

---

## Badge / Pill Style

Feature badges use this treatment:

```
Background:  #1E293B
Border:      1px solid — Cyan or Blue, depending on category
Border-radius: 5–6px
Padding:     8px 12px
Font:        Inter, 13px, 600
Text color:  accent or Muted (94A3B8)
Leading dot: 5px filled circle in accent color
```

Use **Cyan** borders for input-related features (keyboard, source, wired).  
Use **Blue** borders for output-related features (computers, Bluetooth, USB).

---

## GitHub-Specific Usage

| Location | Asset | Notes |
|---|---|---|
| Repository social preview | `social-preview.svg` → export to PNG | GitHub requires a PNG; export at 1280×640 |
| README header | `readme-banner.svg` | Reference as `./branding/readme-banner.svg` in README |
| README inline logo | `logo-dark.svg` | Use with `align="left"` for floating header |
| Issues / Discussions avatar | `icon.svg` | 64px base, GitHub will resize |

### Exporting SVG → PNG

GitHub's social preview field requires a PNG. Export `social-preview.svg` at its native 1280×640 resolution:

```bash
# Using Inkscape (headless)
inkscape branding/social-preview.svg \
  --export-type=png \
  --export-filename=branding/social-preview.png \
  --export-width=1280

# Using rsvg-convert
rsvg-convert -w 1280 -h 640 branding/social-preview.svg -o branding/social-preview.png

# Using Chrome headless
chrome --headless --screenshot=branding/social-preview.png \
  --window-size=1280,640 branding/social-preview.svg
```

---

## Voice & Tone (Brand Alignment)

Although primarily a visual guide, keep these tone principles in mind for copy that appears alongside brand assets:

- **Direct** — state what it does, not what it "empowers" you to do
- **Technical but not jargon-heavy** — assume a capable audience; don't over-explain standard concepts
- **Hardware-grounded** — lead with the physical reality (chips, wires, buttons) before abstractions
- **Open-source honest** — acknowledge trade-offs, show real commands, credit the stack

---

*This guide covers v1.0 of the HIDProxBox brand identity. Update this document when any asset is revised.*
