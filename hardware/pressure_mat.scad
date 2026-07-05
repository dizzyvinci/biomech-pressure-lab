// pressure_mat.scad — printable frame for a DIY Velostat plantar-pressure MAT.
// The sensing layer is a copper-tape ROW x COLUMN matrix sandwiching a Velostat sheet
// (each row/col overlap = one pressure cell). This printed part is the rigid FRAME +
// an alignment COMB that lays the copper strips straight at a fixed pitch, plus a cable
// exit. Read the matrix by driving rows (GPIO) and reading columns via a mux -> ADC
// (firmware/pressure_mat) -> a heel/arch/forefoot pressure map. Coarse but real.
//
// Print: PLA/PETG, low infill for the frame. The comb teeth set the electrode pitch.

$fn = 32;

INNER_W   = 110;   // sensing area width (mm) — a bit wider than a foot
INNER_L   = 260;   // length
PITCH     = 10;    // electrode strip pitch (mm) -> INNER_W/PITCH cols, INNER_L/PITCH rows
WALL      = 4;
FRAME_H   = 6;
TEETH_H   = 4;     // comb teeth height (guide the copper tape)

COLS = floor(INNER_W / PITCH);
ROWS = floor(INNER_L / PITCH);

module frame() {
    // outer border
    difference() {
        cube([INNER_W + 2*WALL, INNER_L + 2*WALL, FRAME_H]);
        translate([WALL, WALL, 2]) cube([INNER_W, INNER_L, FRAME_H]);      // recess for the sandwich
        // cable exit slot
        translate([INNER_W/2 + WALL - 6, -0.1, 2]) cube([12, WALL + 0.2, FRAME_H]);
    }
    // COLUMN comb (teeth along the two long edges -> vertical copper strips)
    for (i = [0 : COLS]) {
        translate([WALL + i*PITCH - 0.6, WALL - 0.1, 2]) cube([1.2, 2.5, TEETH_H]);
        translate([WALL + i*PITCH - 0.6, WALL + INNER_L - 2.4, 2]) cube([1.2, 2.5, TEETH_H]);
    }
    // ROW comb (teeth along the two short edges -> horizontal copper strips)
    for (j = [0 : ROWS]) {
        translate([WALL - 0.1, WALL + j*PITCH - 0.6, 2]) cube([2.5, 1.2, TEETH_H]);
        translate([WALL + INNER_W - 2.4, WALL + j*PITCH - 0.6, 2]) cube([2.5, 1.2, TEETH_H]);
    }
}

// A corner label of the grid size (printed into the frame) — informational only.
// echo(str("matrix = ", COLS, " cols x ", ROWS, " rows = ", COLS*ROWS, " cells"));

frame();
