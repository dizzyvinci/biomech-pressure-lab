#!/usr/bin/env python3
"""
nerve_fascia.py — from the all-day foot-pressure dose to the NERVES & FASCIA it loads.

Peak pressure is one step. PTI is one step's dose. **Cumulative Plantar Tissue Stress**
(CPTS = PTI x loading-cycles-per-day, MPa.s/day) is a whole *day's* dose — and the day's
dose is what overloads tissue (it predicts diabetic-ulcer healing better than pressure or
activity alone; it tracks joint pain too). This module maps our per-zone pressure / PTI /
CPTS + the spatial pressure GRADIENT onto the anatomical structures they load:

  · plantar fascia (tension, windlass)      · Baxter's nerve (medial-heel entrapment)
  · Morton's / interdigital nerve (forefoot) · posterior tibial nerve (tarsal tunnel)

Forefoot cycles/day = gait steps + the at-rest leg-bounce/toe-tap dose (bounce.py) — so a
habit no step-counter sees can dominate forefoot nerve load. Everything is read from the
cited reference DB (refs/plantar_norms.json, `structures`).

    python nerve_fascia.py --demo
    python nerve_fascia.py --day my_day.json --out results/

--day JSON: {"pressure_kPa": {zone: kPa}, "pti_kPa_s": {zone: kPa*s per cycle},
             "gait_steps_per_day": 7000, "bounce_cycles_per_day": 0,
             "heel_strike_fraction": 1.0}

SCREENING / EDUCATION ONLY — these structures overlap and mimic each other; NOT a diagnosis.
"""
import argparse, json, os, sys

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refs", "plantar_norms.json")
ZONES = ["heel_med", "heel_lat", "midfoot", "met1", "met2", "met3", "met4", "met5", "hallux", "toes"]
FOREFOOT = {"met1", "met2", "met3", "met4", "met5", "hallux", "toes"}   # see the bounce dose
HEEL_MID = {"heel_med", "heel_lat", "midfoot"}                          # gait heel-strike cycles
ADJ = {
    "heel_med": ["heel_lat", "midfoot"], "heel_lat": ["heel_med", "midfoot"],
    "midfoot": ["heel_med", "heel_lat", "met1", "met2", "met3", "met4", "met5"],
    "met1": ["met2", "midfoot", "hallux"], "met2": ["met1", "met3", "midfoot"],
    "met3": ["met2", "met4", "midfoot"], "met4": ["met3", "met5", "midfoot"],
    "met5": ["met4", "midfoot"], "hallux": ["met1", "toes"], "toes": ["hallux", "met2"],
}
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def demo_day():
    """A toe-walker with forefoot overload, a leg-bounce habit, and medial heel pain —
    central met heads highest (Morton territory), long forefoot contact (high PTI), reduced
    heel strike, plus the ~40k/day forefoot bounce dose from bounce.py."""
    return {
        "pressure_kPa": {"heel_med": 210, "heel_lat": 120, "midfoot": 90, "met1": 260, "met2": 300,
                         "met3": 290, "met4": 210, "met5": 150, "hallux": 180, "toes": 120},
        "pti_kPa_s":   {"heel_med": 22, "heel_lat": 10, "midfoot": 9, "met1": 40, "met2": 52,
                        "met3": 50, "met4": 30, "met5": 16, "hallux": 24, "toes": 12},
        "gait_steps_per_day": 7000, "bounce_cycles_per_day": 40320, "heel_strike_fraction": 0.35,
        "_note": "synthetic — toe-walker + equinus + leg-bounce dose; see bounce.py / conditions.py",
    }


def cycles_for(zone, day):
    gait = day.get("gait_steps_per_day", 7000)
    if zone in HEEL_MID:
        return gait * day.get("heel_strike_fraction", 1.0)
    return gait + day.get("bounce_cycles_per_day", 0)      # forefoot also sees the at-rest dose


def cpts(day):
    """CPTS_zone (MPa.s/day).
    Rich schema (day_summary.py, real logs): gait PTI/cycle × gait cycles + bounce PTI/cycle ×
      bounce cycles (forefoot). The MEASURED per-zone PTI already encodes any under-loading, so
      no heel-strike fudge factor is applied.
    Simple schema (demo / hand-written): single PTI/cycle × cycles_for()."""
    out = {}
    if "gait" in day or "bounce" in day:
        gp = day.get("gait", {}).get("pti_kPa_s", {}); gc = day.get("gait", {}).get("cycles_per_day", 0)
        bp = day.get("bounce", {}).get("pti_kPa_s", {}); bc = day.get("bounce", {}).get("cycles_per_day", 0)
        for z in ZONES:
            v = gp.get(z, 0) / 1000.0 * gc
            if z in FOREFOOT:
                v += bp.get(z, 0) / 1000.0 * bc
            out[z] = round(v, 1)
        return out
    for z in ZONES:
        pti_MPa_s = day.get("pti_kPa_s", {}).get(z, 0) / 1000.0
        out[z] = round(pti_MPa_s * cycles_for(z, day), 1)
    return out


