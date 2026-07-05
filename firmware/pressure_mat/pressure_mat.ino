// pressure_mat.ino — Velostat ROWxCOL matrix scan -> a plantar pressure map.
// The printed frame (hardware/pressure_mat.scad) holds a copper-tape row/column grid
// sandwiching a Velostat sheet; each overlap is a pressure cell (resistance drops with
// load). Drive one ROW HIGH at a time (GPIO), read every COLUMN through a CD74HC4067
// mux -> ADC. Streams one frame per line: t_ms then N_ROWS*N_COLS readings (row-major).
//
// Start small (e.g. 8x11) and grow. Two caveats: (1) "ghosting" — current sneaks
// through unpressed cells; ground the inactive columns (or add a diode per cell) to
// reduce it; (2) rows use one GPIO each — for a big matrix drive rows with a shift
// register (74HC595) instead. Pipe the frames to a Python heatmap (see docs/build_lab.md).

const int N_ROWS = 8;
const int N_COLS = 11;
const int ROW_PIN[N_ROWS] = {1, 2, 3, 4, 5, 6, 7, 8};   // one GPIO per row
const int MUX_S[4]        = {9, 10, 11, 12};            // CD74HC4067 select lines
const int MUX_SIG         = 13;                          // mux common -> ADC pin
const int SETTLE_US       = 30;                          // let the ADC settle after switching

void muxSelect(int ch) {
  for (int i = 0; i < 4; i++) digitalWrite(MUX_S[i], (ch >> i) & 1);
}

void setup() {
  Serial.begin(115200);
  for (int r = 0; r < N_ROWS; r++) { pinMode(ROW_PIN[r], OUTPUT); digitalWrite(ROW_PIN[r], LOW); }
  for (int i = 0; i < 4; i++) pinMode(MUX_S[i], OUTPUT);
  Serial.print("# pressure_mat "); Serial.print(N_ROWS); Serial.print("x"); Serial.println(N_COLS);
}

void loop() {
  Serial.print(millis());
  for (int r = 0; r < N_ROWS; r++) {
    digitalWrite(ROW_PIN[r], HIGH);                 // energize this row
    for (int c = 0; c < N_COLS; c++) {
      muxSelect(c);
      delayMicroseconds(SETTLE_US);
      Serial.print(","); Serial.print(analogRead(MUX_SIG));
    }
    digitalWrite(ROW_PIN[r], LOW);
  }
  Serial.println();
  delay(20);                                        // ~50 Hz full frames (8x11)
}
