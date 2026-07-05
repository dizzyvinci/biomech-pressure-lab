/*
 * all_day_logger.ino — continuous all-day plantar-pressure + motion logger
 * ------------------------------------------------------------------------
 * Path 2 "tracking" build. Optimized for battery life + wear-most-of-a-day.
 *
 * Reads 8x FSR (via CD74HC4067 mux) + BNO085 IMU, logs CSV to microSD.
 * Records a MODE column (shoe / barefoot) so you can compare the two.
 *
 * Differences vs firmware/smart_insole (session logger):
 *   - auto-starts logging on boot (no button needed to begin)
 *   - default 50 Hz (≈2x runtime vs 100 Hz); change SAMPLE_HZ to trade off
 *   - batched SD writes (power + card longevity)
 *   - BLE OFF (biggest power saver) — offload by pulling the SD card
 *   - 80 MHz CPU + idle between samples
 *   - logs battery voltage; rotates to a new file every ~40 MB
 *   - Button: SHORT = cycle activity phase (walk/stand/bounce/other); LONG = shoe<->barefoot (new file)
 *     The `phase` column lets analysis/day_summary.py split a day into gait vs at-rest bounce
 *     for the CPTS / nerve-fascia dose model (docs/nerve_fascia.md).
 *
 * MCU: ESP32-S3 (in the ankle pod, hardware/ankle_pod.scad).
 * Libraries (Library Manager): "Adafruit BNO08x", "SD".
 * Runtime rule of thumb @50 Hz SD-logging: ~4 h / 500 mAh, ~8-10 h / 1000 mAh.
 */
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_BNO08x.h>

// ---- pins (match the ankle-pod wiring) ----
static const int MUX_SIG = 1;                 // ADC1_CH0
static const int MUX_S[4] = {2, 3, 4, 5};
static const int I2C_SDA = 8, I2C_SCL = 9;
static const int SD_CS = 10, SD_MOSI = 11, SD_SCK = 12, SD_MISO = 13;
static const int PIN_BTN = 14, PIN_LED = 15;
static const int PIN_VBAT = 16;               // LiPo via 2:1 divider (optional; comment out use if unused)

// ---- config (tune battery vs resolution) ----
static const int      NUM_FSR      = 8;
static const uint16_t SAMPLE_HZ    = 50;      // 50 Hz = long runtime; 100 Hz = finer
static const int      FLUSH_EVERY  = 200;     // batch SD flush (power + wear)
static const uint32_t ROTATE_BYTES = 40UL * 1024 * 1024;
static const float    VBAT_DIV     = 2.0f;    // hardware divider ratio on PIN_VBAT

// ---- state ----
Adafruit_BNO08x bno; sh2_SensorValue_t sv;
File logf;
uint32_t rowCount = 0, fileBytes = 0, t0 = 0, fileIdx = 0;
bool  barefoot = false;                       // false = shoe, true = barefoot
const char* PHASES[4] = {"walk", "stand", "bounce", "other"};   // short-press cycles these
int   phaseIdx = 0;                           // -> `phase` column (day_summary segments on it)
float qw = 1, qx = 0, qy = 0, qz = 0, ax = 0, ay = 0, az = 0;
char  rowbuf[210];

void muxSel(int c){ for (int i = 0; i < 4; i++) digitalWrite(MUX_S[i], (c >> i) & 1); }
int  readFSR(int c){ muxSel(c); delayMicroseconds(6); return analogRead(MUX_SIG); }
float readVbat(){ return (analogReadMilliVolts(PIN_VBAT) / 1000.0f) * VBAT_DIV; }

void openLog(){
  if (logf) logf.close();
  char name[40];
  snprintf(name, sizeof(name), "/day_%s_%03u.csv", barefoot ? "bare" : "shoe", (unsigned)fileIdx++);
  logf = SD.open(name, FILE_WRITE);
  if (logf) logf.println("t_ms,mode,phase,fsr0,fsr1,fsr2,fsr3,fsr4,fsr5,fsr6,fsr7,qw,qx,qy,qz,ax,ay,az,vbat");
  fileBytes = 0;
}

void readIMU(){
  if (bno.getSensorEvent(&sv)){
    if (sv.sensorId == SH2_ROTATION_VECTOR){
      qw = sv.un.rotationVector.real; qx = sv.un.rotationVector.i;
      qy = sv.un.rotationVector.j;    qz = sv.un.rotationVector.k;
    } else if (sv.sensorId == SH2_LINEAR_ACCELERATION){
      ax = sv.un.linearAcceleration.x; ay = sv.un.linearAcceleration.y; az = sv.un.linearAcceleration.z;
    }
  }
}

void handleButton(){
  static uint32_t down = 0; static bool was = false;
  bool d = (digitalRead(PIN_BTN) == LOW);
  if (d && !was){ down = millis(); was = true; }
  if (!d && was){
    was = false; uint32_t held = millis() - down;
    if (held > 800){ barefoot = !barefoot; openLog(); }            // long: shoe<->barefoot, new file
    else { phaseIdx = (phaseIdx + 1) % 4; }                        // short: cycle activity phase
  }
}

void setup(){
  setCpuFrequencyMhz(80);                       // power save
  pinMode(PIN_BTN, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT);
  for (int i = 0; i < 4; i++) pinMode(MUX_S[i], OUTPUT);
  analogReadResolution(12); analogSetAttenuation(ADC_11db);

  Wire.begin(I2C_SDA, I2C_SCL);
  if (bno.begin_I2C()){ bno.enableReport(SH2_ROTATION_VECTOR, 20000); bno.enableReport(SH2_LINEAR_ACCELERATION, 20000); }

  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  while (!SD.begin(SD_CS)){ digitalWrite(PIN_LED, (millis() / 150) & 1); delay(150); }  // wait for card

  t0 = millis(); openLog();
}

void loop(){
  static uint32_t nextUs = micros();
  const uint32_t periodUs = 1000000UL / SAMPLE_HZ;
  handleButton(); readIMU();

  if ((int32_t)(micros() - nextUs) >= 0){
    nextUs += periodUs;
    uint32_t t = millis() - t0;
    int f[NUM_FSR]; for (int i = 0; i < NUM_FSR; i++) f[i] = readFSR(i);
    int n = snprintf(rowbuf, sizeof(rowbuf),
      "%lu,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%.3f,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%.2f",
      (unsigned long)t, barefoot ? "barefoot" : "shoe", PHASES[phaseIdx],
      f[0],f[1],f[2],f[3],f[4],f[5],f[6],f[7], qw,qx,qy,qz, ax,ay,az, readVbat());
    if (logf){ logf.println(rowbuf); fileBytes += n + 2; }
    if ((++rowCount % FLUSH_EVERY) == 0 && logf){ logf.flush(); digitalWrite(PIN_LED, !digitalRead(PIN_LED)); }
    if (fileBytes > ROTATE_BYTES) openLog();
  } else {
    delayMicroseconds(200);                      // idle a touch between samples
  }
}
