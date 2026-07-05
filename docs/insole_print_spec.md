# Insole print spec — variable-density TPU with a targeted relief window

The payoff of the whole lab: a printed insole that is **soft exactly where you hurt, firm where you need support, and hollowed out (offloaded) under the hot spot** the pressure analysis found. Off-the-shelf pads can't do any of that.

Printer: **Bambu H2D** + **TPU High-Flow Kit** (dual nozzle → soft + firm in one print).

---

## 1. Get the base geometry (scan your orthotic — don't scan a bare foot)
Your existing custom orthotic is a rigid object that already encodes your foot; it scans far better than a soft, moving foot.

1. Matte it (baby powder / matte spray — kill any gloss).
2. Set on newspaper/patterned mat, even light. iPhone: **Scaniverse** or **Polycam** (LiDAR **or** photo). Photo mode = finer detail for a small object.
3. Orbit high + low; flip it, scan the underside too. Include a **ruler/coin** if using pure photogrammetry (for true scale).
4. Export **STL** → clean in Blender/Fusion (remove stray faces, make watertight).

## 2. Zone the insole (from `analysis/results/hotspot.json`)
| Region | Material / nozzle | Lattice | Durometer target |
|---|---|---|---|
| **Heel cushion** (your hot zone) | soft nozzle | gyroid/honeycomb **~12–18%** | soft TPU **~85–90A** or foaming TPU (VarioShore) |
| **Arch / support shell** | firm nozzle | **~35–45%** | **TPU 95A HF** |
| **Forefoot** | soft/medium | ~20–25% | 90–95A |
| **Relief window** (under hot spot) | soft, recessed | see below | — |

## 3. The relief window (the special sauce)
Place it at the **overall_hot_zone** from `hotspot.json` (e.g. `heel_med`):
- A shallow **recess** (1.5–3 mm deep) in the top surface directly under the sore point, **surrounded by a raised "doughnut"** so load transfers to the healthy tissue around it — classic offloading.
- Fill the recess with the **softest lattice** (or leave a thin membrane over a low-density pocket) so it deflects first.
- Keep the window **~15–25 mm** across — big enough to unload the spot, small enough that you don't sink through.

## 4. Design tooling (pick one)
- **Ergono3D** (parametric insole → print-ready STL; add zones) — fastest.
- **Fusion 360 / Blender** — import scan, sculpt top surface, boolean the relief recess, apply variable infill via **modifier meshes** in Bambu Studio (per-zone infill %).
- In **Bambu Studio**: assign the two filaments to the two nozzles; use **modifier volumes** to set infill density per zone and to switch soft↔firm material by region.

## 5. Print settings (starting point, TPU High-Flow hotend)
- Nozzle 235–250 °C, bed 45–55 °C, **0.6 mm hotend** for the cushion (fast, thick, forgiving), 0.4 mm for detail.
- Speed 20–35 mm/s for soft TPU; **infill = honeycomb** (best energy absorption) in cushion zones.
- Feed soft/foaming TPU from an **external spool** (not AMS). VarioShore: print ~10–20 °C hotter to trigger foaming, slower flow → softer.
- Walls 2–3, top/bottom 3–4 so the lattice doesn't telegraph through.

## 6. Sensor-carrier version (for measuring, before/after)
Print a **second, thin (2–3 mm) flat TPU insole** with **8 shallow pockets** at the `SENSOR_XY` positions to seat the FSR402 pads, plus a routed channel to the instep for the wiring bundle. Slide it under your normal insole to record → this is what generates the logs `analyze_pressure.py` reads.

## 7. ESP32 enclosure
Small printed clip-on box (PLA/PETG fine here — no flex needed) for the ESP32-S3 + LiPo + SD, worn at the ankle/laces. Include: USB-C cutout, a hole for the button (GPIO14), a light pipe for the LED (GPIO15), and a slot for the sensor ribbon.

---

## The loop
1. Print **sensor-carrier** → record `stand/walk/stairs/pivot` → `analyze_pressure.py` → get **hot zone**.
2. Print **insole v1** with the relief window at that zone.
3. Re-record **with v1 installed** → confirm peak + impulse at the hot zone **dropped**.
4. Not enough? Enlarge/soften the window, drop cushion infill 3–5%, reprint. Repeat until the hot-zone impulse flattens out.
