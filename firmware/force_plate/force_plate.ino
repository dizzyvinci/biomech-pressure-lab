// force_plate.ino — 4x HX711 load cells -> vertical GRF (N, xBW) + center of pressure.
// The printed hardware (hardware/force_plate.scad): 4 feet + top plate, one bar load
// cell per corner. Each cell -> its own HX711 (share the SCK clock, separate DOUT).
// Summed forces = vertical GRF; corner-weighted = center of pressure. Feeds the same
// analysis as the insole (landing xBW, balance COP) but as a true force plate.
//
// Needs the "HX711" Arduino library (Bogdan Necula) — install via Library Manager.
// Calibrate each cell once: put a known mass on that corner, adjust CAL[i] until the
// reading in grams matches (see docs/build_lab.md).

#include "HX711.h"

const int   SCK_PIN   = 4;                         // shared clock
const int   DOUT[4]   = {5, 6, 7, 15};             // one data pin per cell
float       CAL[4]    = {-7050, -7050, -7050, -7050};  // per-cell scale (grams) — CALIBRATE
const float CORNER_X[4] = {0, 240, 0, 240};        // corner positions (mm) — match your plate
const float CORNER_Y[4] = {0, 0, 240, 240};
const float BODY_N    = 700.0;                     // your body weight in N (for x BW)

HX711 cell[4];

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) {
    cell[i].begin(DOUT[i], SCK_PIN);
    cell[i].set_scale(CAL[i]);
    cell[i].tare();                                // zero with the plate empty
  }
  Serial.println("t_ms,f0,f1,f2,f3,total_N,total_BW,cop_x_mm,cop_y_mm");
}

void loop() {
  float f[4], tot = 0, mx = 0, my = 0;
  for (int i = 0; i < 4; i++) {
    f[i] = cell[i].get_units(1) * 9.81 / 1000.0;   // grams -> N
    if (f[i] < 0) f[i] = 0;
    tot += f[i];
  }
  for (int i = 0; i < 4; i++) { mx += f[i] * CORNER_X[i]; my += f[i] * CORNER_Y[i]; }
  float cx = tot > 1 ? mx / tot : 0, cy = tot > 1 ? my / tot : 0;
  Serial.printf("%lu,%.1f,%.1f,%.1f,%.1f,%.1f,%.2f,%.1f,%.1f\n",
                millis(), f[0], f[1], f[2], f[3], tot, tot / BODY_N, cx, cy);
  // HX711 runs ~10 SPS by default; tie its RATE pin high for 80 SPS (better for landings).
}
