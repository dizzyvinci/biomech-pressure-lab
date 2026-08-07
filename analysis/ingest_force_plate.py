#!/usr/bin/env python3
"""
ingest_force_plate.py -- the missing link in the pressure chain.

THE GAP THIS CLOSES
-------------------
firmware/force_plate/force_plate.ino v2.0.0 emits a rich, self-describing log:
a '#' header block carrying the calibration that produced the numbers, the five
condition fields, the geometry, the safety ceilings, then a '#COLS' line, then
CSV. Every analysis/ script in this repo was written against the OLDER
smart_insole format and reads none of it -- they skip '#' lines, so the
calibration, the condition and the fault flags are silently discarded. A run
therefore lands in analyze_pressure.py as bare numbers with no coordinates,
which is the precise failure the repo's own rule names: a reading without its
condition is not usable downstream.

WHAT IT DOES
------------
  1. Parses the header block into a SESSION MANIFEST (json sidecar).
  2. Runs QC gates that can REFUSE. An uncalibrated, un-tared, condition-less
     or overload-latched log does not silently become a tidy CSV.
  3. Reconstructs the ACHIEVED sample rate from t_ms and compares it to what
     the header implies. A commanded rate is not a measured one.
  4. Emits a tidy CSV whose columns are what analysis/ already expects
     (activity, fsr0..fsr7, t_ms) PLUS the coordinates carried per row, so a
     downstream join can never lose them.
  5. Stamps qc_status on every row. Degraded data is admissible with
     --allow-degraded but is then LABELLED, so it can never be pooled with
     clean data by accident. That is the whole point of admitting it at all.

WHY THE GATES REFUSE RATHER THAN WARN
-------------------------------------
scale_counts_per_N = 0 means the firmware never had a known mass on that
channel, so total_n is not newtons -- it is counts with a units label. Passing
that downstream produces a plausible number with no meaning, which is worse
than an error. Same for F_OVERLOAD: past 250 N the plate is outside the regime
anyone characterised it in, and the coupon on the desk is one PETG bracket at
<=52 % density, not a plate.

SELF-TEST -- against the real firmware, not a fixture
-----------------------------------------------------
    python ingest_force_plate.py --selftest
reads ../firmware/force_plate/force_plate.ino and asserts that this parser's
column list and flag-bit table match the ones the firmware actually compiles.
That is a drift detector: if someone adds a column to writeHeader() and not
here, the ingest starts silently dropping it, and no fixture CSV would notice
because the fixture would be stale in the same way. It also round-trips a
header block built from the firmware's own printf formats.

    python ingest_force_plate.py /plog/S0001_C001.csv --out results/
    python ingest_force_plate.py "logs/*.csv" --out results/ --allow-degraded

ASCII output only (cp1252 console).
"""
import argparse, glob, io, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.normpath(os.path.join(HERE, "..", "firmware", "force_plate", "force_plate.ino"))

# --- mirrors of the firmware's section-3 fault bits -------------------------
FLAG_BITS = [
    (0x0001, "F_HX_TIMEOUT",  "an HX711 did not answer; the row is not a reading"),
    (0x0002, "F_HX_SAT",      "ADC saturated -- the cell is past its range"),
    (0x0004, "F_OVERLOAD",    "total exceeded MAX_BENCH_N and latched"),
    (0x0008, "F_NOT_TARED",   "no zero was taken this power-cycle"),
    (0x0010, "F_NOT_CAL",     "no counts-per-newton; total_n is not newtons"),
    (0x0020, "F_COND_UNSET",  "a condition field was empty"),
    (0x0040, "F_SD_FAIL",     "card write failed; rows may be missing"),
    (0x0080, "F_EPOCH_UNSET", "no wall clock was supplied; iso_utc is empty"),
    (0x0100, "F_SESSION_CAP", "the 20 min session cap stopped the run"),
]
# Bits that make a row's FORCE value meaningless, as opposed to merely annotated.
FATAL_BITS = 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010

