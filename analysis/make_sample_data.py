#!/usr/bin/env python3
"""
make_sample_data.py — generate a realistic *synthetic* day of data so the whole
pipeline can be run and demonstrated with NO hardware (a worked example / demo).

It fabricates, from a physically-consistent FSR model (force -> conductance ->
divider -> ADC), four files:
  cal_points.csv         known-weight calibration points  -> calibrate.py
  sample_day_shoe.csv    ~30 s walking, SHOE  (mode=shoe)
  sample_day_barefoot.csv~30 s walking, BAREFOOT (mode=barefoot)
  sample_balance.csv     quiet standing, eyes_open then eyes_closed (activity=)

The walking data is seeded to show a **medial-heel hot spot with a pronation
tendency and a hard heel strike**, and the shoe *raises* the heel load vs
barefoot — so interpret.py produces a full, non-trivial report. The balance data
is seeded so eyes-closed sway is ~2-3x eyes-open (Romberg > 2).

Because the SAME ground-truth (a,b) per channel is used to synthesize both the
calibration points and the day logs, calibrate.py recovers it (R^2 ~ 0.999) and
interpret.py reports real kPa that round-trip to the intended forces.

    python make_sample_data.py --out ../sample     # deterministic (seed=7)

NOT real measurements — a demo so the repo is self-demonstrating.
"""
import argparse, os
import numpy as np
import pandas as pd

FS = 50.0                      # Hz (matches all_day_logger)
# 1 kOhm divider keeps body-weight forces (2-56 N) across the ADC's sensitive
# span (~370-3660) instead of saturating a 10 k divider -> good calibration fit.
VCC, R_FIXED, ADC_MAX = 3.3, 1000.0, 4095
FOOT_W_MM_, FOOT_L_MM_ = 95.0, 255.0   # match balance.py so mm targets are faithful
ZONES = ["heel_med", "heel_lat", "midfoot", "met1", "met3", "met5", "hallux", "toes"]

# ground-truth per-channel power law F = a * G^b (small per-sensor spread)
def truth(seed=7):
    rng = np.random.default_rng(seed)
    a = 2000.0 * (1 + 0.06 * rng.standard_normal(8))
    b = 0.75 + 0.02 * rng.standard_normal(8)
    return a, b, rng


def force_to_adc(F, a, b, rng, baseline=14.0, noise=5.0):
    """Invert the divider model: F(N) -> ADC counts. Zero force -> ~baseline."""
    F = np.clip(np.asarray(F, float), 0, None)
    G = np.power(np.clip(F, 1e-9, None) / a, 1.0 / b)      # siemens (F=a G^b)
    r_fsr = 1.0 / np.clip(G, 1e-12, None)
    adc = ADC_MAX * R_FIXED / (r_fsr + R_FIXED)            # node voltage divider
    adc = np.where(F <= 1e-9, 0.0, adc) + baseline
    adc = adc + noise * rng.standard_normal(np.shape(adc))
    return np.clip(np.round(adc), 0, ADC_MAX).astype(int)


# ---- gait force model -------------------------------------------------------
# per-zone peak force (N) and stance-phase center; widths shared.
# Tuned so SHOE reads: heel_med hot spot, concentrated (aggressive relief),
# medial pronation, heel-dominant, hard heel strike; BAREFOOT spreads the heel
# load, so the shoe clearly *raises* heel_med vs barefoot.
SHOE_PEAK = np.array([70, 30, 8, 14, 12, 8, 11, 6], float)
BARE_PEAK = np.array([44, 28, 10, 16, 14, 10, 13, 8], float)
CENTER    = np.array([.12, .15, .38, .62, .60, .64, .80, .84])  # heel->toe rollover
SIG       = np.array([.10, .11, .13, .11, .11, .11, .10, .10])


