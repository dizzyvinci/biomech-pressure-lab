// insole_fsr_layout.scad — flat FSR "sensor carrier" plate for the 6-zone STEMMA-QT rig
// (heel_med, heel_lat, midfoot, met1, met5, hallux — one FSR402 per zone, straight into the
// ESP32-C6 Feather's 6 analog pins A0..A5, no mux). Coordinates + rationale are written up in
// docs/insole_sensor_layout.md — read that alongside this file.
//
// This is a companion to hardware/barefoot_sole.scad, not a replacement: barefoot_sole.scad is
// the original 8-zone carrier for the ESP32-S3+mux rig. This file is thinner-scoped (6 zones)
// and, unlike that file, is driven by a SINGLE top-level parameter (FOOT_LEN) — width is derived
// from it, using the same length:width ratio the rest of the repo's norms DB uses
// (refs/plantar_norms.json: 95 mm width / 255 mm length), so the whole plate rescales from one
// number instead of two independent ones.
//
// Two ways to use it:
//   1. Print thin in TPU (~2.5 mm, soft 85A, external dryer spool) as an actual wearable
//      carrier — slide it under your regular insole, same idea as barefoot_sole.scad.
//   2. Print quick in scrap PLA (skip the TPU entirely) as a flat LAYOUT JIG — just to trace/
//      mark the 6 zone positions onto a shoe insole or orthotic before you commit to TPU.
//
// Usage: open in OpenSCAD -> F6 -> Export STL. All units mm.

/* ================= PARAMETERS ================= */
FOOT_LEN   = 267;          // heel->toe reference length (mm). Default = men's ~US10 (~10.5 in);
                            // ±5 mm across shoe-size charts — measure your own foot
                            // (docs/fit_to_your_foot.md) and set this for a true fit.
WIDTH_RATIO = 95 / 255;     // ball-width : length ratio from refs/plantar_norms.json's reference
                            // foot — the same convention analysis/zone_load.py's zone_mm() uses.
FOOT_W = FOOT_LEN * WIDTH_RATIO;   // derived ball width (~99.5 mm at the default length)

THICK    = 2.5;   // plate thickness (thinner than barefoot_sole.scad's 3.5 — this is a
                   // layout/reference carrier, meant to ride under an existing insole)
POCKET_D = 15;     // FSR402 pocket diameter (12.7 mm active area + slack)
POCKET_H = 1.4;    // recess depth — leaves a thin membrane over the sensor
CHAN_W   = 6;       // wire-routing channel width
$fn      = 48;

// FSR zone positions — normalized [x medial->lateral 0..1, y heel->toe 0..1].
// Same coordinate convention (and same numbers) as SENSOR_XY / ZONES in
// analysis/analyze_pressure.py and the zones array in barefoot_sole.scad — this is the
// heel_med/heel_lat/midfoot/met1/met5/hallux SUBSET of that 8-zone list (met3 and toes
// dropped; see docs/insole_sensor_layout.md for why 6, and the fsr0..fsr5 -> A0..A5 wiring
// order these are listed in).
zones = [
  [0.35, 0.08],   // 0  heel_med  -> A0
  [0.65, 0.08],   // 1  heel_lat  -> A1
  [0.50, 0.45],   // 2  midfoot   -> A2
  [0.30, 0.72],   // 3  met1      -> A3
  [0.70, 0.72],   // 4  met5      -> A4
  [0.28, 0.92],   // 5  hallux    -> A5
];

// exit point (medial instep) where all routing channels converge toward the ribbon/JST
// cable running up to the ankle pod
EXIT_X = 0.15;
EXIT_Y = 0.50;

/* ================= GEOMETRY ================= */
// heel/ball/toe outline, same hull-of-3-circles shape as barefoot_sole.scad, driven by the
// two derived dimensions above instead of independent hardcoded ones
module footbed(){
  hull(){
    translate([FOOT_W/2, FOOT_W*0.28,          0]) cylinder(d = FOOT_W*0.62, h = THICK); // heel
    translate([FOOT_W/2, FOOT_LEN - FOOT_W*0.42,0]) cylinder(d = FOOT_W*0.92, h = THICK); // ball
    translate([FOOT_W/2, FOOT_LEN - 6,          0]) cylinder(d = FOOT_W*0.50, h = THICK); // toe
  }
}

module pockets_and_channels(){
  for (z = zones){
    px = z[0]*FOOT_W; py = z[1]*FOOT_LEN;
    // FSR pocket, recessed from the top face — compatible with hardware/fsr_puck.scad
    translate([px, py, THICK - POCKET_H]) cylinder(d = POCKET_D, h = POCKET_H + 1);
    // wire channel from each pocket toward the medial-instep exit
    hull(){
      translate([px, py, THICK - 1.0]) cylinder(d = CHAN_W, h = 1.2);
      translate([FOOT_W*EXIT_X, FOOT_LEN*EXIT_Y, THICK - 1.0]) cylinder(d = CHAN_W, h = 1.2);
    }
  }
  // ribbon/JST exit slot out the medial edge, toward the ankle pod
  translate([FOOT_W*EXIT_X - CHAN_W/2, FOOT_LEN*EXIT_Y - 15, THICK - 1.4])
    cube([CHAN_W, 30, 1.5]);
}

module strap_slots(){          // toe + ankle transverse straps, same convention as barefoot_sole
  for (y = [FOOT_LEN*0.72, FOOT_LEN*0.30])
    for (sx = [0.12, 0.88])
      translate([FOOT_W*sx, y, -0.5]) cube([5, 18, THICK + 1], center = true);
}

difference(){
  footbed();
  pockets_and_channels();
  strap_slots();
}
