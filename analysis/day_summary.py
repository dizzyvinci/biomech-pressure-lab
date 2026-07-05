#!/usr/bin/env python3
"""
day_summary.py — real logs -> a DAY summary (per-zone peak, PTI-per-cycle, cycles/day).

This is the bridge from what the insole actually records to what nerve_fascia.py needs.
It reads your session CSVs (from firmware/all_day_logger or smart_insole), calibrates ADC ->
kPa, splits them into **gait** (walking) vs **at-rest bounce** (leg-jiggle / toe-tap), and
for each computes:
  · peak pressure (kPa) per zone            — the day's high-water mark (drives the gradient)
  · pressure-time integral PER CYCLE (kPa·s) — one loading cycle's dose, per zone
  · loading cycles per day                   — cadence x walking hours; bounce freq x sitting hours

CPTS (all-day dose) is then PTI-per-cycle x cycles/day, summed over gait + bounce — computed
downstream in nerve_fascia.py. Sessions are classified by their mode/activity label, or, when
unlabelled, by an FFT check for a sustained ~2-3 Hz forefoot bounce.

    python day_summary.py "sample/sample_day_*.csv" --calibration sample/calibration.json \
        --walk-hours 10 --bounce-hours 4 --out results/
    # -> results/day.json  (feed to: nerve_fascia.py --day results/day.json)

met2 & met4 are interpolated from neighbors (as elsewhere). NOT a medical device.
"""
import argparse, glob, json, os, re, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bounce import dominant_freq, sample_rate, FORE, HEEL
try:
    import calib
except Exception:
    calib = None
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FSR = [f"fsr{i}" for i in range(8)]
SENSOR_ZONES = ["heel_med", "heel_lat", "midfoot", "met1", "met3", "met5", "hallux", "toes"]
BOUNCE_RE = re.compile(r"bounce|seat|tap|rest|jiggle|fidget|idle", re.I)


def label_of(df):
    for c in ("phase", "activity", "mode"):
        if c in df.columns and df[c].notna().any():
            return str(df[c].dropna().mode().iloc[0])
    return ""


def values_kPa(df, cal):
    adc = df[FSR].to_numpy(float)
    if cal is not None and calib is not None:
        return calib.frame_to_pressure(adc, cal)      # kPa
    return adc                                         # relative ADC (uncalibrated)


def count_cycles(sig, fs, min_gap_s=0.4):
    """Loading cycles = threshold rising-edges, with a refractory gap so a mid-stance force
    dip doesn't count one step twice (one stance = one cycle)."""
    s = np.asarray(sig, float) - np.min(sig)
    thr = 0.25 * (s.max() or 1.0)
    c = s > thr
    rises = np.where((~c[:-1]) & (c[1:]))[0]
    if len(rises) == 0:
        return 1
    gap = int(min_gap_s * fs)
    kept = [rises[0]]
    for r in rises[1:]:
        if r - kept[-1] >= gap:
            kept.append(r)
    return max(len(kept), 1)


def to10(d8):
    d = dict(d8)
    d["met2"] = round((d["met1"] + d["met3"]) / 2, 2)
    d["met4"] = round((d["met3"] + d["met5"]) / 2, 2)
    return d


def session_stats(df, cal):
    df = df.sort_values("t_ms")
    t = df["t_ms"].to_numpy(float) / 1000.0
    dur = max(t[-1] - t[0], 1e-6)
    fs = sample_rate(df["t_ms"])
    p = values_kPa(df, cal)                             # (n, 8) kPa
    dt = np.gradient(t)
    pti_total = (p * dt[:, None]).sum(0)               # kPa*s per zone over the session
    peak = p.max(0)
    fore = p[:, FORE].mean(1)
    total = p.sum(1)
    freq, frac = dominant_freq(fore, fs)
    return dict(dur=dur, fs=fs, peak=peak, pti_total=pti_total,
                fore=fore, total=total, freq=freq, frac=frac,
                n_gait_cycles=count_cycles(total, fs))


def is_bounce(label, st):
    if BOUNCE_RE.search(label or ""):
        return True
    # unlabelled: sustained ~2-3 Hz forefoot oscillation with little heel loading
    forefoot_dominant = st["fore"].mean() > 1.2 * (st["peak"][HEEL].mean() + 1e-9)
    return st["frac"] > 0.15 and 1.5 <= st["freq"] <= 4.0 and forefoot_dominant


