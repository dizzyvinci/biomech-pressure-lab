# Maker hacks — squeezing lab-grade data out of $150 of parts

Cheap sensors have **known, documented failure modes**: Velostat and FSRs drift, creep, and
ghost; the HX711 is noisy; a coarse matrix looks blocky. None of that is fatal — the maker /
research community has field-tested tricks that recover most of the accuracy for pennies.
This is that toolbox, each hack tied to the exact problem it fixes and cited to the source.

Ethos (same as [`lab_scope.md`](lab_scope.md)): we're chasing **r≈0.87, not 1.0** — trend-level
truth for *your* foot, cheaply, at scale. The hacks below are what get us from "toy" to "0.87".
The code-able ones are already baked into the firmware + scripts (see the last section).

---

## 0 · Universal (any DIY sensor)

| Problem | Hack | Why / source |
|---|---|---|
| **Break-in drift** — the first minute + first cycles read high/low as the material settles | **Precondition:** cycle the sensor 15–20× to your working load, then discard the first ~60 s of every session before recording | Velostat shows cyclic drift up to **0.00715 V/cycle** and up to a **67% range shift** from cyclic+thermal effects — most of it is early; loading it in first stabilizes the curve ([Velostat in-socket study](https://ieeexplore.ieee.org/document/9024130/)) |
| **Nonlinearity** — raw resistance ≠ force; a single calibration point lies everywhere else | **Ladder-calibrate + per-sensor curve fit:** load a *series* of known masses (1 L water = 1.00 kg; a bathroom scale as ground truth) and fit the power-law `F = a·Gᵇ` **per sensor** | Interlink's own guide: a **per-device parametric curve fit is the most complete calibration**; each FSR varies enough to need its own coefficients ([FSR Integration Guide](https://cdn.sparkfun.com/assets/e/3/b/3/8/force_sensing_resistor_guide.pdf)) |
| **Long-term drift** — the zero and gain wander over days/temperature | **Re-tare on drift, not on a schedule:** watch the empty-baseline; only recalibrate when it exceeds a threshold. Log room temp alongside | Velostat arrays stay usable over **210 days** *if* re-referenced; fixed-schedule recal wastes effort and misses fast drift ([210-day reliability](https://www.researchgate.net/publication/376363749_Investigation_of_the_Long-term_Reliability_of_a_Velostat-Based_Flexible_Pressure_Sensor_Array_for_210_Days)) |
| **Electrical noise** on a 24-bit ADC | **Twist + shorten + shield** every sensor lead; route away from motors / switching supplies / Wi-Fi antenna | Standard HX711 practice — many cheap boards are noisy from long, parallel, unshielded leads ([HX711_ADC notes](https://github.com/olkal/HX711_ADC)) |

---

## 1 · Velostat pressure mat

**The enemy is ghosting (crosstalk).** In a row×column resistive matrix, current sneaks
*backwards* through unpressed cells, so pressing one cell drops the reading of others in its
row and column — and phantom "ghost" cells light up at the crossings.

- **Driven-ground / zero-potential scan (the real fix).** Drive the active row; **hold every
  *other* row AND column at 0 V** so no potential difference exists across the idle cells —
  no sneak current, no ghost. The clean hardware version reads the active column through an
  **op-amp virtual ground** while grounding the rest through analog switches.
  → [Zero-potential method analysis (IET)](https://digital-library.theiet.org/doi/10.1049/iet-smt.2016.0363),
  [Circuit analysis for eliminating crosstalk in pressure mats (Unizar PDF)](https://zaguan.unizar.es/record/133171/files/texto_completo.pdf),
  [Cross-talk compensation in low-cost resistive matrices (TU-Ilmenau)](https://www.tu-ilmenau.de/fileadmin/Bereiche/IA/neurob/Publikationen/conferences_int/2019/Mueller-ICM-2019.pdf).
- **Software-only 80% version** (what's in our firmware): actively drive **all idle rows LOW as
  sinks** (not floating), and after switching the mux, **throw away the first ADC read** so the
  channel settles before you keep a sample. Cheap, no extra parts, kills most of the ghost.
- **Hardware upgrade:** a **Schottky diode in series with each cell** blocks the reverse sneak
  path entirely — the gold standard if you don't want the op-amp. Note the residual limit: even
  the virtual-ground trick leaves *some* crosstalk from the analog-switch on-resistance.
- **Spread the load:** lay a thin firm foam / EVA layer over the matrix so a toe doesn't fall
  *between* electrodes — improves repeatability and stops single-cell spikes.
- **Preload the stack:** a light constant compression (foam + rigid backing) parks Velostat in
  a more linear part of its curve and cuts the creep-to-settle time.

**Resolution hack — interpolate.** An 8×11 mat is blocky, but you don't need more cells to *see*
the hot region: **bicubic-interpolate** the coarse grid up (e.g. → 100×100) for the heatmap.
Bicubic matches linear on error (RMSE ≈ **0.089** vs nearest-neighbor's 0.126) and reads far
cleaner. → [Interpolation techniques for a flexible plantar-pressure mat (IEEE)](https://ieeexplore.ieee.org/document/10101098/),
[FSR plantar pressure + interpolation](https://www.researchgate.net/publication/382404198_Measurement_of_Plantar_Pressures_through_FSR_Sensors_and_Spatial_Resolution_through_Interpolation).
*Done for you:* [`analysis/mat_heatmap.py`](../analysis/mat_heatmap.py) (`--demo`).

---

## 2 · FSR insole (the 8-zone rig)

FSRs are convenient but **hysteretic and drifty** — "drift" here is literally the resistance
changing under a *constant* static load ([Interlink guide](https://cdn.sparkfun.com/assets/e/3/b/3/8/force_sensing_resistor_guide.pdf)).
Tame them:

- **Force concentrator (puck).** Put a small **rigid disc** over the FSR's active area so
  distributed load funnels onto the sensor the *same way every time* — the single biggest
  repeatability win, and it boosts sensitivity. Print [`hardware/fsr_puck.scad`](../hardware/fsr_puck.scad).
- **Firm, flat, smooth backing.** Interlink: mounting an FSR on a **curved** surface pre-loads
  it → lost dynamic range + drift. Keep the sensor sandwiched flat and rigid on the sensing side.
- **Tune the divider resistor R_M to your force band.** In the `Vout = V+ / (1 + R_FSR/R_M)`
  divider, pick R_M so your *actual* forefoot/heel loads land mid-range (not railed high or low).
  For body-weight loads that usually means a **lower** R_M than the datasheet default.
- **Fit each sensor.** Our `calibrate.py` already does the power-law fit — run it **per sensor**,
  not once for the set; FSR-to-FSR spread is large.

---

## 3 · Load-cell force plate

The load cells are the accurate part (**0.1% of capacity** is achievable with a clean mount);
the **HX711 and the mechanics** are where you lose or keep it.

- **Median-*then*-average filter.** A **median** first stage rejects the impulse spikes the
  HX711 throws (10–15× cleaner), *then* a short moving average smooths the rest — averaging alone
  just smears a spike across your readings. → [olkal/HX711_ADC](https://github.com/olkal/HX711_ADC) does
  exactly this (median + moving-average, default 16); [Parallax thread](https://forums.parallax.com/discussion/166836/how-to-filter-noise-on-ad-hx711-load-cell-amp).
  *Baked into* [`force_plate.ino`](../firmware/force_plate/force_plate.ino).
- **Pick the sample rate for the job.** **80 SPS is the *noisiest* rate** — use it *only* for fast
  landing transients where you need the time resolution; for standing, balance, and calibration,
  **10 SPS** is quieter. (Heavy per-sample filtering also caps your effective rate — light filter
  for landings, heavy for quiet stands.)
- **Mechanics decide crosstalk.** Rigid top plate, each load cell's **free end floats in its air
  gap** (don't let it bottom out), fixed end solidly bolted. Off-axis load = false reading.
- **Corner sanity check.** Before trusting the total, press each corner alone and confirm it
  responds — one dead/reversed corner skews the sum (and any CoP).
- **Warm up, then tare.** Let the electronics sit 1–2 min; the HX711 has real thermal drift.
  Tare cold→warm, and re-tare if the empty baseline wanders ([HX711 drift](https://github.com/bogde/HX711/issues/51)).

---

## What's already baked into the repo

| Hack | Where |
|---|---|
| Median-then-average HX711 filter + SPS-for-the-job note | [`firmware/force_plate/force_plate.ino`](../firmware/force_plate/force_plate.ino) |
| Anti-ghost scan (idle rows sunk LOW + settle-throwaway read) + diode/op-amp notes | [`firmware/pressure_mat/pressure_mat.ino`](../firmware/pressure_mat/pressure_mat.ino) |
| Bicubic interpolation of the coarse mat → clean heatmap | [`analysis/mat_heatmap.py`](../analysis/mat_heatmap.py) `--demo` |
| Printable FSR force-concentrator puck | [`hardware/fsr_puck.scad`](../hardware/fsr_puck.scad) |
| Ladder / per-sensor power-law calibration | [`analysis/calibrate.py`](../analysis/calibrate.py) |

**Honest limit (unchanged):** these hacks recover *accuracy and repeatability*, not **shear** or
**6-axis** — that gap stays (see [`lab_scope.md`](lab_scope.md)). And a resistive rig will always
drift more than a capacitive pedar: read **trends**, recalibrate, and don't quote absolutes to a
clinician. Not a medical device.
