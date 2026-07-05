#!/usr/bin/env python3
"""
beam_balance.py — specialized balance for athletes (gymnasts on the beam).

Clinical balance asks "are you safe?"; elite balance asks "how clean was that?".
On a 10 cm beam, mediolateral (side-to-side) sway is what makes you fall off, and
the signature score is the **landing "stick"** — judges deduct for wobbles and
steps. This module, from the same insole COP + IMU, scores:

  - **Static holds** (scale / relevé / arabesque): ML-focused sway + a hold grade
  - **Landing stick**: detect the impact, then settling time, post-landing sway,
    **wobble count**, and **step** detection -> a judge-style 0-10 stick score
  - **Relevé load**: forefoot vs heel share (beam work lives on the ball of the foot)
  - **Vision independence** (if eyes_open/closed present): gymnasts SHOULD balance
    well eyes-closed — a *low* Romberg is elite (inverse of the clinical read)

    python beam_balance.py --demo --out results/
    python beam_balance.py "session.csv" --calibration cal.json --out results/
        # label segments via the activity/mode column: 'releve_hold', 'landing_1', ...

Leverages existing kit: sync landings to your **video review** by timestamp — the
sensor adds the objective COP layer the camera can't see. NOT a medical device.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from balance import load, group_col, values, cop_mm, ellipse_area, XY, FOOT_W_MM
try:
    import calib
except Exception:
    calib = None
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HEEL, FORE = [0, 1], [3, 4, 5, 6, 7]


def sample_rate(t_ms):
    dt = np.median(np.diff(t_ms.to_numpy(float))) / 1000.0
    return 1.0 / dt if dt > 0 else 100.0


def count_peaks(x, thr):
    return int(sum(1 for i in range(1, len(x) - 1)
                   if x[i] > thr and x[i] >= x[i - 1] and x[i] > x[i + 1]))


def smooth(a, w=7):
    a = np.asarray(a, float)
    if w < 2 or len(a) < w:
        return a
    p = w // 2
    ap = np.pad(a, p, mode="edge")                          # edge-pad: no false jump at the ends
    return np.convolve(ap, np.ones(w) / w, mode="valid")[:len(a)]


def cop_speed(t, cop):
    cx, cy = smooth(cop[:, 0]), smooth(cop[:, 1])            # low-pass so noise isn't read as sway
    d = np.hypot(np.diff(cx), np.diff(cy))
    return np.r_[0, d / np.clip(np.diff(t), 1e-6, None)]     # mm/s


def hold_metrics(t, cop, f):
    ml = cop[:, 0] - cop[:, 0].mean(); ap = cop[:, 1] - cop[:, 1].mean()
    dur = max(t[-1] - t[0], 1e-6)
    z = f.mean(0); tot = z.sum() or 1e-9
    ml_rms = float(ml.std())
    grade = "elite" if ml_rms < 2 else "solid" if ml_rms < 4 else "shaky"
    return dict(ml_rms=round(ml_rms, 2), ap_rms=round(float(ap.std()), 2),
                area_mm2=round(ellipse_area(cop), 1), vel_mms=round(float(cop_speed(t, cop).mean()), 1),
                forefoot_pct=round(100 * z[FORE].sum() / tot, 0), heel_pct=round(100 * z[HEEL].sum() / tot, 0),
                dur_s=round(dur, 1), grade=grade)


def landing_metrics(t, cop, total):
    imp = int(np.argmax(np.gradient(total, t)))                 # impact = steepest force onset
    t0 = t[imp]
    m = (t >= t0) & (t <= t0 + 3.0)
    tp, cp, tt = t[m], cop[m], total[m]
    if len(tp) < 6:
        return None
    spd = cop_speed(tp, cp)
    above = np.where(spd > 25.0)[0]                             # "settled" = COP speed < 25 mm/s
    settle = float(round(tp[above[-1]] - t0, 2)) if len(above) else 0.0
    m2 = tp <= t0 + 2.0
    area = round(ellipse_area(cp[m2]), 0) if m2.sum() > 3 else 0.0
    wob = count_peaks(spd, 45.0)
    ml_exc = float(cp[:, 0].max() - cp[:, 0].min())
    step = ml_exc > 28 or (tt.min() < 0.35 * tt.max())         # big ML shift OR a re-unweight (hop/step)
    # judge-style execution deductions (points)
    ded = (0.3 if settle > 1.0 else 0.1 if settle > 0.5 else 0.0)
    ded += min(0.5, 0.1 * wob) + (0.5 if step else 0.0) + (0.1 if area > 800 else 0.0)
    return dict(settle_s=round(settle, 2), post_sway_mm2=area, wobbles=wob,
                ml_excursion_mm=round(ml_exc, 1), step=bool(step),
                deductions=round(ded, 1), stick_score=round(max(0.0, 10 - ded), 1))


def seg_kind(label):
    s = str(label).lower()
    if any(k in s for k in ("land", "dismount", "stick", "vault")): return "landing"
    if any(k in s for k in ("hold", "scale", "releve", "relevé", "arabesque", "stand", "pose")): return "hold"
    return "hold"


# ---- demo ------------------------------------------------------------------
def _synthF(cx, cy, total, sigma=0.22):
    d2 = (XY[None, :, 0] - cx[:, None]) ** 2 + (XY[None, :, 1] - cy[:, None]) ** 2
    w = np.exp(-d2 / (2 * sigma ** 2)); w /= w.sum(1, keepdims=True)
    return total[:, None] * w


def demo(fs=100):
    rng = np.random.default_rng(7)
    parts = []

    def seg(label, cx, cy, total):
        n = len(cx)
        F = _synthF(cx, cy, total) * (1 + 0.01 * rng.standard_normal((n, 8)))
        d = {"t_ms": None, "activity": label}
        for i in range(8): d[f"fsr{i}"] = F[:, i]
        d["qw"] = 1.0; d["qx"] = 0; d["qy"] = 0; d["qz"] = 0
        d["ax"] = 0.02 * rng.standard_normal(n); d["ay"] = 0.02 * rng.standard_normal(n)
        d["az"] = 9.81 + total / 80.0
        return pd.DataFrame(d)

    # 1) relevé hold, 8s: forefoot, tiny ML sway (elite)
    n = 8 * fs; t = np.arange(n) / fs
    cx = 0.50 + 0.015 * np.sin(2 * np.pi * 0.4 * t); cy = 0.80 + 0.01 * np.sin(2 * np.pi * 0.3 * t)
    parts.append(seg("releve_hold", cx, cy, np.full(n, 700.0)))

    def landing(label, amp, tau, freq, stepped):
        n = int(3.0 * fs); t = np.arange(n) / fs
        total = np.full(n, 700.0); tp = t - 0.5
        fly = t < 0.5; total[fly] = 5.0                        # flight
        imp = (t >= 0.5) & (t < 0.58); total[imp] = 1500.0     # impact spike
        cx = np.full(n, 0.50); cy = np.full(n, 0.72)
        post = t >= 0.5
        cx[post] = 0.50 + amp * np.exp(-tp[post] / tau) * np.sin(2 * np.pi * freq * tp[post])
        if stepped:
            s = (t >= 1.4); cx[s] += 0.10                      # a corrective step
            hop = (t >= 1.35) & (t < 1.45); total[hop] = 180.0  # brief re-unweight
        return seg(label, cx, cy, total)

    parts.append(landing("landing_clean", amp=0.02, tau=0.14, freq=2.5, stepped=False))
    parts.append(landing("landing_wobble", amp=0.07, tau=0.55, freq=2.2, stepped=True))

    df = pd.concat(parts, ignore_index=True)
    df["t_ms"] = (np.arange(len(df)) / fs * 1000).astype(int)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default="results")
    ap.add_argument("--calibration")
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
    gc = group_col(df)

    L = ["# Beam / athlete balance — findings",
         "_Elite balance: mediolateral control + landing 'stick'. From the insole COP + IMU._", ""]
    out = {}
    for name, sub in df.groupby(gc):
        sub = sub.sort_values("t_ms")
        t = sub["t_ms"].to_numpy(float) / 1000.0
        f = values(sub, cal)
        cop = cop_mm(f); total = f.sum(1)
        kind = seg_kind(name)
        if kind == "landing":
            r = landing_metrics(t, cop, total)
            out[str(name)] = {"kind": "landing", **(r or {})}
            if r:
                verdict = ("STUCK — clean" if r["stick_score"] >= 9.7 else
                           "small check" if r["stick_score"] >= 9.0 else "wobbly / step")
                L += [f"\n## {name} — landing  ·  **stick {r['stick_score']}/10** ({verdict})\n",
                      f"- settle {r['settle_s']}s · post-sway {r['post_sway_mm2']:.0f} mm² · "
                      f"{r['wobbles']} wobble(s) · ML swing {r['ml_excursion_mm']} mm · "
                      f"step: {'YES' if r['step'] else 'no'}",
                      f"- execution deduction ~{r['deductions']} pt"]
        else:
            r = hold_metrics(t, cop, f)
            out[str(name)] = {"kind": "hold", **r}
            L += [f"\n## {name} — hold  ·  **ML sway {r['ml_rms']} mm ({r['grade']})**\n",
                  f"- area {r['area_mm2']} mm² · vel {r['vel_mms']} mm/s · held {r['dur_s']}s",
                  f"- load: {r['forefoot_pct']:.0f}% forefoot / {r['heel_pct']:.0f}% heel "
                  f"({'relevé — on the ball' if r['forefoot_pct'] > 65 else 'flat'})"]

    # vision independence (athlete Romberg — LOW is elite)
    areas = {seg_kind(k): out[k].get("area_mm2") for k in out}
    L.append("\n_On a beam, watch ML sway (not total). A clean stick is ≥9.7; each wobble ~0.1, a step ~0.5. "
             "Trend these across a season._")

    with open(os.path.join(args.out, "report_beam_balance.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(args.out, "beam_balance.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/report_beam_balance.md + beam_balance.json")


if __name__ == "__main__":
    main()