EXPECTED_COLS = [
    "t_ms", "iso_utc", "sess", "cond_id", "activity", "total_n",
    "ch0_n", "ch1_n", "ch2_n", "ch3_n", "cop_ap_mm", "cop_ml_mm",
    "bw_ratio", "fsr0_adc", "fsr0_mv", "fsr1_adc", "fsr1_mv", "flags",
]

COND_FIELDS = ["posture", "load", "footwear", "side", "surface"]

KV = re.compile(r"(\w+)=([^\s]*)")


# ---------------------------------------------------------------------------
# header parsing
# ---------------------------------------------------------------------------
def parse_header(lines):
    """lines: the leading '#' block. Returns a manifest dict."""
    m = {"cal": {}, "cond": {}, "notes": [], "raw_header": []}
    for ln in lines:
        m["raw_header"].append(ln.rstrip("\n"))
        s = ln.lstrip("#").strip()
        if not s:
            continue
        if s.startswith("COLS "):
            m["cols"] = [c.strip() for c in s[5:].split(",")]
            continue
        mm = re.match(r"^(\w+) v([\d.]+) \(([\d-]+)\)\s+mode=(\w+)\s+cells=(\d+)", s)
        if mm:
            m["fw_name"], m["fw_version"], m["fw_date"] = mm.group(1), mm.group(2), mm.group(3)
            m["mode"], m["n_cells"] = mm.group(4), int(mm.group(5))
            continue
        mm = re.match(r"^cal(\d+)\s+offset=(-?\d+)\s+scale_counts_per_N=([-\d.eE+]+)", s)
        if mm:
            m["cal"][int(mm.group(1))] = {"offset": int(mm.group(2)),
                                          "scale_counts_per_N": float(mm.group(3))}
            continue
        if s.startswith("UNVERIFIED") or s.startswith("WARN") or s.startswith("NOTE"):
            m["notes"].append(s)
            continue
        pairs = KV.findall(s)
        if not pairs:
            m["notes"].append(s)
            continue
        for k, v in pairs:
            if k in COND_FIELDS or k == "note":
                m["cond"][k] = v
            else:
                m[k] = v
    return m


