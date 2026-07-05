#!/usr/bin/env python3
"""
interpret.py — plantar-pressure logs -> METRICS -> plain-language IMPLICATIONS
               -> concrete insole-design directives.

Reads the same CSV logs as analyze_pressure.py (session OR all-day; auto-detects
the 'mode' [shoe/barefoot] or 'activity' grouping column). For each condition it
computes a rich metric set, then a transparent rules engine translates numbers
into: (1) findings — what the data says, (2) design — what to print into the
insole, (3) a barefoot-vs-shoe delta — what your footwear is doing.

Outputs:  results/report.md  (human)  +  results/insole_spec.json  (machine)

NOT a medical device — a design/measurement aid. Pair with a podiatrist for pain.

Usage:
    python interpret.py "day_*.csv" --out results/
    python interpret.py logs/*.csv --calibrated
"""
import argparse, glob, json, os
import numpy as np
import pandas as pd

FSR   = [f"fsr{i}" for i in range(8)]
ZONES = ["heel_med", "heel_lat", "midfoot", "met1", "met3", "met5", "hallux", "toes"]
XY    = np.array([[.35, .08], [.65, .08], [.50, .45], [.30, .72],
                  [.50, .74], [.70, .72], [.28, .92], [.55, .95]])
MEDIAL, LATERAL = [0, 3, 6], [1, 5]      # by zone index
HEEL, FORE      = [0, 1], [3, 4, 5, 6, 7]
CALIB = {i: (1.0, 0.0) for i in range(8)}  # force_N = m*adc + b; fill after calibration


def load(paths):
    frames = []
    for p in paths:
        d = pd.read_csv(p, comment="#")
        d["__src"] = os.path.basename(p)
        frames.append(d)
    if not frames:
        raise SystemExit("no logs matched")
    return pd.concat(frames, ignore_index=True)


def group_col(df):
    for c in ("mode", "activity"):
        if c in df.columns:
            return c
    df["__all"] = "all"
    return "__all"


def to_force(df, calibrated):
    a = df[FSR].to_numpy(float)
    if calibrated:
        for i in range(8):
            a[:, i] = CALIB[i][0] * a[:, i] + CALIB[i][1]
        a = np.clip(a, 0, None)
    return a


def metrics(t_ms, f):
    t = t_ms.to_numpy(float) / 1000.0
    dt = np.gradient(t) if len(t) > 1 else np.array([0.02])
    peak = f.max(0)
    impulse = (f * dt[:, None]).sum(0)            # ∫F dt per zone — injury-relevant
    total = impulse.sum() or 1e-9
    load_pct = 100 * impulse / total
    tot = f.sum(1, keepdims=True); tot[tot == 0] = 1e-9
    cop = (f @ XY) / tot                           # center of pressure (N,2)
    ml, ap = cop[:, 0], cop[:, 1]
    heel = f[:, HEEL].sum(1)
    loading_rate = float(np.max(np.abs(np.gradient(heel, t)))) if len(t) > 1 else 0.0
    # cadence from heel contacts
    thr = 0.2 * (heel.max() or 1)
    contact = heel > thr
    strikes = np.where((~contact[:-1]) & (contact[1:]))[0] + 1
    cadence = None
    if len(strikes) >= 2:
        stride = np.diff(t[strikes]); stride = stride[(stride > 0.2) & (stride < 2.5)]
        if len(stride):
            cadence = round(60 / stride.mean(), 1)
    return dict(
        peak=peak, impulse=impulse, load_pct=load_pct, hot=int(np.argmax(impulse)),
        medial=float(load_pct[MEDIAL].sum()), lateral=float(load_pct[LATERAL].sum()),
        heel=float(load_pct[HEEL].sum()), fore=float(load_pct[FORE].sum()),
        ml_exc=float(ml.max() - ml.min()), ap_range=float(ap.max() - ap.min()),
        loading_rate=loading_rate, cadence=cadence,
    )


