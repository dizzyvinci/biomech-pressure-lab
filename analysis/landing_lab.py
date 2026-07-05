#!/usr/bin/env python3
"""
landing_lab.py — discipline-aware landing analysis (gymnastics / figure skating / dance).

A landing is a different question in each sport (all contact FOREFOOT-first, then diverge):

  GYMNASTICS "stick"  — forefoot -> heel drops -> STOP dead. Score = settle to
                        stillness; hops / steps / wobbles deduct.
  FIGURE SKATING      — ONE foot, back-outside EDGE, plie, FLOW OUT in a glide.
                        Score = single-foot + edge (ML) control + smooth forward
                        flow; step-out / stumble / hard slam deduct. Not static.
  DANCE / BALLET      — toe -> ball -> heel ROLL through the foot with demi-plie,
                        SOFT + quiet. Score = low impact + a real roll + control.

Same insole; detect the impact, then score per discipline.

    python landing_lab.py --demo
    python landing_lab.py session.csv --discipline figure_skating --calibration cal.json
        # or label segments in the log and use --discipline per file

Outputs results/report_landing_lab.md + landing_lab.json.  NOT a medical device.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from balance import load, group_col, values, cop_mm, ellipse_area, FOOT_L_MM
from beam_balance import smooth, cop_speed, count_peaks, sample_rate, _synthF
try:
    import calib
except Exception:
    calib = None
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MEDIAL, LATERAL, HEEL, FORE = [0, 3, 6], [1, 5], [0, 1], [3, 4, 5, 6, 7]


def landing_primitives(t, f):
    """Shared landing features: impact, loading rate, forefoot/heel roll, COP flow."""
    total = f.sum(1)
    dtot = np.gradient(total, t)
    imp = int(np.argmax(dtot)); t0 = t[imp]
    m = (t >= t0 - 0.05) & (t <= t0 + 2.5)
    tp, fp = t[m], f[m]
    tot = fp.sum(1)
    cop = cop_mm(fp)
    fore = fp[:, FORE].sum(1); heel = fp[:, HEEL].sum(1)
    roll_lag = float(tp[np.argmax(heel)] - tp[np.argmax(fore)])   # + = forefoot then heel (rolled through)
    med = fp[:, MEDIAL].sum(1); lat = fp[:, LATERAL].sum(1)
    edge = "outside/lateral" if lat.mean() > med.mean() else "inside/medial"
    ml = cop[:, 0]; ap = cop[:, 1]
    spd = cop_speed(tp, cop)
    above = np.where(spd > 25.0)[0]
    settle = float(round(tp[above[-1]] - t0, 2)) if len(above) else 0.0
    return dict(
        t0=t0, dur=float(tp[-1] - t0), impact_peak=float(tot.max()),
        loading_rate=float(np.max(np.gradient(tot, tp))),           # N/s — high = hard/slam
        roll_lag_s=round(roll_lag, 2),
        ml_std=round(float(smooth(ml, 7).std()), 2),                # edge chatter
        ml_excursion=round(float(ml.max() - ml.min()), 1),
        ap_flow=round(float(smooth(ap, 9)[-1] - smooth(ap, 9)[:5].mean()), 1),  # + = flows forward
        edge=edge, settle_s=settle, wobbles=count_peaks(spd, 45.0),
        forefoot_pct=round(100 * fore.mean() / (tot.mean() or 1e-9), 0),
    )


def score_gymnastics(p):
    step = p["ml_excursion"] > 28
    ded = (0.3 if p["settle_s"] > 1.0 else 0.1 if p["settle_s"] > 0.5 else 0.0)
    ded += min(0.5, 0.1 * p["wobbles"]) + (0.5 if step else 0.0)
    v = "STUCK — clean" if 10 - ded >= 9.7 else "small check" if 10 - ded >= 9 else "wobbly / step"
    return round(max(0.0, 10 - ded), 1), v, [
        f"settle {p['settle_s']}s · {p['wobbles']} wobble(s) · step {'YES' if step else 'no'}",
        "forefoot-first then heel, then hold — that's the stick."]


def score_skating(p):
    stepout = p["ml_excursion"] > 30
    hard = p["loading_rate"] > 12000
    noflow = p["ap_flow"] < 8
    ded = (0.5 if stepout else 0.0) + min(0.4, 0.1 * p["wobbles"]) + \
          (0.2 if hard else 0.0) + (0.3 if noflow else 0.0) + min(0.3, p["ml_std"] / 10)
    v = "clean edge check-out" if 10 - ded >= 9.3 else "held but not clean" if 10 - ded >= 8.3 else "step-out / two-foot"
    return round(max(0.0, 10 - ded), 1), v, [
        f"landed on the {p['edge']} edge · edge chatter (ML std) {p['ml_std']} mm",
        f"forward flow-out {p['ap_flow']} mm ({'smooth glide' if not noflow else 'stalled'}) · "
        f"absorption {'soft plié' if not hard else 'hard slam'}"]


def score_dance(p):
    hard = p["loading_rate"] > 9000
    flat = p["roll_lag_s"] < 0.05
    ded = (0.4 if hard else 0.0) + (0.3 if flat else 0.0) + min(0.4, 0.1 * p["wobbles"]) + \
          (0.2 if p["impact_peak"] > 3.5 * 700 else 0.0)
    v = "soft & rolled" if 10 - ded >= 9.3 else "a bit heavy" if 10 - ded >= 8.3 else "hard / flat landing"
    return round(max(0.0, 10 - ded), 1), v, [
        f"toe->ball->heel roll: {'yes' if not flat else 'no (flat slap)'} (heel {p['roll_lag_s']}s after forefoot)",
        f"impact {'soft' if not hard else 'heavy'} (loading rate {p['loading_rate']:.0f} N/s) · demi-plié absorbs it"]


SCORERS = {"gymnastics": score_gymnastics, "figure_skating": score_skating, "dance": score_dance}


# ---- demo: one clean landing per discipline --------------------------------
def _seg(label, cx, cy, total, rng):
    n = len(cx)
    F = _synthF(cx, cy, total, sigma=0.15) * (1 + 0.01 * rng.standard_normal((n, 8)))
    d = {"activity": label}
    for i in range(8): d[f"fsr{i}"] = F[:, i]
    d["qw"] = 1.0; d["qx"] = 0.0; d["qy"] = 0.0; d["qz"] = 0.0
    d["ax"] = 0.02 * rng.standard_normal(n); d["ay"] = 0.02 * rng.standard_normal(n); d["az"] = 9.81 + total / 80.0
    return pd.DataFrame(d)


def demo(fs=100):
    rng = np.random.default_rng(11)
    out = []

    def base(n, flight=0.4):
        t = np.arange(n) / fs
        return t, (t < flight)

    # gymnastics: sharp slam, forefoot->heel, then freeze
    n = int(2.5 * fs); t, fly = base(n)
    total = np.full(n, 700.0); total[fly] = 5.0
    sl = (t >= 0.4) & (t < 0.46); total[sl] = 1400.0
    cy = np.where(t < 0.4, 0.75, np.clip(0.78 - 0.35 * np.exp(-(t - 0.4) / 0.15), 0.45, 0.8))
    cx = 0.50 + np.where(t < 0.4, 0, 0.015 * np.exp(-(t - 0.4) / 0.14) * np.sin(2 * np.pi * 2.5 * (t - 0.4)))
    out.append(("gymnastics_stick", _seg("gymnastics_stick", cx, cy, total, rng)))

    # figure skating: gradual plié, outside(lateral) edge, forward flow-out, one foot
    n = int(2.5 * fs); t, fly = base(n)
    ramp = np.clip((t - 0.4) / 0.25, 0, 1); total = 5 + (720 - 5) * ramp; total[fly] = 5.0
    cx = np.where(t < 0.4, 0.5, 0.64 + 0.01 * np.sin(2 * np.pi * 1.5 * (t - 0.4)))  # outside edge, steady
    cy = np.where(t < 0.4, 0.72, np.clip(0.72 + 0.16 * ramp, 0.72, 0.9))            # flows forward
    out.append(("skating_checkout", _seg("skating_checkout", cx, cy, total, rng)))

    # dance: soft gradual, toe->ball->heel roll, demi-plié
    n = int(2.5 * fs); t, fly = base(n)
    ramp = np.clip((t - 0.4) / 0.30, 0, 1); total = 5 + (620 - 5) * ramp; total[fly] = 5.0
    cy = np.where(t < 0.4, 0.84, np.clip(0.84 - 0.5 * np.clip((t - 0.42) / 0.28, 0, 1), 0.34, 0.84))  # roll to heel
    cx = 0.50 + np.where(t < 0.4, 0, 0.01 * np.exp(-(t - 0.4) / 0.3) * np.sin(2 * np.pi * 2 * (t - 0.4)))
    out.append(("dance_landing", _seg("dance_landing", cx, cy, total, rng)))

    df = pd.concat([s for _, s in out], ignore_index=True)
    df["t_ms"] = (np.arange(len(df)) / fs * 1000).astype(int)
    kinds = {"gymnastics_stick": "gymnastics", "skating_checkout": "figure_skating", "dance_landing": "dance"}
    return df, kinds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--discipline", choices=list(SCORERS), default="gymnastics")
    ap.add_argument("--out", default="results")
    ap.add_argument("--calibration")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    cal = calib.load(args.calibration) if (args.calibration and calib) else None

    if args.demo:
        df, kinds = demo()
    else:
        paths = []
        for g in args.logs:
            paths += glob.glob(g)
        df = load(paths); kinds = {}

    gc = group_col(df)
    L = ["# Landing lab — discipline-aware landing scores",
         "_All land forefoot-first; the discipline decides what 'good' means. From the insole COP + IMU._", ""]
    res = {}
    for name, sub in df.groupby(gc):
        sub = sub.sort_values("t_ms")
        t = sub["t_ms"].to_numpy(float) / 1000.0
        f = values(sub, cal)
        p = landing_primitives(t, f)
        disc = kinds.get(str(name), args.discipline)
        score, verdict, notes = SCORERS[disc](p)
        res[str(name)] = {"discipline": disc, "score": score, "verdict": verdict, **p}
        L += [f"\n## {name} — {disc.replace('_', ' ')}  ·  **{score}/10** ({verdict})\n"] + [f"- {x}" for x in notes]

    L.append("\n_Gymnastics rewards stopping; skating rewards a clean gliding edge; dance rewards a soft roll. "
             "Same sensor, three rubrics. Sync each rep to your video by timestamp._")
    with open(os.path.join(args.out, "report_landing_lab.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(args.out, "landing_lab.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/report_landing_lab.md + landing_lab.json")


if __name__ == "__main__":
    main()
