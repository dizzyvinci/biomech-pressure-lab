#!/usr/bin/env python3
"""
gait_cue.py — freezing-of-gait (FOG) detection + external CUEING for Parkinson's.

Freezing of gait ("my feet are glued to the floor") is a major fall cause in
Parkinson's. The evidence-based fix is an external cue that breaks the freeze and
paces stepping: **visual cues** (AR floor-lines in cueing glasses, or laser lines
from the shoe) you step over, an **auditory** metronome, or a **haptic** buzz.

This module detects freezes from the ankle IMU and emits a CUE-EVENT stream that a
paired device consumes (BLE/serial). Detection = the classic **Freeze Index**
(Moore 2008 / Bachlin 2010):

    FI = power(3-8 Hz "freeze" band) / power(0.5-3 Hz "locomotor" band)

computed over sliding windows of vertical acceleration. A freeze is flagged when FI
exceeds a threshold AND there is enough movement power (so quiet standing, which has
no locomotor power, isn't misread as a freeze).

    python gait_cue.py --demo                    # synth a walk w/ freezes -> cue stream
    python gait_cue.py walk.csv --out results/   # a real insole log (needs ax,ay,az)

Outputs results/cue_events.json + results/fog_timeline.json.
NOT a medical device — an assistive prototype; use with a clinician.
"""
import argparse, json, os, sys
import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def vertical_accel(df):
    """Best available vertical/overall acceleration channel from an insole log."""
    if "az" in df.columns:
        a = df[["ax", "ay", "az"]].to_numpy(float) if {"ax", "ay"}.issubset(df.columns) else df[["az"]].to_numpy(float)
        return np.linalg.norm(a, axis=1) if a.shape[1] == 3 else a[:, 0]
    raise SystemExit("log needs at least an 'az' column")


def sample_rate(t_ms):
    dt = np.median(np.diff(t_ms.to_numpy(float))) / 1000.0
    return 1.0 / dt if dt > 0 else 50.0


def freeze_series(acc, fs, win_s=4.0, step_s=0.5,
                  f_freeze=(3.0, 8.0), f_loco=(0.5, 3.0)):
    """Sliding-window Freeze Index + band power. Returns list of (t, FI, power)."""
    win = max(int(win_s * fs), 8)
    step = max(int(step_s * fs), 1)
    w = np.hanning(win)
    f = np.fft.rfftfreq(win, 1.0 / fs)
    m_frz = (f >= f_freeze[0]) & (f < f_freeze[1])
    m_loc = (f >= f_loco[0]) & (f < f_loco[1])
    out = []
    for i in range(0, len(acc) - win + 1, step):
        seg = acc[i:i + win]; seg = (seg - seg.mean()) * w
        P = np.abs(np.fft.rfft(seg)) ** 2
        loco = float(P[m_loc].sum()); frz = float(P[m_frz].sum())
        out.append(((i + win / 2) / fs, frz / max(loco, 1e-9), loco + frz))
    return out


def target_cadence(fi_series, fs):
    """Estimate a metronome BPM from the locomotor rhythm during non-freeze windows."""
    # steps/min ~ 2 x dominant locomotor frequency (Hz) x 60; default a safe 100 spm
    return 110


def cue_events(fi_series, fi_thr, pow_thr, bpm):
    """Freeze detection -> cue stream a device (glasses/laser/metronome/haptic) acts on."""
    ev, frozen = [], False
    for t, fi, power in fi_series:
        is_freeze = fi > fi_thr and power > pow_thr
        if is_freeze and not frozen:
            frozen = True
            t = round(t, 2)
            ev += [
                {"t": t, "channel": "visual_lines", "action": "on",
                 "params": {"spacing_cm": 40, "note": "AR floor-lines / laser to step over"}},
                {"t": t, "channel": "metronome", "action": "start", "params": {"bpm": bpm}},
                {"t": t, "channel": "haptic", "action": "buzz", "params": {"ms": 300}},
            ]
        elif not is_freeze and frozen:
            frozen = False
            ev += [{"t": round(t, 2), "channel": "visual_lines", "action": "off"},
                   {"t": round(t, 2), "channel": "metronome", "action": "stop"}]
    return ev


def episodes(fi_series, fi_thr, pow_thr):
    eps, start = [], None
    for t, fi, power in fi_series:
        f = fi > fi_thr and power > pow_thr
        if f and start is None:
            start = t
        elif not f and start is not None:
            eps.append([float(round(start, 1)), float(round(t, 1))]); start = None
    if start is not None:
        eps.append([float(round(start, 1)), float(round(fi_series[-1][0], 1))])
    return eps


def demo_log(fs=50, dur=40):
    rng = np.random.default_rng(3)
    t = np.arange(int(dur * fs)) / fs
    acc = 9.81 + 0.55 * np.sin(2 * np.pi * 2.0 * t)               # ~2 Hz walking (locomotor)
    for a, b in [(12, 18), (26, 32)]:                            # two freeze episodes
        m = (t >= a) & (t < b)
        acc[m] = 9.81 + 0.16 * np.sin(2 * np.pi * 6.5 * t[m])     # trembling, no stepping
    acc += 0.03 * rng.standard_normal(len(t))
    return pd.DataFrame({"t_ms": (t * 1000).astype(int), "ax": 0.02 * rng.standard_normal(len(t)),
                         "ay": 0.02 * rng.standard_normal(len(t)), "az": acc})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?", help="insole CSV with ax,ay,az")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default="results")
    ap.add_argument("--fi-threshold", type=float, default=2.0)
    ap.add_argument("--power-threshold", type=float, default=0.0,
                    help="min movement power to count (0 = auto: 3%% of peak, filters quiet standing)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    df = demo_log() if args.demo else pd.read_csv(args.log, comment="#")
    fs = sample_rate(df["t_ms"])
    acc = vertical_accel(df)
    fis = freeze_series(acc, fs)
    # movement floor = 3% of PEAK window power: rejects quiet standing (near-zero)
    # while still passing freeze-trembling (which is lower power than full stepping).
    peak_pow = max((p for _, _, p in fis), default=1.0)
    pow_thr = args.power_threshold or 0.03 * peak_pow
    bpm = target_cadence(fis, fs)

    eps = episodes(fis, args.fi_threshold, pow_thr)
    ev = cue_events(fis, args.fi_threshold, pow_thr, bpm)
    with open(os.path.join(args.out, "cue_events.json"), "w") as f:
        json.dump({"metronome_bpm": bpm, "events": ev}, f, indent=2)
    with open(os.path.join(args.out, "fog_timeline.json"), "w") as f:
        json.dump({"fs_hz": round(fs, 1), "freeze_episodes_s": eps,
                   "n_freezes": len(eps)}, f, indent=2)

    print(f"sample rate {fs:.0f} Hz · {len(fis)} windows · FI>{args.fi_threshold}, power>{pow_thr:.0f}")
    print(f"FREEZES detected: {len(eps)}  -> {eps}")
    print(f"cue events: {len(ev)}  (visual lines + metronome @ {bpm} bpm + haptic on each freeze)")
    for e in ev[:6]:
        print(f"  t={e['t']:5}s  {e['channel']:13} {e['action']}"
              + (f"  {e['params']}" if e.get("params") else ""))
    print(f"\n-> {args.out}/cue_events.json + fog_timeline.json")


if __name__ == "__main__":
    main()
