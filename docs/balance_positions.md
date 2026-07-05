# Balance across stance positions

`balance.py` scores one stance (eyes open/closed → Romberg). **`balance_positions.py`**
runs the full clinical battery across many positions — the same FSR center-of-pressure
+ IMU, now a **sensory-organization + stability screen**.

![balance across positions](balance_positions.svg)

## What it runs
| Protocol | Positions to record | Tells you |
|---|---|---|
| **mCTSIB** | `firm_eo`, `firm_ec`, `foam_eo`, `foam_ec` | which sense you rely on — vision / somatosensation / vestibular |
| **Romberg** | `firm_eo`, `firm_ec` | vision reliance (eyes-closed ÷ eyes-open sway) |
| **Single-leg** | `single_leg_L`, `single_leg_R` | left/right **asymmetry** + hold time |
| **Tandem** | `tandem` (+ `tandem_ec` = sharpened Romberg) | narrow-base, mediolateral control |
| **Limits of Stability** | `los` (a lean-to-your-edges run) | directional COP **reach** + workable base of support |
| **Load** *(every position)* | — | heel/forefoot & medial/lateral weight share from the FSRs |

## How to record
Long-press the pod button to name each run (it becomes the `mode`/`activity` column);
common aliases are recognised (`eyes_open`↔`firm_eo`, `sl_l`↔`single_leg_L`, `lean`↔`los`).
30 s per quiet condition; for **foam**, stand on a cushion/balance pad; for **LOS**, keep
your feet planted and lean to your limits front / back / left / right.

```bash
python balance_positions.py "sample/sample_balance_positions.csv" \
    --calibration sample/calibration.json --out sample/results
```

## Worked example ([report](../sample/results/report_balance_positions.md))
From the committed synthetic battery — a coherent, non-trivial read:

- **mCTSIB:** eyes-closed on firm ×2.3 (**vision-reliant**), foam eyes-open ×2.95 (leans on
  foot feel), **foam + eyes-closed ×7.9 — the failure mode → a vestibular contribution and
  real fall risk.**
- **Single-leg:** left 1260 vs right 623 mm² → **51 % asymmetry, left weaker** — train that side.
- **Tandem:** mediolateral-dominant, as expected for a narrow base.
- **LOS:** forward reach 104 mm, back 49, left/right 15 — A/P naturally exceeds M/L; compare
  *within* an axis to spot a weak direction.

## Reading it
A high ratio means that condition **degraded** balance — i.e. you were leaning on the sense
it removed. The foam + eyes-closed condition isolates the **vestibular** system; if that's
where sway explodes, it's the most fall-relevant finding. Single-leg asymmetry points to a
specific side to train; LOS points to a specific direction.

Not a medical device — a screening / training aid. Pair with a clinician (physical therapist
/ audiologist / neurologist) for anything the vestibular condition flags.
