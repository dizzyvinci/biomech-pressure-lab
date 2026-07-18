# FSR sensor layout — the 6-zone STEMMA-QT rig

Zone coordinates for the updated Path 2 electronics: **ESP32-C6 Feather + 6× FSR402**, no mux.
Companion to [`hardware/insole_fsr_layout.scad`](../hardware/insole_fsr_layout.scad) (the flat
carrier plate) — read them together. This doc gives the numbers; the `.scad` turns them into a
printable part.

> This is a **6-zone variant** of the repo's existing 8-zone scheme (see `ZONES` /
> `SENSOR_XY` in [`analysis/analyze_pressure.py`](../analysis/analyze_pressure.py) and the
> `zones` array in [`hardware/barefoot_sole.scad`](../hardware/barefoot_sole.scad)). Same
> coordinate convention, same zone names, just **met3 and toes dropped**. That's not an
> accuracy compromise picked at random — it's sized to the hardware: the ESP32-C6 Feather
> exposes exactly **six** analog-capable pins (`A0`–`A5`), so 6 FSRs wire straight in with no
> multiplexer, one sensor per pin. The 8-zone rig needs a `CD74HC4067` mux for that reason; this
> one doesn't. If you want the finer 8-zone map later, add the mux back (same part as the
> existing rig) and go back to the full `ZONES` list — the FSR 10-pack has the sensors for it
> already, this is a wiring-simplicity choice, not a hardware ceiling.

## Zones — normalized position

Same `[x medial→lateral, y heel→toe]` fractions used elsewhere in the repo (0..1 each), and the
wiring order they land on (`fsr0`..`fsr5` → `A0`..`A5` on the Feather):

| # | Zone | x_frac | y_frac | Feather pin |
|---|---|---|---|---|
| 0 | `heel_med` | 0.35 | 0.08 | `A0` |
| 1 | `heel_lat` | 0.65 | 0.08 | `A1` |
| 2 | `midfoot`  | 0.50 | 0.45 | `A2` |
| 3 | `met1`     | 0.30 | 0.72 | `A3` |
| 4 | `met5`     | 0.70 | 0.72 | `A4` |
| 5 | `hallux`   | 0.28 | 0.92 | `A5` |

`x_frac` is measured across a **`FOOT_W`-wide band centered under the foot** (medial edge = 0),
not the full shoe width; `y_frac` is measured heel-back-edge (0) to toe (1) along the foot's long
axis. This is the same simplification `analysis/zone_load.py`'s `zone_mm()` and
`hardware/barefoot_sole.scad` already use — one width value for the whole foot, not a per-row
taper.

## Coordinates in mm — worked example, men's ~US10

```
FOOT_LEN = 267 mm                          # men's ~US10 (~10.5"); ±5 mm across shoe-size charts
FOOT_W   = FOOT_LEN × (95 / 255) ≈ 99.5 mm  # same length:width ratio as refs/plantar_norms.json's
                                             # reference foot — the repo's existing norms-DB ratio
x_mm = x_frac × FOOT_W
y_mm = y_frac × FOOT_LEN     # from the heel's back edge
```

| Zone | x (mm, from medial edge) | y (mm, from heel) |
|---|---|---|
| `heel_med` | 35 | 21 |
| `heel_lat` | 65 | 21 |
| `midfoot`  | 50 | 120 |
| `met1`     | 30 | 192 |
| `met5`     | 70 | 192 |
| `hallux`   | 28 | 246 |

## Scaling to your own foot

Two options, same as [`docs/fit_to_your_foot.md`](fit_to_your_foot.md):

1. **Just change `FOOT_LEN`** in `hardware/insole_fsr_layout.scad` (or the formula above) — width
   rescales automatically off the 95:255 ratio. Fastest, ~90% accurate.
2. **Use your real measurements** — if you've already measured `length` / `forefoot-width` for
   `build_insole.py` (docs/fit_to_your_foot.md §Level 2), reuse those directly instead of the
   derived ratio: `x_mm = x_frac × your_forefoot_width_mm`, `y_mm = y_frac × your_length_mm`.
   Closer fit if your foot is unusually narrow/wide for its length.

## Compatibility note for the analysis scripts

`analyze_pressure.py`, `zone_load.py`, `day_summary.py`, `nerve_fascia.py`, and
`make_sample_data.py` all currently expect **8** FSR columns (`ZONES`/`SENSOR_ZONES` includes
`met3` and `toes`). Logs from this 6-zone rig only have `fsr0..fsr5`. Two ways to reconcile —
neither is done yet, flagged here the same way `path2_tracking_build.md` flags its own
`mode`-column TODO:
- **Quick:** zero-fill (or interpolate, like `zone_load.py` already does for `met2`/`met4`) the
  missing `met3`/`toes` columns before feeding a log into the existing scripts.
- **Clean:** edit the `ZONES` list at the top of each script to the 6-zone set in the table
  above and drop the `met3`/`toes` references. Small, mechanical change — same pattern as adding
  the mux back if you upgrade to 8 zones later.

## Printing

[`hardware/insole_fsr_layout.scad`](../hardware/insole_fsr_layout.scad) turns this table into a
part — either a thin TPU wearable carrier, or a quick PLA layout jig to trace the zones onto a
shoe/orthotic by hand. Pockets are sized for the same
[`hardware/fsr_puck.scad`](../hardware/fsr_puck.scad) force-concentrator used elsewhere in the
repo. Full print settings + assembly order: [`BUILD_PLAN.md`](BUILD_PLAN.md).

Not a medical device — a build reference, same as the rest of `docs/`.
