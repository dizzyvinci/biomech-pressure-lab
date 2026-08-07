/*
 * fsr_calibrate.ino — stream FSR ADC values for calibration.
 * ----------------------------------------------------------------
 * Board: Adafruit ESP32-C6 Feather   esp32:esp32:adafruit_feather_esp32c6
 *        (SENSING_DEVICES_PLAN.md:587 N1 — this board is the insole/ankle pod.)
 *
 * Procedure (per sensor, several forces across its range):
 *   1. Flash this, open Serial Monitor @115200.
 *   2. Rest a KNOWN weight squarely on ONE FSR pad. Note that column's ADC.
 *   3. Record a row  sensor,force_N,adc  in cal_points.csv
 *      (force_N = mass_kg * 9.81; e.g. a 1 kg weight = 9.81 N).
 *   4. Repeat with ~4-6 different weights per sensor (light -> heavy).
 *   5. Run:  python analysis/calibrate.py cal_points.csv
 *
 * Tip: a small flat cap over the pad spreads the weight; keep it centered.
 *      The printed `fsr_puck` (BIO-FSR-PUCK-01, 12.065 x 12.065 x 4.0 mm) IS
 *      that cap — it is on the desk and this is what it is for.
 *
 * ============================================================================
 * 2026-08-07 — ADDED `FSR_DIRECT` MODE. The mux path is no longer the default.
 * ============================================================================
 * Why: this sketch read 8 channels through a CD74HC4067 analogue mux, and that
 * part cannot be shown to exist. ergonomics/carts/INVENTORY.md gives it THREE
 * mutually exclusive states in one file — :45 "verify on the shelf", :328
 * "assume absent", and a delivered row — and no photo settles it. Breadboards
 * and jumpers are separately and unambiguously NOT owned (:162), so even a
 * present mux has nothing to sit in.
 *
 * What IS owned, verified: an FSR 4-pack (thin-film) plus 2x Adafruit FSR402
 * = SIX sensors, and 25x 10 k resistors for the dividers (Adafruit order
 * #3716034, delivered ~07-28, packing slip photographed IMG_0765).
 *
 * Six sensors fit on the Feather's six analogue pins with no mux at all. That
 * is also exactly the architecture docs/WIRING.md §2 already specifies (FSR
 * zone -> divider node -> A0..A5) and what SENSING_DEVICES_PLAN N1 assigns.
 * The mux was solving a channel-count problem the owned sensor count does not
 * have. FSR_DIRECT is therefore the default; the mux path is preserved intact
 * behind FSR_MUX for whenever a 4067 is confirmed and a 8+ sensor map is built.
 *
 * NOTE ON WIRE: the FSR leads run inside a shoe, not on the head or across a
 * hypermobile joint, so 22 AWG silicone is the correct spec here (WIRING.md:199)
 * — and it is NOT ON HAND (:193 / INVENTORY:478). The owned 28 AWG 10-way
 * silicone ribbon (Adafruit 3890) is reserved for the rib follower loom and for
 * anything worn on the head; do not burn it here. See the CART note in
 * firmware/force_plate/README.md §8.
 *
 * UNTESTED ON HARDWARE. Compiles clean; never run against a physical FSR.
 * ============================================================================
 */
#include <Arduino.h>

#define FSR_DIRECT 0   // 6 sensors straight onto A0..A5. Matches owned hardware.
#define FSR_MUX    1   // 8 sensors via CD74HC4067. Mux is UNVERIFIED on the shelf.

#ifndef FSR_MODE
#define FSR_MODE FSR_DIRECT
#endif

#if FSR_MODE == FSR_MUX
// --- legacy 8-channel mux path (unchanged) ---------------------------------
static const int MUX_SIG = 1;
static const int MUX_S[4] = {2, 3, 4, 5};
static const int N_FSR = 8;

void muxSel(int c) { for (int i = 0; i < 4; i++) digitalWrite(MUX_S[i], (c >> i) & 1); }
int  readFSR(int c) { muxSel(c); delayMicroseconds(6); return analogRead(MUX_SIG); }
int  readFSRmv(int c) { muxSel(c); delayMicroseconds(6); return analogReadMilliVolts(MUX_SIG); }
void fsrBegin() { for (int i = 0; i < 4; i++) pinMode(MUX_S[i], OUTPUT); }

#else
// --- direct path: one ADC pin per sensor, no mux ---------------------------
// A0..A5 are the core's per-board aliases, so this stays correct if the board
// changes. Order matches docs/WIRING.md §2's zone table.
static const int FSR_PIN[6] = {A0, A1, A2, A3, A4, A5};
static const int N_FSR = 6;

int  readFSR(int c)   { return analogRead(FSR_PIN[c]); }
int  readFSRmv(int c) { return analogReadMilliVolts(FSR_PIN[c]); }
void fsrBegin()       { }   // ADC pins need no pinMode

#endif

void setup() {
  Serial.begin(115200);
  fsrBegin();
  analogReadResolution(12);
#if FSR_MODE == FSR_MUX
  analogSetPinAttenuation(MUX_SIG, ADC_11db);
#else
  for (int i = 0; i < N_FSR; i++) analogSetPinAttenuation(FSR_PIN[i], ADC_11db);
#endif
  delay(300);

  Serial.printf("# fsr_calibrate  mode=%s  channels=%d  divider=10k to GND, 3V3 top\n",
                FSR_MODE == FSR_MUX ? "MUX(unverified hw)" : "DIRECT", N_FSR);
  Serial.println("# columns: adc0..adcN then mv0..mvN. Log the adc columns into");
  Serial.println("# cal_points.csv (sensor,force_N,adc) for analysis/calibrate.py.");
  Serial.println("# mv columns are analogReadMilliVolts() - better linearity, same divider.");
  Serial.println("# UNVERIFIED: never run against a physical FSR.");

  for (int i = 0; i < N_FSR; i++) Serial.printf("adc%d ", i);
  for (int i = 0; i < N_FSR; i++) Serial.printf("mv%d%c", i, i < N_FSR - 1 ? ' ' : '\n');
}

void loop() {
  for (int i = 0; i < N_FSR; i++) { Serial.print(readFSR(i));   Serial.print(' '); }
  for (int i = 0; i < N_FSR; i++) { Serial.print(readFSRmv(i)); Serial.print(i < N_FSR - 1 ? ' ' : '\n'); }
  delay(200);   // ~5 Hz — easy to read while you place weights
}