def walking(peak, dur_s, rng, stride_s=1.10, stance_frac=0.62):
    n = int(dur_s * FS)
    t = np.arange(n) / FS
    F = np.zeros((n, 8))
    phase = (t % stride_s) / stride_s                      # 0..1 within each stride
    in_stance = phase < stance_frac
    p = np.clip(phase / stance_frac, 0, 1)                 # 0..1 across stance
    for z in range(8):
        bump = np.exp(-((p - CENTER[z]) ** 2) / (2 * SIG[z] ** 2))
        F[:, z] = np.where(in_stance, peak[z] * bump, 0.0)
    F *= (1 + 0.04 * rng.standard_normal(F.shape))         # step-to-step variability
    return t, np.clip(F, 0, None)


def imu_walk(n, rng):
    ax = 1.2 * rng.standard_normal(n)
    ay = 0.8 * rng.standard_normal(n)
    az = 9.81 + 0.9 * rng.standard_normal(n)
    return ax, ay, az


# ---- seated leg-bounce / toe-tap model (the at-rest forefoot dose) ----------
# Sitting, ~19% BW through the feet, forefoot loads/unloads at ~2.8 Hz; heel rests
# light. Central met heads carry most (the Morton / interdigital-nerve territory).
BOUNCE_FORE = np.array([0, 0, 0, 22, 30, 18, 20, 10], float)   # per-zone forefoot force (N)


def seated_bounce(dur_s, rng, freq=2.8):
    n = int(dur_s * FS)
    t = np.arange(n) / FS
    cyc = 0.5 + 0.5 * np.sin(2 * np.pi * freq * t)             # 0..1 bounce
    F = np.outer(cyc, BOUNCE_FORE)                             # forefoot oscillates
    F[:, 0] = F[:, 1] = 3.0                                    # light heel rest
    F[:, 2] = 1.0                                              # a little midfoot
    F *= (1 + 0.03 * rng.standard_normal(F.shape))
    ax = 0.05 * rng.standard_normal(n)
    ay = 0.05 * rng.standard_normal(n)
    az = 9.81 + 3.0 * (cyc - 0.5)                              # vertical jiggle
    return t, np.clip(F, 0, None), (ax, ay, az)


# ---- quiet-standing balance model ------------------------------------------
# Drive an EXACT center-of-pressure: ML from the medial/lateral split, AP from
# heel-vs-forefoot split. Decoupling ML and AP keeps the sway ellipse from
# collapsing (a trapezoidal quad correlates the axes and shrinks its area).
# Sensor x: heel_med .35, heel_lat .65, met1 .30, met5 .70 ; heel y .08, fore y .72.
IDX = dict(hm=0, hl=1, m1=3, m5=5)


def sway_unit(t, fset, rng):
    """A slow physiological-looking sway signal normalized to ~unit std."""
    n = len(t)
    s = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) / (i + 1)
            for i, f in enumerate(fset))
    drift = np.cumsum(rng.standard_normal(n)); drift -= drift.mean()
    s = 0.75 * s + 0.25 * (drift / (drift.std() + 1e-9))
    return s / (s.std() + 1e-9)


def standing(dur_s, sig_ml_mm, sig_ap_mm, rng, total=45.0, cx0=.50, cy0=.22):
    """sig_*_mm = target COP RMS in mm; area ~ pi*5.991*sig_ml*sig_ap."""
    n = int(dur_s * FS)
    t = np.arange(n) / FS
    cx = cx0 + (sig_ml_mm / FOOT_W_MM_) * sway_unit(t, [0.15, 0.4, 0.9], rng)
    cy = cy0 + (sig_ap_mm / FOOT_L_MM_) * sway_unit(t, [0.12, 0.35, 0.7], rng)
    fF = np.clip((cy - .08) / .64, 0, 1)                   # forefoot load fraction (AP)
    u_h = np.clip((cx - .35) / .30, 0, 1)                  # heel medial/lateral split (ML)
    u_f = np.clip((cx - .30) / .40, 0, 1)                  # forefoot medial/lateral split
    heel, fore = total * (1 - fF), total * fF
    F = np.zeros((n, 8))
    F[:, IDX["hm"]] = heel * (1 - u_h); F[:, IDX["hl"]] = heel * u_h
    F[:, IDX["m1"]] = fore * (1 - u_f); F[:, IDX["m5"]] = fore * u_f
    F[:, 2] = 1.2                                          # a little arch/midfoot contact
    F *= (1 + 0.015 * rng.standard_normal(F.shape))
    k = (sig_ml_mm + sig_ap_mm) / 6.0                      # trunk accel grows with sway
    ax = k * np.gradient(cx) * FS + 0.03 * rng.standard_normal(n)
    ay = k * np.gradient(cy) * FS + 0.03 * rng.standard_normal(n)
    az = 9.81 + 0.03 * rng.standard_normal(n)
    return t, np.clip(F, 0, None), (ax, ay, az)


