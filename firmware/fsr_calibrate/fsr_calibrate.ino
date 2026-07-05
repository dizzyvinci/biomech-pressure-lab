/*
 * fsr_calibrate.ino — stream all 8 FSR ADC values for calibration.
 * ----------------------------------------------------------------
 * Procedure (per sensor, several forces across its range):
 *   1. Flash this, open Serial Monitor @115200.
 *   2. Rest a KNOWN weight squarely on ONE FSR pad. Note that column's ADC.
 *   3. Record a row  sensor,force_N,adc  in cal_points.csv
 *      (force_N = mass_kg * 9.81; e.g. a 1 kg weight = 9.81 N).
 *   4. Repeat with ~4-6 different weights per sensor (light -> heavy), all 8 sensors.
 *   5. Run:  python analysis/calibrate.py cal_points.csv
 *
 * Tip: a small flat cap over the pad spreads the weight; keep it centered.
 * Wiring/pins match the other sketches (CD74HC4067 mux -> GPIO1).
 */
#include <Arduino.h>

static const int MUX_SIG = 1;
static const int MUX_S[4] = {2, 3, 4, 5};

void muxSel(int c){ for (int i = 0; i < 4; i++) digitalWrite(MUX_S[i], (c >> i) & 1); }
int  readFSR(int c){ muxSel(c); delayMicroseconds(6); return analogRead(MUX_SIG); }

void setup(){
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) pinMode(MUX_S[i], OUTPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  delay(300);
  Serial.println("fsr0 fsr1 fsr2 fsr3 fsr4 fsr5 fsr6 fsr7");
}

void loop(){
  for (int i = 0; i < 8; i++){ Serial.print(readFSR(i)); Serial.print(i < 7 ? ' ' : '\n'); }
  delay(200);   // ~5 Hz — easy to read while you place weights
}