def build_day(paths, cal, walk_hours=10.0, bounce_hours=4.0):
    gait, bounce = [], []
    for p in paths:
        df = pd.read_csv(p, comment="#")
        if not set(FSR).issubset(df.columns):
            continue
        st = session_stats(df, cal)
        st["label"] = label_of(df)
        st["src"] = os.path.basename(p)
        (bounce if is_bounce(st["label"], st) else gait).append(st)

    peak8 = np.zeros(8)
    for st in gait + bounce:
        peak8 = np.maximum(peak8, st["peak"])          # day high-water mark per zone

    def per_cycle(sessions, cycle_key):
        if not sessions:
            return None
        pti = np.zeros(8); cyc = 0
        for st in sessions:
            pti += st["pti_total"]
            cyc += st[cycle_key] if cycle_key == "n_gait_cycles" else max(st["freq"] * st["dur"], 1)
        return pti / max(cyc, 1), cyc, sum(st["dur"] for st in sessions)

    day = {"pressure_kPa": to10({z: round(float(peak8[i]), 1) for i, z in enumerate(SENSOR_ZONES)})}

    g = per_cycle(gait, "n_gait_cycles")
    if g:
        pti_pc, cyc, dur = g
        rate = cyc / max(dur, 1e-6)                     # cycles/sec while walking
        day["gait"] = {
            "pti_kPa_s": to10({z: round(float(pti_pc[i]), 3) for i, z in enumerate(SENSOR_ZONES)}),
            "cycles_per_day": round(rate * walk_hours * 3600),
            "cadence_hz": round(rate, 2), "sessions": len(gait)}

    bnc = per_cycle(bounce, "freq")
    if bnc:
        pti_pc, cyc, dur = bnc
        freq = float(np.mean([st["freq"] for st in bounce]))
        day["bounce"] = {
            "pti_kPa_s": to10({z: round(float(pti_pc[i]), 3) for i, z in enumerate(SENSOR_ZONES)}),
            "cycles_per_day": round(freq * bounce_hours * 3600),
            "freq_hz": round(freq, 2), "sessions": len(bounce)}

    day["provenance"] = {"calibrated": cal is not None, "walk_hours": walk_hours,
                         "bounce_hours": bounce_hours,
                         "gait_sessions": [st["src"] for st in gait],
                         "bounce_sessions": [st["src"] for st in bounce]}
    return day


def main():
    ap = argparse.ArgumentParser(description="Build a day summary (peak/PTI/cycles) from real logs.")
    ap.add_argument("logs", nargs="+", help="session CSV glob(s)")
    ap.add_argument("--calibration", help="calibration.json (from calibrate.py) for real kPa")
    ap.add_argument("--walk-hours", type=float, default=10.0)
    ap.add_argument("--bounce-hours", type=float, default=4.0)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    paths = []
    for g in a.logs:
        paths += glob.glob(g)
    if not paths:
        raise SystemExit("no logs matched")
    cal = calib.load(a.calibration) if (a.calibration and calib) else None
    day = build_day(paths, cal, a.walk_hours, a.bounce_hours)

    unit = "kPa" if cal is not None else "ADC (uncalibrated — add --calibration)"
    print(f"# Day summary  ({unit})")
    print(f"gait: {day.get('gait', {}).get('cycles_per_day', 0):,}/day "
          f"({day.get('gait', {}).get('cadence_hz', 0)} Hz, {day.get('gait', {}).get('sessions', 0)} sessions)  ·  "
          f"bounce: {day.get('bounce', {}).get('cycles_per_day', 0):,}/day "
          f"({day.get('bounce', {}).get('freq_hz', 0)} Hz, {day.get('bounce', {}).get('sessions', 0)} sessions)")
    print("peak kPa:", {k: v for k, v in day["pressure_kPa"].items()})
    with open(os.path.join(a.out, "day.json"), "w") as fh:
        json.dump(day, fh, indent=2)
    print(f"\n-> {a.out}/day.json   (feed: nerve_fascia.py --day {a.out}/day.json)")


if __name__ == "__main__":
    main()
