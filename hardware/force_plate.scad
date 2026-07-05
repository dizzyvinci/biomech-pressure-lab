// force_plate.scad — a DIY vertical-GRF force plate you print on the H2D.
// 4x bar load cells (e.g. 50 kg each = 200 kg / ~2000 N capacity) sit at the corners
// between a printed/plywood TOP and 4 printed FEET. The top floats on the cells and
// deflects them; each cell -> an HX711 -> per-corner force -> total vGRF + center of
// pressure (firmware/force_plate). Validated DIY load-cell rigs reach ICC>0.94 vs a lab
// force plate. Tune the params below to YOUR load cells (measure them).
//
// Print: PETG (stiff, a bit of give) or PLA. Feet 100% infill (they carry load).
// Render F6 -> export foot() (x4) and, if you don't use plywood, top_plate().

$fn = 48;

// ---- load cell (bar / single-point type) — MEASURE yours ----
LC_len       = 80;   // body length (mm)
LC_w         = 13;   // width
LC_h         = 13;   // height
LC_hole_d    = 5.2;  // mounting hole diameter (M5 clearance)
LC_hole_off  = 6;    // hole centre from each end
LC_free_gap  = 2.0;  // air gap so the free end can deflect (do NOT bottom out)

PLATE        = 240;  // top plate size (mm square); use plywood/acrylic to save print time
PLATE_T      = 6;    // printed top thickness (if not plywood)
WALL         = 3;

// A FOOT: clamps the FIXED end of a bar cell to the ground; the free end overhangs
// toward the plate centre with a clearance gap.
module foot() {
    difference() {
        union() {
            cube([LC_w + 2*WALL, LC_hole_off*2 + 14, 6]);              // ground pad
            translate([WALL, 4, 6]) cube([LC_w, LC_hole_off + 6, LC_h + LC_free_gap]); // riser
        }
        // fixed-end mounting hole (through the riser)
        translate([WALL + LC_w/2, 4 + LC_hole_off, 6])
            cylinder(d = LC_hole_d, h = LC_h + LC_free_gap + 2);
        // rubber-foot pocket underneath (grip)
        translate([(LC_w + 2*WALL)/2, LC_hole_off + 4, -0.1]) cylinder(d = 10, h = 2);
    }
}

// A TOP CONTACT boss: bolts to the FREE end of the cell and presses up on the plate.
module top_boss() {
    difference() {
        cube([LC_w, 16, 10]);
        translate([LC_w/2, 8, -0.1]) cylinder(d = LC_hole_d, h = 12);
    }
}

// Optional printed TOP PLATE with 4 corner pockets for the top bosses.
module top_plate() {
    difference() {
        cube([PLATE, PLATE, PLATE_T]);
        for (x = [18, PLATE-18-LC_w], y = [18, PLATE-18-16])
            translate([x, y, PLATE_T-3]) cube([LC_w+1, 17, 4]);   // boss pockets (glue bosses in)
    }
    // grip rim so a person doesn't slide off
    difference() {
        cube([PLATE, PLATE, 2]); translate([WALL, WALL, -0.1]) cube([PLATE-2*WALL, PLATE-2*WALL, 3]);
    }
}

// ---- what gets rendered (uncomment one to export) ----
foot();                                   // print x4
// translate([0,60,0]) top_boss();        // print x4
// translate([0,120,0]) top_plate();      // or use plywood/acrylic
