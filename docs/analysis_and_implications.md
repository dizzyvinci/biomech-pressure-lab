# Analysis & implications — from pressure to a print spec

Two scripts, in order:

1. **`analysis/analyze_pressure.py`** — the number-cruncher. Per condition (auto-groups by `mode` = shoe/barefoot, or `activity`): peak + impulse per zone, center-of-pressure path, cadence, and plots. Writes `summary.csv`, `hotspot.json`, PNGs.
2. **`analysis/interpret.py`** — the **implications engine**. Reads the same logs, computes a richer metric set, then a transparent rules engine turns the numbers into plain-language findings **and** concrete insole directives. Writes `report.md` + `insole_spec.json`.

```powershell
python analysis/analyze_pressure.py "day_*.csv" --out results/    # metrics + plots
python analysis/interpret.py       "day_*.csv" --out results/    # findings + directives
```

## The metrics (what's measured, and why it matters)
| Metric | Meaning | Why it matters |
|---|---|---|
| **Impulse** (∫F·dt) per zone | total load a zone carries over time | best single predictor of *where it hurts* — hot spot = max impulse |
| **Peak** per zone | highest instantaneous force | localized overload / bruising risk |
| **% load** per zone | share of total | balance across the foot |
| **Medial vs lateral** | inner vs outer share | pronation vs supination tendency |
| **Heel vs forefoot** | rear vs front share | where to prioritize cushioning |
| **Center-of-pressure path** | how load rolls foot-to-toe | roll-through quality; ML swing = stability |
| **ML excursion** | side-to-side COP swing | mediolateral instability → deeper heel cup |
| **Loading rate** | dF/dt at heel strike | a hard heel strike → soft heel cushion |
| **Cadence** | steps/min | context |

## The implications (how numbers → directives)
The rules engine is deliberately simple and transparent (read it in `interpret.py`). Examples:
- **max-impulse zone** → *relief window goes here*; if it's >1.6× the next zone → *aggressive* (softer + deeper recess).
- **medial ≫ lateral** → pronation → *medial posting*; **lateral ≫ medial** → supination → *lateral cushioning*.
- **heel > 55%** → *heel cushion priority*; **forefoot > 55%** → *met-pad*.
- **high loading rate** → *soft heel cushion*; **wide ML swing** → *deep heel cup*.

## Barefoot vs shoe (the comparison you asked for)
If both a `shoe` and `barefoot` run are present, `interpret.py` reports the delta at your hot spot:
- shoe **raises** load there → your footwear is *adding* to the problem → the insole should undo it.
- shoe **lowers** it → the shoe already helps → match/extend that.

## The output that drives the print
`insole_spec.json` → the design directives (relief-window zone, posting, cushion priority, heel cup) that feed straight into the [insole print spec](insole_print_spec.md): *put the relief window at zone X, post medial, soft heel.*

## Precision notes (honest)
- FSRs give **relative, repeatable** pressure. For true **kPa/Newtons**, calibrate each channel against known weights and fill `CALIB` in both scripts, then run `--calibrated`.
- More sensors (12–16) or a Velostat mat give a finer map; the 8-zone layout is a solid, cheap baseline.
- This is a measurement/design aid, **not a diagnosis** — pair persistent pain with a podiatrist.
