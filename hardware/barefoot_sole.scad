// barefoot_sole.scad — thin TPU footbed carrying the 8 FSRs (barefoot rig)
// Wear it strapped to a bare foot to log barefoot pressure, then compare vs
// the shoe insole. Also works as a plain shoe insole-carrier.
// Usage: open in OpenSCAD -> F6 -> Export STL. PRINT IN SOFT TPU (85A).
// For a TRUE-FIT version, boolean these pockets/channels into your SCANNED
// footbed instead of this generic outline — see docs/path2_tracking_build.md.
// All units mm.

/* ---------- parameters ---------- */
foot_len = 260;   // heel->toe footbed length (US M11 footbed ≈ 255-265)
foot_w   = 95;    // ball width
thick    = 3.5;   // footbed thickness
pocket_d = 15;    // FSR pocket diameter (pad ≈ 12.5 + slack)
pocket_h = 1.4;   // recess depth (leaves a thin membrane above the sensor)
chan_w   = 6;     // wire-channel width
$fn      = 48;

// FSR zone positions — normalized [x medial->lateral 0..1 , y heel->toe 0..1]
// (matches ZONES / SENSOR_XY in analysis/analyze_pressure.py)
zones = [ [0.35,0.08], [0.65,0.08], [0.50,0.45], [0.30,0.72],
          [0.50,0.74], [0.70,0.72], [0.28,0.92], [0.55,0.95] ];

module footbed(){
  hull(){
    translate([foot_w/2, foot_w*0.28,        0]) cylinder(d = foot_w*0.62, h = thick); // heel
    translate([foot_w/2, foot_len-foot_w*0.42,0]) cylinder(d = foot_w*0.92, h = thick); // ball
    translate([foot_w/2, foot_len-6,         0]) cylinder(d = foot_w*0.50, h = thick); // toe
  }
}

module pockets_and_channels(){
  for (z = zones){
    px = z[0]*foot_w; py = z[1]*foot_len;
    // FSR pocket (recessed from the top face)
    translate([px, py, thick - pocket_h]) cylinder(d = pocket_d, h = pocket_h + 1);
    // wire channel from each pocket toward the medial instep (x≈0.15, y≈0.5)
    hull(){
      translate([px, py, thick - 1.0]) cylinder(d = chan_w, h = 1.2);
      translate([foot_w*0.15, foot_len*0.5, thick - 1.0]) cylinder(d = chan_w, h = 1.2);
    }
  }
  // ribbon exit channel out the medial edge
  translate([foot_w*0.15 - chan_w/2, foot_len*0.5 - 15, thick - 1.4]) cube([chan_w, 30, 1.5]);
}

module strap_slots(){          // toe + ankle transverse straps
  for (y = [foot_len*0.72, foot_len*0.30])
    for (sx = [0.12, 0.88])
      translate([foot_w*sx, y, -0.5]) cube([5, 18, thick + 1], center = true);
}

difference(){
  footbed();
  pockets_and_channels();
  strap_slots();
}
