#!/usr/bin/env python3
"""
build_insole.py — turn an analysis result into a printable insole model,
optionally FITTED TO YOUR FOOT.

Reads insole_spec.json (from analysis/interpret.py) and bakes the directives in:
  relief_window_zone  -> a recessed relief pocket under that foot zone
  relief_window       -> 'aggressive' => deeper + wider pocket, else 'standard'
  posting             -> medial / lateral wedge (pronation / supination)
  cushion_priority    -> 'heel' => thicker heel build-up
  heel_cup            -> 'deep'  => raised heel rim

THREE fit levels (pick one):
  1. Generic     (default)              — a nominal footbed; fine for a first print.
  2. Measurements  --length/--forefoot-width/--heel-width/--arch-height
                                        — the parametric footbed SCALED to your foot.
  3. Scan        --scan your_orthotic.stl
                                        — carve the relief pocket into YOUR real
                                          geometry (scan your current orthotic).
                                          Best fit; the pocket depth follows the
                                          local top surface at the hot spot.

    # generic
    python build_insole.py --spec ../sample/results/insole_spec.json --out .
    # fitted by measurements (mm)
    python build_insole.py --spec ... --length 262 --forefoot-width 99 --heel-width 64 --arch-height 14
    # fitted to a scan of your orthotic
    python build_insole.py --spec ... --scan my_orthotic.stl --name fitted

Renders <name>.stl + .png if OpenSCAD is on PATH.  NOT a medical device.
"""
import argparse, json, os, shutil, struct, subprocess

# normalized foot frame (x: medial->lateral, y: heel->toe) — matches the analysis
ZONE_XY = {
    "heel_med": (.35, .08), "heel_lat": (.65, .08), "midfoot": (.50, .45),
    "met1": (.30, .72), "met3": (.50, .74), "met5": (.70, .72),
    "hallux": (.28, .92), "toes": (.55, .95),
}


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def suggest_arch(spec):
    """A STARTING arch-dome height (mm) from the posting directive — a first guess to
    tune by feel or replace with a measured/scanned arch. Not a prescription."""
    return {"medial": 13.0, "lateral": 15.0, "neutral": 10.0}.get(spec.get("posting", "neutral"), 10.0)


def relief_params(spec):
    zone = spec.get("relief_window_zone", "heel_med")
    zx, zy = ZONE_XY.get(zone, (.35, .08))
    aggressive = "aggres" in str(spec.get("relief_window", "")).lower()
    return dict(zone=zone, zx=zx, zy=zy, r=22.0 if aggressive else 16.0,
                d=3.5 if aggressive else 2.0, aggressive=aggressive)


# ---- STL reader (binary + ASCII) -> vertices ------------------------------
def stl_points(path):
    data = open(path, "rb").read()
    pts = []
    n = struct.unpack("<I", data[80:84])[0] if len(data) >= 84 else 0
    if n > 0 and len(data) == 84 + n * 50:                 # binary STL
        off = 84
        for _ in range(n):
            v = struct.unpack("<12f", data[off:off + 48]); off += 50
            pts += [(v[3], v[4], v[5]), (v[6], v[7], v[8]), (v[9], v[10], v[11])]
    else:                                                  # ASCII STL
        for ln in data.decode("ascii", "ignore").splitlines():
            s = ln.split()
            if len(s) >= 4 and s[0] == "vertex":
                pts.append((float(s[1]), float(s[2]), float(s[3])))
    if not pts:
        raise SystemExit(f"no vertices parsed from {path}")
    return pts


def bbox(pts):
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def local_top_z(pts, cx, cy, radius, zmax):
    """Highest z among vertices within `radius` of (cx,cy) — the surface at the hot spot."""
    near = [p[2] for p in pts if (p[0] - cx) ** 2 + (p[1] - cy) ** 2 <= radius ** 2]
    return max(near) if near else zmax


