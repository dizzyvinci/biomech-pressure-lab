#!/usr/bin/env python3
"""
analyze_pressure.py — turn smart-insole logs into insole-design metrics.

Reads one or more CSV logs (from smart_insole.ino), and for each activity computes:
  * peak + mean force per foot zone
  * pressure-time integral (impulse) per zone   <- best predictor of "where it hurts"
  * center-of-pressure (COP) path
  * simple gait events (heel-strike / toe-off) -> stride time, cadence
  * the HOT SPOT (zone with max impulse) -> where the printed relief window goes
Outputs a summary table (CSV + printed) and PNG plots per activity.

Usage:
    python analyze_pressure.py log_000.csv [log_001.csv ...] --out results/
    python analyze_pressure.py "logs/*.csv" --out results/

FSR values are raw 12-bit ADC by default (relative). To get Newtons, fill CALIB
(per-channel slope/intercept from a known-weight calibration) and pass --calibrated.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FSR_COLS = [f"fsr{i}" for i in range(8)]

# Zone names in channel order (must match how you wired/placed the FSRs).
ZONES = ["heel_med","heel_lat","midfoot","met1","met3","met5","hallux","toes"]

# Approx sensor positions in a normalized foot frame (x=medial→lateral, y=heel→toe).
# Used for center-of-pressure. Tune to your actual placement.
SENSOR_XY = np.array([
    [0.35, 0.08],  # heel_med
    [0.65, 0.08],  # heel_lat
    [0.50, 0.45],  # midfoot
    [0.30, 0.72],  # met1
    [0.50, 0.74],  # met3
    [0.70, 0.72],  # met5
    [0.28, 0.92],  # hallux
    [0.55, 0.95],  # toes
])

# Optional per-channel linear calibration: force_N = slope*adc + intercept
CALIB = {i: (1.0, 0.0) for i in range(8)}  # replace after calibrating


def load_logs(paths):
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        df["__src"] = os.path.basename(p)
        frames.append(df)
    if not frames:
        sys.exit("No logs matched.")
    return pd.concat(frames, ignore_index=True)


def to_force(df, calibrated):
    f = df[FSR_COLS].to_numpy(dtype=float)
    if calibrated:
        for i in range(8):
            s, b = CALIB[i]
            f[:, i] = s * f[:, i] + b
        f = np.clip(f, 0, None)
    return f


def zone_metrics(t_ms, force):
    """Peak, mean, and pressure-time integral (impulse) per zone."""
    t = t_ms.to_numpy(dtype=float) / 1000.0
    dt = np.gradient(t) if len(t) > 1 else np.array([0.01])
    peak = force.max(axis=0)
    mean = force.mean(axis=0)
    impulse = (force * dt[:, None]).sum(axis=0)  # ∫F dt per zone
    return peak, mean, impulse


def center_of_pressure(force):
    tot = force.sum(axis=1, keepdims=True)
    tot[tot == 0] = 1e-9
    cop = (force @ SENSOR_XY) / tot
    return cop  # (N,2)


def gait_events(t_ms, force):
    """Heel-strike / toe-off from heel vs forefoot load. Returns cadence (steps/min)."""
    t = t_ms.to_numpy(dtype=float) / 1000.0
    heel = force[:, 0:2].sum(axis=1)
    thr = 0.2 * (heel.max() if heel.max() > 0 else 1)
    contact = heel > thr
    strikes = np.where((~contact[:-1]) & (contact[1:]))[0] + 1
    if len(strikes) < 2:
        return {"n_steps": int(len(strikes)), "cadence_spm": None, "stride_s": None}
    stride = np.diff(t[strikes])
    stride = stride[(stride > 0.2) & (stride < 2.5)]  # sane range
    if len(stride) == 0:
        return {"n_steps": int(len(strikes)), "cadence_spm": None, "stride_s": None}
    return {"n_steps": int(len(strikes)),
            "cadence_spm": round(60.0 / stride.mean(), 1),
            "stride_s": round(float(stride.mean()), 3)}


def plot_activity(name, t_ms, force, cop, outdir):
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    t = t_ms.to_numpy(dtype=float) / 1000.0

    for i, z in enumerate(ZONES):
        ax[0].plot(t, force[:, i], label=z, lw=0.9)
    ax[0].set(title=f"{name}: force per zone", xlabel="s", ylabel="force (rel)")
    ax[0].legend(fontsize=7, ncol=2)

    peak = force.max(axis=0)
    grid = np.full((10, 10), np.nan)
    for (x, y), v in zip(SENSOR_XY, peak):
        grid[int(y * 9), int(x * 9)] = v
    im = ax[1].imshow(grid, origin="lower", cmap="inferno", interpolation="bilinear")
    ax[1].set(title=f"{name}: peak-pressure map", xticks=[], yticks=[])
    fig.colorbar(im, ax=ax[1], fraction=0.046)

    ax[2].plot(cop[:, 0], cop[:, 1], lw=0.6)
    ax[2].scatter(SENSOR_XY[:, 0], SENSOR_XY[:, 1], c="k", s=12)
    ax[2].set(title=f"{name}: center-of-pressure path", xlim=(0, 1), ylim=(0, 1),
              xlabel="medial→lateral", ylabel="heel→toe")

    fig.tight_layout()
    path = os.path.join(outdir, f"{name}.png")
    fig.savefig(path, dpi=110); plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+", help="CSV file(s) or glob(s)")
    ap.add_argument("--out", default="results")
    ap.add_argument("--calibrated", action="store_true", help="apply CALIB -> Newtons")
    args = ap.parse_args()

    paths = []
    for g in args.logs:
        paths += glob.glob(g)
    os.makedirs(args.out, exist_ok=True)

    df = load_logs(paths)
    if "activity" not in df.columns:
        df["activity"] = "all"

    rows, plots = [], []
    for act, sub in df.groupby("activity"):
        sub = sub.sort_values("t_ms")
        force = to_force(sub, args.calibrated)
        peak, mean, impulse = zone_metrics(sub["t_ms"], force)
        cop = center_of_pressure(force)
        gait = gait_events(sub["t_ms"], force)
        hot = int(np.argmax(impulse))

        rows.append({
            "activity": act, "samples": len(sub),
            "hot_zone": ZONES[hot],
            "hot_peak": round(float(peak[hot]), 1),
            "hot_impulse": round(float(impulse[hot]), 1),
            **{f"peak_{z}": round(float(peak[i]), 1) for i, z in enumerate(ZONES)},
            **{f"impulse_{z}": round(float(impulse[i]), 1) for i, z in enumerate(ZONES)},
            **gait,
        })
        plots.append(plot_activity(str(act), sub["t_ms"], force, cop, args.out))

    summary = pd.DataFrame(rows)
    csv_path = os.path.join(args.out, "summary.csv")
    summary.to_csv(csv_path, index=False)

    # Overall hot spot = zone with highest impulse across weight-bearing activities.
    overall = (summary.filter(like="impulse_")
               .rename(columns=lambda c: c.replace("impulse_", ""))
               .sum().sort_values(ascending=False))
    hot_overall = overall.index[0]

    print("\n=== per-activity ===")
    cols = ["activity", "hot_zone", "hot_peak", "hot_impulse", "cadence_spm", "stride_s"]
    print(summary[cols].to_string(index=False))
    print(f"\n>>> OVERALL HOT SPOT: {hot_overall}  "
          f"(put the printed relief window here — see docs/insole_print_spec.md)")
    print(f"    plots + summary.csv -> {args.out}/")

    with open(os.path.join(args.out, "hotspot.json"), "w") as fh:
        json.dump({"overall_hot_zone": hot_overall,
                   "zone_impulse_rank": overall.round(1).to_dict()}, fh, indent=2)


if __name__ == "__main__":
    main()
