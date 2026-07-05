#!/usr/bin/env python3
"""
balance_positions.py — protocol-aware balance analysis across STANCE POSITIONS.

Beyond eyes-open/closed (balance.py), this reads a set of labeled recordings and
runs standard clinical balance protocols, using the same FSR center-of-pressure +
IMU:

  - mCTSIB  (firm/foam x eyes open/closed)  -> which sense you rely on
            (somatosensory / visual / vestibular) + a composite sway
  - Romberg (feet-together EC vs EO)
  - Single-leg  L vs R                       -> side-to-side asymmetry + hold time
  - Tandem / narrow base                     -> mediolateral challenge
  - Limits of Stability (a 'los'/'lean' run) -> directional COP reach + LOS area
  - Per-position LOAD distribution (heel/forefoot, medial/lateral) from the FSRs

Label each recording via the pod button (long-press -> the mode/activity column).
Common aliases are recognised, e.g. 'eyes_open'|'firm_eo', 'single_leg_l'|'sl_l',
'los'|'lean'.

    python balance_positions.py "sample/sample_balance_positions.csv" \
        --calibration sample/calibration.json --out sample/results

Outputs: results/report_balance_positions.md + balance_positions.json
NOT a medical device — a screening / training aid; pair with a clinician.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from balance import (load, group_col, values, cop_mm, ellipse_area, sway_metrics,
                     FSR, FOOT_W_MM, FOOT_L_MM)
try:
    import calib
except Exception:
    calib = None
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# zone indices (channel order: heel_med,heel_lat,midfoot,met1,met3,met5,hallux,toes)
MEDIAL, LATERAL, HEEL, FORE = [0, 3, 6], [1, 5], [0, 1], [3, 4, 5, 6, 7]

ALIASES = {
    "firm_eo": ["firm_eo", "eyes_open", "eo", "romberg_eo", "feet_together_eo", "ft_eo", "solid_eo"],
    "firm_ec": ["firm_ec", "eyes_closed", "ec", "romberg_ec", "feet_together_ec", "ft_ec", "solid_ec"],
    "foam_eo": ["foam_eo", "foam_open", "foam_eyes_open"],
    "foam_ec": ["foam_ec", "foam_closed", "foam_eyes_closed"],
    "single_leg_l": ["single_leg_l", "sl_l", "left_leg", "single_left", "one_leg_l", "sls_l"],
    "single_leg_r": ["single_leg_r", "sl_r", "right_leg", "single_right", "one_leg_r", "sls_r"],
    "tandem": ["tandem", "tandem_eo"],
    "tandem_ec": ["tandem_ec", "sharpened_romberg", "sharpened", "tandem_closed"],
    "semi_tandem": ["semi_tandem", "semitandem"],
    "los": ["los", "lean", "limits_of_stability", "limits"],
}


def canon(label):
    s = str(label).strip().lower().replace("-", "_").replace(" ", "_")
    for key, al in ALIASES.items():
        if s in al:
            return key
    for key, al in ALIASES.items():
        if any(a in s for a in al):
            return key
    return s


def load_dist(f):
    """Mean load share per region (%) over the recording."""
    z = f.mean(0)
    tot = z.sum() or 1e-9
    return dict(heel=round(100 * z[HEEL].sum() / tot, 0), fore=round(100 * z[FORE].sum() / tot, 0),
                medial=round(100 * z[MEDIAL].sum() / tot, 0), lateral=round(100 * z[LATERAL].sum() / tot, 0))


def hull_area(pts):
    """Convex-hull area (mm^2) via monotone chain + shoelace."""
    P = sorted(set(map(tuple, np.round(pts, 2))))
    if len(P) < 3:
        return 0.0
    def cx(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in P:
        while len(lo) >= 2 and cx(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(P):
        while len(up) >= 2 and cx(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    a = sum(h[i][0]*h[(i+1) % len(h)][1] - h[(i+1) % len(h)][0]*h[i][1] for i in range(len(h)))
    return round(abs(a) / 2, 0)


def los_metrics(cop):
    """Directional COP reach (mm) from the mean + LOS convex-hull area."""
    c = cop - cop.mean(0)
    ml, ap = c[:, 0], c[:, 1]
    return dict(forward=round(float(ap.max()), 1), backward=round(float(-ap.min()), 1),
                right=round(float(ml.max()), 1), left=round(float(-ml.min()), 1),
                los_area_mm2=hull_area(cop), reach_mm=round(float(np.hypot(ml, ap).max()), 1))


# ---- protocol analyses -----------------------------------------------------
def mctsib(A):
    have = [k for k in ("firm_eo", "firm_ec", "foam_eo", "foam_ec") if k in A]
    if "firm_eo" not in A or len(have) < 3:
        return None
    base = max(A["firm_eo"], 1e-6)
    out = {"conditions": {k: A[k] for k in have},
           "composite_mm2": round(float(np.mean([A[k] for k in have])), 0)}
    if "firm_ec" in A: out["ratio_vision_removed"] = round(A["firm_ec"] / base, 2)     # firm EC / firm EO
    if "foam_eo" in A: out["ratio_surface_removed"] = round(A["foam_eo"] / base, 2)    # foam EO / firm EO
    if "foam_ec" in A: out["ratio_vestibular"] = round(A["foam_ec"] / base, 2)         # foam EC / firm EO
    return out


def mctsib_findings(m):
    o = []
    r_vis = m.get("ratio_vision_removed"); r_surf = m.get("ratio_surface_removed"); r_vest = m.get("ratio_vestibular")
    o.append(f"Composite sway across conditions {m['composite_mm2']:.0f} mm^2.")
    if r_vis:
        o.append(f"Eyes-closed on firm ground swells sway x{r_vis} — "
                 + ("**heavy reliance on vision**." if r_vis > 2 else "vision is used but not depended on."))
    if r_surf:
        o.append(f"Foam (eyes open) x{r_surf} — "
                 + ("**heavy reliance on foot/ankle somatosensation**." if r_surf > 2.5 else "somatosensory input intact."))
    if r_vest is not None:
        o.append(f"Foam + eyes-closed x{r_vest} (vestibular-dependent condition) — "
                 + ("**this is the failure mode — likely a vestibular contribution / real fall risk.**"
                    if r_vest > 3.5 else "handled reasonably."))
    return o


def single_leg(A, D):
    if "single_leg_l" not in A or "single_leg_r" not in A:
        return None
    al, ar = A["single_leg_l"], A["single_leg_r"]
    worse = "left" if al > ar else "right"
    asym = round(100 * abs(al - ar) / max(al, ar), 0)
    return dict(left_mm2=al, right_mm2=ar, worse=worse, asymmetry_pct=asym,
                left_hold_s=D.get("single_leg_l"), right_hold_s=D.get("single_leg_r"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--out", default="results")
    ap.add_argument("--calibration")
    args = ap.parse_args()

    paths = []
    for g in args.logs:
        paths += glob.glob(g)
    os.makedirs(args.out, exist_ok=True)
    cal = calib.load(args.calibration) if (args.calibration and calib) else None

    df = load(paths); gc = group_col(df)
    per, A, D, los_raw = {}, {}, {}, None
    for name, sub in df.groupby(gc):
        sub = sub.sort_values("t_ms")
        f = values(sub, cal)
        imu = sub[["ax", "ay", "az"]].to_numpy(float) if {"ax", "ay", "az"}.issubset(sub.columns) else None
        m = sway_metrics(sub["t_ms"], f, imu)
        key = canon(name)
        rec = {"position": str(name), "canonical": key, **m, "load": load_dist(f)}
        if key == "los":
            rec["los"] = los_metrics(cop_mm(f))
            los_raw = rec["los"]
        per[str(name)] = rec
        A[key] = m["area_mm2"]; D[key] = m["dur_s"]

    lines = ["# Balance across stance positions — findings",
             "_COP sway + load per position; standard balance protocols. Screening aid, not a diagnosis._", ""]
    lines.append("## Per position\n")
    lines.append("| position | sway area mm² | velocity mm/s | ML/AP | heel/fore load | med/lat load |")
    lines.append("|---|---|---|---|---|---|")
    for name, r in per.items():
        ld = r["load"]
        mlap = "ML" if r["ml_rms"] > r["ap_rms"] else "AP"
        lines.append(f"| {name} | {r['area_mm2']:.0f} | {r['vel_mms']:.0f} | {mlap}-dom "
                     f"({r['ml_rms']:.1f}/{r['ap_rms']:.1f}) | {ld['heel']:.0f}/{ld['fore']:.0f}% "
                     f"| {ld['medial']:.0f}/{ld['lateral']:.0f}% |")

    m = mctsib(A)
    if m:
        lines += ["\n## mCTSIB — sensory reliance\n"] + [f"- {x}" for x in mctsib_findings(m)]
    if "firm_ec" in A and "firm_eo" in A:
        r = A["firm_ec"] / max(A["firm_eo"], 1e-6)
        lines += ["\n## Romberg\n",
                  f"- Quotient (EC/EO, feet together) = {r:.1f}."
                  + (" **>2 -> vision-reliant.**" if r > 2 else "")]
    sl = single_leg(A, D)
    if sl:
        lines += ["\n## Single-leg (L vs R)\n",
                  f"- Left {sl['left_mm2']:.0f} mm^2 (held {sl['left_hold_s']:.0f}s) vs "
                  f"right {sl['right_mm2']:.0f} mm^2 (held {sl['right_hold_s']:.0f}s).",
                  f"- **{sl['asymmetry_pct']:.0f}% asymmetry — the {sl['worse']} side is less stable**; "
                  f"train the weaker side."]
    if "tandem" in A and "firm_eo" in A:
        lines += ["\n## Tandem (narrow base)\n",
                  f"- Tandem sway {A['tandem']:.0f} mm^2 vs feet-together {A['firm_eo']:.0f} mm^2 — "
                  f"narrow-base control; expect mediolateral challenge."]
    if los_raw:
        l = los_raw
        lines += ["\n## Limits of Stability (intentional lean)\n",
                  f"- Directional COP reach (mm): forward {l['forward']}, back {l['backward']}, "
                  f"left {l['left']}, right {l['right']} (max {l['reach_mm']}).",
                  f"- LOS area {l['los_area_mm2']:.0f} mm^2 (the workable base of support). "
                  f"Compare *within* an axis — forward vs back, left vs right; the short side is a "
                  f"direction to train. A/P naturally exceeds M/L (the foot is longer than wide)."]

    with open(os.path.join(args.out, "report_balance_positions.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    with open(os.path.join(args.out, "balance_positions.json"), "w") as fh:
        json.dump({"per_position": per, "mctsib": m, "single_leg": sl}, fh, indent=2)
    print("\n".join(lines))
    print(f"\n-> {args.out}/report_balance_positions.md + balance_positions.json")


if __name__ == "__main__":
    main()
