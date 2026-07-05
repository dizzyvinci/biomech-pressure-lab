#!/usr/bin/env python3
"""
zone_load.py — per-zone load vs the norm for YOUR sport/movement (down to the 2nd met).

Rubrics get specific: for a given movement, which foot regions are OVER-used or
UNDER-used compared to what the field's research says is normal? Overload maps to
real injuries (the 2nd metatarsal is the #1 stress-fracture site). This reads the
cited reference DB (refs/plantar_norms.json) and compares an athlete's actual
per-zone distribution against it.

Our 8-FSR rig senses 8 zones; **met2 & met4 are interpolated** from neighbors
(met2 ~ mean(met1,met3)) so we can still flag the injury-critical 2nd metatarsal.

    python zone_load.py --demo --profile ballet_releve
    python zone_load.py session.csv --profile running_forefoot \
        --calibration cal.json --bodyweight-kg 62 --out results/

Outputs results/report_zone_load.md + zone_load.json.  NOT a medical device.
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

SENSOR_ZONES = ["heel_med", "heel_lat", "midfoot", "met1", "met3", "met5", "hallux", "toes"]
ZONES10 = ["heel_med", "heel_lat", "midfoot", "met1", "met2", "met3", "met4", "met5", "hallux", "toes"]
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refs", "plantar_norms.json")


def to_10zone(mean8):
    d = dict(zip(SENSOR_ZONES, mean8))
    d["met2"] = (d["met1"] + d["met3"]) / 2      # interpolated
    d["met4"] = (d["met3"] + d["met5"]) / 2
    tot = sum(d[z] for z in ZONES10) or 1e-9
    return {z: round(100 * d[z] / tot, 1) for z in ZONES10}


def zone_mm(db, z, foot_len):
    fr = db.get("zone_anatomy", {}).get(z, {}).get("pos_frac")
    if not fr:
        return None
    ref = db["foot_reference"]
    w = foot_len * (ref["width_mm"] / ref["length_mm"])
    return (round(fr[0] * w), round(fr[1] * foot_len))


def compare(ath, norm):
    over, under, rows = [], [], []
    for z in ZONES10:
        a = ath[z]; n = norm.get(z, 0)
        ratio = round(a / n, 2) if n > 0 else None
        rows.append((z, a, n, ratio))
        if ratio is not None and ratio >= 1.3:
            over.append((z, ratio))
        elif ratio is not None and ratio <= 0.7:
            under.append((z, ratio))
    return rows, over, under


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--calibration")
    ap.add_argument("--bodyweight-kg", type=float)
    ap.add_argument("--foot-length-mm", type=float, default=255.0,
                    help="your foot length (mm) -> report zone positions in mm on YOUR foot")
    ap.add_argument("--condition",
                    help="your adaptive/altered baseline (e.g. toe_walking, plantar_fasciitis, equinus) "
                         "-> don't false-flag adaptive patterns; surface the condition's real risks")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    db = json.load(open(REFS, encoding="utf-8"))
    if args.profile not in db["profiles"]:
        raise SystemExit(f"unknown profile. choose from: {list(db['profiles'])}")
    prof = db["profiles"][args.profile]
    cond = db["profiles"].get(args.condition) if args.condition else None
    adaptive = bool(prof.get("adaptive")) or bool(cond and cond.get("adaptive"))
    cal = calib.load(args.calibration) if (args.calibration and calib) else None

    if args.demo:
        # a dancer with 1st-MTP pain: load shifted OFF the hallux ONTO the met heads
        # (the published pattern) -> should flag met2/met3 over, hallux under.
        rng = np.random.default_rng(2)
        means = np.array([3, 3, 3, 26, 28, 5, 5, 10], float)
        n = 400
        F = means[None, :] * (1 + 0.03 * rng.standard_normal((n, 8)))
        df = pd.DataFrame({"t_ms": (np.arange(n) * 20).astype(int), "activity": args.profile})
        for i in range(8):
            df[f"fsr{i}"] = np.clip(F[:, i], 0, None)
        f = df[[f"fsr{i}" for i in range(8)]].to_numpy(float)
        peak_total = None
    else:
        paths = []
        for g in args.logs:
            paths += glob.glob(g)
        df = load(paths)
        f = values(df, cal)
        peak_total = float(f.sum(1).max()) if cal is not None else None

    ath = to_10zone(f.mean(0))
    rows, over, under = compare(ath, prof["dist_pct"])

    L = [f"# Zone load vs norm — {args.profile}",
         f"_{prof['movement']}. Athlete regional load vs the field's reference (refs/plantar_norms.json). "
         f"met2/met4 interpolated. Not a medical device._", ""]
    L.append("| zone | you % | norm % | ratio | |")
    L.append("|---|---|---|---|---|")
    for z, a, n, r in rows:
        tag = "🔴 OVER" if (r and r >= 1.3) else "🔵 under" if (r and r <= 0.7) else ""
        star = " *(interp)*" if z in ("met2", "met4") else ""
        L.append(f"| {z}{star} | {a} | {n} | {r if r is not None else '—'} | {tag} |")

    if over:
        L.append("\n**Over-used** (≥1.3× the norm): " + ", ".join(f"{z} ({r}×)" for z, r in over))
        for z, r in over:
            mm = zone_mm(db, z, args.foot_length_mm)
            lm = db.get("zone_anatomy", {}).get(z, {}).get("landmark", "")
            if mm:
                L.append(f"  · **{z}** at ~(x {mm[0]}, y {mm[1]}) mm on your {args.foot_length_mm:.0f} mm foot — {lm}")
    if under:
        parts = []
        for z, r in under:
            expected = adaptive and z in ("heel_med", "heel_lat")
            parts.append(f"{z} ({r}×)" + (" _(expected — adaptive baseline, not a flag)_" if expected else ""))
        L.append("**Under-used** (≤0.7× the norm): " + ", ".join(parts))

    # condition awareness: adaptive baseline + real risks + management (from profile and/or --condition)
    for src in (prof, cond):
        if not src:
            continue
        rp = src.get("region_pct_published")
        if rp:
            L.append(f"\n_Published baseline — {src.get('movement','')}: forefoot {rp['forefoot']}% / "
                     f"midfoot {rp['midfoot']}% / hindfoot {rp['hindfoot']}% ({rp.get('vs_normal','')})._")
        if src.get("baseline_note"):
            L.append(f"\n🧭 **Adaptive baseline:** {src['baseline_note']}")
        if src.get("management_note"):
            L.append(f"🩺 **Management:** {src['management_note']}")

    if prof.get("chain_injury"):
        L.append(f"\n🔗 **Kinetic chain (it's all connected to the foot):** {prof['chain_injury']}")
        cr = prof.get("chain_rule")
        if cr and cr in db.get("chain_rules", {}):
            rule = db["chain_rules"][cr]
            L.append(f"   signature: _{rule['signal']}_ → {', '.join(rule['chain'])}")

    watch = prof.get("watch_zones", [])
    flagged = [z for z, _ in over if z in watch]
    if flagged:
        L.append(f"\n⚠️ **Injury-relevant overload at {', '.join(flagged)}** — {prof.get('injury', '')}")
    if any(z == "hallux" for z, _ in under) and any(z in ("met2", "met3") for z, _ in over):
        L.append("→ Load has shifted **off the hallux onto the central met heads** — the published "
                 "1st-MTP-pain pattern; central-met (2nd-met) overload is the 'dancer's fracture' route. "
                 "Cue big-toe engagement / check the 1st ray.")

    # landing force vs published range
    force = prof.get("peak_force_BW", {})
    if peak_total is not None and args.bodyweight_kg:
        bw = args.bodyweight_kg * 9.81
        bw_mult = round(peak_total / bw, 1)
        rng_ = force.get("range")
        verdict = ("above the typical range — high impact; check technique/fatigue"
                   if rng_ and bw_mult > rng_[1] else "within the reported range")
        L.append(f"\n**Peak landing force ≈ {bw_mult}× body weight** vs reported "
                 f"{force.get('typical','?')}× (range {force.get('range','?')}, {force.get('confidence','?')}) — {verdict}.")
    elif force:
        L.append(f"\n_Reference peak force for this movement: **{force.get('typical','?')}× BW** "
                 f"(range {force.get('range','?')}, {force.get('confidence')}). "
                 f"Add --calibration + --bodyweight-kg to compare yours._")

    # real pressure (kPa): published reference + clinical caution + your actual (if calibrated)
    pk = prof.get("peak_pressure_kPa", {})
    ct = db.get("clinical_thresholds", {})
    ref_vals = [(z, pk[z]) for z in prof.get("watch_zones", []) if isinstance(pk.get(z), (int, float))]
    if ref_vals:
        L.append("\n**Reference peak pressure (published):** "
                 + " · ".join(f"{z} ~{v} kPa" for z, v in ref_vals) + f"  ({pk.get('confidence', '')})")
    if pk and ct:
        L.append(f"_Caution: {ct['in_shoe_ulcer_kPa']} kPa in-shoe / {ct['barefoot_kPa']} kPa barefoot are "
                 f"**at-risk/neuropathic** ulcer thresholds — healthy athletic tissue tolerates far higher transiently._")
    if cal is not None:
        peaks = dict(zip(SENSOR_ZONES, f.max(0)))
        hi = max(peaks, key=peaks.get)
        L.append(f"**Your peak pressure:** {hi} **{peaks[hi]:.0f} kPa** (highest sensed zone)"
                 + (f" vs published ~{pk[hi]} kPa" if isinstance(pk.get(hi), (int, float)) else ""))
        thr = ct.get("in_shoe_ulcer_kPa")
        if thr and peaks[hi] > thr:
            L.append(f"  · above the {thr} kPa in-shoe caution (normal for healthy athletic loading; flag only for at-risk feet).")

    src = prof.get("dist_source") or prof.get("note")
    if src and src in db["sources"]:
        s = db["sources"][src]
        L.append(f"\n_Distribution basis: {prof.get('dist_confidence','?')} — {s['cite']} ({s['url']})._")

    with open(os.path.join(args.out, "report_zone_load.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(args.out, "zone_load.json"), "w") as fh:
        json.dump({"profile": args.profile, "athlete_pct": ath,
                   "over_used": over, "under_used": under}, fh, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/report_zone_load.md + zone_load.json")


if __name__ == "__main__":
    main()
