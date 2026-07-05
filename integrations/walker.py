#!/usr/bin/env python3
"""
walker.py — fuse a sensorized walker / rollator with the insole; drive assist feedback.

A balance walker with handle force sensors (and, on robotic rollators, electronic
brakes) plus the insole gives two halves of one picture:
  - the **insole** measures load through the FEET,
  - the **walker** measures load through the HANDLES.
Together -> **how much of your weight goes through the walker** (walker dependence,
a rehab-progress metric that should fall over time), left/right handle lean, and a
**grab detector**: a sudden spike of weight onto the handles + drop of foot load =
a near-loss of balance. On a grab the module emits an assist command — engage the
adaptive brake and alert — that a robotic walker consumes.

    python walker.py --demo --out results/
    python walker.py walker_telemetry.csv --out results/
        # CSV columns: t_ms, handle_L_N, handle_R_N, speed_mps[, foot_load_N]
        # (foot_load_N optional -> otherwise pass --insole a calibrated insole log)

Outputs results/report_walker.md + walker_feedback.json.  NOT a medical device.
"""
import argparse, json, os, sys
import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def demo(fs=50, dur=40):
    rng = np.random.default_rng(5)
    t = np.arange(int(dur * fs)) / fs
    foot = 680 + 30 * np.sin(2 * np.pi * 0.9 * t) + 8 * rng.standard_normal(len(t))
    hL = 46 + 8 * rng.standard_normal(len(t))
    hR = 40 + 8 * rng.standard_normal(len(t))
    speed = 0.60 + 0.05 * rng.standard_normal(len(t))
    for c in (10, 22, 33):                        # three near-losses of balance
        m = (t >= c) & (t < c + 1.5)
        foot[m] *= 0.45; hL[m] += 165; hR[m] += 140; speed[m] *= 0.30
    return pd.DataFrame({"t_ms": (t * 1000).astype(int), "handle_L_N": np.clip(hL, 0, None),
                         "handle_R_N": np.clip(hR, 0, None), "speed_mps": np.clip(speed, 0, None),
                         "foot_load_N": np.clip(foot, 0, None)})


def grab_episodes(t, handle, thr):
    eps, s = [], None
    for i in range(len(t)):
        hot = handle[i] > thr
        if hot and s is None: s = t[i]
        elif not hot and s is not None:
            if t[i] - s > 0.2: eps.append([float(round(s, 1)), float(round(t[i], 1))])
            s = None
    if s is not None: eps.append([float(round(s, 1)), float(round(t[-1], 1))])
    return eps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("telemetry", nargs="?")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--insole", help="calibrated insole log for foot_load if telemetry lacks it")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    df = demo() if args.demo else pd.read_csv(args.telemetry, comment="#")
    t = df["t_ms"].to_numpy(float) / 1000.0
    hL, hR = df["handle_L_N"].to_numpy(float), df["handle_R_N"].to_numpy(float)
    handle = hL + hR
    if "foot_load_N" in df.columns:
        foot = df["foot_load_N"].to_numpy(float)
    elif args.insole:
        ins = pd.read_csv(args.insole, comment="#")
        foot = ins[[f"fsr{i}" for i in range(8)]].to_numpy(float).sum(1)  # relative if uncalibrated
    else:
        foot = np.full(len(t), np.nan)

    support = 100 * handle / np.clip(handle + foot, 1e-9, None)
    asym = 100 * np.abs(hL - hR) / np.clip(hL + hR, 1e-9, None)
    lean = "left" if hL.mean() > hR.mean() else "right"
    half = len(t) // 2
    trend = round(float(support[half:].mean() - support[:half].mean()), 1)

    base = np.median(handle); mad = np.median(np.abs(handle - base)) or 1.0
    thr = base + 4.0 * mad
    grabs = grab_episodes(t, handle, thr)
    feedback = []
    for a, b in grabs:
        feedback += [{"t": a, "channel": "brake", "action": "engage", "params": {"level": "high"}},
                     {"t": a, "channel": "alert", "action": "notify", "params": {"msg": "steady — weight forward onto your feet"}},
                     {"t": b, "channel": "brake", "action": "release"}]

    L = ["# Smart-walker fusion — findings", ""]
    L.append(f"- **Weight through the walker: {support.mean():.0f}%** of total support "
             f"(handles {handle.mean():.0f} N vs feet {np.nanmean(foot):.0f} N).")
    L.append(f"- Trend across the session: {trend:+.1f}% "
             + ("(leaning on it MORE — watch fatigue)" if trend > 2 else
                "(steady / less dependent — good)" if trend < -2 else "(steady)") + ".")
    L.append(f"- Handle lean: {asym.mean():.0f}% toward the **{lean}** — pushes to that side.")
    L.append(f"- **Near-losses of balance (grabs): {len(grabs)}** {grabs} — each fired an "
             f"adaptive-brake + alert command.")
    if support.mean() > 40:
        L.append("- **High walker dependence (>40%)** — prioritize the balance-training plan; "
                 "the mCTSIB / single-leg findings say where.")
    L.append("\n_Assist commands stream to a robotic walker over BLE/serial. Screening aid, not a diagnosis._")

    with open(os.path.join(args.out, "report_walker.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    with open(os.path.join(args.out, "walker_feedback.json"), "w") as f:
        json.dump({"support_pct_mean": round(float(support.mean()), 1), "trend_pct": trend,
                   "handle_lean": lean, "asymmetry_pct": round(float(asym.mean()), 1),
                   "grabs": grabs, "feedback": feedback}, f, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/report_walker.md + walker_feedback.json")


if __name__ == "__main__":
    main()
