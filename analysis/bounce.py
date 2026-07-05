#!/usr/bin/env python3
"""
bounce.py — the at-rest forefoot DOSE of leg-bouncing / toe-tapping ("the jiggle").

Leg-bouncing and toe-tapping are repetitive forefoot loading at ~2-3 Hz that NO gait
study counts — you're not walking, so it's invisible to step counters and gait labs.
But it's real mechanical dose on the ball of the foot, and for a forefoot-loader
(toe-walking / equinus) it stacks onto an already-high forefoot exposure ALL DAY.

At ~2.8 Hz (the measured toe-tap frequency), a few hours of bouncing is tens of
thousands of forefoot loading cycles — often MORE than a day's walking steps. This
detects the bounce (FFT), counts the cycles, and integrates the FOREFOOT pressure-time
(PTI) — the cumulative dose that peak pressure misses.

    python bounce.py --demo
    python bounce.py seated_session.csv --calibration cal.json --hours-per-day 4

Reads FSR (+ IMU). Outputs results/bounce.json + report_bounce.md. NOT a medical device.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from balance import load, group_col, values
try:
    import calib
except Exception:
    calib = None
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FORE, HEEL = [3, 4, 5, 6, 7], [0, 1]
TYPICAL_DAILY_STEPS = 7000        # midpoint of common ~5-10k estimates (for context)


def sample_rate(t_ms):
    dt = np.median(np.diff(t_ms.to_numpy(float))) / 1000.0
    return 1.0 / dt if dt > 0 else 100.0


def dominant_freq(sig, fs, lo=1.5, hi=4.0):
    """Peak frequency in the bounce band + that band's share of AC power."""
    sig = np.asarray(sig, float); sig = sig - sig.mean()
    n = len(sig)
    if n < 8:
        return 0.0, 0.0
    f = np.fft.rfftfreq(n, 1.0 / fs)
    P = np.abs(np.fft.rfft(sig * np.hanning(n))) ** 2
    band = (f >= lo) & (f <= hi)
    if not band.any() or P[1:].sum() <= 0:
        return 0.0, 0.0
    pk = f[band][int(np.argmax(P[band]))]
    frac = float(P[band].sum() / P[1:].sum())     # bounce-band share of AC power
    return float(pk), frac


def demo(fs=100, dur=60):
    rng = np.random.default_rng(9)
    t = np.arange(int(dur * fs)) / fs
    # seated bounce: forefoot loads/unloads at 2.8 Hz; heel stays light
    cyc = 0.5 + 0.5 * np.sin(2 * np.pi * 2.8 * t)          # 0..1 bounce
    fore = 120 + 520 * cyc                                  # ADC-ish forefoot load
    df = pd.DataFrame({"t_ms": (t * 1000).astype(int), "activity": "seated_bounce"})
    # met1,met3,met5,hallux,toes carry the bounce; heel/midfoot light
    for i in range(8):
        base = (fore if i in FORE else np.full_like(t, 40.0))
        df[f"fsr{i}"] = np.clip(base * (1 + 0.03 * rng.standard_normal(len(t))), 0, None)
    df["qw"] = 1.0; df["qx"] = 0.0; df["qy"] = 0.0
    df["qz"] = 0.0; df["ax"] = 0.02 * rng.standard_normal(len(t))
    df["ay"] = 0.02 * rng.standard_normal(len(t)); df["az"] = 9.81 + 3.0 * (cyc - 0.5)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--calibration")
    ap.add_argument("--hours-per-day", type=float, default=4.0)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    cal = calib.load(args.calibration) if (args.calibration and calib) else None

    if args.demo:
        df = demo()
    else:
        paths = []
        for g in args.logs:
            paths += glob.glob(g)
        df = load(paths)
    df = df.sort_values("t_ms")
    fs = sample_rate(df["t_ms"])
    t = df["t_ms"].to_numpy(float) / 1000.0
    dur = max(t[-1] - t[0], 1e-6)
    f = values(df, cal)                                    # kPa if calibrated, else ADC
    fore = f[:, FORE].mean(1)                              # forefoot pressure/load signal

    freq, frac = dominant_freq(fore, fs)
    bouncing = frac > 0.15 and freq >= 1.5
    cycles_session = freq * dur
    cycles_per_day = freq * args.hours_per_day * 3600
    dt = np.gradient(t)
    pti_session = float((fore * dt).sum())                 # forefoot pressure-time integral
    unit = "kPa·s" if cal is not None else "rel·s"
    pti_per_day = pti_session / dur * (args.hours_per_day * 3600)
    vs_steps = cycles_per_day / TYPICAL_DAILY_STEPS

    L = ["# At-rest forefoot dose — leg-bounce / toe-tap", ""]
    if not bouncing:
        L.append(f"- No sustained bounce detected (band power {frac:.0%}, peak {freq:.1f} Hz).")
    else:
        L.append(f"- **Bouncing detected: {freq:.1f} Hz** (toe-tap band; {frac:.0%} of the signal's motion).")
        L.append(f"- **{cycles_session:.0f} forefoot cycles** this {dur:.0f}s session.")
        L.append(f"- Projected **{cycles_per_day:,.0f} forefoot loading cycles/day** at {args.hours_per_day:.0f} h/day —")
        L.append(f"  **≈ {vs_steps:.1f}× a typical day's walking steps ({TYPICAL_DAILY_STEPS:,}).** "
                 f"This is the HIDDEN dose no step-counter sees.")
        L.append(f"- Forefoot **pressure-time integral (dose): {pti_session:.0f} {unit}** this session → "
                 f"~{pti_per_day:,.0f} {unit}/day.")
        L.append("\n_For a forefoot-loader (toe-walking / equinus), this stacks ON TOP of gait — the ball of the "
                 "foot never gets a rest. Options: vary the pattern, a soft forefoot pad while seated, or a "
                 "different fidget outlet. Not a reason to suppress a self-regulating movement — just to dose it._")
    if cal is None:
        L.append("\n_(Relative units — add --calibration for the dose in real kPa·s.)_")

    with open(os.path.join(args.out, "report_bounce.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(args.out, "bounce.json"), "w") as fh:
        json.dump({"bouncing": bool(bouncing), "freq_hz": round(freq, 2), "band_power_frac": round(frac, 3),
                   "cycles_session": round(cycles_session), "cycles_per_day": round(cycles_per_day),
                   "vs_daily_steps": round(vs_steps, 1), "forefoot_pti_session": round(pti_session, 1),
                   "unit": unit, "hours_per_day": args.hours_per_day}, fh, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/report_bounce.md + bounce.json")


if __name__ == "__main__":
    main()
