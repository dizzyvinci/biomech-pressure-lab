// ankle_pod_enclosure.scad — parametric 2-part enclosure for the STEMMA-QT ankle pod
// (ESP32-C6 Feather + flat-pouch LiPo underneath it + MPU-6050, strapped to the lower shin/ankle)
//
// This is the STEMMA-QT / Feather revision of the Path 2 electronics — see docs/BUILD_PLAN.md.
// It's a SEPARATE part from hardware/ankle_pod.scad, which holds the older ESP32-S3 DevKitC +
// CD74HC4067 mux + BNO085 rig documented in the main README. Both designs are kept in the repo;
// use whichever matches the BOM you actually bought.
//
// Usage: open in OpenSCAD -> F6 (render) -> Export as STL. base() and lid() print side by side.
// Print in PETG or PLA-CF (stiffer, but more brittle at the snap ribs — PETG is the safer bet
// if you'll open the lid often). Skip TPU for the shell itself; if you want the pod to hug a
// curved shin instead of being lashed flat, print the STRAP itself in TPU (flexible, no sewing)
// and thread it through the slots below — see strap_keeper() at the bottom.
//
// ⚠️ MEASURE your actual Feather, LiPo, and MPU-6050 breakout and correct the numbers below —
// especially feather_hole_dx/dy (this is the standard Adafruit Feather 2.0"x0.9" spacing, but
// confirm against your board) and the MPU-6050 footprint (many small STEMMA QT breakouts have
// NO standardized mounting holes, which is why it's zip-tied into a lip pocket here rather than
// screwed down).
//
// All units mm.

/* ================= PARAMETERS ================= */

// -- fit --
wall = 2.0;       // shell wall thickness
tol  = 0.3;       // clearance around components / lid friction-fit allowance per side
$fn  = 64;

// -- ESP32-C6 Feather (Adafruit #5933, STEMMA QT) --
feather_l       = 50.8;   // board length, long axis — USB-C sits on the short +X end
feather_w       = 22.8;   // board width
feather_hole_dx = 45.72;  // 1.8" — Adafruit Feather-standard mounting-hole spacing, long axis
feather_hole_dy = 17.78;  // 0.7" — Feather-standard mounting-hole spacing, short axis
feather_hole_d  = 2.5;    // Feather mounting-hole diameter
board_clear_h   = 7;      // clearance above the board TOP for the USB-C plug + STEMMA QT
                           // header + any solder — the lid's inner ceiling sits this high above it

// -- LiPo flat pouch cell (rides UNDER the Feather, stacked) --
// ⚠️ FORM FACTOR IS A DESIGN CONSTRAINT, NOT A PREFERENCE. This pod is body-worn, and variants
// of it ride the shin, the foot, inside a shoe, or on an AFO. It MUST be a flat pouch cell.
// A cylindrical 18650 (18 mm dia x 65 mm) will NOT work here — it's a rigid tube that cannot
// sit under a board or against a limb. Keep an 18650 for the STATIONARY builds only
// (bed mat / force-plate electronics), never for anything worn.
//
// Runtime is NOT the binding constraint — the pod records sessions (gait passes, stance trials),
// not 24/7 — so trade capacity for thinness every time.
//
// Adafruit flat-pouch options (all ship with JST-PH 2-pin + protection circuit):
//   500 mAh  -> 30 x 19 x 6    ~5 h   thinnest; use for in-shoe / under-AFO
//   1200 mAh -> 35 x 20 x 6    ~10 h  DEFAULT — best thinness/runtime balance
//   2000 mAh -> 60 x 36 x 7    ~18 h  long; shin-pod only
//   2500 mAh -> 50 x 34 x 10   ~22 h  too thick for shoe/AFO use
//
// NOTE: at 20 mm wide the cell is NARROWER than the Feather (22.8 mm), so the FEATHER now sets
// the case width — the shell gets ~12 mm slimmer than the old 2500 mAh build, and standoff_h
// drops from 11 mm to 7 mm. That slimming is the whole point of the change.
lipo_l   = 35;              // 1200 mAh flat pouch
lipo_w   = 20;
lipo_h   = 6;
lipo_gap = 1;               // clearance between the LiPo top and the Feather standoffs

// -- MPU-6050 STEMMA QT breakout — mounted in its own end bay, floor-level --
imu_l          = 18;
imu_w          = 13;
imu_pocket_pad = 1.5;       // clearance around the board inside its retaining lip
imu_lip_h      = 1.8;       // retaining-lip wall height (straight extrusion — zero overhang)
imu_zip_w      = 3;         // zip-tie slot width — belt-and-suspenders retention, since most
                             // small IMU breakouts have no trustworthy screw-hole pattern

// -- connectors / cutouts --
usb_w    = 10;   usb_h    = 4.2;  // USB-C opening — charge + flash without opening the case
stemma_w = 7;    stemma_h = 3.5;  // STEMMA QT cable exit — continues the I2C chain out to the
                                    // externally-worn VCNL4200 (see docs/BUILD_PLAN.md)
