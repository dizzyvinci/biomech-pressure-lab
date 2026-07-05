#!/usr/bin/env python3
"""
balance.py — postural balance / stability from the SAME insole rig.

For people with BALANCE issues (not just foot pain): the FSR center-of-pressure
plus the IMU turn the wearable into a wearable posturography tool. Record a
quiet-standing (or single-leg / eyes-closed) session; this computes standard
sway metrics + fall-risk flags + plain-language findings.

Reads the same CSV logs (auto-groups by 'mode'/'activity' — e.g. label runs
`eyes_open` / `eyes_closed` / `single_leg`). Outputs:
    results/report_balance.md  +  results/balance_metrics.json

Metrics (standard posturography):
  - COP path length + mean velocity (mm, mm/s)
  - 95% confidence-ellipse AREA — the classic sway measure
  - ML / AP RMS + range, and which direction dominates
  - trunk-sway RMS from the IMU
  - Romberg quotient if eyes_closed & eyes_open are both present

NOT a medical device — a screening / training aid; pair with a clinician.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import calib
except Exception:
    calib = None

try:                       # keep console output safe on Windows code pages
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FSR = [f"fsr{i}" for i in range(8)]
XY = np.array([[.35, .08], [.65, .08], [.50, .45], [.30, .72],
               [.50, .74], [.70, .72], [.28, .92], [.55, .95]])
FOOT_W_MM, FOOT_L_MM = 95.0, 255.0     # footbed size -> real sway distances (approx)


def load(paths):
    fr = []
    for p in paths:
        d = pd.read_csv(p, comment="#"); d["__src"] = os.path.basename(p); fr.append(d)
    if not fr:
        raise SystemExit("no logs matched")
    return pd.concat(fr, ignore_index=True)


def group_col(df):
    for c in ("mode", "activity"):
        if c in df.columns:
            return c
    df["__all"] = "all"
    return "__all"


def values(df, cal):
    adc = df[FSR].to_numpy(float)
    return calib.frame_to_pressure(adc, cal) if (cal is not None and calib is not None) else adc


def cop_mm(f):
    tot = f.sum(1, keepdims=True); tot[tot == 0] = 1e-9
    c = (f @ XY) / tot
    return np.column_stack([c[:, 0] * FOOT_W_MM, c[:, 1] * FOOT_L_MM])   # mm


def ellipse_area(cop):
    """95% confidence-ellipse area = pi * 5.991 * sqrt(det(cov))."""
    c = cop - cop.mean(0)
    cov = np.cov(c.T)
    return float(np.pi * 5.991 * np.sqrt(max(np.linalg.det(cov), 0.0)))


def sway_metrics(t_ms, f, imu):
    t = t_ms.to_numpy(float) / 1000.0
    cop = cop_mm(f)
    d = np.diff(cop, axis=0); seg = np.hypot(d[:, 0], d[:, 1])
    path = float(seg.sum()); dur = max(t[-1] - t[0], 1e-6)
    ml = cop[:, 0] - cop[:, 0].mean(); ap = cop[:, 1] - cop[:, 1].mean()
    trunk = None
    if imu is not None and imu.shape[0] > 1:
        trunk = float(np.sqrt((imu[:, :2] ** 2).sum(1)).std())   # ax,ay horizontal accel std
    return dict(
        path_mm=round(path, 1), vel_mms=round(path / dur, 1), area_mm2=round(ellipse_area(cop), 1),
        ml_rms=round(float(ml.std()), 2), ap_rms=round(float(ap.std()), 2),
        ml_range=round(float(ml.max() - ml.min()), 1), ap_range=round(float(ap.max() - ap.min()), 1),
        trunk_sway=round(trunk, 3) if trunk is not None else None, dur_s=round(dur, 1),
    )


def interpret(m):
    out, flags = [], []
    out.append(f"Sway ellipse area {m['area_mm2']} mm^2, path {m['path_mm']} mm over "
               f"{m['dur_s']} s (velocity {m['vel_mms']} mm/s).")
    if m["area_mm2"] > 700:
        flags.append("large sway area")
        out.append("**Elevated sway area** — reduced postural stability; a fall-risk screen is warranted.")
    if m["vel_mms"] > 25:
        flags.append("high sway velocity")
        out.append("**High sway velocity** — many fast corrections (fatigue / vestibular / proprioceptive contribution possible).")
    if m["ml_rms"] > m["ap_rms"] * 1.3:
        out.append("Instability is **side-to-side (mediolateral)** — a wider base or lateral support helps.")
    elif m["ap_rms"] > m["ml_rms"] * 1.3:
        out.append("Instability is **front-to-back (anteroposterior)** — ankle strategy / heel-toe support.")
    if m["trunk_sway"] is not None:
        out.append(f"Trunk sway (IMU) {m['trunk_sway']} — {'high' if m['trunk_sway'] > 0.6 else 'moderate'}.")
    return out, flags


def romberg(by):
    if "eyes_closed" in by and "eyes_open" in by:
        r = by["eyes_closed"]["area_mm2"] / max(by["eyes_open"]["area_mm2"], 1e-6)
        msg = f"Romberg quotient (eyes-closed / eyes-open sway area) = {r:.1f}."
        if r > 2.0:
            msg += " **>2 -> strong reliance on vision** (proprioceptive/vestibular deficit pattern)."
        return [msg]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--out", default="results")
    ap.add_argument("--calibration", help="calibration.json for real units")
    args = ap.parse_args()

    paths = []
    for g in args.logs:
        paths += glob.glob(g)
    os.makedirs(args.out, exist_ok=True)
    cal = calib.load(args.calibration) if (args.calibration and calib) else None

    df = load(paths); gc = group_col(df)
    by = {}
    for name, sub in df.groupby(gc):
        sub = sub.sort_values("t_ms")
        f = values(sub, cal)
        imu = sub[["ax", "ay", "az"]].to_numpy(float) if {"ax", "ay", "az"}.issubset(sub.columns) else None
        by[str(name)] = sway_metrics(sub["t_ms"], f, imu)

    lines = ["# Balance / posturography — findings",
             "_Sway from center-of-pressure + IMU. A screening / training aid, not a diagnosis._", ""]
    for name, m in by.items():
        findings, flags = interpret(m)
        lines.append(f"\n## {name}\n")
        lines += [f"- {x}" for x in findings]
        if flags:
            lines.append(f"\n**Flags:** {', '.join(flags)}")
    rb = romberg(by)
    if rb:
        lines += ["\n## Romberg\n"] + [f"- {x}" for x in rb]

    with open(os.path.join(args.out, "report_balance.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    with open(os.path.join(args.out, "balance_metrics.json"), "w") as fh:
        json.dump(by, fh, indent=2)
    print("\n".join(lines))
    print(f"\n-> {args.out}/report_balance.md + balance_metrics.json")


if __name__ == "__main__":
    main()
