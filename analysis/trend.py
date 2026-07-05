#!/usr/bin/env python3
"""
trend.py — track the all-day dose (CPTS per nerve/fascia structure) over days/weeks.

The whole point of the dose model is watching YOUR numbers MOVE — after a met pad, ball-of-
foot rest windows, calf work. Log a day.json (from day_summary.py) each day and this charts
the per-structure CPTS trend, so an insole / behavior change shows up as a falling line.

  record  add one day.json to the history file (tagged with a date)
  chart    history -> a per-structure CPTS trend chart + a markdown summary

    python trend.py record results/day.json --date 2026-07-05 --history results/cpts_history.jsonl
    python trend.py chart  --history results/cpts_history.jsonl --out results/
    python trend.py --demo --out results/      # synth ~6 weeks with a falling forefoot dose

Reuses nerve_fascia.analyze() so a tracked day scores identically to a one-off. NOT a medical device.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nerve_fascia as nf

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refs", "plantar_norms.json")
COLORS = {"plantar_fascia": "#f59e0b", "morton_neuroma": "#2563eb",
          "tibial_nerve_tarsal_tunnel": "#16a34a", "baxter_nerve": "#e11d48"}
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def db_load():
    return json.load(open(REFS, encoding="utf-8"))


def row_from_day(day, db, date):
    res = nf.analyze(day, db)
    return {"date": date, "forefoot": res["forefoot"], "heel": res["heel"],
            "structures": {x["name"]: x["load"] for x in res["structures"]}}


def read_history(path):
    rows = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    rows.sort(key=lambda r: r["date"])
    return rows


def demo_history(db):
    """~6 weekly snapshots of a forefoot-loader who adds a met pad + rest windows at week 3 ->
    bounce cycles & forefoot PTI fall, so Morton/fascia CPTS decline while the heel holds."""
    base_press = {"heel_med": 210, "heel_lat": 120, "midfoot": 90, "met1": 260, "met2": 300,
                  "met3": 290, "met4": 210, "met5": 150, "hallux": 180, "toes": 120}
    base_gp = {"heel_med": 22, "heel_lat": 10, "midfoot": 9, "met1": 12, "met2": 12, "met3": 11,
               "met4": 9, "met5": 7, "hallux": 9, "toes": 5}
    base_bp = {"met1": 32, "met2": 38, "met3": 43, "met4": 35, "met5": 26, "hallux": 29, "toes": 14}
    dates = ["2026-05-25", "2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29", "2026-07-05"]
    mult = [1.00, 1.02, 0.98, 0.86, 0.72, 0.61, 0.55]           # forefoot-dose multiplier
    bounce = [40320, 41000, 39500, 33000, 27000, 22000, 20000]  # cycles/day (intervention at wk3)
    rows = []
    for d, m, bc in zip(dates, mult, bounce):
        day = {"pressure_kPa": dict(base_press),
               "gait": {"pti_kPa_s": dict(base_gp), "cycles_per_day": 7000},
               "bounce": {"pti_kPa_s": {z: round(v * m, 1) for z, v in base_bp.items()},
                          "cycles_per_day": bc}}
        rows.append(row_from_day(day, db, d))
    return rows


def chart(rows, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = sorted(rows[0]["structures"])
    dates = [r["date"][5:] for r in rows]                 # MM-DD
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for n in names:
        ys = [r["structures"].get(n, 0) for r in rows]
        ax.plot(dates, ys, "-o", lw=2, ms=4, color=COLORS.get(n), label=n.replace("_", " "))
    ax.set(title="Structure CPTS over time — the all-day dose", ylabel="CPTS (MPa·s/day)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "trend.png"), dpi=130)

    first, last = rows[0], rows[-1]
    L = ["# CPTS trend — the all-day dose over time",
         f"_{len(rows)} snapshots, {first['date']} → {last['date']}. Watching your own numbers move is "
         "the whole point of the dose model. Not a medical device._", "", "![trend](trend.png)", "",
         "| structure | first | last | Δ | |", "|---|---|---|---|---|"]
    for n in names:
        a = first["structures"].get(n, 0); b = last["structures"].get(n, 0)
        d = b - a; pct = (100 * d / a) if a else 0
        arrow = "🟢 ↓" if d < -1 else "🔴 ↑" if d > 1 else "→"
        L.append(f"| {n.replace('_', ' ')} | {a:,.0f} | {b:,.0f} | {d:+,.0f} ({pct:+.0f}%) | {arrow} |")
    L.append(f"\n- forefoot dose {first['forefoot']:,.0f} → {last['forefoot']:,.0f} MPa·s/day; "
             f"heel/mid {first['heel']:,.0f} → {last['heel']:,.0f}.")
    L.append("- A falling forefoot line after a met pad / rest-window habit is the intervention working; "
             "a rising line says the dose is creeping back. Log a day.json weekly and re-chart.")
    with open(os.path.join(out, "report_trend.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description="Track CPTS per nerve/fascia structure over time.")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default="results")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("record")
    r.add_argument("day"); r.add_argument("--date", required=True)
    r.add_argument("--history", default="results/cpts_history.jsonl")
    c = sub.add_parser("chart")
    c.add_argument("--history", default="results/cpts_history.jsonl")
    c.add_argument("--out", default="results")
    a = ap.parse_args()
    db = db_load()

    if a.demo:
        os.makedirs(a.out, exist_ok=True)
        rows = demo_history(db)
        with open(os.path.join(a.out, "cpts_history.jsonl"), "w") as fh:
            fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
        chart(rows, a.out)
        print(f"-> {a.out}/trend.png + report_trend.md + cpts_history.jsonl ({len(rows)} days)")
    elif a.cmd == "record":
        row = row_from_day(json.load(open(a.day, encoding="utf-8")), db, a.date)
        os.makedirs(os.path.dirname(a.history) or ".", exist_ok=True)
        with open(a.history, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"recorded {a.date}: forefoot {row['forefoot']:,.0f} · "
              + " · ".join(f"{k} {v:,.0f}" for k, v in row["structures"].items()))
    elif a.cmd == "chart":
        os.makedirs(a.out, exist_ok=True)
        rows = read_history(a.history)
        if len(rows) < 2:
            raise SystemExit("need >=2 recorded days to chart a trend")
        chart(rows, a.out)
        print(f"-> {a.out}/trend.png + report_trend.md ({len(rows)} days)")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