def fsr_from_cop(cx, cy, rng, total=45.0):
    """COP (normalized) -> 8 FSR forces (same decoupled mapping as standing())."""
    n = len(cx)
    fF = np.clip((cy - .08) / .64, 0, 1)
    u_h = np.clip((cx - .35) / .30, 0, 1)
    u_f = np.clip((cx - .30) / .40, 0, 1)
    heel, fore = total * (1 - fF), total * fF
    F = np.zeros((n, 8))
    F[:, IDX["hm"]] = heel * (1 - u_h); F[:, IDX["hl"]] = heel * u_h
    F[:, IDX["m1"]] = fore * (1 - u_f); F[:, IDX["m5"]] = fore * u_f
    F[:, 2] = 1.2
    F *= (1 + 0.015 * rng.standard_normal(F.shape))
    return np.clip(F, 0, None)


def imu_from_cop(cx, cy, gain, rng):
    n = len(cx)
    ax = gain * np.gradient(cx) * FS + 0.03 * rng.standard_normal(n)
    ay = gain * np.gradient(cy) * FS + 0.03 * rng.standard_normal(n)
    az = 9.81 + 0.03 * rng.standard_normal(n)
    return ax, ay, az


def quiet_cop(dur, sig_ml, sig_ap, rng, cx0=.50, cy0=.22):
    n = int(dur * FS); t = np.arange(n) / FS
    cx = cx0 + (sig_ml / FOOT_W_MM_) * sway_unit(t, [0.15, 0.4, 0.9], rng)
    cy = cy0 + (sig_ap / FOOT_L_MM_) * sway_unit(t, [0.12, 0.35, 0.7], rng)
    return t, cx, cy, (sig_ml + sig_ap) / 6.0


def los_cop(dur, rng, cx0=.50, cy0=.22):
    """Intentional lean: COP visits front / right / back / left extremes and returns."""
    n = int(dur * FS); t = np.arange(n) / FS; u = t / max(dur, 1e-6)
    fr = [0, .12, .25, .37, .50, .62, .75, .87, 1.0]
    xs = [cx0, cx0, cx0, .68, cx0, cx0, cx0, .32, cx0]
    ys = [cy0, .82, cy0, .30, cy0, .11, cy0, .30, cy0]
    cx = np.interp(u, fr, xs) + 0.006 * rng.standard_normal(n)
    cy = np.interp(u, fr, ys) + 0.006 * rng.standard_normal(n)
    return t, cx, cy, 0.9


