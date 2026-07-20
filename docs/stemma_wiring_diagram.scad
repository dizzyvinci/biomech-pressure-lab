// stemma_wiring_diagram.scad -- connection diagram for the first sensor bring-up.
//
// Adafruit ESP32-C6 Feather  --[STEMMA QT cable]--  MPU-6050 breakout
//
// ⚠️ THIS IS A CONNECTION SCHEMATIC, NOT A SCALE DRAWING. Board outlines are close to real
// (Feather 50.8 x 22.8mm, MPU-6050 breakout ~25.5 x 17.8mm) but the exact position of each
// connector along an edge is drawn for legibility, not measured. Use it to understand WHAT
// plugs into WHAT. Do not key any printed part off these coordinates -- caliper the real
// boards instead, which is what START_HERE.md 1.3 asks you to do.
//
// There is no soldering anywhere in this diagram. That is the entire point of having chosen
// STEMMA QT parts: the connector is keyed, so it physically cannot be inserted backwards, and
// power plus both I2C lines travel down the one 4-conductor cable.
//
// Render:
//   openscad -o wiring_top.png --imgsize=1600,900 --projection=o \
//            --camera=0,0,40,0,0,0,260 --colorscheme=Tomorrow stemma_wiring_diagram.scad

$fn = 32;

PCB_T      = 1.6;
LABEL_Z    = 3.2;
FEATHER_L  = 50.8;
FEATHER_W  = 22.8;
MPU_L      = 25.5;
MPU_W      = 17.8;

FEATHER_X  = -42;
MPU_X      =  46;

module label(txt, size = 4.2, col = [0.10, 0.10, 0.12]) {
    color(col) linear_extrude(0.6) text(txt, size = size, halign = "center", valign = "center");
}

// ---- STEMMA QT / Qwiic connector: 4-pin JST-SH, 1mm pitch. The white body with the keyed
//      slot is the thing you actually look for on a board.
module stemma_port(rot = 0) {
    rotate([0, 0, rot]) {
        color([0.93, 0.93, 0.90]) translate([-3.0, -2.2, 0]) cube([6.0, 4.4, 2.9]);
        color([0.35, 0.35, 0.38]) translate([-3.0, -2.2, 2.6]) cube([6.0, 4.4, 0.5]);   // keyway lip
    }
}

module usb_c() {
    color([0.72, 0.74, 0.78])
        translate([-4.4, -3.2, 0]) cube([4.6, 6.4, 3.2]);
}

// ---- Adafruit ESP32-C6 Feather --------------------------------------------------------------
module feather() {
    translate([FEATHER_X, 0, 0]) {
        color([0.13, 0.30, 0.20]) translate([-FEATHER_L / 2, -FEATHER_W / 2, 0])
            cube([FEATHER_L, FEATHER_W, PCB_T]);
        // ESP32-C6 module + antenna
        color([0.80, 0.80, 0.83]) translate([-6, -7, PCB_T]) cube([16, 14, 1.2]);
        color([0.85, 0.75, 0.20]) translate([10, -3, PCB_T]) cube([7, 6, 0.6]);
        // USB-C, at the -X end
        translate([-FEATHER_L / 2, 0, PCB_T]) usb_c();
        // STEMMA QT port, +X end
        translate([FEATHER_L / 2 - 6, 0, PCB_T]) stemma_port(0);
        // header pin rows, drawn as dots so the board reads as a Feather at a glance
        color([0.55, 0.55, 0.58])
            for (sy = [-1, 1], i = [0 : 11])
                translate([-FEATHER_L / 2 + 4 + i * 3.6, sy * (FEATHER_W / 2 - 1.6), PCB_T])
                    cylinder(d = 1.5, h = 1.0);
    }
}

// ---- Adafruit MPU-6050 breakout -------------------------------------------------------------
module mpu6050() {
    translate([MPU_X, 0, 0]) {
        color([0.10, 0.10, 0.12]) translate([-MPU_L / 2, -MPU_W / 2, 0])
            cube([MPU_L, MPU_W, PCB_T]);
        color([0.22, 0.22, 0.25]) translate([-3.5, -3, PCB_T]) cube([7, 6, 1.1]);   // the IMU chip
        // TWO ports, wired in parallel -- either one works, the second is for chaining
        translate([-MPU_L / 2 + 6, 0, PCB_T]) stemma_port(180);
        translate([ MPU_L / 2 - 6, 0, PCB_T]) stemma_port(0);
    }
}

// ---- the cable ------------------------------------------------------------------------------
// One 4-conductor cable carries 3V3, GND, SDA and SCL. Drawn with a gentle sag so it reads as
// a flexible cable rather than a rigid bar.
module cable() {
    x0 = FEATHER_X + FEATHER_L / 2 - 3;
    x1 = MPU_X - MPU_L / 2 + 3;
    steps = 44;
    color([0.12, 0.12, 0.14])
        for (i = [0 : steps - 1]) {
            t0 = i / steps;  t1 = (i + 1) / steps;
            xa = x0 + (x1 - x0) * t0;   ya = -7 * sin(180 * t0);
            xb = x0 + (x1 - x0) * t1;   yb = -7 * sin(180 * t1);
            hull() {
                translate([xa, ya, PCB_T + 1.4]) sphere(d = 2.4);
                translate([xb, yb, PCB_T + 1.4]) sphere(d = 2.4);
            }
        }
}

// ---- annotation -----------------------------------------------------------------------------
module annotations() {
    translate([0, 46, LABEL_Z])       label("ESP32-C6 Feather  --[ STEMMA QT ]--  MPU-6050", 5.6);
    translate([0, 37, LABEL_Z])       label("one keyed cable: 3V3 + GND + SDA + SCL. no soldering.", 3.6,
                                            [0.30, 0.30, 0.34]);

    translate([FEATHER_X, -22, LABEL_Z]) label("Feather ESP32-C6", 4.2);
    translate([MPU_X,     -22, LABEL_Z]) label("MPU-6050", 4.2);
    translate([MPU_X,     -28, LABEL_Z]) label("answers at 0x68", 3.4, [0.30, 0.30, 0.34]);

    translate([FEATHER_X - FEATHER_L / 2 - 13, 0, LABEL_Z]) label("USB-C", 3.4, [0.30, 0.30, 0.34]);
    translate([FEATHER_X - FEATHER_L / 2 - 13, -5, LABEL_Z]) label("to PC", 3.4, [0.30, 0.30, 0.34]);

    translate([0, -14, LABEL_Z])      label("either port -- both wired in parallel", 3.4,
                                            [0.30, 0.30, 0.34]);

    translate([0, 20, LABEL_Z])       label("STEMMA QT / Qwiic", 3.6, [0.30, 0.30, 0.34]);

    // the one thing that actually catches people out
    translate([0, -36, LABEL_Z])      label("port stays UNPOWERED until firmware drives IO20 HIGH", 4.0,
                                            [0.72, 0.22, 0.10]);
    translate([0, -42, LABEL_Z])      label("no devices found? drive IO20, then reseat BOTH ends", 3.4,
                                            [0.72, 0.22, 0.10]);
}

feather();
mpu6050();
cable();
annotations();
