// force_plate.ino — 4x 50kg half-bridge load cells wired as ONE full Wheatstone
// bridge -> a single HX711 -> total vertical GRF (N, xBW). This matches the cheap
// "4x 50kg load cell + 1 HX711" kit (the bathroom-scale topology): the four corner
// cells sum into one reading. That total-vGRF trace — peak xBW, loading rate — is the
// number the insole can't give, and DIY load-cell rigs reach ICC>0.94 vs a lab plate.
//
// Want per-corner CENTER OF PRESSURE too? The half-bridge kit can't: CoP needs 4 FULL-
// bridge cells on 4 separate HX711 (one channel each) — see the COP_MODE block below and
// docs/build_lab.md. With this kit you get total force only, and CoP already comes from
// the insole / Velostat mat. So the default build is the single-HX711 total-force plate.
//
// Needs the "HX711" Arduino library (Bogdan Necula) — install via Library Manager.
// Wiring the four half-bridge cells into one full bridge: the standard SparkFun "load-cell
// combinator" pattern (each cell has 3 wires; opposite corners take tension vs compression
// so they sum). Calibrate CAL once with a known mass until the reading in kg reads true.

#include "HX711.h"

#define COP_MODE 0                 // 0 = single HX711, total force (matches the cheap kit)
                                   // 1 = 4x HX711 + 4 FULL-bridge cells -> also center of pressure

const float BODY_N = 700.0;        // your body weight in N (for x BW) — set after calibrating

#if COP_MODE == 0
// ---- Default: one HX711, total vertical GRF ----------------------------------------
const int DOUT_PIN = 5;            // HX711 data
const int SCK_PIN  = 4;            // HX711 clock
float     CAL      = -7050;        // scale factor — CALIBRATE with a known mass

HX711 scale;

void setup() {
  Serial.begin(115200);
  scale.begin(DOUT_PIN, SCK_PIN);
  scale.set_scale(CAL);
  scale.tare();                    // zero with the plate empty
  Serial.println("t_ms,total_N,total_BW");
}

void loop() {
  float kg = scale.get_units(1);   // one averaged read
  if (kg < 0) kg = 0;
  float n = kg * 9.81;
  Serial.printf("%lu,%.1f,%.2f\n", millis(), n, n / BODY_N);
  // HX711 ~10 SPS default; tie its RATE pin HIGH for 80 SPS (better for landings).
}

#else
// ---- Upgrade: 4x FULL-bridge cells on 4 HX711 -> force + center of pressure ---------
// Needs four FULL-bridge (4-wire) load cells, not the half-bridge kit. Share the SCK
// clock, one DOUT per cell. Corner-weighted forces give CoP (mm) for balance/sway work.
const int   SCK_PIN     = 4;                       // shared clock
const int   DOUT[4]     = {5, 6, 7, 15};           // one data pin per cell
float       CAL[4]      = {-7050, -7050, -7050, -7050}; // per-cell — CALIBRATE each
const float CORNER_X[4] = {0, 240, 0, 240};        // corner positions (mm) — match your plate
const float CORNER_Y[4] = {0, 0, 240, 240};

HX711 cell[4];

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) {
    cell[i].begin(DOUT[i], SCK_PIN);
    cell[i].set_scale(CAL[i]);
    cell[i].tare();
  }
  Serial.println("t_ms,f0,f1,f2,f3,total_N,total_BW,cop_x_mm,cop_y_mm");
}

void loop() {
  float f[4], tot = 0, mx = 0, my = 0;
  for (int i = 0; i < 4; i++) {
    f[i] = cell[i].get_units(1) * 9.81;            // kg -> N
    if (f[i] < 0) f[i] = 0;
    tot += f[i];
  }
  for (int i = 0; i < 4; i++) { mx += f[i] * CORNER_X[i]; my += f[i] * CORNER_Y[i]; }
  float cx = tot > 1 ? mx / tot : 0, cy = tot > 1 ? my / tot : 0;
  Serial.printf("%lu,%.1f,%.1f,%.1f,%.1f,%.1f,%.2f,%.1f,%.1f\n",
                millis(), f[0], f[1], f[2], f[3], tot, tot / BODY_N, cx, cy);
}
#endif