# ---- mode 1/2: parametric footbed, scaled to measurements -----------------
def scad_parametric(spec, L, WF, WH, ARCH, side, targets=None):
    rp = relief_params(spec)
    zx = 1 - rp["zx"] if side == "left" else rp["zx"]
    rr, rd = rp["r"], rp["d"]
    targets = targets if targets is not None else spec.get("structure_target", [])
    met_pad = "morton_neuroma" in targets                 # offload the interdigital nerve
    MP_H = 5.0
    heel_cushion = spec.get("cushion_priority") == "heel"
    heel_t = 9.0 if heel_cushion else 6.5
    base_t = 4.0
    posting = spec.get("posting", "neutral")
    post_h = 4.0 if posting in ("medial", "lateral") else 0.0
    # medial edge = low x for a right foot; mirror for left / for lateral posting
    medial_low = (side != "left")
    post_low = medial_low if posting == "medial" else (not medial_low)
    heel_cup = 3.0 if str(spec.get("heel_cup", "")).startswith("deep") else 0.0

    rx = clamp(zx * WF, rr + 3, WF - rr - 3)
    ry = clamp(rp["zy"] * L, rr + 3, L - rr - 3)
    top_z = heel_t if ry < L * 0.45 else base_t
    post_x = "2" if post_low else "WF-3"

    arch_block = ""
    if ARCH > 0:
        ax = WF * (0.28 if medial_low else 0.72)
        arch_block = f"""
    intersection() {{      // medial longitudinal arch dome
        translate([{ax:.1f}, L*0.50, base_t]) scale([1, 2.3, 1])
            difference() {{ sphere(r={ARCH}); translate([0,0,-{ARCH}-1]) cube({2*ARCH+2}, center=true); }}
        linear_extrude(height = base_t + heel_t + {ARCH}) outline2d();
    }}"""

    mp_block = ""
    if met_pad:
        mp_block = f"""
    intersection() {{      // metatarsal pad — PROXIMAL to the met heads: splays met2-4 and
        translate([WF*0.50, L*0.66, base_t])            // offloads the interdigital nerve (Morton target)
            scale([{WF*0.020:.3f}, {L*0.005:.3f}, {MP_H/10.0:.3f}])
            difference() {{ sphere(r=10); translate([0,0,-11]) cube(22, center=true); }}
        linear_extrude(height = base_t + heel_t + {MP_H}) outline2d();
    }}"""

    return f"""// AUTO-GENERATED by build_insole.py — DO NOT hand-edit.
// FIT: parametric, scaled to L={L} x WF={WF} x WH={WH} mm, arch={ARCH} mm, {side} foot.
// relief={rp['zone']} ({'aggressive' if rp['aggressive'] else 'standard'}) · posting={posting}
//   · cushion={'heel' if heel_cushion else 'balanced'} · structures={targets or 'none'}
//   · met_pad={'YES (Morton offload)' if met_pad else 'no'} · arch={ARCH} mm
// Print: firm TPU 95A shell + soft TPU 85A heel/relief{' + met pad' if met_pad else ''} (dual material on the H2D).
$fn = 72;
L = {L}; WF = {WF}; WH = {WH};
base_t = {base_t}; heel_t = {heel_t};
relief_x = {rx:.1f}; relief_y = {ry:.1f}; relief_r = {rr}; relief_d = {rd};
post_h = {post_h}; heel_cup = {heel_cup};

module outline2d() {{
    hull() {{
        translate([WH/2, WH*0.48]) circle(r=WH/2);      // heel
        translate([WF*0.40, L*0.47]) circle(r=WF*0.42); // arch
        translate([WF/2, L*0.80]) circle(r=WF/2);       // forefoot
        translate([WF/2, L*0.93]) circle(r=WF*0.33);    // toes
    }}
}}
module heel_region() translate([-1,-1,0]) cube([WF+2, L*0.42, heel_t+heel_cup+1]);

module body() {{
    linear_extrude(height = base_t) outline2d();
    intersection() {{ linear_extrude(height = heel_t) outline2d(); heel_region(); }}{arch_block}{mp_block}
    if (post_h > 0) intersection() {{
        hull() {{
            translate([{post_x}, L*0.18, base_t]) cube([1, L*0.42, post_h]);
            translate([WF/2, L*0.18, base_t]) cube([1, L*0.42, 0.1]);
        }}
        linear_extrude(height = base_t + heel_t + post_h) outline2d();
    }}
    if (heel_cup > 0) intersection() {{
        difference() {{
            linear_extrude(height = heel_t + heel_cup) outline2d();
            translate([0,0,heel_t]) linear_extrude(height = heel_cup+1) offset(r=-7) outline2d();
        }}
        heel_region();
    }}
}}

difference() {{
    body();
    translate([relief_x, relief_y, ({top_z}) - relief_d + 0.01])
        cylinder(r1 = relief_r*0.7, r2 = relief_r, h = relief_d + 1);
}}
"""


