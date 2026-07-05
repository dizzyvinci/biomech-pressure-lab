#!/usr/bin/env python3
"""
video_force.py — estimate landing FORCE from video (pose), check it vs the research.

The insole measures pressure directly; video estimates the whole-body force even
when there's no sensor — from an athlete's center-of-mass motion. 2D-pose -> vGRF is
validated (Estimation of vGRF from 2D video + pose AI, PMC11057390). This connector
takes the CoM vertical trajectory (from any pose estimator: MediaPipe / OpenPose /
BlazePose exported as JSON) and applies the single-body CoM model:

        F_vertical(t) = m * (a_com(t) + g)      # a from d2y/dt2

then cross-references the peak against the CITED published range for that sport
(refs/plantar_norms.json), and flags **L/R asymmetry** (an ACL precursor >10-15%).

    python video_force.py --demo
    python video_force.py --pose com_y.json --mass-kg 60 --profile jump_landing
    python video_force.py --flight-time 0.42 --contact-time 0.12 --mass-kg 60 --profile jump_landing
    python video_force.py --peak-left-bw 4.6 --peak-right-bw 3.7   # asymmetry only

pose json = {"fps": 120, "com_y_m": [ ... ]}  (CoM height in metres, per frame)
Outputs results/video_force.json.  Estimation, NOT a measurement; not a medical device.
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
from beam_balance import smooth
G = 9.81
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refs", "plantar_norms.json")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def com_to_force(t, y, mass):
    """CoM vertical trajectory (m) -> vertical GRF (N). Single-body inverse-dynamics."""
    y = smooth(np.asarray(y, float), 7)                 # video/pose is noisy -> low-pass
    v = np.gradient(y, t)
    a = np.gradient(v, t)
    F = np.clip(mass * (a + G), 0, None)                # ground can only push up
    peak = float(F.max())
    lr = float(np.max(np.gradient(F, t)))               # loading rate (N/s) — an ACL flag
    return peak, lr, F


def flighttime_to_force(flight_s, contact_s, mass):
    """Fallback when you only have flight & contact times (frame counting)."""
    v = G * flight_s / 2.0                               # landing velocity (symmetric flight)
    mean_net = mass * v / max(contact_s, 1e-3)           # impulse arrests m*v over contact
    peak = (np.pi / 2) * mean_net + mass * G             # half-sine impulse -> peak total
    return float(peak)


def demo():
    fps = 120.0
    t = np.arange(int(1.2 * fps)) / fps
    # true CoM: flight (freefall from apex) then a half-sine deceleration on landing
    H = 0.45; v_land = np.sqrt(2 * G * H); t_c = 0.55; t_dec = 0.11
    a = np.full_like(t, -G)                              # flight: freefall
    dec = (t >= t_c) & (t < t_c + t_dec)
    A_peak = v_land * np.pi / (2 * t_dec)
    a[dec] = A_peak * np.sin(np.pi * (t[dec] - t_c) / t_dec) - G
    a[t >= t_c + t_dec] = 0.0                            # settled (standing)
    v = np.cumsum(a) / fps
    y = 1.0 + np.cumsum(v) / fps                         # integrate to CoM height (m)
    y += 0.002 * np.random.default_rng(4).standard_normal(len(y))   # video noise
    return t, y, 60.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--pose", help="json {fps, com_y_m:[...]}")
    ap.add_argument("--mass-kg", type=float, default=60.0)
    ap.add_argument("--flight-time", type=float)
    ap.add_argument("--contact-time", type=float, default=0.12)
    ap.add_argument("--profile", default="jump_landing")
    ap.add_argument("--peak-left-bw", type=float)
    ap.add_argument("--peak-right-bw", type=float)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    db = json.load(open(REFS, encoding="utf-8"))
    prof = db["profiles"].get(args.profile, {})
    ref_force = prof.get("peak_force_BW", {})

    L = ["# Video -> force estimate", ""]
    out = {"profile": args.profile}
    peak_n = lr = None

    if args.demo or args.pose:
        if args.demo:
            t, y, mass = demo()
        else:
            d = json.load(open(args.pose)); fps = d["fps"]
            y = d["com_y_m"]; t = np.arange(len(y)) / fps; mass = args.mass_kg
        peak_n, lr, _ = com_to_force(t, y, mass)
        bw = peak_n / (mass * G)
        out.update(method="com_trajectory", peak_N=round(peak_n), peak_BW=round(bw, 1),
                   loading_rate_N_s=round(lr))
        L.append(f"- **Method:** CoM trajectory (pose) → inverse dynamics, mass {mass:.0f} kg")
        L.append(f"- **Estimated peak vGRF ≈ {round(peak_n)} N = {bw:.1f}× body weight**  "
                 f"(loading rate {round(lr)} N/s)")
    elif args.flight_time:
        peak_n = flighttime_to_force(args.flight_time, args.contact_time, args.mass_kg)
        bw = peak_n / (args.mass_kg * G)
        out.update(method="flight_time", peak_N=round(peak_n), peak_BW=round(bw, 1))
        L.append(f"- **Method:** flight/contact time, mass {args.mass_kg:.0f} kg")
        L.append(f"- **Estimated peak vGRF ≈ {round(peak_n)} N = {bw:.1f}× body weight**")

    if peak_n is not None and ref_force:
        bw = peak_n / ((args.mass_kg if not (args.demo or args.pose) else 60.0) * G)
        rng = ref_force.get("range")
        within = rng and rng[0] <= bw <= rng[1]
        verdict = ("within" if within else "ABOVE — high impact, injury-relevant" if rng and bw > rng[1]
                   else "below the reported range")
        L.append(f"- **Vs published** {args.profile}: typical {ref_force.get('typical')}× "
                 f"(range {rng}, {ref_force.get('confidence')}) → **{verdict}**.")
        if prof.get("chain_injury"):
            L.append(f"- 🔗 {prof['chain_injury']}")
        out["vs_published"] = {"typical": ref_force.get("typical"), "range": rng, "verdict": verdict}

    # L/R asymmetry -> ACL precursor
    pl, pr = args.peak_left_bw, args.peak_right_bw
    if pl and pr:
        asym = round(100 * abs(pl - pr) / max(pl, pr), 0)
        flag = asym > 10
        L.append(f"\n## Limb asymmetry\n- Left {pl}× vs right {pr}× BW → **{asym:.0f}% asymmetry** "
                 f"— {'⚠ >10-15% is a non-contact ACL precursor (acl_asym); train the weaker limb' if flag else 'within a safe band'}.")
        out["asymmetry_pct"] = asym; out["acl_flag"] = bool(flag)

    if not any([args.demo, args.pose, args.flight_time, pl and pr]):
        L.append("_Nothing to estimate — try --demo, --pose, --flight-time, or --peak-left-bw/--peak-right-bw._")

    L.append(f"\n_Estimation via the single-body CoM model / impulse; pose→GRF basis: "
             f"{db['sources']['pose_grf']['cite']} ({db['sources']['pose_grf']['url']}). "
             f"Estimate, not a measurement. Not a medical device._")
    with open(os.path.join(args.out, "report_video_force.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(args.out, "video_force.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("\n".join(L))
    print(f"\n-> {args.out}/video_force.json")


if __name__ == "__main__":
    main()
