// fsr_puck.scad — force-concentrator "puck" for an FSR (the Interlink integration hack).
// A small RIGID disc sitting over the FSR's active area funnels distributed load onto the
// sensor the SAME way every time -> the single biggest repeatability win for a resistive
// insole (and it lifts sensitivity). Print rigid (PLA/PETG), one per sensor, seat it
// centered on the active dot. See docs/maker_hacks.md and the Interlink FSR Integration Guide.
//
// Sized for FSR402 (0.5" round, ~12.7 mm active-area diameter). Change ACTIVE_D for others
// (FSR400 ~5 mm; for a square sensor set ACTIVE_D to the side length).
//
// Built as one revolved profile (rotate_extrude) so it's a single clean manifold solid:
// a relieved flat contact face, a straight wall, and a load-collecting spherical dome.

ACTIVE_D = 12.7;   // FSR active-area diameter (mm)
COVER    = 0.95;   // puck diameter as a fraction of the active area (sit just inside the ring)
DISC_H   = 2.4;    // flat contact-disc height (mm)
DOME_H   = 1.6;    // dome-cap height (mm) — collects the incoming load and feeds it to the disc
RIM      = 0.5;    // relieved contact edge so the rim can't score the sensor film
DOME_N   = 32;     // dome arc resolution
$fn      = 128;

function dome_pts(a, h, zc, r, n) =
    [ for (i = [0 : n]) let (x = a * (1 - i/n)) [x, zc + sqrt(max(r*r - x*x, 0))] ];

module puck() {
    a  = ACTIVE_D * COVER / 2;               // puck radius
    r  = (a*a + DOME_H*DOME_H) / (2*DOME_H); // dome sphere radius from cap geometry
    zc = DISC_H + DOME_H - r;                // sphere center z (so dome base sits at DISC_H)
    profile = concat(
        [[0, 0], [a - RIM, 0], [a, RIM], [a, DISC_H]],  // face relief + straight wall
        dome_pts(a, DOME_H, zc, r, DOME_N)              // spherical dome, a -> 0
    );
    rotate_extrude() polygon(profile);
}

puck();
