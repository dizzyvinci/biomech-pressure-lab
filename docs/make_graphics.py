#!/usr/bin/env python3
"""
make_graphics.py — generate the fleshed-out annotated diagrams (SVG) from code,
so geometry (footprint sensor dots, timelines, sway ellipses) is exact and the
graphics are reproducible. Writes into docs/.

    python make_graphics.py

Produces: physical_setup.svg, pipeline.svg, software_metrics.svg,
          day_in_the_life.svg, balance_detail.svg
Numbers shown come from the committed worked example (sample/results/).
"""
import math
import os

NAVY, SLATE, MUTE = "#0f172a", "#475569", "#64748b"
LINE, BORDER = "#94a3b8", "#e2e8f0"
PANEL, PANEL2 = "#f8fafc", "#eef2f7"
RED, REDBG = "#e11d48", "#fdecef"
BLUE, BLUEBG = "#2563eb", "#eff6ff"
AMBER = "#f59e0b"
GREEN, GREENBG = "#16a34a", "#f0fdf4"
FONT = "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
HERE = os.path.dirname(os.path.abspath(__file__))

# 8-zone normalized layout (x: medial->lateral, y: heel->toe) — matches analysis
ZONES = ["heel_med", "heel_lat", "midfoot", "met1", "met3", "met5", "hallux", "toes"]
XY = [(.35, .08), (.65, .08), (.50, .45), (.30, .72),
      (.50, .74), (.70, .72), (.28, .92), (.55, .95)]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(w, h, body, title, desc):
    title, desc = esc(title), esc(desc)
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'font-family="{FONT}">\n<title>{title}</title>\n<desc>{desc}</desc>\n'
            f'<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="6" refY="3" '
            f'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{MUTE}"/></marker>'
            f'<marker id="arr" markerWidth="9" markerHeight="9" refX="6" refY="3" '
            f'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{RED}"/></marker></defs>\n'
            f'<rect x="4" y="4" width="{w-8}" height="{h-8}" rx="14" fill="#ffffff" '
            f'stroke="{BORDER}" stroke-width="2"/>\n{body}\n</svg>\n')