sensor_w = 9;    sensor_h = 4;     // FSR lead-bundle / JST exit toward the insole
drain_d  = 1.6;                    // USB-end drain holes — this pod rides the shin, exposed to
                                    // sweat/rain; lets moisture that gets in run back out

// -- strap --
strap_w    = 25;   // ~25 mm elastic, per the project brief
strap_boss = 7;     // boss length along X (each strap-slot pillar)

// -- lid snap feature (base's groove + lid's rib, see base()/lid()) --
snap_engage  = 0.2;    // rib interference against the wall DURING insertion travel — small
                        // and safe for PETG/PLA-CF, not a big structural flex
snap_relief  = 0.35;   // groove relief depth, cut into the wall — deliberately deeper than
                        // snap_engage so the rib has slack once fully seated (the "click")
snap_depth   = 1.5;    // how far below the cavity's top opening the snap band sits
snap_len     = 6;      // rib/groove length along X
snap_h       = 1.6;    // rib/groove height along Z

/* ================= DERIVED ================= */
main_inner_l = max(feather_l, lipo_l) + 2*tol + 3;   // Feather+LiPo bay footprint
main_inner_w = max(feather_w, lipo_w) + 2*tol + 3;   // FEATHER (22.8 mm) governs this now — the 20 mm cell is narrower
standoff_h   = lipo_h + lipo_gap;                     // Feather standoff height off the floor
inner_h      = standoff_h + board_clear_h;            // shared by the whole case — simplest,
                                                        // most printable: one uniform height

imu_bay_l = imu_l + 2*imu_pocket_pad + 4;             // extra LENGTH tacked on one end for the
                                                        // IMU — its 13 mm width fits easily
                                                        // inside the Feather-driven case width, so
                                                        // no extra width is needed, only length

inner_l = main_inner_l + imu_bay_l;
inner_w = main_inner_w;

out_l = inner_l + 2*wall;
out_w = inner_w + 2*wall;
out_h = inner_h + wall;     // open-top shell; lid is separate
rad   = 3;

// X layout (case centered at the origin in X/Y):
//   [-out_l/2] USB-C end -- Feather+LiPo bay -- IMU end bay -- [+out_l/2] STEMMA/FSR end
main_x0 = -inner_l/2;                 // start of the Feather+LiPo bay (at the USB end)
main_x1 = main_x0 + main_inner_l;     // end of that bay / start of the IMU bay
imu_x1  = inner_l/2;                  // end of the IMU bay (= +X inner wall)
imu_cx  = (main_x1 + imu_x1) / 2;     // IMU pocket center X

/* ================= HELPERS ================= */
// rounded box, centered in X/Y, base at z=0
module rbox(l, w, h, r){
  hull() for (x = [-1,1], y = [-1,1])
    translate([x*(l/2 - r), y*(w/2 - r), 0]) cylinder(r = r, h = h);
}

// horizontal stadium-shaped cutout through a wall (same low-overhang technique as
// hardware/ankle_pod.scad's USB/ribbon slots — small round-ended holes bridge cleanly on
// the H2D with no supports)
module wall_slot(w, h, len, axis){
  if (axis == "x") rotate([0,90,0]) hull() for (y=[-1,1]) translate([0, y*(w/2 - h/2), 0]) cylinder(d=h, h=len);
  else              rotate([90,0,0]) hull() for (x=[-1,1]) translate([x*(w/2 - h/2), 0, 0]) cylinder(d=h, h=len);
}

/* ================= BASE ================= */
module base(){
  difference(){
    rbox(out_l, out_w, out_h, rad);

    // ---- one continuous interior cavity: LiPo+Feather bay AND the IMU end bay ----
    // (they're one rectangle, not two — the "bay" split is just extra length at one end;
    // splitting the cut in two would only add a seam with no functional purpose)
    translate([0, 0, wall]) rbox(inner_l, inner_w, inner_h + 1, max(rad - 1, 1));

    // ---- USB-C cutout, -X end, centered on the Feather's short edge ----
    // (wall_slot's "x" branch extrudes in +X from the translate point, so — unlike the
    // STEMMA cutout below, which sits at the +X end and starts just inside the wall — this
    // one has to start just OUTSIDE the -X face and cut inward through the wall)
    translate([-out_l/2 - 1, 0, wall + standoff_h + 3])
      wall_slot(usb_w, usb_h, wall + 3, "x");

    // ---- USB-end drain holes (floor) — shin-worn = sweat/rain exposure near the port ----
    for (dy = [-3, 3])
      translate([main_x0 + 4, dy, -0.5]) cylinder(d = drain_d, h = wall + 1);

    // ---- STEMMA QT cable exit, +X end wall — continues the I2C chain to the external
    //      VCNL4200 (mounted separately; see docs/BUILD_PLAN.md) ----
    translate([out_l/2 - wall - 0.1, inner_w*0.22, wall + inner_h*0.55])
      wall_slot(stemma_w, stemma_h, wall + 2, "x");

    // ---- FSR lead-bundle / JST exit, -Y side wall near the Feather's analog-pin edge ----
    translate([main_x0 + main_inner_l*0.68, -out_w/2 + wall + 0.1, wall + standoff_h*0.6])
      wall_slot(sensor_w, sensor_h, wall + 2, "y");

    // ---- strap slots (~25 mm elastic threads through, under the base) ----
    for (sx = [main_x0 + main_inner_l*0.22, imu_cx])
      translate([sx, 0, -0.1]) cube([strap_boss - 2, strap_w, wall + 0.2], center = true);

    // ---- IMU zip-tie retention slots through the floor — loop a tie up through one,
    //      over the breakout, down through the other, cinch from underneath ----
    for (zx = [imu_cx - imu_l*0.28, imu_cx + imu_l*0.28])
      translate([zx, 0, -0.5]) cube([imu_zip_w, 4, wall + 1], center = true);

    // ---- snap-groove: a shallow relief cut into both long walls, snap_depth below the
    //      cavity's top opening. The lid's ribs (see lid()) ride tight against the wall on
    //      the way in — a small, safe snap_engage interference — then relax into this relief
    //      once fully seated, for a real click-stop rather than friction alone. Starts
    //      exactly at the wall's true inner face (inner_w/2) and cuts snap_relief further in. ----
    for (sy = [-1,1])
      translate([main_x0 + main_inner_l*0.5, sy*(inner_w/2 + snap_relief/2), out_h - snap_depth])
        cube([snap_len + 1, snap_relief, snap_h + 0.4], center = true);
  }