def interpret(m):
    """rules engine -> (findings[], design directives{})"""
    z, out, design = ZONES, [], {}
    hot = m["hot"]
    out.append(f"Highest sustained load (impulse) is at **{z[hot]}** "
               f"({m['load_pct'][hot]:.0f}% of total) — this is your hot spot.")
    design["relief_window_zone"] = z[hot]

    order = np.argsort(m["impulse"])[::-1]
    if m["impulse"][order[0]] > 1.6 * m["impulse"][order[1]]:
        out.append(f"Load is **concentrated** at {z[order[0]]} (>1.6× the next zone) — "
                   f"a localized overload; offload it aggressively.")
        design["relief_window"] = "aggressive (softer + deeper recess)"
    else:
        design["relief_window"] = "standard"

    if m["medial"] > m["lateral"] * 1.5:
        out.append(f"Medial load ({m['medial']:.0f}%) ≫ lateral ({m['lateral']:.0f}%) — "
                   f"a **pronation** tendency; consider mild medial posting / arch support.")
        design["posting"] = "medial"
    elif m["lateral"] > m["medial"] * 1.5:
        out.append(f"Lateral load ({m['lateral']:.0f}%) ≫ medial ({m['medial']:.0f}%) — "
                   f"a **supination** tendency; add lateral cushioning.")
        design["posting"] = "lateral"
    else:
        design["posting"] = "neutral"

    if m["heel"] > 55:
        out.append(f"Heel-dominant ({m['heel']:.0f}% at the heel) — prioritize heel cushioning + the relief window.")
        design["cushion_priority"] = "heel"
    elif m["fore"] > 55:
        out.append(f"Forefoot-dominant ({m['fore']:.0f}% forefoot) — add a metatarsal cushion / offload the met heads.")
        design["cushion_priority"] = "forefoot"
    else:
        design["cushion_priority"] = "balanced"

    if m["loading_rate"] > 0:
        hard = m["loading_rate"] > 800
        out.append(f"Heel-strike loading rate ≈ {m['loading_rate']:.0f} rel/s — "
                   f"{'a hard heel strike; a soft heel cushion helps' if hard else 'moderate'}.")
        if hard:
            design["heel_cushion"] = "soft"

    if m["ml_exc"] > 0.35:
        out.append(f"Wide side-to-side center-of-pressure swing ({m['ml_exc']:.2f}) — "
                   f"some mediolateral instability; a deeper heel cup helps.")
        design["heel_cup"] = "deep"

    if m["cadence"]:
        out.append(f"Cadence ≈ {m['cadence']} steps/min.")
    return out, design


def compare(by):
    if "barefoot" in by and "shoe" in by:
        b, s = by["barefoot"], by["shoe"]
        hz = b["hot"]
        d = s["load_pct"][hz] - b["load_pct"][hz]
        if d > 3:
            return [f"Your **shoe raises** load at {ZONES[hz]} by {d:.0f} pts vs barefoot — "
                    f"the shoe is *adding* to your hot spot. The printed insole should undo that "
                    f"(relief window + softer heel)."]
        if d < -3:
            return [f"Your **shoe lowers** load at {ZONES[hz]} by {abs(d):.0f} pts vs barefoot — "
                    f"the shoe already helps here; match or extend that with the insole."]
        return [f"Shoe vs barefoot load at {ZONES[hz]} is similar — footwear isn't the main driver at your hot spot."]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--out", default="results")
    ap.add_argument("--calibrated", action="store_true")
    args = ap.parse_args()

    paths = []
    for g in args.logs:
        paths += glob.glob(g)
    os.makedirs(args.out, exist_ok=True)

    df = load(paths)
    gc = group_col(df)
    by = {}
    for name, sub in df.groupby(gc):
        sub = sub.sort_values("t_ms")
        by[str(name)] = metrics(sub["t_ms"], to_force(sub, args.calibrated))

    lines = ["# Pressure analysis — findings & insole directives\n",
             "_Relative FSR pressure. A design/measurement aid, not medical advice._\n"]
    spec = {}
    for name, m in by.items():
        findings, design = interpret(m)
        lines.append(f"\n## {name}\n")
        lines += [f"- {x}" for x in findings]
        lines.append(f"\n**Design directives:** `{json.dumps(design)}`")
        spec[name] = design

    delta = compare(by)
    if delta:
        lines.append("\n## Barefoot vs shoe\n")
        lines += [f"- {x}" for x in delta]

    chosen = spec.get("shoe") or next(iter(spec.values()))
    lines.append("\n## → Print these into the insole\n")
    lines.append(f"- **Relief window** at `{chosen['relief_window_zone']}` ({chosen.get('relief_window', 'standard')})")
    extras = f" · **{chosen['heel_cup']} heel cup**" if chosen.get("heel_cup") else ""
    lines.append(f"- **Posting:** {chosen['posting']} · **Cushion priority:** {chosen['cushion_priority']}{extras}")

    with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    with open(os.path.join(args.out, "insole_spec.json"), "w", encoding="utf-8") as fh:
        json.dump({"per_condition": spec, "chosen": chosen}, fh, indent=2)

    print("\n".join(lines))
    print(f"\n-> {args.out}/report.md + insole_spec.json")


if __name__ == "__main__":
    main()