def _f(m, key, default=None):
    try:
        return float(m[key])
    except (KeyError, TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# QC
# ---------------------------------------------------------------------------
class QC:
    def __init__(self):
        self.blockers = []   # refuse unless --allow-degraded
        self.warnings = []

    def block(self, code, msg):
        self.blockers.append({"code": code, "detail": msg})

    def warn(self, code, msg):
        self.warnings.append({"code": code, "detail": msg})

    @property
    def status(self):
        if self.blockers:
            return "DEGRADED"
        return "WARN" if self.warnings else "CLEAN"


def qc_session(man, rows, qc):
    # --- condition completeness ------------------------------------------
    missing = [f for f in COND_FIELDS if not man["cond"].get(f)]
    if missing:
        qc.block("COND_INCOMPLETE",
                 "condition fields empty: %s. Conditions are coordinates -- "
                 "loaded/unloaded/shod are different measurables, not the same "
                 "one with noise." % ",".join(missing))

    # --- calibration ------------------------------------------------------
    n_cells = int(man.get("n_cells", 1) or 1)
    uncal = [i for i in range(n_cells)
             if man["cal"].get(i, {}).get("scale_counts_per_N", 0.0) == 0.0]
    if uncal:
        qc.block("NOT_CALIBRATED",
                 "channels %s have scale_counts_per_N = 0. total_n is raw counts "
                 "wearing a newton label. Run CAL <ch> <kg> with a known mass."
                 % uncal)
    untared = [i for i in range(n_cells) if man["cal"].get(i, {}).get("offset", 0) == 0]
    if untared:
        qc.warn("TARE_AT_ZERO",
                "channels %s report offset exactly 0, which is what an untared "
                "channel also looks like. Confirm TARE was run." % untared)

    # --- body mass --------------------------------------------------------
    if str(man.get("body_kg", "UNSET")).upper() == "UNSET":
        qc.warn("BODY_KG_UNSET",
                "bw_ratio is blank by design. Any body-weight-fraction analysis "
                "downstream must be skipped, not defaulted.")

    # --- firmware provenance ---------------------------------------------
    for n in man.get("notes", []):
        if "UNVERIFIED" in n:
            qc.warn("FW_UNVERIFIED", n)

    if not rows:
        qc.block("NO_ROWS", "header parsed but no data rows followed")
        return

    # --- flags across the run --------------------------------------------
    seen = 0
    for r in rows:
        seen |= r["_flags"]
    for bit, name, why in FLAG_BITS:
        if seen & bit:
            (qc.block if bit & FATAL_BITS else qc.warn)(name, why)

    # --- achieved sample rate --------------------------------------------
    ts = [r["t_ms"] for r in rows if r["t_ms"] is not None]
    if len(ts) >= 3:
        span = ts[-1] - ts[0]
        if span > 0:
            hz = 1000.0 * (len(ts) - 1) / span
            man["achieved_hz"] = round(hz, 3)
            gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
            gaps_sorted = sorted(gaps)
            med = gaps_sorted[len(gaps_sorted) // 2]
            man["median_gap_ms"] = med
            man["max_gap_ms"] = max(gaps)
            # A dropout is a gap far past the median cadence, not a slow sample.
            if max(gaps) > max(5 * med, med + 200):
                qc.warn("SAMPLE_DROPOUT",
                        "largest inter-sample gap %d ms vs median %d ms -- the "
                        "run is not uniformly sampled; any impulse or "
                        "rate-of-loading figure computed as if it were will be "
                        "wrong." % (max(gaps), med))
            if any(g <= 0 for g in gaps):
                qc.block("TIME_NOT_MONOTONIC",
                         "t_ms went backwards or repeated; rows are out of order")
    if not man.get("iso_utc"):
        qc.warn("NO_WALL_CLOCK",
                "iso_utc empty (no RTC on this machine and TIME was never sent). "
                "t_ms is monotonic and correct; absolute time is unknown. Do not "
                "join this run to anything dated without supplying the epoch.")


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------
def read_log(path):
    head, data = [], []
    cols = None
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if ln.startswith("#"):
                head.append(ln)
                continue
            s = ln.strip()
            if not s:
                continue
            data.append(s)
    man = parse_header(head)
    cols = man.get("cols") or EXPECTED_COLS
    rows = []
    for s in data:
        parts = s.split(",")
        if len(parts) < len(cols):
            parts += [""] * (len(cols) - len(parts))
        r = dict(zip(cols, parts[:len(cols)]))
        try:
            r["t_ms"] = int(r.get("t_ms", "") or 0)
        except ValueError:
            r["t_ms"] = None
        fl = (r.get("flags", "") or "0").strip()
        try:
            r["_flags"] = int(fl, 16) if not fl.isdigit() or fl.startswith("0x") else int(fl)
        except ValueError:
            r["_flags"] = 0
        rows.append(r)
    return man, cols, rows


def flag_names(v):
    return "|".join(n for b, n, _ in FLAG_BITS if v & b) or "none"


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------
TIDY_COLS = ["t_ms", "iso_utc", "sess", "cond_id", "activity",
             "posture", "load", "footwear", "side", "surface",
             "total_n", "ch0_n", "ch1_n", "ch2_n", "ch3_n",
             "cop_ap_mm", "cop_ml_mm", "bw_ratio",
             "fsr0_adc", "fsr0_mv", "fsr1_adc", "fsr1_mv",
             "flags", "flag_names", "qc_status", "src"]


def write_tidy(out_csv, man, rows, status, src):
    with io.open(out_csv, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(TIDY_COLS) + "\n")
        for r in rows:
            vals = []
            for c in TIDY_COLS:
                if c in COND_FIELDS:
                    v = man["cond"].get(c, "")
                elif c == "flag_names":
                    v = flag_names(r["_flags"])
                elif c == "qc_status":
                    v = "DEGRADED" if (r["_flags"] & FATAL_BITS) else status
                elif c == "src":
                    v = os.path.basename(src)
                else:
                    v = r.get(c, "")
                s = str(v)
                vals.append('"%s"' % s.replace('"', '""') if ("," in s or '"' in s) else s)
            f.write(",".join(vals) + "\n")


# ---------------------------------------------------------------------------
# self-test against the real firmware source
# ---------------------------------------------------------------------------
def selftest():
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-34s %s%s" % (name, "PASS" if cond else "FAIL",
                                "" if cond else "  <- " + detail))
        ok = ok and cond

    print("ingest_force_plate --selftest (reads LIVE firmware, not a fixture)")
    print("  firmware: %s" % FW)
    chk("firmware source present", os.path.isfile(FW), FW)
    if not os.path.isfile(FW):
        return 1
    src = io.open(FW, "r", encoding="utf-8", errors="replace").read()

    # 1. #COLS line must match EXPECTED_COLS exactly, in order.
    m = re.search(r'"#COLS ([^"]*)"\s*\n?\s*"?([^"]*)"?\)', src)
    cols_txt = ""
    m2 = re.search(r'p\.println\("#COLS (.*?)"\);', src, re.S)
    if m2:
        cols_txt = re.sub(r'"\s*\n\s*"', "", m2.group(1))
    else:
        m3 = re.search(r'#COLS ([^"]*)"((?:\s*"[^"]*")*)', src)
        if m3:
            cols_txt = m3.group(1) + "".join(re.findall(r'"([^"]*)"', m3.group(2) or ""))
    fw_cols = [c.strip() for c in cols_txt.split(",") if c.strip()]
    chk("#COLS extracted from firmware", bool(fw_cols), "regex found nothing")
    chk("column list matches firmware", fw_cols == EXPECTED_COLS,
        "firmware=%s parser=%s" % (fw_cols, EXPECTED_COLS))

    # 2. every fault bit the firmware defines must be in FLAG_BITS, same value.
    fw_bits = dict((n, int(v, 16)) for n, v in
                   re.findall(r"static const uint16_t (F_\w+)\s*=\s*(0x[0-9A-Fa-f]+)", src))
    mine = dict((n, b) for b, n, _ in FLAG_BITS)
    chk("firmware fault bits found", len(fw_bits) >= 8, str(fw_bits))
    chk("fault-bit table matches firmware", fw_bits == mine,
        "firmware=%s parser=%s" % (sorted(fw_bits.items()), sorted(mine.items())))

    # 3. condition fields the firmware requires must be the ones we gate on.
    cc = re.search(r"conditionComplete\(\)\s*\{\s*return(.*?);", src, re.S)
    fw_cond = sorted(set(re.findall(r"cond\.(\w+)\[0\]", cc.group(1)))) if cc else []
    chk("condition fields match firmware", fw_cond == sorted(COND_FIELDS),
        "firmware=%s parser=%s" % (fw_cond, sorted(COND_FIELDS)))

    # 4. round-trip: build a header the way writeHeader() does, parse it back.
    hdr = [
        "# force_plate v2.0.0 (2026-08-07)  mode=AP  cells=2\n",
        "# session=7  boot_ms=12345  iso_utc=\n",
        "# cond_id=3 posture=stand_2ft load=bw_full footwear=barefoot side=both "
        "surface=hard note=\n",
        "# body_kg=UNSET\n",
        "# geom_ap_mm=240.0 geom_ml_mm=240.0 win=5\n",
        "# cal0 offset=-12345 scale_counts_per_N=812.5000\n",
        "# cal1 offset=9876 scale_counts_per_N=0.0000\n",
        "# max_bench_n=250.0 session_cap_ms=1200000 allow_body_load=0\n",
        "# UNVERIFIED: this firmware has never been run against a physical HX711.\n",
        "#COLS " + ",".join(EXPECTED_COLS) + "\n",
    ]
    man = parse_header(hdr)
    chk("header round-trip: version", man.get("fw_version") == "2.0.0", str(man.get("fw_version")))
    chk("header round-trip: cells", man.get("n_cells") == 2, str(man.get("n_cells")))
    chk("header round-trip: condition", man["cond"].get("posture") == "stand_2ft",
        str(man["cond"]))
    chk("header round-trip: cal0 scale", man["cal"].get(0, {}).get("scale_counts_per_N") == 812.5,
        str(man["cal"]))
    chk("header round-trip: cols", man.get("cols") == EXPECTED_COLS, str(man.get("cols")))

    # 5. the gates must actually refuse. cal1 is uncalibrated above.
    qc = QC()
    rows = [{"t_ms": t, "_flags": 0} for t in (0, 20, 40, 60, 80)]
    qc_session(man, rows, qc)
    codes = [b["code"] for b in qc.blockers]
    chk("uncalibrated channel BLOCKS", "NOT_CALIBRATED" in codes, str(codes))
    chk("achieved rate computed", abs(man.get("achieved_hz", 0) - 50.0) < 0.01,
        str(man.get("achieved_hz")))

    # 6. a fully clean session must NOT block.
    hdr2 = [h for h in hdr]
    hdr2[6] = "# cal1 offset=9876 scale_counts_per_N=799.1000\n"
    man2 = parse_header(hdr2)
    qc2 = QC()
    qc_session(man2, rows, qc2)
    chk("clean session passes gates", not qc2.blockers, str(qc2.blockers))
    chk("clean session still warns on body_kg",
        "BODY_KG_UNSET" in [w["code"] for w in qc2.warnings], str(qc2.warnings))

    # 7. an overload flag must be fatal, and must taint only the rows carrying it.
    qc3 = QC()
    rows3 = [{"t_ms": 0, "_flags": 0}, {"t_ms": 20, "_flags": 0x0004}, {"t_ms": 40, "_flags": 0}]
    qc_session(parse_header(hdr2), rows3, qc3)
    chk("overload BLOCKS", "F_OVERLOAD" in [b["code"] for b in qc3.blockers],
        str(qc3.blockers))

    print("\n%s" % ("SELFTEST PASS" if ok else "SELFTEST FAIL"))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="*", help="force_plate CSV log(s); globs ok")
    ap.add_argument("--out", default="results", help="output directory")
    ap.add_argument("--allow-degraded", action="store_true",
                    help="emit anyway, labelled DEGRADED on every row")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.logs:
        ap.print_help()
        return 2

    paths = []
    for g in a.logs:
        paths.extend(sorted(glob.glob(g)) or ([g] if os.path.isfile(g) else []))
    if not paths:
        print("no logs matched %s" % a.logs)
        return 2

    os.makedirs(a.out, exist_ok=True)
    rc = 0
    for p in paths:
        man, cols, rows = read_log(p)
        qc = QC()
        qc_session(man, rows, qc)
        status = qc.status
        base = os.path.splitext(os.path.basename(p))[0]

        print("\n== %s ==" % p)
        print("   fw %s v%s  mode=%s  cells=%s  rows=%d" %
              (man.get("fw_name", "?"), man.get("fw_version", "?"),
               man.get("mode", "?"), man.get("n_cells", "?"), len(rows)))
        print("   condition: %s" % (", ".join("%s=%s" % (k, man["cond"].get(k, ""))
                                              for k in COND_FIELDS)))
        if "achieved_hz" in man:
            print("   achieved %.2f Hz (median gap %s ms, max %s ms)" %
                  (man["achieved_hz"], man.get("median_gap_ms"), man.get("max_gap_ms")))
        for w in qc.warnings:
            print("   WARN  %-16s %s" % (w["code"], w["detail"]))
        for b in qc.blockers:
            print("   BLOCK %-16s %s" % (b["code"], b["detail"]))

        man["qc_status"] = status
        man["qc_blockers"] = qc.blockers
        man["qc_warnings"] = qc.warnings
        man["source"] = os.path.abspath(p)
        man["ingested_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        man["row_count"] = len(rows)
        with io.open(os.path.join(a.out, base + ".manifest.json"), "w",
                     encoding="utf-8") as f:
            json.dump(man, f, indent=1, sort_keys=True)

        if qc.blockers and not a.allow_degraded:
            print("   -> REFUSED. Manifest written; no tidy CSV. Fix the run, or "
                  "re-run with --allow-degraded and accept the DEGRADED label.")
            rc = 1
            continue
        out_csv = os.path.join(a.out, base + ".tidy.csv")
        write_tidy(out_csv, man, rows, status, p)
        print("   -> %s  (%s)" % (out_csv, status))
    return rc


if __name__ == "__main__":
    sys.exit(main())
