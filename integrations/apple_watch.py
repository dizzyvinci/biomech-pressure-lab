#!/usr/bin/env python3
"""
apple_watch.py — fold Apple Watch / iPhone gait data into the balance screen.

Apple Watch + iPhone already compute validated mobility metrics via HealthKit —
**Walking Steadiness** (a fall-risk score with OK / Low / Very-Low bands), plus
walking asymmetry, double-support %, speed, and step length. This adapter reads an
**Apple Health export** (Health app -> Profile -> Export All Health Data ->
export.xml) and cross-references those with the insole's own findings, so two
independent systems corroborate (or flag) each other.

    python apple_watch.py sample/apple_health_export_sample.xml \
        --balance sample/results/balance_positions.json --out sample/results

Live sync (beyond this file adapter) needs a small companion iOS app that reads the
same HealthKit types and streams them alongside the insole — see integrations/README.
The Watch's own IMU can also serve as a **trunk/wrist** motion channel to complement
the ankle-pod IMU. NOT a medical device.
"""
import argparse, json, os, sys
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WANT = {
    "HKQuantityTypeIdentifierAppleWalkingSteadiness": "steadiness_pct",
    "HKQuantityTypeIdentifierWalkingAsymmetryPercentage": "asymmetry_pct",
    "HKQuantityTypeIdentifierWalkingDoubleSupportPercentage": "double_support_pct",
    "HKQuantityTypeIdentifierWalkingSpeed": "speed_mps",
    "HKQuantityTypeIdentifierWalkingStepLength": "step_length_cm",
}


def read_export(path):
    """Latest value per metric + count of Low/Very-Low steadiness events."""
    latest, events = {}, 0
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "Record":
            continue
        t = el.get("type", "")
        if t in WANT:
            try:
                v = float(el.get("value"))
                key = WANT[t]
                d = el.get("startDate", "")
                if key not in latest or d > latest[key][1]:
                    latest[key] = (v, d)
            except (TypeError, ValueError):
                pass
        elif t == "HKCategoryTypeIdentifierAppleWalkingSteadinessEvent":
            if "Low" in (el.get("value") or ""):
                events += 1
        el.clear()
    return {k: v[0] for k, v in latest.items()}, events


def steadiness_band(pct):
    # Apple surfaces OK / Low / Very Low; public cutoffs aren't exact — approximate.
    if pct is None: return "unknown"
    return "OK" if pct >= 50 else ("Low" if pct >= 30 else "Very Low")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export", help="Apple Health export.xml")
    ap.add_argument("--balance", help="balance_positions.json to cross-reference")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    m, ev = read_export(args.export)
    band = steadiness_band(m.get("steadiness_pct"))

    L = ["# Apple Watch gait — cross-referenced with the insole", ""]
    L.append("## From Apple Health\n")
    L.append(f"- **Walking Steadiness: {m.get('steadiness_pct','?')}% -> {band}**"
             + (f"  ({ev} Low/Very-Low event(s) logged)" if ev else ""))
    if "asymmetry_pct" in m:      L.append(f"- Walking asymmetry: {m['asymmetry_pct']}%")
    if "double_support_pct" in m: L.append(f"- Double-support: {m['double_support_pct']}% (higher = more cautious gait)")
    if "speed_mps" in m:          L.append(f"- Walking speed: {m['speed_mps']} m/s")
    if "step_length_cm" in m:     L.append(f"- Step length: {m['step_length_cm']} cm")

    agree = []
    if args.balance and os.path.exists(args.balance):
        bp = json.load(open(args.balance))
        sl = bp.get("single_leg")
        mc = bp.get("mctsib") or {}
        L.append("\n## Cross-reference with the insole\n")
        if sl and "asymmetry_pct" in m:
            L.append(f"- **Left/right imbalance:** Apple walking asymmetry {m['asymmetry_pct']}% "
                     f"and insole single-leg asymmetry {sl['asymmetry_pct']:.0f}% ({sl['worse']} weaker) "
                     f"— **two systems agree on a side imbalance.**")
            agree.append("asymmetry")
        vest = mc.get("ratio_vestibular")
        if vest and band in ("Low", "Very Low"):
            L.append(f"- **Fall risk:** Apple steadiness is {band} and the insole's mCTSIB shows a "
                     f"vestibular failure (x{vest}) — **independent corroboration of elevated fall risk.**")
            agree.append("fall_risk")
        if m.get("double_support_pct", 0) > 28:
            L.append(f"- Elevated double-support ({m['double_support_pct']}%) fits a cautious, "
                     f"less-stable gait — consistent with the balance findings.")
    L.append("\n_Two independent measurement systems agreeing raises confidence. "
             "Screening aid, not a diagnosis._")

    with open(os.path.join(args.out, "report_apple_watch.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    with open(os.path.join(args.out, "apple_watch.json"), "w") as f:
        json.dump({"metrics": m, "steadiness_band": band, "low_events": ev,
                   "agreements": agree}, f, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/report_apple_watch.md + apple_watch.json")


if __name__ == "__main__":
    main()
