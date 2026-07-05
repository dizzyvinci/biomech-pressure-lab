#!/usr/bin/env python3
"""
calibrate.py — fit each FSR's ADC->Force curve from known-weight points.

INPUT  CSV: columns  sensor,force_N,adc   (several rows per sensor across the range)
           force_N = mass_kg * 9.81. Collect ADC with firmware/fsr_calibrate.
OUTPUT     calibration.json  (per-sensor power-law F = a*G^b + divider constants).

Fit quality (R^2) is printed per channel; aim for >0.95. Then run the analysis
with  --calibration calibration.json  to get real kPa.

Usage:
    python calibrate.py cal_points.csv --out calibration.json
"""
import argparse
import json
import numpy as np
import pandas as pd
from calib import adc_to_conductance


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("points", help="CSV: sensor,force_N,adc")
    ap.add_argument("--out", default="calibration.json")
    ap.add_argument("--vcc", type=float, default=3.3)
    ap.add_argument("--r-fixed", type=float, default=10000.0)
    ap.add_argument("--adc-max", type=int, default=4095)
    ap.add_argument("--pad-area-mm2", type=float, default=122.7,  # 12.5 mm dia round FSR
                    help="FSR active-pad area (mm^2); 122.7 for a 12.5 mm round pad")
    args = ap.parse_args()

    df = pd.read_csv(args.points)
    cal = {"vcc": args.vcc, "r_fixed": args.r_fixed, "adc_max": args.adc_max,
           "pad_area_mm2": args.pad_area_mm2, "sensors": {}}

    print(f"{'ch':>3} {'a':>11} {'b':>7} {'R2':>6} {'n':>3}")
    for ch, sub in df.groupby("sensor"):
        sub = sub[(sub.force_N > 0) & (sub.adc > 0)]
        if len(sub) < 2:
            print(f"{int(ch):>3}   (need >=2 points, skipped)")
            continue
        g = adc_to_conductance(sub.adc.to_numpy(), args.vcc, args.r_fixed, args.adc_max)
        F = sub.force_N.to_numpy()
        # log F = b*log G + log a  (power law)
        b, la = np.polyfit(np.log(np.clip(g, 1e-12, None)), np.log(np.clip(F, 1e-6, None)), 1)
        A = float(np.exp(la))
        pred = A * np.power(g, b)
        ss_res = float(np.sum((F - pred) ** 2))
        ss_tot = float(np.sum((F - F.mean()) ** 2)) or 1e-9
        r2 = 1 - ss_res / ss_tot
        cal["sensors"][str(int(ch))] = {"a": A, "b": float(b), "r2": round(float(r2), 3)}
        print(f"{int(ch):>3} {A:>11.4g} {b:>7.3f} {r2:>6.2f} {len(sub):>3}")

    with open(args.out, "w") as f:
        json.dump(cal, f, indent=2)
    print(f"\n-> {args.out}   (use: interpret.py \"...\" --calibration {args.out})")


if __name__ == "__main__":
    main()
