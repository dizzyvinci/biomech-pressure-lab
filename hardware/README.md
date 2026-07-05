# hardware — the printable 3D models

Parametric **OpenSCAD** source (the print-ready models). OpenSCAD is free; STL is one click.

| File | Print in | What |
|---|---|---|
| [`ankle_pod.scad`](ankle_pod.scad) | PLA / PETG | Enclosure for ESP32-S3 + LiPo + microSD; USB-C + button + ribbon cutouts + strap slots |
| [`barefoot_sole.scad`](barefoot_sole.scad) | **soft TPU 85A** | Thin footbed with 8 FSR pockets + wire channels + strap slots |

## Get STLs (2 minutes)
1. Install **[OpenSCAD](https://openscad.org/downloads.html)** (free, Win/Mac/Linux).
2. Open a `.scad` file.
3. **Edit the parameters at the top** to your parts (measure your board / your foot).
4. Press **F6** (full render) → **File ▸ Export ▸ Export as STL**.
5. Slice in **Bambu Studio** and print.

## Print settings (starting points)
| Part | Material | Notes |
|---|---|---|
| **Ankle pod** | PLA or PETG | 0.4 mm, 3 walls, 20% infill; PETG if it'll get warm/sweaty |
| **Barefoot sole** | **soft TPU 85A** | 0.4/0.6 mm (TPU High-Flow hotend), ~15% gyroid, 3 walls; glue stick helps release |
| **Final insole** | soft + firm TPU | see [`../docs/insole_print_spec.md`](../docs/insole_print_spec.md) — dual-material on the H2D |

## True-fit tip
For a shoe insole that matches your foot, don't use the generic `barefoot_sole` outline — **boolean the FSR-pocket pattern into your *scanned* orthotic/insole** (scan per [`../docs/insole_print_spec.md`](../docs/insole_print_spec.md)).
