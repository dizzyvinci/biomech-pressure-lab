# Calibration — turn the FSRs into real pressure (kPa)

FSRs are **nonlinear**, so raw ADC ≠ force. This one-time step fits each sensor's
curve from known weights, so the analysis reports **real kPa** instead of relative units.

## The model (what's happening)
1. **ADC → resistance.** From the voltage divider (`3V3 — FSR — node — 10 kΩ — GND`, ADC reads the node): `R_fsr = R_fixed · (Vcc − Vout) / Vout`.
2. **Resistance → conductance** `G = 1/R` (roughly proportional to force).
3. **Conductance → force**, per sensor, via a fitted power law **`F = a · G^b`** (`calibrate.py` finds `a, b`).
4. **Force → pressure** `P(kPa) = F(N) / pad_area(m²) / 1000`. Default pad area = **122.7 mm²** (a 12.5 mm round FSR) — set `--pad-area-mm2` to yours.

## Do it once (~20 min)
1. **Flash** [`firmware/fsr_calibrate/`](../firmware/fsr_calibrate/fsr_calibrate.ino), open Serial Monitor @115200 — it streams `fsr0..fsr7`.
2. For **each sensor**, rest a **known weight** squarely on the pad and note that column's ADC. Use ~4–6 weights across the range (e.g., 0.5, 1, 2, 5, 10 kg). `force_N = mass_kg × 9.81`.
   - A small flat cap over the pad spreads the load; keep it centered.
3. Record rows in a CSV (see [`analysis/cal_points_template.csv`](../analysis/cal_points_template.csv)):
   ```
   sensor,force_N,adc
   0,9.81,1500
   0,49.0,3350
   ...
   ```
4. **Fit:**
   ```powershell
   python analysis/calibrate.py cal_points.csv --out calibration.json
   ```
   It prints `a b R2 n` per channel — **aim for R² > 0.95**. Add more weight points to any low-R² channel.
5. **Use it** — the analysis now reports kPa:
   ```powershell
   python analysis/interpret.py       "day_*.csv" --calibration calibration.json --out results/
   python analysis/analyze_pressure.py "day_*.csv" --calibration calibration.json --out results/
   ```

## Accuracy notes (honest)
- Even calibrated, FSRs are **±10–20%** absolute — great for *trends, hot spots, before/after*, not lab-grade metrology.
- Calibrate **in situ** if you can (sensor mounted in the sole), since the mounting surface affects response.
- Re-check occasionally; FSRs drift with heavy use.
- No calibration? The analysis still works in **relative units** — you just lose the kPa axis.