def T(x, y, s, size=11, fill=NAVY, weight="400", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')


def box(x, y, w, h, fill="#ffffff", stroke=LINE, sw=1.4, rx=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def head(w, title, sub):
    return (T(24, 36, title, 18, NAVY, "700") +
            T(24, 55, sub, 11.5, SLATE))


def footprint(cx, top, length, width, fill="#dbe4ef", stroke=LINE):
    """Top-down footbed: forefoot ellipse + heel ellipse, toe at 'top'."""
    fw, hw = width / 2, width / 2 * 0.72
    fore_cy = top + length * 0.30
    heel_cy = top + length * 0.82
    s = (f'<ellipse cx="{cx}" cy="{fore_cy:.0f}" rx="{fw:.0f}" ry="{length*0.34:.0f}" '
         f'fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
         f'<ellipse cx="{cx}" cy="{heel_cy:.0f}" rx="{hw:.0f}" ry="{length*0.26:.0f}" '
         f'fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
         f'<rect x="{cx-hw:.0f}" y="{top+length*0.35:.0f}" width="{2*hw:.0f}" '
         f'height="{length*0.34:.0f}" fill="{fill}"/>')
    return s


def zone_xy(cx, top, length, width, i):
    xn, yn = XY[i]
    sx = cx - width / 2 + xn * width
    sy = top + (1 - yn) * length
    return sx, sy


def dots(cx, top, length, width, hot=None, r=6, color="#334155", label=False):
    out = []
    for i in range(8):
        sx, sy = zone_xy(cx, top, length, width, i)
        c = RED if i == hot else color
        out.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{r}" fill="{c}" '
                   f'stroke="#ffffff" stroke-width="1.2"/>')
        if label:
            out.append(T(sx + r + 2, sy + 3, ZONES[i], 8.5, MUTE))
    return "".join(out)


# ---------------------------------------------------------------- worn setup
def g_physical():
    w, h = 900, 560
    b = [head(w, "How it's worn — electronics OFF the foot",
              "An ankle pod carries the brain + battery; only paper-thin FSRs sit under the foot")]
    # LEFT: schematic leg + pod + ribbon
    b.append(box(30, 78, 300, 400, PANEL, BORDER, 1.6, 12))
    b.append(T(46, 104, "Worn on the body", 12.5, NAVY, "700"))
    # shin + foot (schematic)
    b.append('<rect x="150" y="120" width="46" height="150" rx="16" fill="#e6ebf2" stroke="#94a3b8"/>')
    b.append('<rect x="150" y="270" width="150" height="34" rx="14" fill="#e6ebf2" stroke="#94a3b8"/>')
    b.append(T(230, 292, "foot", 9.5, MUTE, "400", "middle"))
    # ankle pod
    b.append(box(120, 150, 92, 74, "#ffffff", RED, 2, 10))
    b.append(T(166, 170, "ANKLE POD", 10.5, RED, "700", "middle"))
    b.append(T(166, 186, "ESP32-S3", 8.5, SLATE, "400", "middle"))
    b.append(T(166, 198, "LiPo + microSD", 8.5, SLATE, "400", "middle"))
    b.append(T(166, 210, "IMU (motion)", 8.5, SLATE, "400", "middle"))
    # ribbon path pod -> under foot
    b.append(f'<path d="M173 224 L173 258 Q173 286 210 288 L240 288" fill="none" '
             f'stroke="{RED}" stroke-width="2.4" marker-end="url(#arr)"/>')
    b.append(T(196, 250, "thin ribbon", 8.5, RED, "700"))
    b.append(T(196, 262, "(only wire on you)", 8, MUTE))
    # sensor dots under foot
    for sx in (232, 252, 272):
        b.append(f'<circle cx="{sx}" cy="303" r="4.5" fill="{NAVY}"/>')
    b.append(T(300, 306, "FSRs", 8.5, MUTE))
    b.append(T(46, 350, "• Nothing bulky underfoot — the sole", 10, SLATE))
    b.append(T(46, 366, "  is paper-thin.", 10, SLATE))
    b.append(T(46, 388, "• Pod straps at the ankle; the", 10, SLATE))
    b.append(T(46, 404, "  ribbon is the only thing on the", 10, SLATE))
    b.append(T(46, 420, "  foot besides the sensors.", 10, SLATE))
    b.append(T(46, 448, "→ solves \"3D-print around the", 10.5, RED, "700"))
    b.append(T(46, 464, "   electronics\": we don't.", 10.5, RED, "700"))

    # MIDDLE: the sensor sole with 8 labeled zones
    b.append(box(354, 78, 268, 400, "#ffffff", BORDER, 1.6, 12))
    b.append(T(370, 104, "Sensor sole — 8 FSR zones", 12.5, NAVY, "700"))
    cx, top, length, width = 488, 130, 300, 150
    b.append(footprint(cx, top, length, width))
    b.append(dots(cx, top, length, width, hot=None, r=7, label=True))
    b.append(T(370, 460, "heel · midfoot · met heads · hallux · toes", 9.5, MUTE))

    # RIGHT: swap sole barefoot vs shoe
    b.append(box(646, 78, 224, 400, PANEL2, BORDER, 1.6, 12))
    b.append(T(662, 104, "Swap the sole", 12.5, NAVY, "700"))
    b.append(footprint(720, 130, 150, 78, "#dbe4ef"))
    b.append(dots(720, 130, 150, 78, r=4.5, color="#475569"))
    b.append(T(758, 210, "barefoot", 10, SLATE, "700"))
    b.append(footprint(720, 300, 150, 78, "#e7d9c3"))
    b.append(dots(720, 300, 150, 78, r=4.5, color="#7c5e33"))
    b.append(T(758, 380, "in-shoe", 10, SLATE, "700"))
    b.append(T(662, 430, "Same 8 sensors, two soles →", 9.5, SLATE))
    b.append(T(662, 445, "compare shoe vs barefoot load.", 9.5, SLATE))
    b.append(T(24, 528, "Electronics ride at the ankle; the foot only carries thin FSRs + one ribbon. "
                        "Reprint the sole cheaply when it wears.", 10.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "How the rig is worn: an ankle pod holds the ESP32, LiPo, microSD and IMU; a thin ribbon runs to a paper-thin sole with 8 FSRs; swap the sole for barefoot vs in-shoe.",
                "Left: schematic leg with an ankle pod and ribbon to under-foot sensors. Middle: top-down sole with 8 labeled FSR zones. Right: barefoot vs in-shoe sole swap.")


# ---------------------------------------------------------------- closed loop
def g_pipeline():
    w, h = 900, 470
    b = [head(w, "Measure → design → print → re-measure (with real numbers)",
              "The committed worked example, end to end — every box is a script you can run")]
    steps = [
        ("1 · Wear & log", "shoe + barefoot, all day\nFSR ×8 + IMU → microSD", PANEL2, LINE),
        ("2 · calibrate.py", "known weights → F=a·G^b\nR² = 1.00 → real kPa", REDBG, RED),
        ("3 · interpret.py", "heel_med 645 kPa (40%)\nmedial pronation · +13 pts shoe", PANEL2, LINE),
        ("4 · build_insole.py", "aggressive heel relief +\nmedial post → .scad/.stl", REDBG, RED),
        ("5 · H2D prints", "soft TPU 85A heel/relief\n+ firm TPU 95A shell", PANEL2, LINE),
        ("6 · Re-measure", "did heel load drop?\niterate the window", GREENBG, GREEN),
    ]
    x0, y0, bw, bh, gap = 34, 92, 250, 92, 40
    positions = [(x0, y0), (x0 + bw + gap, y0), (x0 + 2 * (bw + gap), y0),
                 (x0 + 2 * (bw + gap), y0 + bh + 54), (x0 + bw + gap, y0 + bh + 54),
                 (x0, y0 + bh + 54)]
    for (px, py), (title, body, fill, stroke) in zip(positions, steps):
        b.append(box(px, py, bw, bh, fill, stroke, 1.6, 10))
        b.append(T(px + 14, py + 24, title, 12.5, NAVY, "700"))
        for j, line in enumerate(body.split("\n")):
            b.append(T(px + 14, py + 44 + j * 15, line, 9.5, SLATE))
    # arrows along the S-path
    def arrow(x1, y1, x2, y2):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTE}" stroke-width="1.8" marker-end="url(#ar)"/>'
    b.append(arrow(x0 + bw + 6, y0 + bh / 2, x0 + bw + gap - 4, y0 + bh / 2))
    b.append(arrow(x0 + 2 * bw + gap + 6, y0 + bh / 2, x0 + 2 * (bw + gap) - 4, y0 + bh / 2))
    b.append(arrow(positions[2][0] + bw / 2, y0 + bh + 6, positions[3][0] + bw / 2, y0 + bh + 54 - 4))
    b.append(arrow(positions[3][0] - 6, y0 + bh + 54 + bh / 2, positions[4][0] + bw + 4, y0 + bh + 54 + bh / 2))
    b.append(arrow(positions[4][0] - 6, y0 + bh + 54 + bh / 2, positions[5][0] + bw + 4, y0 + bh + 54 + bh / 2))
    # loop-back arrow 6 -> 1
    b.append(f'<path d="M{x0+bw/2} {y0+bh+54} L{x0+bw/2} {y0+bh+30} L{x0+bw/2} {y0+bh+6}" '
             f'fill="none" stroke="{GREEN}" stroke-width="1.8" marker-end="url(#ar)"/>')
    b.append(T(x0 + bw / 2 + 8, y0 + bh + 24, "iterate", 9, GREEN, "700"))
    b.append(T(24, 440, "Calibration is the hinge: raw FSRs are nonlinear — without it the hot spot reads wrong. "
                        "With it, every number above is real kPa.", 10.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Closed loop with real worked-example numbers: wear & log, calibrate to kPa (R2=1.0), interpret (heel_med 645 kPa), build_insole.py, print on H2D, re-measure and iterate.",
                "Six connected steps in an S-layout with a loop-back arrow, each labeled with the script and its output.")


# ---------------------------------------------------------------- software
def g_software():
    w, h = 900, 520
    b = [head(w, "The software — two modules from one sensor set",
              "The same FSR + IMU logs (calibrated to kPa) drive foot-pressure AND balance analysis")]
    b.append(box(24, 74, 150, 40, PANEL2, LINE, 1.4))
    b.append(T(99, 92, "Logs on SD", 11, NAVY, "700", "middle"))
    b.append(T(99, 106, "FSR×8 + IMU", 8, MUTE, "400", "middle"))
    b.append(box(24, 128, 150, 40, REDBG, RED, 1.6))
    b.append(T(99, 146, "calibrate.py", 11, NAVY, "700", "middle"))
    b.append(T(99, 160, "ADC → kPa (R²=1.0)", 8, MUTE, "400", "middle"))
    b.append(f'<path d="M174 148 L210 148 L210 210 L250 210" fill="none" stroke="{MUTE}" stroke-width="1.6" marker-end="url(#ar)"/>')
    b.append(f'<path d="M174 148 L210 148 L210 360 L250 360" fill="none" stroke="{MUTE}" stroke-width="1.6" marker-end="url(#ar)"/>')

    # PRESSURE module
    b.append(box(250, 188, 620, 150, "#ffffff", BORDER, 1.6, 10))
    b.append('<rect x="250" y="188" width="620" height="26" rx="10" fill="#0f172a"/>')
    b.append(T(266, 206, "PRESSURE — foot pain / insole  (interpret.py)", 11.5, "#ffffff", "700"))
    # mini heatmap footprint
    cx, top, length, width = 320, 224, 100, 60
    b.append(footprint(cx, top, length, width, "#e2e8f0"))
    hm = zone_xy(cx, top, length, width, 0)
    b.append(f'<circle cx="{hm[0]:.0f}" cy="{hm[1]:.0f}" r="22" fill="{RED}" opacity="0.75"/>')
    b.append(f'<circle cx="{hm[0]:.0f}" cy="{hm[1]:.0f}" r="12" fill="{AMBER}" opacity="0.9"/>')
    for i in (1, 3, 4, 5):
        sx, sy = zone_xy(cx, top, length, width, i)
        b.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="7" fill="{BLUE}" opacity="0.55"/>')
    b.append(T(cx, top + length + 16, "peak-pressure map", 8.5, MUTE, "400", "middle"))
    metrics_p = ["peak · impulse (∫F·dt)", "center-of-pressure path", "medial/lateral · heel/forefoot",
                 "loading rate · cadence", "barefoot vs shoe delta"]
    for j, m in enumerate(metrics_p):
        b.append(T(400, 236 + j * 17, "• " + m, 9.5, SLATE))
    b.append(box(600, 224, 258, 96, PANEL, BORDER, 1.2))
    b.append(T(614, 244, "Example (worked sample)", 9.5, NAVY, "700"))
    b.append(T(614, 262, "heel_med hot spot — 40% of load", 9, SLATE))
    b.append(T(614, 278, "medial 56% vs lateral 25%", 9, SLATE))
    b.append(T(614, 294, "→ aggressive relief + medial post", 9.5, RED, "700"))
    b.append(T(614, 310, "→ soft heel cushion", 9.5, RED, "700"))

    # BALANCE module
    b.append(box(250, 350, 620, 150, "#ffffff", BORDER, 1.6, 10))
    b.append('<rect x="250" y="350" width="620" height="26" rx="10" fill="#0f172a"/>')
    b.append(T(266, 368, "BALANCE — stability / fall risk  (balance.py)", 11.5, "#ffffff", "700"))
    # sway ellipses
    ex, ey = 320, 432
    b.append(f'<ellipse cx="{ex}" cy="{ey}" rx="34" ry="24" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')
    b.append(f'<ellipse cx="{ex}" cy="{ey}" rx="15" ry="11" fill="none" stroke="{GREEN}" stroke-width="1.8"/>')
    b.append(f'<circle cx="{ex}" cy="{ey}" r="2" fill="{NAVY}"/>')
    b.append(T(ex, ey + 44, "sway ellipse", 8.5, MUTE, "400", "middle"))
    b.append(T(ex - 40, ey - 30, "eyes-closed", 8, RED, "700"))
    b.append(T(ex + 20, ey + 2, "eyes-open", 8, GREEN, "700"))
    metrics_b = ["95% sway-ellipse area", "path length · velocity", "ML vs AP direction",
                 "trunk sway (IMU)", "Romberg quotient (EC/EO)"]
    for j, m in enumerate(metrics_b):
        b.append(T(400, 398 + j * 17, "• " + m, 9.5, SLATE))
    b.append(box(600, 386, 258, 96, PANEL, BORDER, 1.2))
    b.append(T(614, 406, "Example (worked sample)", 9.5, NAVY, "700"))
    b.append(T(614, 424, "eyes-open 211 mm² → closed 770 mm²", 9, SLATE))
    b.append(T(614, 440, "Romberg = 3.6  (>2 = vision-reliant)", 9, SLATE))
    b.append(T(614, 456, "→ lateral support · balance cues", 9.5, RED, "700"))
    b.append(T(614, 472, "→ fall-risk screen", 9.5, RED, "700"))
    return wrap(w, h, "\n".join(b),
                "Two software modules from one sensor set: pressure (interpret.py) yields a hot-spot map and insole directives; balance (balance.py) yields sway metrics, Romberg and fall-risk flags. Example values from the worked sample.",
                "Top branch pressure module with a mini heatmap and example directives; bottom branch balance module with sway ellipses and Romberg example.")


# ---------------------------------------------------------------- day in life
def g_day():
    w, h = 900, 470
    b = [head(w, "A day of use — lifespans & battery",
              "Strap on in the morning, log through the day, offload + recharge at night")]
    # timeline
    tx0, tx1, ty = 60, 840, 150
    hours = [(0, "7a"), (1/6, "9a"), (2/6, "12p"), (3/6, "3p"), (4/6, "6p"), (5/6, "9p"), (1, "7a")]
    b.append(f'<line x1="{tx0}" y1="{ty}" x2="{tx1}" y2="{ty}" stroke="{LINE}" stroke-width="2"/>')
    for f, lab in hours:
        x = tx0 + f * (tx1 - tx0)
        b.append(f'<line x1="{x:.0f}" y1="{ty-5}" x2="{x:.0f}" y2="{ty+5}" stroke="{LINE}" stroke-width="2"/>')
        b.append(T(x, ty + 20, lab, 9, MUTE, "400", "middle"))
    # wear span
    ws, we = tx0 + 0 * (tx1 - tx0), tx0 + (5/6) * (tx1 - tx0)
    b.append(f'<rect x="{ws:.0f}" y="{ty-34}" width="{we-ws:.0f}" height="20" rx="6" fill="{BLUEBG}" stroke="{BLUE}"/>')
    b.append(T((ws + we) / 2, ty - 20, "wear + log  (shoe & barefoot)  ~8–14 h", 9.5, BLUE, "700", "middle"))
    # markers
    def marker(f, label, sub, color):
        x = tx0 + f * (tx1 - tx0)
        return (f'<circle cx="{x:.0f}" cy="{ty}" r="5" fill="{color}"/>' +
                T(x, ty + 42, label, 9.5, NAVY, "700", "middle") +
                T(x, ty + 56, sub, 8.5, MUTE, "400", "middle"))
    b.append(marker(0, "strap on", "pod at ankle", RED))
    b.append(marker(2.5/6, "30 s balance", "eyes open/closed", GREEN))
    b.append(marker(5/6, "pull microSD", "→ analyze", RED))
    b.append(marker(1, "recharge", "overnight", AMBER))
    # battery bar
    b.append(T(60, 235, "Battery (1000–1500 mAh)", 11, NAVY, "700"))
    b.append(box(60, 245, 640, 26, "#ffffff", LINE, 1.4, 6))
    b.append(f'<rect x="62" y="247" width="{640*0.62:.0f}" height="22" rx="5" fill="{GREEN}"/>')
    b.append(f'<rect x="{62+640*0.62:.0f}" y="247" width="{640*0.20:.0f}" height="22" rx="0" fill="{AMBER}"/>')
    b.append(f'<rect x="{62+640*0.82:.0f}" y="247" width="{640*0.18:.0f}" height="22" fill="#fee2e2"/>')
    b.append(T(80, 262, "100% morning", 9, "#ffffff", "700"))
    b.append(T(560, 262, "~20% by 9p", 9, "#7c2d12", "700"))
    b.append(T(715, 262, "then recharge", 9, "#7c2d12", "700"))
    # lifespan chips
    chips = [
        ("Battery", "~8–14 h / charge → a waking day", GREEN),
        ("microSD", "offload nightly · ~unlimited", BLUE),
        ("Barefoot sole", "weeks–months · cheap to reprint", AMBER),
        ("Ankle pod (PLA/PETG)", "indefinite", MUTE),
        ("FSRs", "recalibrate / swap over months", RED),
        ("Final insole (TPU)", "months · reprint to re-tune", NAVY),
    ]
    cx0, cy0, cw, ch, gx, gy = 60, 300, 250, 46, 20, 14
    for i, (name, life, color) in enumerate(chips):
        px = cx0 + (i % 3) * (cw + gx)
        py = cy0 + (i // 3) * (ch + gy)
        b.append(box(px, py, cw, ch, PANEL, BORDER, 1.2, 8))
        b.append(f'<rect x="{px}" y="{py}" width="5" height="{ch}" rx="2" fill="{color}"/>')
        b.append(T(px + 14, py + 19, name, 10, NAVY, "700"))
        b.append(T(px + 14, py + 35, life, 9, SLATE))
    b.append(T(24, 440, "The rig doesn't need literal 24/7 wear — a waking day per charge is plenty to trend load & sway; "
                        "recharge while you sleep.", 10.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "A day of use: strap on in the morning, wear and log shoe and barefoot for 8-14 hours, run a 30-second balance test, pull the microSD at night to analyze, and recharge overnight. Plus per-piece lifespans.",
                "A 24-hour timeline with a wear span and markers, a battery drain bar, and six lifespan chips.")


# ---------------------------------------------------------------- balance detail
def g_balance():
    w, h = 900, 480
    b = [head(w, "Balance module — a wearable posturography lab",
              "For balance issues, not just foot pain: the same rig screens stability & fall risk")]
    # standing figure with COP
    b.append(box(30, 78, 250, 372, PANEL, BORDER, 1.6, 12))
    b.append(T(46, 104, "Quiet standing", 12.5, NAVY, "700"))
    # simple figure
    b.append(f'<circle cx="155" cy="150" r="16" fill="#cbd5e1"/>')
    b.append(f'<rect x="140" y="168" width="30" height="70" rx="10" fill="#cbd5e1"/>')
    b.append(f'<rect x="146" y="238" width="10" height="60" fill="#cbd5e1"/>')
    b.append(f'<rect x="158" y="238" width="10" height="60" fill="#cbd5e1"/>')
    b.append(footprint(140, 300, 60, 34, "#dbe4ef"))
    b.append(footprint(178, 300, 60, 34, "#dbe4ef"))
    # sway trace under feet
    b.append(f'<path d="M150 335 q8 -6 14 2 q-10 8 -4 14 q12 -2 6 10" fill="none" stroke="{RED}" stroke-width="1.6"/>')
    b.append(T(46, 380, "IMU adds trunk sway;", 9.5, SLATE))
    b.append(T(46, 395, "FSR center-of-pressure", 9.5, SLATE))
    b.append(T(46, 410, "traces the body's sway.", 9.5, SLATE))
    b.append(T(46, 434, "30 s per condition.", 9.5, MUTE))

    # sway ellipses eyes open vs closed
    b.append(box(300, 78, 300, 372, "#ffffff", BORDER, 1.6, 12))
    b.append(T(316, 104, "Sway area — eyes open vs closed", 12, NAVY, "700"))
    ecx, ecy = 450, 250
    # grid
    b.append(f'<line x1="{ecx}" y1="140" x2="{ecx}" y2="380" stroke="{BORDER}"/>')
    b.append(f'<line x1="330" y1="{ecy}" x2="570" y2="{ecy}" stroke="{BORDER}"/>')
    b.append(f'<ellipse cx="{ecx}" cy="{ecy}" rx="96" ry="70" fill="{REDBG}" stroke="{RED}" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append(f'<ellipse cx="{ecx}" cy="{ecy}" rx="46" ry="34" fill="{GREENBG}" stroke="{GREEN}" stroke-width="2"/>')
    b.append(T(ecx, ecy + 3, "COP", 8.5, NAVY, "400", "middle"))
    b.append(T(ecx + 100, ecy - 60, "eyes-closed", 9.5, RED, "700", "end"))
    b.append(T(ecx + 100, ecy - 46, "770 mm²", 9, RED, "400", "end"))
    b.append(T(ecx + 50, ecy + 50, "eyes-open", 9.5, GREEN, "700"))
    b.append(T(ecx + 50, ecy + 64, "211 mm²", 9, GREEN, "400"))
    b.append(T(336, 400, "ML →", 9, MUTE))
    b.append(T(ecx + 6, 152, "AP", 9, MUTE))

    # metrics + Romberg + directives
    b.append(box(620, 78, 250, 372, PANEL, BORDER, 1.6, 12))
    b.append(T(636, 104, "What it reports", 12.5, NAVY, "700"))
    ms = ["95% sway-ellipse area (mm²)", "path length + mean velocity", "ML vs AP dominance",
          "trunk-sway RMS (IMU)", "fall-risk flags"]
    for j, m in enumerate(ms):
        b.append(T(636, 130 + j * 18, "• " + m, 9.5, SLATE))
    b.append(box(636, 228, 218, 60, "#ffffff", RED, 1.8, 8))
    b.append(T(745, 250, "Romberg = 3.6", 13, NAVY, "700", "middle"))
    b.append(T(745, 268, "eyes-closed ÷ eyes-open area", 8.5, MUTE, "400", "middle"))
    b.append(T(745, 281, ">2 → strong reliance on vision", 8.5, RED, "700", "middle"))
    b.append(T(636, 316, "→ device class:", 10.5, NAVY, "700"))
    for j, d in enumerate(["lateral-support insole / wider base",
                           "balance-training cues", "monitor trend over weeks"]):
        b.append(T(636, 336 + j * 17, "• " + d, 9.5, SLATE))
    b.append(T(636, 410, "A screening / training aid,", 9, MUTE))
    b.append(T(636, 424, "not a diagnosis.", 9, MUTE))
    b.append(T(24, 466, "Same ~$100 rig, second capability: what a clinical posturography plate measures — sway area, "
                        "velocity, Romberg — worn, all day.", 10.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Balance module detail: a standing figure with center-of-pressure sway, an eyes-open vs eyes-closed sway-ellipse comparison (211 vs 770 mm2), the Romberg quotient (3.6, vision-reliant), and the resulting device directives.",
                "Three panels: standing figure with COP trace, sway-ellipse comparison, and a metrics/Romberg/directives panel.")


def g_balance_positions():
    w, h = 900, 500
    b = [head(w, "Balance across positions — mCTSIB & beyond",
              "Label each stance; the module runs the standard sensory + stability protocols")]
    # ---- mCTSIB 2x2 grid ----
    b.append(box(24, 74, 430, 330, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "mCTSIB — which sense you rely on", 12.5, NAVY, "700"))
    b.append(T(190, 126, "FIRM ground", 10, MUTE, "700", "middle"))
    b.append(T(330, 126, "FOAM pad", 10, MUTE, "700", "middle"))
    b.append(T(58, 192, "eyes", 9, SLATE, "700", "middle") + T(58, 205, "OPEN", 9, SLATE, "700", "middle"))
    b.append(T(58, 300, "eyes", 9, SLATE, "700", "middle") + T(58, 313, "SHUT", 9, SLATE, "700", "middle"))
    for cx, cy, area, red in [(130, 145, 208, False), (270, 145, 614, False),
                              (130, 255, 471, False), (270, 255, 1640, True)]:
        cw, ch = 120, 92
        r = min(40, (area ** 0.5) * 0.9)
        b.append(box(cx, cy, cw, ch, REDBG if red else "#ffffff", RED if red else LINE, 1.8 if red else 1.3))
        b.append(f'<circle cx="{cx+cw/2:.0f}" cy="{cy+40}" r="{r:.0f}" fill="{RED if red else BLUE}" opacity="{0.35 if red else 0.22}"/>')
        b.append(T(cx + cw / 2, cy + 44, f"{area}", 11.5, NAVY, "700", "middle"))
        b.append(T(cx + cw / 2, cy + ch - 8, "mm²", 8, MUTE, "400", "middle"))
    b.append(T(40, 392, "↓ take away vision   → take away ground-feel   ◣ foam+shut = vestibular only", 8.5, MUTE))
    # ---- right: verdict + single-leg + LOS ----
    b.append(box(470, 74, 406, 330, "#ffffff", BORDER, 1.6, 12))
    b.append(T(486, 100, "Read-out (worked example)", 12.5, NAVY, "700"))
    for i, (lab, val, note, red) in enumerate([
            ("vision (shut/open, firm)", "×2.3", "vision-reliant", False),
            ("somatosensory (foam, open)", "×2.95", "leans on foot feel", False),
            ("vestibular (foam + shut)", "×7.9", "FAILURE MODE", True)]):
        y = 126 + i * 26
        b.append(T(486, y, lab, 9.5, SLATE))
        b.append(T(712, y, val, 11, RED if red else NAVY, "700", "end"))
        b.append(T(724, y, note, 8.5, RED if red else MUTE, "700" if red else "400"))
    b.append(T(486, 224, "Single-leg  L vs R", 10.5, NAVY, "700"))
    b.append(f'<rect x="486" y="232" width="{1260/1640*300:.0f}" height="15" rx="4" fill="{RED}"/>')
    b.append(T(486 + 1260 / 1640 * 300 + 6, 244, "L 1260", 9, RED, "700"))
    b.append(f'<rect x="486" y="252" width="{623/1640*300:.0f}" height="15" rx="4" fill="{GREEN}"/>')
    b.append(T(486 + 623 / 1640 * 300 + 6, 264, "R 623", 9, GREEN, "700"))
    b.append(T(486, 286, "51% asymmetry — left weaker → train it", 9.5, SLATE))
    b.append(T(486, 320, "Limits of Stability (lean)", 10.5, NAVY, "700"))
    ccx, ccy, k = 545, 360, 0.28
    for dx, dy, mm, lab in [(0, -104, 104, "fwd"), (0, 49, 49, "back"), (-15, 0, 15, "L"), (15, 0, 15, "R")]:
        b.append(f'<line x1="{ccx}" y1="{ccy}" x2="{ccx+dx*k:.0f}" y2="{ccy+dy*k:.0f}" stroke="{BLUE}" stroke-width="3"/>')
    b.append(f'<circle cx="{ccx}" cy="{ccy}" r="2.5" fill="{NAVY}"/>')
    b.append(T(ccx + 12, ccy - 22, "fwd 104", 8.5, MUTE) + T(ccx + 12, ccy + 16, "back 49", 8.5, MUTE)
             + T(ccx + 12, ccy + 2, "L/R 15", 8.5, MUTE))
    b.append(T(660, 356, "A/P > M/L (foot is longer than", 9, MUTE) + T(660, 369, "wide) — compare within an axis.", 9, MUTE))
    b.append(T(24, 430, "Read: vision-reliant, and foam + eyes-shut is the failure mode → a vestibular contribution "
                        "and real fall risk; left leg weaker.", 10.5, RED, "700"))
    b.append(T(24, 452, "Same ~$100 rig, same 8 sensors — now a full sensory-organization + stability screen.", 10, MUTE))
    return wrap(w, h, "\n".join(b),
                "Balance across positions: an mCTSIB 2x2 grid (firm/foam x eyes open/closed) with sway values, sensory-reliance ratios (vision x2.3, somatosensory x2.95, vestibular x7.9 = failure mode), single-leg L-vs-R asymmetry, and a limits-of-stability lean diagram.",
                "Left: mCTSIB 2x2 grid of sway. Right: sensory ratios, single-leg bars, and an LOS reach cross.")


def g_balance_assist():
    w, h = 900, 470
    b = [head(w, "Balance-assist ecosystem — sense → decide → assist",
              "The insole senses; it closes the loop with devices people already use")]
    for x, lab in [(140, "SENSE"), (460, "DECIDE"), (770, "ASSIST")]:
        b.append(T(x, 92, lab, 12, MUTE, "700", "middle"))

    def node(x, y, ww, hh, title, note, fill, stroke):
        return (box(x, y, ww, hh, fill, stroke, 1.6, 9) +
                T(x + 12, y + 22, title, 11, NAVY, "700") +
                T(x + 12, y + 39, note, 8.5, MUTE))
    # SENSE
    S = [(108, "Insole (FSR + IMU)", "645 kPa · sway · Romberg", BLUEBG, BLUE),
         (180, "Apple Watch", "steadiness Low (42%)", GREENBG, GREEN),
         (252, "Smart walker", "handle load · 3 grabs", "#fff7ed", AMBER)]
    for y, t1, t2, f, s in S:
        b.append(node(34, y, 210, 58, t1, t2, f, s))
    # DECIDE
    b.append(node(370, 120, 190, 66, "Balance + fall-risk", "mCTSIB · single-leg · LOS", "#ffffff", NAVY))
    b.append(node(370, 210, 190, 66, "Freezing-of-gait", "Freeze Index (3-8/0.5-3 Hz)", REDBG, RED))
    # ASSIST
    A = [(108, "Parkinson's cue glasses", "lines + metronome @110", REDBG, RED),
         (180, "Smart walker", "adaptive brake + alert", "#fff7ed", AMBER),
         (252, "Haptic buzz", "pod / watch", PANEL2, LINE)]
    for y, t1, t2, f, s in A:
        b.append(node(656, y, 214, 58, t1, t2, f, s))
    # arrows: sense -> decide hub, decide -> assist
    for y in (137, 209, 281):
        b.append(f'<line x1="244" y1="{y}" x2="366" y2="{170 if y<230 else 243}" stroke="{MUTE}" stroke-width="1.5" marker-end="url(#ar)"/>')
    b.append(f'<line x1="560" y1="153" x2="652" y2="137" stroke="{MUTE}" stroke-width="1.5" marker-end="url(#ar)"/>')
    b.append(f'<line x1="560" y1="243" x2="652" y2="209" stroke="{RED}" stroke-width="1.8" marker-end="url(#arr)"/>')
    b.append(f'<line x1="560" y1="243" x2="652" y2="281" stroke="{MUTE}" stroke-width="1.5" marker-end="url(#ar)"/>')
    b.append(f'<line x1="465" y1="186" x2="465" y2="210" stroke="{MUTE}" stroke-width="1.4" marker-end="url(#ar)"/>')

    b.append(T(24, 360, "Worked example: 2 freezes → 10 cue events (lines + metronome + buzz); "
                        "walker 3 grabs → brake+alert; Apple steadiness Low corroborates the insole's fall-risk.", 10, SLATE))
    b.append(T(24, 384, "What's built = the algorithms + data contracts (cue-event / telemetry JSON). "
                        "The last hop is a thin BLE/serial transport the device defines.", 10, MUTE))
    b.append(T(24, 430, "Freezing-of-gait cueing and walker braking are assistive prototypes — not a medical device; pair with a clinician.",
               9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "A balance-assist ecosystem: SENSE (insole FSR+IMU, Apple Watch gait, smart-walker handle load) feeds DECIDE (balance/fall-risk + freezing-of-gait detection), which drives ASSIST (Parkinson's cueing glasses with lines/metronome, smart-walker adaptive brake + alert, haptic buzz).",
                "Three columns Sense/Decide/Assist with nodes and arrows; the freezing-of-gait path to the cue glasses is highlighted.")


def g_beam_balance():
    w, h = 900, 460
    b = [head(w, "Beam / athlete balance — the specialized case",
              "Elite balance isn't \"are you safe?\" but \"how clean was that?\" — ML control + the landing stick")]
    # LEFT: the beam, ML is everything
    b.append(box(24, 74, 268, 320, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "On the beam — ML is everything", 12, NAVY, "700"))
    b.append('<rect x="52" y="210" width="208" height="14" rx="3" fill="#cbb28a" stroke="#94a3b8"/>')
    b.append(T(156, 246, "beam — 10 cm wide", 9, MUTE, "400", "middle"))
    b.append(f'<ellipse cx="156" cy="205" rx="16" ry="30" fill="#dbe4ef" stroke="{LINE}"/>')  # foot along beam
    b.append(f'<circle cx="156" cy="205" r="4" fill="{NAVY}"/>')
    # ML arrows (vertical = off the sides)
    b.append(f'<line x1="156" y1="150" x2="156" y2="180" stroke="{RED}" stroke-width="2.4" marker-end="url(#arr)"/>')
    b.append(f'<line x1="156" y1="262" x2="156" y2="290" stroke="{RED}" stroke-width="2.4" marker-end="url(#arr)"/>')
    b.append(T(168, 140, "ML sway = fall off", 9.5, RED, "700"))
    # AP arrows (along beam = fine)
    b.append(f'<line x1="70" y1="330" x2="45" y2="330" stroke="{MUTE}" stroke-width="1.6" marker-end="url(#ar)"/>')
    b.append(f'<line x1="242" y1="330" x2="267" y2="330" stroke="{MUTE}" stroke-width="1.6" marker-end="url(#ar)"/>')
    b.append(T(156, 333, "AP = along the beam, fine", 9, MUTE, "400", "middle"))
    b.append(T(40, 372, "So we score ML sway, not total.", 9.5, SLATE))

    # MIDDLE: landing stick — two settle scatter plots
    b.append(box(304, 74, 268, 320, "#ffffff", BORDER, 1.6, 12))
    b.append(T(320, 100, "Landing \"stick\" — the signature score", 11.5, NAVY, "700"))
    # clean
    b.append(box(320, 116, 236, 120, GREENBG, GREEN, 1.4))
    b.append(f'<line x1="438" y1="130" x2="438" y2="220" stroke="{BORDER}"/><line x1="345" y1="176" x2="531" y2="176" stroke="{BORDER}"/>')
    for dx, dy in [(0, 0), (2, -1), (-1, 2), (1, 1), (-2, -1), (0, 2)]:
        b.append(f'<circle cx="{438+dx*3}" cy="{176+dy*3}" r="2.4" fill="{GREEN}"/>')
    b.append(T(440, 210, "COP settles at once", 8, MUTE, "400", "middle"))
    b.append(T(330, 132, "clean", 9.5, GREEN, "700"))
    b.append(T(546, 132, "STUCK 10.0", 11, GREEN, "700", "end"))
    # wobble
    b.append(box(320, 246, 236, 120, "#fff7ed", AMBER, 1.4))
    b.append(f'<line x1="438" y1="260" x2="438" y2="350" stroke="{BORDER}"/><line x1="345" y1="306" x2="531" y2="306" stroke="{BORDER}"/>')
    for dx, dy in [(0, 0), (6, -3), (-5, 4), (10, 2), (-8, -3), (14, 6), (3, -7), (-3, 8)]:
        b.append(f'<circle cx="{438+dx*3}" cy="{306+dy*3}" r="2.4" fill="{AMBER}"/>')
    for dx, dy in [(30, 2), (33, 5), (28, -2)]:                     # the step — a shifted cluster
        b.append(f'<circle cx="{438+dx*3}" cy="{306+dy*3}" r="2.4" fill="{RED}"/>')
    b.append(T(330, 262, "wobble", 9.5, AMBER, "700"))
    b.append(T(546, 262, "9.2 · step", 11, RED, "700", "end"))
    b.append(T(500, 330, "step →", 8, RED, "700", "end"))

    # RIGHT: what it scores
    b.append(box(584, 74, 292, 320, PANEL, BORDER, 1.6, 12))
    b.append(T(600, 100, "What it scores", 12, NAVY, "700"))
    b.append(T(600, 126, "Landing (judge-style deductions):", 9.5, NAVY, "700"))
    for i, s in enumerate(["settle time (COP speed < 25 mm/s)", "wobbles (~0.1 each)",
                           "a step / hop (~0.5)", "post-landing sway"]):
        b.append(T(610, 146 + i * 17, "• " + s, 9, SLATE))
    b.append(T(600, 232, "Static hold:", 9.5, NAVY, "700"))
    b.append(T(610, 250, "• ML sway 0.42 mm → elite grade", 9, SLATE))
    b.append(T(610, 267, "• 92% forefoot → relevé (on the ball)", 9, SLATE))
    b.append(T(600, 300, "Vision independence (athlete Romberg):", 9.5, NAVY, "700"))
    b.append(T(610, 318, "• low eyes-closed sway = elite (spotting)", 9, SLATE))
    b.append(T(600, 352, "Trend stick scores + ML sway across a season.", 9, MUTE))

    b.append(T(24, 424, "The niche: we own the foot-pressure + COP layer the camera can't see — sync each landing to "
                        "your video by timestamp. Not a medical device.", 9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Specialized beam/athlete balance: on a 10cm beam mediolateral sway is what makes you fall, so the module scores ML sway plus the landing 'stick' — a clean landing settles instantly (10.0), a wobbly one with a step scores 9.2. Also relevé forefoot load and an athlete Romberg where low eyes-closed sway is elite.",
                "Left: a beam with ML-sway arrows. Middle: clean vs wobbly landing COP scatter with stick scores. Right: what it scores.")


def g_landing_lab():
    w, h = 900, 470
    b = [head(w, "Landing lab — one sensor, three rubrics",
              "All land forefoot-first; the discipline decides what 'good' means")]
    cols = [
        (24, "Gymnastics", "the \"stick\"", GREEN, GREENBG, "9.8", "STUCK",
         "forefoot → heel → FREEZE", "reward: settle to stillness", "deduct: hop · step · wobble"),
        (312, "Figure skating", "edge check-out", BLUE, BLUEBG, "9.7", "EDGE",
         "ball · outside edge → GLIDE", "reward: 1-foot · edge · flow", "deduct: step-out · stumble · slam"),
        (600, "Dance / ballet", "soft roll", RED, REDBG, "9.9", "SOFT",
         "toe → ball → heel · quiet", "reward: soft impact · full roll", "deduct: heavy/loud · flat slap"),
    ]
    for x, name, sub, c, cbg, score, tag, pattern, rew, ded in cols:
        b.append(box(x, 74, 276, 356, cbg, c, 1.6, 12))
        b.append(T(x + 18, 100, name, 13, NAVY, "700"))
        b.append(T(x + 18, 117, sub, 10, c, "700"))
        b.append(f'<circle cx="{x+232}" cy="106" r="22" fill="{c}"/>')
        b.append(T(x + 232, 104, score, 12.5, "#ffffff", "700", "middle") + T(x + 232, 118, tag, 6.5, "#ffffff", "700", "middle"))
        cx, top, length, width = x + 120, 150, 120, 58
        b.append(footprint(cx, top, length, width, "#ffffff"))
        fx, fy = zone_xy(cx, top, length, width, 4)      # forefoot (met3)
        hx, hy = zone_xy(cx, top, length, width, 0)      # heel
        if name.startswith("Gym"):
            b.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="9" fill="{AMBER}" opacity="0.8"/>')
            b.append(f'<circle cx="{hx:.0f}" cy="{hy:.0f}" r="9" fill="{RED}" opacity="0.8"/>')
            b.append(f'<line x1="{fx:.0f}" y1="{fy+9:.0f}" x2="{hx:.0f}" y2="{hy-9:.0f}" stroke="{NAVY}" stroke-width="1.6" marker-end="url(#ar)"/>')
            b.append(T(hx + 14, hy + 3, "■ freeze", 8.5, NAVY, "700"))
        elif name.startswith("Fig"):
            lx, ly = zone_xy(cx, top, length, width, 5)  # met5 = lateral edge
            b.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="9" fill="{BLUE}" opacity="0.8"/>')
            b.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="7" fill="{BLUE}" opacity="0.55"/>')
            b.append(T(lx + 10, ly + 3, "outside edge", 8, BLUE, "700"))
            b.append(f'<line x1="{cx}" y1="{top+6}" x2="{cx}" y2="{top-16}" stroke="{BLUE}" stroke-width="2.2" marker-end="url(#ar)"/>')
            b.append(T(cx + 8, top - 8, "glide", 8.5, BLUE, "700"))
        else:
            b.append(f'<path d="M{fx:.0f} {fy-6:.0f} q26 40 {hx-fx:.0f} {hy-fy+12:.0f}" fill="none" stroke="{RED}" stroke-width="2.2" marker-end="url(#arr)"/>')
            b.append(T(fx + 10, fy - 8, "toe", 8, MUTE) + T(hx - 4, hy + 14, "heel", 8, MUTE))
        b.append(box(x + 18, 300, 240, 30, "#ffffff", c, 1.4))
        b.append(T(x + 30, 320, pattern, 9.5, NAVY, "700"))
        b.append(T(x + 18, 352, rew, 9, SLATE))
        b.append(T(x + 18, 369, ded, 9, MUTE))
    b.append(T(24, 404, "Gymnastics rewards stopping · skating rewards a gliding edge · dance rewards a soft roll — "
                        "same center-of-pressure data, three rubrics.", 10, SLATE))
    b.append(T(24, 452, "Sync each rep to your video by timestamp; the sensor adds the pressure layer the camera can't see. Not a medical device.",
               9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Landing lab: three disciplines scored from the same insole. Gymnastics 'stick' (forefoot to heel then freeze, 9.8), figure skating edge check-out (ball, outside edge, glide forward, 9.7), dance soft roll (toe-ball-heel, 9.9). Each has its own reward/deduct rubric.",
                "Three discipline columns with a footprint showing the landing pattern, a score badge, and the rubric.")


def g_zone_load():
    w, h = 900, 470
    b = [head(w, "Zone load vs the field — down to the 2nd metatarsal",
              "Which regions are over/under-used vs published norms for THIS movement; overload maps to injury")]
    XY10 = {"heel_med": (.35, .08), "heel_lat": (.65, .08), "midfoot": (.50, .45),
            "met1": (.30, .72), "met2": (.40, .74), "met3": (.50, .75), "met4": (.60, .74),
            "met5": (.70, .72), "hallux": (.26, .93), "toes": (.56, .96)}
    state = {"met2": "over", "met3": "over", "met4": "over", "hallux": "under", "toes": "under"}
    ratio = {"heel_med": 0.8, "heel_lat": 0.8, "midfoot": 0.8, "met1": 1.1, "met2": 1.3,
             "met3": 1.8, "met4": 2.2, "met5": 0.8, "hallux": 0.2, "toes": 0.5}
    b.append(box(24, 74, 300, 358, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "Your foot map — ballet relevé", 12, NAVY, "700"))
    cx, top, length, width = 168, 128, 268, 150
    b.append(footprint(cx, top, length, width))
    for z, (xn, yn) in XY10.items():
        sx = cx - width / 2 + xn * width; sy = top + (1 - yn) * length
        st = state.get(z)
        col = RED if st == "over" else BLUE if st == "under" else "#94a3b8"
        b.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="13" fill="{col}" opacity="{0.85 if st else 0.4}" stroke="#fff" stroke-width="1.3"/>')
        b.append(T(sx, sy + 3.5, f"{ratio[z]}×", 8, "#ffffff" if st else NAVY, "700", "middle"))
    b.append(T(40, 400, "● over-used  ● under-used  ● normal   ·   number = ×norm", 9, MUTE))
    b.append(T(40, 418, "met2 / met4 are interpolated from neighbors", 8.5, MUTE))

    # right: findings
    b.append(box(340, 74, 536, 358, "#ffffff", BORDER, 1.6, 12))
    b.append(T(356, 100, "Vs the ballet-relevé norm (cited)", 12.5, NAVY, "700"))
    b.append(T(356, 124, "🔴 Over-used:", 10.5, RED, "700"))
    b.append(T(460, 124, "met4 2.2× · met3 1.8× · met2 1.3× (interp)", 10, SLATE))
    b.append(T(356, 144, "🔵 Under-used:", 10.5, BLUE, "700"))
    b.append(T(460, 144, "hallux 0.2× · toes 0.5×", 10, SLATE))
    b.append(box(356, 158, 504, 62, REDBG, RED, 1.6, 8))
    b.append(T(370, 180, "⚠ 2nd-met overload + hallux off-loaded = the published 1st-MTP-pain pattern", 10, NAVY, "700"))
    b.append(T(370, 197, "→ the \"dancer's fracture\" route (base of 2nd met). Cue big-toe engagement,", 9.5, SLATE))
    b.append(T(370, 211, "check the 1st ray.", 9.5, SLATE))
    b.append(T(356, 246, "Published peak landing force (× body weight):", 10.5, NAVY, "700"))
    for i, (sport, val, conf) in enumerate([("Gymnastics landing", "7.1–15.8", "published"),
                                            ("Figure-skating (1-leg)", "5–8", "published"),
                                            ("Running", "2.5–3", "estimated"),
                                            ("Ballet jump", "1–2", "estimated")]):
        y = 266 + i * 18
        b.append(T(370, y, "• " + sport, 9.5, SLATE))
        b.append(T(720, y, val + " ×BW", 9.5, NAVY, "700", "end"))
        b.append(T(730, y, conf, 8, MUTE if conf == "published" else AMBER))
    b.append(T(356, 350, "Confidence flagged per value (published / published-order / estimated);", 9, MUTE))
    b.append(T(356, 365, "the DB tightens as sources + our own captures are added.", 9, MUTE))
    b.append(T(356, 392, "Sources: gymnastics Front. Sports 2025 · skating ACSM · running PMC5112690 ·", 8.5, MUTE))
    b.append(T(356, 405, "ballet Children 2022 · 2nd-met injury Physiopedia (refs/plantar_norms.json).", 8.5, MUTE))
    b.append(T(24, 452, "Rubrics get specific: per-zone load vs the field's research, overload → the injury it predicts. Not a medical device.",
               9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Zone-load vs the field: a foot map of a ballet relevé showing the 2nd/3rd/4th metatarsals over-used (1.3-2.2x the published norm) and the hallux/toes under-used (0.2-0.5x) — the published 1st-MTP-pain pattern that routes to a 2nd-metatarsal 'dancer's fracture'. Plus published peak landing forces per sport in body weights.",
                "Left: footprint with 10 zones colored over/under/normal vs norm. Right: findings, injury note, and published force ranges.")


def g_chain():
    w, h = 900, 480
    b = [head(w, "Kinetic chain — it's all connected to the foot",
              "A foot-loading signature is the input; the injury often shows up up the chain")]
    # LEFT: leg with injury sites
    b.append(box(24, 74, 250, 372, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "Where it shows up", 12, NAVY, "700"))
    lx = 120
    b.append(f'<rect x="{lx-22}" y="120" width="44" height="86" rx="14" fill="#cbd5e1"/>')   # thigh
    b.append(f'<circle cx="{lx}" cy="212" r="15" fill="#b6c2d4"/>')                            # knee
    b.append(f'<rect x="{lx-16}" y="224" width="32" height="82" rx="12" fill="#cbd5e1"/>')     # shin
    b.append(f'<circle cx="{lx}" cy="312" r="12" fill="#b6c2d4"/>')                            # ankle
    b.append(f'<rect x="{lx-14}" y="318" width="74" height="18" rx="8" fill="#cbd5e1"/>')      # foot
    def site(y, cyc, lab, col):
        return (f'<circle cx="{lx+ (22 if cyc else 0)}" cy="{y}" r="4.5" fill="{col}"/>' +
                f'<line x1="{lx+(26 if cyc else 4)}" y1="{y}" x2="176" y2="{y}" stroke="{col}" stroke-width="1.2"/>' +
                T(180, y + 3, lab, 8.5, NAVY, "700"))
    b.append(site(150, True, "hamstring", RED))
    b.append(T(180, 163, "(sprint late-swing)", 7.5, MUTE))
    b.append(site(212, False, "ACL", RED))
    b.append(T(180, 225, "(landing / cut)", 7.5, MUTE))
    b.append(site(262, False, "shin splints (MTSS)", BLUE))
    b.append(site(312, False, "ankle sprain", BLUE))
    b.append(site(330, False, "2nd-met stress fx · PF", AMBER))
    b.append(T(40, 400, "Foot marker positions are anatomical", 8.5, MUTE))
    b.append(T(40, 415, "(mm on your foot, e.g. met2 ≈ 38×189).", 8.5, MUTE))

    # RIGHT: signature -> chain rows
    b.append(box(290, 74, 586, 372, "#ffffff", BORDER, 1.6, 12))
    b.append(T(306, 100, "Foot-loading signature → chain injury", 12.5, NAVY, "700"))
    rows = [
        ("High vGRF + loading rate (stiff landing)", "ACL · tibial bone stress", "jump / gym", RED, REDBG),
        ("L/R asymmetry > 10–15%", "non-contact ACL · hamstring", "soccer cut", RED, REDBG),
        ("Over-stride: foot lands ahead in sprint", "HAMSTRING (late-swing eccentric)", "soccer sprint", AMBER, "#fff7ed"),
        ("Medial collapse / overpronation", "shin splints (MTSS) · PF · knee valgus → ACL", "runner", BLUE, BLUEBG),
        ("Lateral overload / supination", "ankle sprain · 5th-met (Jones) · IT band", "cutter", BLUE, BLUEBG),
    ]
    y = 118
    for sig, inj, sport, c, cbg in rows:
        b.append(box(306, y, 554, 52, cbg, c, 1.3, 8))
        b.append(T(320, y + 20, sig, 10, NAVY, "700"))
        b.append(f'<text x="500" y="{y+20}" font-size="11" fill="{MUTE}">→</text>')
        b.append(T(320, y + 39, inj, 9.5, c, "700"))
        b.append(T(848, y + 20, sport, 8.5, MUTE, "400", "end"))
        y += 60
    b.append(T(24, 466, "Rubrics can flag proximal injuries from the foot signature — and video→force (cited pose→GRF) "
                        "estimates the load even without a sensor. Not a medical device.", 9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Kinetic-chain injury map: foot-loading signatures map to injuries up the chain — high vGRF/loading rate -> ACL and tibial stress; L/R asymmetry >10-15% -> non-contact ACL and hamstring; overstride in sprint -> hamstring; medial collapse -> shin splints/plantar fasciitis/knee valgus; lateral overload -> ankle sprain/5th met/IT band. Foot markers are anatomical (mm).",
                "Left: a leg with injury sites (hamstring, ACL, shin, ankle, foot). Right: five foot-signature -> chain-injury rows with the sport.")


def g_pressure_atlas():
    w, h = 900, 490
    b = [head(w, "Plantar pressure atlas — real kPa (bottom of the foot)",
              "Published peak pressures per foot region; the engine compares you to these, not guesses")]
    # LEFT: footprint with walking peak kPa, colored by magnitude
    kpa = {"heel_med": 264, "heel_lat": 230, "midfoot": 110, "met1": 248, "met2": 246,
           "met3": 225, "met4": 180, "met5": 150, "hallux": 280, "toes": 170}
    XY10 = {"heel_med": (.35, .08), "heel_lat": (.65, .08), "midfoot": (.50, .45),
            "met1": (.30, .72), "met2": (.40, .74), "met3": (.50, .75), "met4": (.60, .74),
            "met5": (.70, .72), "hallux": (.26, .93), "toes": (.56, .96)}
    def pcol(v):
        return RED if v >= 250 else AMBER if v >= 180 else BLUE
    b.append(box(24, 74, 300, 372, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "Barefoot walking — peak kPa", 12, NAVY, "700"))
    cx, top, length, width = 172, 130, 280, 150
    b.append(footprint(cx, top, length, width))
    for z, (xn, yn) in XY10.items():
        sx = cx - width / 2 + xn * width; sy = top + (1 - yn) * length
        c = pcol(kpa[z])
        b.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="14" fill="{c}" opacity="0.85" stroke="#fff" stroke-width="1.3"/>')
        b.append(T(sx, sy + 3.5, f"{kpa[z]}", 8, "#ffffff", "700", "middle"))
    b.append(T(40, 420, "● ≥250  ● 180–249  ● <180 kPa  ·  hallux 280 & heel 264 lead", 9, MUTE))
    b.append(T(40, 435, "(healthy adults; hallux/heel/met1–3 published)", 8.5, MUTE))

    # RIGHT: peak central-forefoot pressure by activity + thresholds
    b.append(box(340, 74, 536, 372, "#ffffff", BORDER, 1.6, 12))
    b.append(T(356, 100, "Peak central-forefoot pressure by activity", 12, NAVY, "700"))
    bx0, bw, scale = 356, 420, 420 / 850.0        # 0..850 kPa
    acts = [("Standing", 53, MUTE), ("Walking", 246, BLUE), ("Running", 313, AMBER),
            ("Basketball land", 403, RED), ("Basketball hallux", 794, RED)]
    for i, (lab, v, c) in enumerate(acts):
        y = 128 + i * 42
        b.append(T(bx0, y - 2, lab, 9.5, NAVY, "700"))
        b.append(box(bx0, y + 4, bw, 16, PANEL, BORDER, 1, 4))
        b.append(f'<rect x="{bx0}" y="{y+4}" width="{v*scale:.0f}" height="16" rx="4" fill="{c}"/>')
        b.append(T(bx0 + v * scale + 6, y + 16, f"{v} kPa", 9, NAVY, "700"))
    # threshold lines
    for thr, lab, col in [(200, "200 in-shoe", "#0f172a"), (450, "450 barefoot", "#7c2d12"), (750, "750", "#7c2d12")]:
        x = bx0 + thr * scale
        b.append(f'<line x1="{x:.0f}" y1="120" x2="{x:.0f}" y2="336" stroke="{col}" stroke-width="1" stroke-dasharray="3 3"/>')
        b.append(T(x, 350, lab, 7.5, col, "700", "middle"))
    b.append(T(356, 372, "Dashed = diabetic/neuropathic-tissue ulcer thresholds (200 kPa in-shoe;", 8.5, MUTE))
    b.append(T(356, 385, "450/750 barefoot). Healthy athletes routinely exceed them transiently —", 8.5, MUTE))
    b.append(T(356, 398, "e.g. basketball-landing hallux ~794 kPa. Context matters, not a hard cap.", 8.5, MUTE))
    b.append(T(356, 424, "Sources: walking PMC2902454 · standing Cavanagh · running PMC5112690 ·", 8, MUTE))
    b.append(T(356, 436, "basketball LER · thresholds PMC10882031 (refs/plantar_norms.json).", 8, MUTE))
    b.append(T(24, 470, "Every number is confidence-flagged (published / estimated) and gets more rigid as sources + our own captures are added.",
               9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Plantar pressure atlas: a footprint labeled with published barefoot-walking peak pressures per zone (hallux 280, heel 264, met1 248, met2 246, met3 225 kPa) and a bar chart of peak central-forefoot pressure by activity (standing 53, walking 246, running 313, basketball landing 403, basketball hallux 794 kPa) against the 200/450/750 kPa clinical thresholds.",
                "Left: footprint with per-zone kPa colored by magnitude. Right: peak pressure by activity vs ulcer thresholds.")


def g_conditions():
    w, h = 900, 470
    b = [head(w, "Condition-aware — adaptive gait isn't an injury flag",
              "Heel pain, toe-walking, equinus: the engine uses YOUR baseline, then flags the real risk")]
    b.append(box(24, 74, 320, 360, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "Load shift — normal vs toe-walking", 11.5, NAVY, "700"))
    def gbar(y, lab, normal, itw):
        s = [T(40, y - 4, lab, 10, NAVY, "700")]
        s.append(T(48, y + 17, "normal", 8.5, MUTE))
        s.append(box(112, y + 7, 170, 13, PANEL2, BORDER, 1, 4))
        s.append(f'<rect x="112" y="{y+7}" width="{normal/70*170:.0f}" height="13" rx="4" fill="{BLUE}"/>')
        s.append(T(112 + normal / 70 * 170 + 5, y + 17, f"{normal}%", 8.5, NAVY, "700"))
        s.append(T(48, y + 40, "toe-walk", 8.5, MUTE))
        s.append(box(112, y + 30, 170, 13, PANEL2, BORDER, 1, 4))
        s.append(f'<rect x="112" y="{y+30}" width="{itw/70*170:.0f}" height="13" rx="4" fill="{RED}"/>')
        s.append(T(112 + itw / 70 * 170 + 5, y + 40, f"{itw}%", 8.5, RED, "700"))
        return "".join(s)
    b.append(gbar(140, "Forefoot load", 39, 62))
    b.append(gbar(216, "Hindfoot (heel) load", 30, 23))
    b.append(T(40, 300, "Toe-walking shifts load FORWARD.", 10, NAVY, "700"))
    b.append(T(40, 318, "ITW published: forefoot 61.7 / midfoot 15.3 /", 8.5, MUTE))
    b.append(T(40, 330, "hindfoot 22.8% (vs normal ~39 / – / 30).", 8.5, MUTE))
    b.append(T(40, 358, "So low heel loading is this person's NORM.", 9.5, SLATE))
    b.append(T(40, 374, "The engine won't call it a deficit — it", 9.5, SLATE))
    b.append(T(40, 388, "tracks forefoot-overload TRENDS + calf /", 9.5, SLATE))
    b.append(T(40, 402, "ankle dorsiflexion instead.", 9.5, SLATE))

    b.append(box(360, 74, 516, 360, "#ffffff", BORDER, 1.6, 12))
    b.append(T(376, 100, "Conditions the engine now knows", 12, NAVY, "700"))
    conds = [
        ("Plantar fasciitis (medial heel pain)", "altered medial-heel pressure + forefoot overstrain; first-step AM pain",
         "engine → watch heel_med; offload + restore dorsiflexion", AMBER),
        ("Toe-walking (adaptive)", "forefoot 62% / heel 23% — pain-avoidant / sensory / retained",
         "engine → heel under-use = EXPECTED, not a flag; watch met overload + calf", RED),
        ("Equinus (< 10° dorsiflexion)", "forefoot peak 677.8 vs 565.6 kPa; premature heel rise",
         "engine → forefoot overload = metatarsalgia / met stress / PF", RED),
    ]
    y = 118
    for title, sig, eng, c in conds:
        b.append(box(376, y, 484, 90, PANEL, c, 1.4, 8))
        b.append(T(390, y + 22, title, 10.5, NAVY, "700"))
        b.append(T(390, y + 42, sig, 9, SLATE))
        b.append(T(390, y + 66, eng, 9.5, c, "700"))
        y += 100
    b.append(T(24, 452, "Adaptive ≠ injury. Management is person-specific: hypermobile → LOAD / strengthen, don't over-stretch a lax system. Not medical advice.",
               9.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "Condition-aware analysis: toe-walking shifts load forward (forefoot 39%->62%, heel 30%->23% per published ITW data), so the engine treats low heel loading as the adaptive baseline, not a deficit, and instead flags forefoot overload + calf tightness. Plus plantar-fasciitis (medial heel) and equinus (forefoot 677.8 kPa) condition profiles. Management is person-specific (hypermobile -> load not stretch).",
                "Left: normal-vs-toe-walking forefoot/hindfoot load bars. Right: three condition cards with the engine's condition-aware response.")


def g_footwear():
    w, h = 900, 460
    b = [head(w, "Heel lifts & pressure-time integral — designing the fix",
              "Offloading a painful heel can overload the forefoot; and cumulative dose (PTI) matters, not just peak")]
    # LEFT: the heel-lift trade-off
    b.append(box(24, 74, 400, 360, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "The heel-lift trade-off", 12, NAVY, "700"))
    # foot side-view + wedge
    b.append('<rect x="70" y="180" width="200" height="22" rx="10" fill="#e6ebf2" stroke="#94a3b8"/>')
    b.append(f'<polygon points="70,202 150,202 70,226" fill="{AMBER}" stroke="#94a3b8"/>')
    b.append(T(78, 244, "heel lift", 8.5, "#7c2d12", "700"))
    b.append(f'<line x1="105" y1="150" x2="105" y2="176" stroke="{BLUE}" stroke-width="2.6" marker-end="url(#ar)"/>')
    b.append(T(50, 146, "heel pressure ↓", 9, BLUE, "700"))
    b.append(T(50, 158, "offloads the pain", 7.5, MUTE))
    b.append(f'<line x1="235" y1="176" x2="235" y2="150" stroke="{RED}" stroke-width="2.6" marker-end="url(#arr)"/>')
    b.append(T(284, 165, "forefoot pressure ↑", 9, RED, "700"))
    b.append(T(284, 177, "+ PTI · met overload", 7.5, MUTE))
    b.append(T(40, 278, "A lift ALONE trades heel pain for metatarsalgia —", 9.5, NAVY, "700"))
    b.append(T(40, 292, "worse if you already toe-walk / have equinus.", 9.5, SLATE))
    b.append(box(40, 306, 368, 110, "#ffffff", GREEN, 1.6, 8))
    b.append(T(54, 328, "✓ The design rule", 11, GREEN, "700"))
    b.append(T(54, 348, "Do BOTH: heel offload/cushion + forefoot cushion", 9.5, SLATE))
    b.append(T(54, 363, "(met pad) + preserved arch — not a lift alone.", 9.5, SLATE))
    b.append(T(54, 383, "Softer lift (PORON ~15 Shore) beats a hard flat one.", 9.5, SLATE))
    b.append(T(54, 401, "Hypermobile → LOAD the calf/plantar, don't just stretch.", 9.5, NAVY, "700"))

    # RIGHT: peak vs PTI
    b.append(box(440, 74, 436, 360, "#ffffff", BORDER, 1.6, 12))
    b.append(T(456, 100, "Peak vs pressure-time integral (PTI)", 12, NAVY, "700"))
    b.append(T(456, 122, "Peak = highest pressure · PTI = cumulative dose over time", 9, MUTE))
    def pbars(y, act, peak, pti):
        s = [T(456, y, act, 10, NAVY, "700")]
        s.append(T(466, y + 20, "peak", 8.5, RED))
        s.append(box(520, y + 10, 300, 13, PANEL2, BORDER, 1, 4))
        s.append(f'<rect x="520" y="{y+10}" width="{peak/100*300:.0f}" height="13" rx="4" fill="{RED}"/>')
        s.append(T(466, y + 42, "PTI", 8.5, BLUE))
        s.append(box(520, y + 32, 300, 13, PANEL2, BORDER, 1, 4))
        s.append(f'<rect x="520" y="{y+32}" width="{pti/100*300:.0f}" height="13" rx="4" fill="{BLUE}"/>')
        return "".join(s)
    b.append(pbars(148, "Running (brief, hard)", 95, 40))
    b.append(pbars(214, "Walking", 60, 65))
    b.append(pbars(280, "Standing (long, soft)", 20, 90))
    b.append(T(456, 344, "Running has the HIGHEST peak but a LOWER PTI (short", 9, SLATE))
    b.append(T(456, 358, "contact); standing is the reverse. A brief hard hit and a", 9, SLATE))
    b.append(T(456, 372, "long sustained load injure differently — track both.", 9, SLATE))
    b.append(T(456, 396, "PTI is the better overuse/tissue predictor (met2 ~38.4 kPa·s).", 9, NAVY, "700"))
    b.append(T(456, 410, "interpret.py's per-zone impulse IS the calibrated PTI.", 8.5, MUTE))
    b.append(T(24, 448, "Sources: heel lifts PubMed 24440428 · PTI PMC11336220 · cutting J Biomech 2014 (refs/plantar_norms.json). Not medical advice.",
               9, MUTE))
    return wrap(w, h, "\n".join(b),
                "Heel lifts attenuate heel peak pressure but raise forefoot pressure and PTI, so a lift alone trades heel pain for metatarsalgia — the design rule is heel offload PLUS forefoot cushion plus preserved arch (softer lift; hypermobile load not stretch). And peak vs pressure-time integral: running has the highest peak but lower PTI, standing the reverse; PTI is the better overuse predictor.",
                "Left: heel-lift trade-off with a side-view foot + wedge and the design rule. Right: peak-vs-PTI bars for running/walking/standing.")


def g_bounce():
    w, h = 900, 440
    b = [head(w, "The hidden forefoot dose — leg-bounce / toe-tap",
              "Repetitive forefoot loading at ~2.8 Hz that no step-counter or gait lab counts")]
    # LEFT: cycles/day comparison
    b.append(box(24, 74, 470, 330, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "Forefoot loading cycles per day", 12, NAVY, "700"))
    scale = 400 / 45000.0
    for i, (lab, v, c, sub) in enumerate([
            ("Walking (a day's steps)", 7000, BLUE, "~7,000 steps"),
            ("Leg-bounce (4 h @ 2.8 Hz)", 40320, RED, "≈ 5.8× your walking")]):
        y = 140 + i * 80
        b.append(T(40, y, lab, 10.5, NAVY, "700"))
        b.append(box(40, y + 10, 400, 26, "#ffffff", BORDER, 1, 6))
        b.append(f'<rect x="40" y="{y+10}" width="{v*scale:.0f}" height="26" rx="6" fill="{c}"/>')
        b.append(T(40 + v * scale + 8, y + 28, f"{v:,}", 11, NAVY, "700"))
        b.append(T(44, y + 52, sub, 8.5, MUTE))
    b.append(T(40, 320, "Bouncing a few hours can out-load a full day of walking —", 9.5, NAVY, "700"))
    b.append(T(40, 335, "on the ball of the foot, the spot that's already overloaded", 9.5, SLATE))
    b.append(T(40, 349, "in toe-walking / equinus. And it never registers as \"activity.\"", 9.5, SLATE))
    b.append(T(40, 378, "analysis/bounce.py detects the ~2.8 Hz bounce, counts cycles,", 8.5, MUTE))
    b.append(T(40, 391, "and integrates forefoot pressure-time (the dose peak misses).", 8.5, MUTE))

    # RIGHT: concept + framing
    b.append(box(510, 74, 366, 330, "#ffffff", BORDER, 1.6, 12))
    b.append(T(526, 100, "~2.8 Hz forefoot loading", 12, NAVY, "700"))
    # waveform
    pts = " ".join(f"{526 + x*3.1:.0f},{140 - 16*math.sin(x*0.9):.0f}" for x in range(0, 108))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{RED}" stroke-width="2"/>')
    b.append(T(526, 172, "each bump = one load on the ball of the foot", 8.5, MUTE))
    b.append(T(526, 202, "Your total forefoot exposure:", 10.5, NAVY, "700"))
    b.append(box(526, 212, 334, 26, BLUEBG, BLUE, 1.2, 5))
    b.append(T(536, 229, "gait steps", 9, BLUE, "700"))
    b.append('<text x="640" y="229" font-size="11" fill="#64748b">+</text>')
    b.append(box(660, 212, 200, 26, REDBG, RED, 1.2, 5))
    b.append(T(670, 229, "at-rest bounce dose", 9, RED, "700"))
    b.append(T(526, 256, "= what the ball of your foot actually sees all day.", 9, SLATE))
    b.append(box(526, 274, 334, 116, GREENBG, GREEN, 1.6, 8))
    b.append(T(540, 296, "✓ Dose it, don't suppress it", 11, GREEN, "700"))
    b.append(T(540, 316, "Leg-bounce is a self-regulating / stim movement", 9.5, SLATE))
    b.append(T(540, 330, "(ADHD / autism / anxiety) — it's not the enemy.", 9.5, SLATE))
    b.append(T(540, 350, "Protect the forefoot while you do it (soft met pad,", 9.5, SLATE))
    b.append(T(540, 364, "cushion), take ball-of-foot rest windows, vary the", 9.5, SLATE))
    b.append(T(540, 378, "pattern. Measure it so you can manage it.", 9.5, NAVY, "700"))
    b.append(T(24, 428, "Sources: seated foot load (seating clinical) · toe-tap 2.8 Hz PMC12819309 · PTI PMC11336220. Not medical advice.",
               9, MUTE))
    return wrap(w, h, "\n".join(b),
                "The hidden forefoot dose of leg-bouncing: at ~2.8 Hz for 4 hours a day that is ~40,320 forefoot loading cycles, about 5.8x a typical day's 7,000 walking steps, and invisible to step counters. It stacks onto gait on the ball of the foot. bounce.py detects the bounce and integrates the forefoot pressure-time dose. Framed as a self-regulating movement to dose, not suppress.",
                "Left: bars of forefoot loading cycles per day (walking 7,000 vs leg-bounce 40,320). Right: the 2.8 Hz waveform, gait+bounce stacking, and a dose-don't-suppress framing.")


def g_lab_scope():
    w, h = 900, 500
    b = [head(w, "Personal-lab scope — catching up to the papers' equipment",
              "What the cited studies used vs what we can 3D-print / DIY — and the honest gaps")]
    cols = [(40, "Measurement"), (196, "The papers use ($$$)"), (452, "Our DIY build (3D-print + buy)"), (742, "Match?")]
    for x, lab in cols:
        b.append(T(x, 104, lab, 9.5, MUTE, "700"))
    b.append(f'<line x1="24" y1="112" x2="876" y2="112" stroke="{BORDER}"/>')
    rows = [
        ("In-shoe pressure", "pedar / F-Scan (capacitive,\nRMSE 2.6 kPa · $10–30k)", "FSR insole (have) + calib.py\npower-law — resistive, drifts", "PARTIAL", AMBER, "r≈0.87"),
        ("Full-foot pressure map", "emed / MatScan platform\n(1.4–2 sensors/cm²)", "3D-print frame + Velostat +\ncopper-tape matrix (~$40)", "PARTIAL", AMBER, "coarse map"),
        ("Vertical GRF (× BW)", "AMTI / Kistler force plate\n($5–30k)", "4× load cell + HX711 +\nprinted plate (~$80)", "YES", GREEN, "ICC>0.94"),
        ("Shear / 6-axis", "tri-axial transducers,\n6-axis plates (custom)", "— no maker-grade option\n(shear is hard)", "GAP", RED, "can't (yet)"),
        ("GRF from motion", "Vicon marker mocap\n($$$, lab)", "phone + pose AI →\nvideo_force.py (free)", "YES", GREEN, "2D"),
        ("Calibration", "materials tester /\nreference loads", "known weights →\ncalibrate.py", "YES", GREEN, "R²=1.0 demo"),
    ]
    y = 124
    for meas, papers, diy, verdict, c, note in rows:
        b.append(box(24, y, 852, 56, PANEL if (y // 56) % 2 else "#ffffff", BORDER, 1, 6))
        b.append(T(40, y + 22, meas, 10, NAVY, "700"))
        for j, line in enumerate(papers.split("\n")):
            b.append(T(196, y + 20 + j * 14, line, 8.5, SLATE))
        for j, line in enumerate(diy.split("\n")):
            b.append(T(452, y + 20 + j * 14, line, 8.5, SLATE))
        b.append(f'<rect x="742" y="{y+14}" width="66" height="20" rx="10" fill="{c}"/>')
        b.append(T(775, y + 28, verdict, 8.5, "#ffffff", "700", "middle"))
        b.append(T(742, y + 48, note, 8, MUTE))
        y += 60
    b.append(T(24, 476, "The H2D prints every frame/enclosure. ~$150–250 of parts → trend-level versions of 4 of 6; SHEAR + lab-grade accuracy stay out of reach.",
               9.5, NAVY, "700"))
    b.append(T(24, 492, "That's the whole ethos: r≈0.87, not 1.0 — a ~$250 lab that does what a ~$30k one does at trend level. Sources in refs/plantar_norms.json + lab_scope.md.",
               9, MUTE))
    return wrap(w, h, "\n".join(b),
                "Personal-lab equipment scope: in-shoe pressure (papers: pedar capacitive RMSE 2.6 kPa $10-30k; us: FSR insole r0.87 PARTIAL), full-foot pressure map (emed/MatScan 1.4-2 sensors/cm2; us: 3D-printed Velostat copper-matrix mat ~$40 PARTIAL), vertical GRF (AMTI/Kistler $5-30k; us: 4 load cells + HX711 + printed plate ~$80, ICC>0.94 YES), shear/6-axis (tri-axial transducers; us: GAP, can't DIY), GRF from motion (Vicon; us: phone pose AI free YES), calibration (us: known weights YES). ~$150-250 of parts + the H2D gets trend-level versions of 4 of 6.",
                "A scope table: measurement, what the papers use, our DIY build, and whether we can match (partial/yes/gap).")


def g_nerve_fascia():
    w, h = 900, 520
    b = [head(w, "From foot pressure → nerve & fascia impact",
              "CPTS (the all-day dose) + the pressure gradient → which nerves & fascia your loading overloads")]
    # ---- LEFT: foot map with structures ----
    b.append(box(24, 74, 300, 410, PANEL, BORDER, 1.6, 12))
    b.append(T(40, 100, "Where the load lands", 12.5, NAVY, "700"))
    cx, top, length, width = 176, 120, 290, 150
    b.append(footprint(cx, top, length, width, "#e7edf4"))

    def zx(i):
        return zone_xy(cx, top, length, width, i)
    hm = zx(0); m1 = zx(3); m3 = zx(4); m5 = zx(5)
    # plantar fascia band (heel -> forefoot), amber, translucent
    b.append(f'<path d="M{hm[0]-6:.0f} {hm[1]-4:.0f} L{m1[0]-4:.0f} {m1[1]+6:.0f} '
             f'L{m5[0]+4:.0f} {m5[1]+6:.0f} L{hm[0]+10:.0f} {hm[1]-2:.0f} Z" '
             f'fill="{AMBER}" opacity="0.22" stroke="{AMBER}" stroke-width="1.2"/>')
    b.append(T(cx + 40, (hm[1]+m3[1])/2, "plantar fascia", 8.5, "#b45309", "700"))
    b.append(T(cx + 44, (hm[1]+m3[1])/2 + 12, "(tension · windlass)", 7.5, MUTE))
    # Morton interdigital markers at met2/met3/met4 interspaces
    for (px, py) in [((m1[0]+m3[0])/2, (m1[1]+m3[1])/2), (m3[0], m3[1]), ((m3[0]+m5[0])/2, (m3[1]+m5[1])/2)]:
        b.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="6.5" fill="{BLUE}" opacity="0.85" stroke="#fff" stroke-width="1.2"/>')
    b.append(f'<line x1="{m5[0]+8:.0f}" y1="{m3[1]:.0f}" x2="266" y2="176" stroke="{BLUE}" stroke-width="1.2"/>')
    b.append(T(268, 172, "Morton /", 8.5, BLUE, "700") + T(268, 183, "interdigital n.", 8.5, BLUE, "700"))
    # Baxter at medial heel
    b.append(f'<circle cx="{hm[0]-8:.0f}" cy="{hm[1]:.0f}" r="6.5" fill="{RED}" opacity="0.9" stroke="#fff" stroke-width="1.2"/>')
    b.append(f'<line x1="{hm[0]-14:.0f}" y1="{hm[1]:.0f}" x2="70" y2="404" stroke="{RED}" stroke-width="1.2"/>')
    b.append(T(40, 400, "Baxter's n.", 8.5, RED, "700") + T(40, 411, "(medial heel)", 7.5, MUTE))
    # tibial at medial arch
    mid = zone_xy(cx, top, length, width, 2)
    b.append(f'<circle cx="{mid[0]-24:.0f}" cy="{mid[1]:.0f}" r="6.5" fill="{GREEN}" opacity="0.85" stroke="#fff" stroke-width="1.2"/>')
    b.append(f'<line x1="{mid[0]-30:.0f}" y1="{mid[1]:.0f}" x2="60" y2="300" stroke="{GREEN}" stroke-width="1.2"/>')
    b.append(T(40, 296, "post. tibial n.", 8.5, GREEN, "700") + T(40, 307, "(tarsal tunnel)", 7.5, MUTE))
    b.append(T(40, 462, "peak → PTI → CPTS: one step → one step's", 8, MUTE))
    b.append(T(40, 473, "dose → a whole DAY's dose.", 8, MUTE))

    # ---- MIDDLE: the all-day dose ----
    b.append(box(344, 74, 250, 410, "#ffffff", BORDER, 1.6, 12))
    b.append(T(360, 100, "The all-day dose (CPTS)", 12, NAVY, "700"))
    b.append(T(360, 118, "PTI × cycles/day (MPa·s/day)", 9, MUTE))
    # forefoot vs heel bars (log-ish: forefoot huge)
    b.append(T(360, 146, "forefoot", 9.5, NAVY, "700"))
    b.append(f'<rect x="360" y="152" width="210" height="20" rx="5" fill="{RED}"/>')
    b.append(T(366, 166, "≈ 10,600", 9, "#ffffff", "700"))
    b.append(T(360, 190, "heel / mid", 9.5, NAVY, "700"))
    b.append(f'<rect x="360" y="196" width="14" height="20" rx="5" fill="{BLUE}"/>')
    b.append(T(380, 210, "≈ 100", 9, SLATE, "700"))
    # bounce callout
    b.append(box(360, 230, 218, 62, REDBG, RED, 1.4, 8))
    b.append(T(372, 250, "⚡ 85% of forefoot cycles", 10, RED, "700"))
    b.append(T(372, 265, "= the at-rest bounce/tap dose", 8.5, SLATE))
    b.append(T(372, 278, "no step-counter ever sees.", 8.5, SLATE))
    # structure ranking bars
    b.append(T(360, 314, "Structure load (this demo day)", 9.5, NAVY, "700"))
    ranks = [("plantar fascia", 8477, AMBER), ("Morton / interdigital", 6246, BLUE),
             ("post. tibial", 1969, GREEN), ("Baxter's nerve", 54, RED)]
    mxr = 8477
    for i, (nm, v, c) in enumerate(ranks):
        y = 330 + i * 32
        b.append(T(360, y, nm, 8.5, SLATE))
        b.append(box(360, y + 4, 210, 15, "#ffffff", BORDER, 1, 4))
        b.append(f'<rect x="360" y="{y+4}" width="{max(4, 210*v/mxr):.0f}" height="15" rx="4" fill="{c}"/>')
        b.append(T(574, y + 15, f"{v:,}", 8, MUTE, "700", "end"))

    # ---- RIGHT: tell them apart ----
    b.append(box(614, 74, 262, 410, PANEL2, BORDER, 1.6, 12))
    b.append(T(630, 100, "Same spot — which structure?", 12, NAVY, "700"))
    b.append(box(630, 116, 230, 78, "#ffffff", BORDER, 1.3, 8))
    b.append(T(642, 136, "Medial heel pain: read the clock", 9.5, NAVY, "700"))
    b.append(f'<circle cx="648" cy="153" r="4" fill="{AMBER}"/>')
    b.append(T(658, 156, "MORNING first-steps → fascia", 8.5, SLATE))
    b.append(f'<circle cx="648" cy="173" r="4" fill="{RED}"/>')
    b.append(T(658, 176, "worse THROUGH THE DAY → Baxter", 8.5, SLATE))
    b.append(T(630, 214, "Forefoot burning / numb toes,", 9, SLATE))
    b.append(T(630, 227, "'pebble', Mulder's click → Morton.", 9, SLATE))
    b.append(T(630, 245, "Medial-ANKLE Tinel, radiating", 9, SLATE))
    b.append(T(630, 258, "sole → tarsal tunnel (tibial).", 9, SLATE))
    b.append(box(630, 276, 230, 92, GREENBG, GREEN, 1.4, 8))
    b.append(T(642, 296, "Manage the dose, don't suppress:", 9.5, GREEN, "700"))
    b.append(T(642, 313, "• met pad PROXIMAL to the heads", 8.5, SLATE))
    b.append(T(642, 327, "• wider toe box · ball-of-foot rests", 8.5, SLATE))
    b.append(T(642, 341, "• offload heel AND cushion forefoot", 8.5, SLATE))
    b.append(T(642, 355, "• calf length work (equinus = 23× PF)", 8.5, SLATE))
    b.append(T(630, 392, "Steep forefoot gradient → subsurface", 8.5, MUTE))
    b.append(T(630, 404, "shear near the digital nerves.", 8.5, MUTE))
    b.append(T(630, 428, "analysis/nerve_fascia.py --demo", 8.5, NAVY, "700"))
    b.append(T(630, 440, "refs: structures{} + CPTS metric", 8, MUTE))

    b.append(T(24, 506, "CPTS anchor 140–275 MPa·s/day is a diabetic-ULCER figure (at-risk tissue), not a healthy limit — "
                        "compare zones & track your own trend. Associations published; weights estimated. SCREENING, not diagnosis.",
               8.5, MUTE))
    return wrap(w, h, "\n".join(b),
                "From foot pressure to nerve and fascia impact. A foot map marks plantar fascia (heel-to-forefoot tension band), Baxter's nerve (medial heel), Morton's/interdigital nerve (met2-4 interspaces), and posterior tibial nerve (tarsal tunnel, medial arch). The all-day dose CPTS = PTI x cycles/day is forefoot ~10,600 vs heel ~100 MPa.s/day, with 85% of forefoot cycles from the at-rest bounce dose; structure loads plantar fascia 8477, Morton 6246, tibial 1969, Baxter 54. Tell them apart: medial heel pain worse in the morning = fascia, worse through the day = Baxter's; forefoot burning/numb toes = Morton; medial-ankle Tinel = tarsal tunnel. Manage the dose (met pad, wider toe box, rest windows, calf work). Screening, not diagnosis.",
                "Left: foot map with four structures marked on their zones. Middle: CPTS dose bars (forefoot vs heel), the 85% bounce-dose callout, and structure-load ranking. Right: how to tell the structures apart by symptom/time-of-day and how to manage the dose.")


def g_maker_hacks():
    w, h = 900, 500
    b = [head(w, "Maker hacks — clawing back the accuracy cheap sensors lose",
              "Every cheap part has a documented failure mode; these field-tested tricks recover most of it")]
    panels = [
        (24, "FSR insole", "drift · hysteresis", BLUE, BLUEBG, [
            ("Force-concentrator puck", "funnel load onto the sensor the", "same way every time — the #1 win", "PRINT"),
            ("Firm, flat backing", "a curved mount pre-loads →", "lost range + drift (Interlink)", ""),
            ("Per-sensor fit + tune Rₘ", "fit each FSR's power-law; centre", "the divider on your force band", ""),
        ]),
        (312, "Velostat mat", "ghosting (crosstalk)", RED, REDBG, [
            ("Sink idle rows + settle-read", "hold other rows at 0 V, discard", "the 1st mux read — no parts", "CODE"),
            ("Diode / op-amp virtual gnd", "block the reverse sneak path", "entirely — the full fix", ""),
            ("Bicubic-interpolate the grid", "8×11 → smooth map; bicubic ≈", "linear error, beats blocky", "CODE"),
        ]),
        (600, "Load-cell plate", "HX711 noise · drift", GREEN, GREENBG, [
            ("Median-THEN-average", "median rejects the spikes an", "average would smear (10–15×)", "CODE"),
            ("Right SPS for the job", "10 SPS quiet stands; 80 SPS", "(noisiest) only for landings", ""),
            ("Warm up · re-tare on drift", "1–2 min warm-up; re-zero when", "the empty baseline wanders", ""),
        ]),
    ]
    for x, name, problem, c, cbg, hacks in panels:
        b.append(box(x, 74, 276, 340, "#ffffff", BORDER, 1.6, 12))
        b.append(f'<rect x="{x}" y="74" width="276" height="30" rx="12" fill="{NAVY}"/>')
        b.append(f'<rect x="{x}" y="90" width="276" height="14" fill="{NAVY}"/>')
        b.append(T(x + 16, 94, name, 12.5, "#ffffff", "700"))
        b.append(box(x + 16, 116, 244, 24, cbg, c, 1.3, 6))
        b.append(T(x + 28, 132, "⚠ " + problem, 9.5, c, "700"))
        yy = 160
        for title, l1, l2, tag in hacks:
            b.append(f'<circle cx="{x+22}" cy="{yy+4}" r="3.5" fill="{c}"/>')
            b.append(T(x + 34, yy + 8, title, 10, NAVY, "700"))
            if tag:
                tagc = GREEN if tag == "CODE" else BLUE
                tbg = GREENBG if tag == "CODE" else BLUEBG
                b.append(box(x + 208, yy - 5, 52, 16, tbg, tagc, 1, 5))
                b.append(T(x + 234, yy + 6, tag, 7.5, tagc, "700", "middle"))
            b.append(T(x + 34, yy + 24, l1, 8.5, SLATE))
            b.append(T(x + 34, yy + 37, l2, 8.5, SLATE))
            yy += 60
    b.append(box(24, 426, 852, 34, PANEL2, BORDER, 1.4, 8))
    b.append(T(40, 447, "Universal:", 10, NAVY, "700"))
    b.append(T(116, 447, "precondition (break-in the first minute)  ·  ladder-calibrate + per-sensor fit  ·  "
                         "twist + shorten + shield leads  ·  re-tare on drift, not on a schedule", 9.2, SLATE))
    b.append(T(24, 484, "Ethos: r≈0.87, not 1.0 — recover repeatability, read trends, don't quote absolutes. Baked into "
                        "force_plate.ino · pressure_mat.ino · mat_heatmap.py · fsr_puck.scad. Sources in docs/maker_hacks.md. Not a medical device.",
               9, MUTE))
    return wrap(w, h, "\n".join(b),
                "Maker hacks that recover the accuracy cheap sensors lose, per instrument. FSR insole (drift/hysteresis): force-concentrator puck, firm flat backing, per-sensor fit + tune the divider. Velostat mat (ghosting): sink idle rows + settle-read, diode/op-amp virtual ground, bicubic interpolation. Load-cell plate (HX711 noise/drift): median-then-average filter, right SPS for the job (10 quiet / 80 landings), warm up and re-tare on drift. Universal: precondition, ladder-calibrate, shield leads, re-tare on drift. Ethos r=0.87 not 1.0.",
                "Three instrument panels (FSR insole, Velostat mat, load-cell plate), each with a problem chip and three hacks tagged CODE or PRINT where baked into the repo, plus a universal strip.")


def main():
    for name, fn in [("physical_setup", g_physical), ("pipeline", g_pipeline),
                     ("software_metrics", g_software), ("day_in_the_life", g_day),
                     ("balance_detail", g_balance), ("balance_positions", g_balance_positions),
                     ("balance_assist", g_balance_assist), ("beam_balance", g_beam_balance),
                     ("landing_lab", g_landing_lab), ("zone_load", g_zone_load), ("chain", g_chain),
                     ("pressure_atlas", g_pressure_atlas), ("conditions", g_conditions),
                     ("footwear", g_footwear), ("bounce", g_bounce), ("lab_scope", g_lab_scope),
                     ("maker_hacks", g_maker_hacks), ("nerve_fascia", g_nerve_fascia)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(fn())
        print(f"-> {name}.svg")


if __name__ == "__main__":
    main()