def gradients(press):
    """Steepest pressure step (kPa) from each zone to a neighbor — proxy for subsurface shear."""
    return {z: max((abs(press.get(z, 0) - press.get(n, 0)) for n in ADJ[z]), default=0) for z in ZONES}


def band(frac):
    return ("🔴 HIGH", "high") if frac >= 0.66 else ("🟠 elevated", "elevated") if frac >= 0.33 else ("🟢 watch", "watch")


def analyze(day, db):
    """Full read: per-zone CPTS + gradient + ranked per-structure load + forefoot/heel totals.
    Shared by the CLI and by trend.py (so both score identically)."""
    press = day.get("pressure_kPa", {})
    C = cpts(day)
    G = gradients(press)
    scored = []
    for name, s in db.get("structures", {}).items():
        if name == "about":
            continue
        zs = s["loads_from"]
        load = round(sum(C.get(z, 0) for z in zs), 1)
        peak_z = max(zs, key=lambda z: press.get(z, 0))
        grad = round(max((G.get(z, 0) for z in zs), default=0), 0)
        scored.append({"name": name, "s": s, "load": load, "peak_z": peak_z,
                       "peak_kPa": press.get(peak_z, 0), "grad": grad, "zones": zs})
    scored.sort(key=lambda x: x["load"], reverse=True)
    return {"cpts": C, "grad": G, "structures": scored,
            "forefoot": round(sum(C[z] for z in FOREFOOT), 0),
            "heel": round(sum(C[z] for z in HEEL_MID), 0)}