# ---- mode 3: carve the relief into a SCAN of your orthotic -----------------
def scad_from_scan(spec, scan_fwd, pts, side):
    rp = relief_params(spec)
    xmin, xmax, ymin, ymax, zmin, zmax = bbox(pts)
    xlen, ylen = xmax - xmin, ymax - ymin
    # longer horizontal axis = foot length (heel->toe); the other = width
    if ylen >= xlen:
        laxis, Ln, l0 = "y", ylen, ymin
        Wd, w0 = xlen, xmin
    else:
        laxis, Ln, l0 = "x", xlen, xmin
        Wd, w0 = ylen, ymin
    zx = 1 - rp["zx"] if side == "left" else rp["zx"]
    lc = l0 + rp["zy"] * Ln                    # along length (heel=0 end)
    wc = w0 + zx * Wd                          # across width (medial=low)
    rx, ry = (lc, wc) if laxis == "x" else (wc, lc)
    rr, rd = rp["r"], rp["d"]
    tz = local_top_z(pts, rx, ry, rr, zmax)    # surface height at the hot spot
    depth = zmax - zmin

    return f"""// AUTO-GENERATED by build_insole.py — fitted to a SCAN of your orthotic.
// Your scan supplies the outline + arch contour; we carve the data-driven relief.
// relief={rp['zone']} ({'aggressive' if rp['aggressive'] else 'standard'}) at scan XY ({rx:.1f}, {ry:.1f}).
// If the boolean fails, the mesh is likely non-manifold -> clean it first
// (Meshmixer 'Make Solid' / Blender 3D-Print toolbox), then re-run.
$fn = 64;
module orthotic() {{ import("{scan_fwd}", convexity = 10); }}

difference() {{
    orthotic();
    // relief pocket: carved from the local top surface ({tz:.1f}) down {rd} mm
    translate([{rx:.1f}, {ry:.1f}, {tz:.1f} - {rd}])
        cylinder(r1 = {rr*0.7:.1f}, r2 = {rr:.1f}, h = {rd} + {depth:.1f});
}}
"""


def render(exe, scad_path, name, out):
    # --render forces CGAL geometry for the PNG so imported-mesh (scan) previews aren't blank
    for ext, extra in (("stl", []), ("png", ["--render", "--imgsize=820,900", "--viewall",
                                             "--autocenter", "--colorscheme=Tomorrow"])):
        dst = os.path.join(out, f"{name}.{ext}")
        r = subprocess.run([exe, "-o", dst, *extra, scad_path], capture_output=True, text=True)
        if os.path.exists(dst):
            print(f"-> {dst}")
        else:
            print(f"   !! {ext} render failed: {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="../sample/results/insole_spec.json")
    ap.add_argument("--out", default=".")
    ap.add_argument("--name", default="relief_insole")
    ap.add_argument("--side", choices=["right", "left"], default="right")
    # measurement fit (mm)
    ap.add_argument("--length", type=float, default=255.0)
    ap.add_argument("--forefoot-width", type=float, default=95.0)
    ap.add_argument("--heel-width", type=float, default=62.0)
    ap.add_argument("--arch-height", type=float, default=0.0)
    ap.add_argument("--arch-auto", action="store_true",
                    help="start the arch dome from the posting directive (tune by feel)")
    # scan fit
    ap.add_argument("--scan", help="STL of your orthotic/foot to carve the relief into")
    args = ap.parse_args()

    with open(args.spec) as f:
        data = json.load(f)
    spec = data.get("chosen", data)
    os.makedirs(args.out, exist_ok=True)

    targets = spec.get("structure_target", [])
    sa = suggest_arch(spec)
    print(f"   suggested arch ~{sa:.0f} mm (from posting={spec.get('posting')}; "
          f"a starting guess — measure/scan for the real value)")
    if args.arch_auto and args.arch_height == 0.0:
        args.arch_height = sa
    # a fascia/tibial structure target wants arch support (windlass / anti-pronation traction)
    if (not args.scan) and args.arch_height == 0.0 and \
            any(t in ("plantar_fascia", "tibial_nerve_tarsal_tunnel") for t in targets):
        args.arch_height = sa
        print(f"   structure target {targets} -> enabling arch support ~{sa:.0f} mm (windlass / anti-pronation)")

    if args.scan:
        pts = stl_points(args.scan)
        scan_fwd = os.path.abspath(args.scan).replace("\\", "/")
        code = scad_from_scan(spec, scan_fwd, pts, args.side)
        mode = f"scan-fit ({os.path.basename(args.scan)}, {len(pts)} verts)"
    else:
        code = scad_parametric(spec, args.length, args.forefoot_width,
                               args.heel_width, args.arch_height, args.side, targets)
        mode = f"parametric {args.length:.0f}x{args.forefoot_width:.0f} mm, arch {args.arch_height:.0f}"

    scad_path = os.path.join(args.out, f"{args.name}.scad")
    with open(scad_path, "w") as f:
        f.write(code)
    print(f"-> {scad_path}   [{mode}]")
    print(f"   relief@{spec.get('relief_window_zone')} · {spec.get('relief_window')} · "
          f"posting={spec.get('posting')} · cushion={spec.get('cushion_priority')} · {args.side} foot")
    if targets:
        print(f"   structure target: {', '.join(targets)}"
              + ("  + metatarsal pad (Morton offload)" if "morton_neuroma" in targets else ""))

    exe = shutil.which("openscad") or (
        r"C:\Program Files\OpenSCAD\openscad.exe"
        if os.path.exists(r"C:\Program Files\OpenSCAD\openscad.exe") else None)
    if exe:
        render(exe, scad_path, args.name, args.out)
    else:
        print("   (OpenSCAD not found — open the .scad and F6 -> Export STL)")


if __name__ == "__main__":
    main()
