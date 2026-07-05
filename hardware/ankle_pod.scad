// ankle_pod.scad — parametric enclosure for the Path 2 tracking pod
// Holds ESP32-S3 DevKitC + LiPo + microSD module; clips to ankle/laces.
// Usage: open in OpenSCAD -> F6 -> Export as STL. Print in PLA or PETG.
// ⚠️ MEASURE your actual boards + battery and edit the parameters below.
// All units mm.

/* ---------- parameters (edit to your parts) ---------- */
wall     = 2.0;
inner_l  = 67;    // interior length  (ESP32-S3 board + a little slack)
inner_w  = 30;    // interior width
inner_h  = 24;    // interior height  (board stacked over the LiPo)
rad      = 3;     // outer corner radius
usb_w    = 12;    // USB-C opening width  (for charging + flashing)
usb_h    = 7;     // USB-C opening height
btn_d    = 8;     // button hole diameter
ribbon_w = 12;    // sensor-ribbon slot width
ribbon_h = 3;     // sensor-ribbon slot height
strap_w  = 24;    // ankle strap width it must pass
$fn      = 48;

out_l = inner_l + 2*wall;
out_w = inner_w + 2*wall;
out_h = inner_h + wall;          // open-top shell; lid is separate

/* ---------- helpers ---------- */
module rbox(l, w, h, r){         // rounded box, centered in X/Y, base at z=0
  hull() for (x = [-1,1], y = [-1,1])
    translate([x*(l/2 - r), y*(w/2 - r), 0]) cylinder(r = r, h = h);
}

/* ---------- the pod (shell) ---------- */
module pod(){
  difference(){
    rbox(out_l, out_w, out_h, rad);
    // interior cavity
    translate([0, 0, wall]) rbox(inner_l, inner_w, inner_h + 1, max(rad - 1, 1));
    // USB-C cutout on the +X end
    translate([out_l/2 - wall - 0.1, 0, wall + 3]) rotate([0, 90, 0])
      hull() for (y = [-1,1]) translate([0, y*(usb_w/2 - usb_h/2), 0]) cylinder(d = usb_h, h = wall + 2);
    // button hole on the +Y side (near the top)
    translate([0, out_w/2 - wall - 0.1, wall + inner_h - 6]) rotate([-90, 0, 0]) cylinder(d = btn_d, h = wall + 2);
    // sensor-ribbon slot on the -X end, near the floor
    translate([-out_l/2 - 0.1, 0, wall + 1]) rotate([0, 90, 0])
      hull() for (y = [-1,1]) translate([0, y*(ribbon_w/2 - ribbon_h/2), 0]) cylinder(d = ribbon_h, h = wall + 2);
  }
  // two strap slots under the base to thread an ankle strap
  for (sx = [-1, 1]) translate([sx*(out_l/2 - 8), 0, 0]) difference(){
    translate([0, 0, -6]) rbox(6, out_w, 6, 1.5);
    translate([0, 0, -7]) cube([3, strap_w, 8], center = true);
  }
}

/* ---------- press-fit lid (printed beside the pod) ---------- */
module lid(){
  translate([0, out_w + 10, 0]){
    rbox(out_l, out_w, wall, rad);
    translate([0, 0, wall]) rbox(inner_l - 0.6, inner_w - 0.6, 2, max(rad - 1, 1));  // lip
  }
}

pod();
lid();