def main():
    ap = argparse.ArgumentParser(description="Map the all-day foot-pressure dose to nerves & fascia.")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--day", help="prebuilt day-summary JSON (from day_summary.py, or hand-written)")
    ap.add_argument("--logs", nargs="+", help="raw session CSV glob(s) — build the day inline via day_summary")
    ap.add_argument("--calibration", help="calibration.json for real kPa (with --logs)")
    ap.add_argument("--walk-hours", type=float, default=10.0)
    ap.add_argument("--bounce-hours", type=float, default=4.0)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    db = json.load(open(REFS, encoding="utf-8"))
    structs = db["structures"]

    if a.demo:
        day = demo_day()
    elif a.day:
        day = json.load(open(a.day, encoding="utf-8"))
    elif a.logs:
        import glob as _glob, day_summary
        paths = [p for g in a.logs for p in _glob.glob(g)]
        if not paths:
            raise SystemExit("no logs matched")
        cal = None
        if a.calibration:
            import calib
            cal = calib.load(a.calibration)
        day = day_summary.build_day(paths, cal, a.walk_hours, a.bounce_hours)
    else:
        raise SystemExit("pass --demo, --day day.json, or --logs '*.csv' [--calibration cal.json]")

    press = day.get("pressure_kPa", {})
    res = analyze(day, db)
    C, G, scored = res["cpts"], res["grad"], res["structures"]
    anchor = db["metrics"]["cumulative_plantar_tissue_stress_MPa_s_day"]["healing_anchor_MPa_s_day"]
    mx = max((x["load"] for x in scored), default=1) or 1

    L = ["# Nerve & fascia load — from the all-day pressure dose",
         "_Which nerves/fascia your day's loading overloads, via **CPTS = PTI × cycles/day** "
         "(gait steps + the at-rest bounce dose) and the pressure gradient. "
         "Associations published (refs/plantar_norms.json `structures`); zone weights estimated. "
         "**SCREENING/EDUCATION, NOT A DIAGNOSIS** — these structures overlap & mimic each other._", ""]

    tot_fore = round(sum(C[z] for z in FOREFOOT), 0)
    tot_heel = round(sum(C[z] for z in HEEL_MID), 0)
    L.append(f"**Daily dose (CPTS, MPa·s/day):** forefoot **{tot_fore:.0f}** · heel/mid **{tot_heel:.0f}** "
             f"  _(diabetic-ulcer healing anchor {anchor[0]}–{anchor[1]}; an order-of-magnitude reference for "
             f"AT-RISK tissue, not a healthy-foot limit — use it to compare zones & track your own trend)._")
    gait_cyc = day.get("gait", {}).get("cycles_per_day", day.get("gait_steps_per_day", 0))
    bounce_cyc = day.get("bounce", {}).get("cycles_per_day", day.get("bounce_cycles_per_day", 0))
    if bounce_cyc:
        share = round(100 * bounce_cyc / max(gait_cyc + bounce_cyc, 1))
        L.append(f"> ⚡ **{share}% of the forefoot's daily loading cycles come from the at-rest bounce/tap dose** "
                 f"({bounce_cyc:,}/day vs {gait_cyc:,} gait) — invisible to any step-counter, landing on the "
                 f"same met heads gait already loads.")
    L.append("")

    L.append("| structure | kind | load (CPTS) | | driving zones | peak | Δgrad |")
    L.append("|---|---|---|---|---|---|---|")
    for x in scored:
        frac = x["load"] / mx
        tag = band(frac)[0]
        bar = "█" * max(1, round(12 * frac))
        L.append(f"| **{x['name']}** | {x['s']['kind']} | {x['load']:.0f} | {bar} {tag} | "
                 f"{', '.join(x['zones'])} | {x['peak_z']} {x['peak_kPa']:.0f} kPa | {x['grad']:.0f} kPa |")

    L.append("\n## What's driving each (mechanism · clue · manage)")
    for x in scored:
        s = x["s"]
        cites = ", ".join(f"[{k}]({db['sources'][k]['url']})" for k in s.get("sources", []) if k in db["sources"])
        L.append(f"\n### {x['name']}  ·  {s['kind']}  ·  {band(x['load']/mx)[0]}")
        L.append(f"- _aka_ {s['aka']}")
        L.append(f"- **mode:** {s['mode']}")
        L.append(f"- **driver:** {s['driver']}")
        L.append(f"- **tell it apart:** {s['differentiator']}")
        L.append(f"- **manage:** {s['manage']}")
        L.append(f"- load {x['load']:.0f} MPa·s/day from {', '.join(x['zones'])}; peak {x['peak_z']} "
                 f"{x['peak_kPa']:.0f} kPa; steepest gradient {x['grad']:.0f} kPa. _Sources: {cites}._")

    # cross-cutting reads
    L.append("\n## Reads")
    fore_hi = [x for x in scored if x["name"] == "morton_neuroma"]
    if fore_hi and fore_hi[0]["load"] >= tot_heel:
        L.append("- **Forefoot dominates the day's dose** → interdigital-nerve (Morton) + met-head load is the "
                 "biggest cumulative exposure. The bounce dose is a big, hidden part of it — dose it, don't "
                 "just suppress it: metatarsal pad, wider toe box, ball-of-foot rest windows.")
    heel = next((x for x in scored if x["name"] == "baxter_nerve"), None)
    pf = next((x for x in scored if x["name"] == "plantar_fascia"), None)
    if heel and pf:
        L.append("- **Medial heel pain? Time-of-day tells fascia from nerve:** plantar fasciitis = worst first "
                 "steps in the **morning**; Baxter's nerve = worse **as the day's weight-bearing accumulates**. "
                 "Same spot, different fix — log when it hurts.")
    if max(G.get(z, 0) for z in FOREFOOT) >= 120:
        gz = max(FOREFOOT, key=lambda z: G.get(z, 0))
        L.append(f"- **Steep forefoot pressure gradient at {gz} ({G[gz]:.0f} kPa jump)** → concentrated "
                 "subsurface shear near the digital nerves (gradient discriminates breakdown risk better than "
                 "peak alone). Smooth it with a met pad / cushioning that spreads the load.")

    L.append("\n---\n_Not a medical device; not medical advice. A screening/education aid to discuss with a "
             "clinician — confirming which nerve or fascia is involved usually needs exam + ultrasound/MRI or a "
             "diagnostic block. Structures & mechanisms: refs/plantar_norms.json `structures`._")

    with open(os.path.join(a.out, "report_nerve_fascia.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(a.out, "nerve_fascia.json"), "w") as fh:
        json.dump({"cpts_MPa_s_day": C, "gradient_kPa": G,
                   "forefoot_cpts": tot_fore, "heel_cpts": tot_heel,
                   "structures": [{"name": x["name"], "load": x["load"], "peak_zone": x["peak_z"],
                                   "peak_kPa": x["peak_kPa"], "gradient_kPa": x["grad"]} for x in scored]},
                  fh, indent=2)
    print("\n".join(L))
    print(f"\n-> {a.out}/report_nerve_fascia.md + nerve_fascia.json")


if __name__ == "__main__":
    main()