  // ---- Feather standoff posts — screw into the 2.5 mm mounting holes. Pilot hole is sized
  //      for a self-tapping M2.5/#4 screw; for a mount you'll open/close a lot, drill out to
  //      2.5 mm through and press in an M2.5 heat-set insert instead (see docs/BUILD_PLAN.md). ----
  for (hx = [-1,1], hy = [-1,1])
    translate([main_x0 + main_inner_l/2 + hx*feather_hole_dx/2, hy*feather_hole_dy/2, wall])
      difference(){
        cylinder(d = feather_hole_d + 3.5, h = standoff_h);
        translate([0, 0, -0.5]) cylinder(d = 2.0, h = standoff_h + 1);   // self-tap pilot
      }

  // ---- IMU retaining lip — a straight-walled pocket (zero overhang, prints clean) that
  //      locates the MPU-6050 breakout; the zip-tie slots above do the actual holding-down,
  //      since most STEMMA QT breakouts this size don't have a trustworthy screw pattern ----
  translate([imu_cx, 0, wall])
    difference(){
      rbox(imu_l + 2*imu_pocket_pad + 2.4, imu_w + 2*imu_pocket_pad + 2.4, imu_lip_h, 1.5);
      translate([0, 0, -0.1])
        rbox(imu_l + 2*imu_pocket_pad, imu_w + 2*imu_pocket_pad, imu_lip_h + 0.2, 1);
    }
}

/* ================= LID ================= */
module lid(){
  translate([0, out_w + 14, 0]){
    // flat panel
    rbox(out_l, out_w, wall, rad);

    // friction-fit lip — drops into the cavity opening (interference = 2*tol total)
    translate([0, 0, wall])
      rbox(inner_l - 2*tol, inner_w - 2*tol, 2.8, max(rad - 1, 1));

    // snap ribs — straight vertical ridges (NOT domes: zero overhang, prints clean standing
    // up), one per long side of the lip. Each spans from solidly inside the lip body (so it
    // bonds cleanly, no floating shell) out to snap_engage past the wall's TRUE inner face —
    // a small, safe interference during insertion, not a big structural flex.
    //
    // Z placement: the lid prints flat, lip pointing UP (same orientation as the base). When
    // you flip it onto the base for assembly, local Z inverts: global_z = (out_h+wall) -
    // local_z. Placing the rib at local Z = wall+snap_depth lands it at global
    // (out_h+wall)-(wall+snap_depth) = out_h-snap_depth — exactly the base's groove Z above.
    for (sy = [-1,1]){
      rib_outer = sy*(inner_w/2 + snap_engage);
      rib_inner = sy*(inner_w/2 - tol - 0.4);   // reaches back into the lip body for a clean bond
      translate([main_x0 + main_inner_l*0.5, (rib_outer + rib_inner)/2, wall + snap_depth])
        cube([snap_len, abs(rib_outer - rib_inner), snap_h], center = true);
    }
  }
}

/* ================= OPTIONAL: TPU strap keeper ================= */
// A small flexible loop, printed in TPU, that clips into the strap slots as an alternative to
// sewn/threaded elastic — flex-fits around the shin without any sewing. Not instantiated by
// default; uncomment strap_keeper() below to add it to the plate.
module strap_keeper(){
  translate([0, -(out_w + 14), 0])
    difference(){
      rbox(strap_boss + 10, strap_w + 6, 3, 2);
      translate([0, 0, -0.5]) cube([strap_boss - 1, strap_w - 4, 4], center = true);
    }
}

base();
lid();
// strap_keeper();
