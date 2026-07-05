# Balance module — posturography from the same rig

**The extrapolation:** the same insole hardware (FSR center-of-pressure + IMU) is also a **wearable balance lab**. For people with **balance issues** — not just foot pain — `analysis/balance.py` turns a standing recording into standard **posturography** metrics + fall-risk flags. Same sensors, same pod, new capability.

## Who it's for
Anyone screening or training **postural stability**: older adults (fall risk), vestibular / proprioceptive issues, neurological conditions, hypermobility, post-injury return-to-play. **Not a diagnosis** — a screening/training aid to use with a clinician.

## Protocols (label the runs)
Long-press the pod button to name each condition (it becomes the `mode` column):
- **`eyes_open`** — quiet standing, 30 s, feet together.
- **`eyes_closed`** — same, eyes shut (isolates vision → the Romberg test).
- **`single_leg`** — one-leg stance (harder; stability/time).
- Optional: firm vs foam surface, dual-task (counting), etc.

## Metrics (standard posturography)
| Metric | What it is | Higher = |
|---|---|---|
| **Sway ellipse area** (mm²) | 95% confidence ellipse of COP | more instability |
| **Path length / velocity** | how far/fast the COP travels | more correction effort |
| **ML vs AP RMS** | side-to-side vs front-back sway | direction of instability |
| **Trunk sway** (IMU) | upper-body wobble | more instability |
| **Romberg quotient** | eyes-closed area / eyes-open area | **>2 → strong vision reliance** |

## What it tells you (transparent rules)
- **Large ellipse area / high velocity** → reduced stability → fall-risk screen warranted.
- **ML-dominant** → side-to-side instability → wider base / lateral support.
- **AP-dominant** → front-back → ankle strategy / heel-toe support.
- **Romberg > 2** → leans heavily on vision (proprioceptive/vestibular deficit pattern) → balance training with eyes closed.

## Run it
```powershell
python analysis/balance.py "stand_*.csv" --out results/           # relative units
python analysis/balance.py "stand_*.csv" --calibration calibration.json --out results/
```
→ `results/report_balance.md` (findings + flags) + `balance_metrics.json`.

## Where it goes next (the assist tie-in)
Balance findings map to **device classes** the same way pressure maps to insole tweaks — e.g. ML instability → a wider/lateral-support base; strong vision reliance → a haptic/cue trainer. (This mirrors the `bml assist` "analysis → device" layer in the sibling **biomech-lab** platform.) A natural expansion, same hardware.

## Honest limits
Sway thresholds here are **relative screening** values — calibrate to the individual (baseline them) before reading absolutes. FSR COP is coarser than a lab force plate but tracks the *same* trends and is wearable + cheap.