def frame(t, F, a, b, rng, imu, label_col, label):
    ax, ay, az = imu
    n = len(t)
    d = {"t_ms": (t * 1000).round().astype(int), label_col: label}
    adc = np.column_stack([force_to_adc(F[:, z], a[z], b[z], rng) for z in range(8)])
    for z in range(8):
        d[f"fsr{z}"] = adc[:, z]
    d["qw"] = np.round(1 + 0.01 * rng.standard_normal(n), 4)
    for q in ("qx", "qy", "qz"):
        d[q] = np.round(0.02 * rng.standard_normal(n), 4)
    d["ax"] = np.round(ax, 3); d["ay"] = np.round(ay, 3); d["az"] = np.round(az, 3)
    return pd.DataFrame(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="sample")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    a, b, rng = truth(args.seed)

    # calibration points: several known weights per sensor
    forces = np.array([1, 2, 5, 10, 20, 35, 50], float)
    rows = []
    for ch in range(8):
        adc = force_to_adc(forces, a[ch], b[ch], rng, noise=8.0)
        for F, A in zip(forces, adc):
            rows.append({"sensor": ch, "force_N": F, "adc": int(A)})
    pd.DataFrame(rows).to_csv(os.path.join(args.out, "cal_points.csv"), index=False)

    # walking, shoe + barefoot
    for label, peak in (("shoe", SHOE_PEAK), ("barefoot", BARE_PEAK)):
        t, F = walking(peak, 30, rng)
        frame(t, F, a, b, rng, imu_walk(len(t), rng), "mode", label) \
            .to_csv(os.path.join(args.out, f"sample_day_{label}.csv"), index=False)

    # balance, eyes_open + eyes_closed (closed sways ~2x -> Romberg > 2)
    # target COP RMS in mm -> ellipse area ~ pi*5.991*sig_ml*sig_ap
    parts = []
    t0, F0, imu0 = standing(30, sig_ml_mm=3.0, sig_ap_mm=4.0, rng=rng)   # ~226 mm^2
    parts.append(frame(t0, F0, a, b, rng, imu0, "activity", "eyes_open"))
    t1, F1, imu1 = standing(30, sig_ml_mm=5.5, sig_ap_mm=8.0, rng=rng)   # ~828 mm^2
    t1 = t1 + (t0[-1] + 1 / FS)
    parts.append(frame(t1, F1, a, b, rng, imu1, "activity", "eyes_closed"))
    pd.concat(parts, ignore_index=True) \
        .to_csv(os.path.join(args.out, "sample_balance.csv"), index=False)

    # balance ACROSS POSITIONS — mCTSIB (firm/foam x eyes) + single-leg L/R + tandem + LOS.
    # Seeded story: vision-reliant + a vestibular (foam-EC) failure; left leg weaker.
    conds = [
        ("firm_eo",      quiet_cop(25, 3.0, 4.0, rng)),
        ("firm_ec",      quiet_cop(25, 4.5, 6.0, rng)),
        ("foam_eo",      quiet_cop(25, 5.0, 7.0, rng)),
        ("foam_ec",      quiet_cop(25, 8.5, 11.5, rng)),
        ("single_leg_L", quiet_cop(15, 9.0, 9.0, rng, cy0=.34)),
        ("single_leg_R", quiet_cop(15, 6.5, 7.0, rng, cy0=.34)),
        ("tandem",       quiet_cop(20, 10.0, 4.5, rng, cy0=.28)),
        ("los",          los_cop(30, rng)),
    ]
    pparts, toff = [], 0.0
    for label, (tt, cx, cy, gain) in conds:
        F = fsr_from_cop(cx, cy, rng)
        tg = tt + toff
        pparts.append(frame(tg, F, a, b, rng, imu_from_cop(cx, cy, gain, rng), "activity", label))
        toff = tg[-1] + 1 / FS
    pd.concat(pparts, ignore_index=True) \
        .to_csv(os.path.join(args.out, "sample_balance_positions.csv"), index=False)

    # seated leg-bounce / toe-tap (the at-rest forefoot dose) — activity=seated_bounce.
    # Uses a SEPARATE rng and runs LAST so it never perturbs the walking/balance streams.
    # Named OUTSIDE the sample_day_*.csv glob so gait analysis (interpret/analyze) skips it;
    # day_summary.py picks it up explicitly for the all-day dose.
    rng_b = np.random.default_rng(args.seed + 101)
    tb, Fb, imub = seated_bounce(30, rng_b)
    frame(tb, Fb, a, b, rng_b, imub, "activity", "seated_bounce") \
        .to_csv(os.path.join(args.out, "sample_seated_bounce.csv"), index=False)

    print(f"wrote cal_points.csv, sample_day_shoe/barefoot.csv, sample_seated_bounce.csv, "
          f"sample_balance.csv, sample_balance_positions.csv -> {args.out}/")


if __name__ == "__main__":
    main()
