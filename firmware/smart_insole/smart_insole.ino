/*
 * Smart Insole — dynamic plantar-pressure + IMU logger
 * ----------------------------------------------------
 * MCU  : ESP32-S3 (Arduino core v3.x)
 * Sense: 8x FSR402 via CD74HC4067 mux -> 1 ADC pin
 *        Adafruit BNO085 IMU (I2C)  ->  fused quaternion + accel
 * Store: microSD (SPI), CSV at ~100 Hz
 * Link : BLE Nordic-UART, notifies rows at ~20 Hz (SD keeps full rate)
 *
 * Button (GPIO14 -> GND): short press = start/stop recording,
 *                         long press  = cycle activity label.
 * LED (GPIO15): solid = recording, blink = idle.
 *
 * Libraries (Library Manager): "Adafruit BNO08x", "SD", core ESP32 BLE.
 * See ../../README.md for wiring + BOM.
 */

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_BNO08x.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ---------- pins ----------
static const int MUX_SIG = 1;                 // ADC1_CH0
static const int MUX_S[4] = {2, 3, 4, 5};     // S0..S3
static const int I2C_SDA = 8, I2C_SCL = 9;
static const int SD_CS = 10, SD_MOSI = 11, SD_SCK = 12, SD_MISO = 13;
static const int PIN_BTN = 14, PIN_LED = 15;

// ---------- config ----------
static const int   NUM_FSR      = 8;
static const uint32_t SAMPLE_HZ = 100;
static const uint32_t SAMPLE_US = 1000000UL / SAMPLE_HZ;
static const int   BLE_DECIMATE = 5;          // BLE every 5th sample (~20 Hz)
const char* ACTIVITIES[] = {"stand","walk","fast_walk","stairs_up","stairs_down","pivot","single_leg"};
static const int NUM_ACT = sizeof(ACTIVITIES)/sizeof(ACTIVITIES[0]);

// ---------- state ----------
Adafruit_BNO08x bno;
sh2_SensorValue_t sv;
bool     recording = false;
int      activity  = 0;
File     logFile;
uint32_t t0_ms = 0, sampleCount = 0;
float    qw=1,qx=0,qy=0,qz=0, ax=0,ay=0,az=0;

// ---------- BLE ----------
#define NUS_SVC  "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX   "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
BLECharacteristic* txChar = nullptr;
bool bleConnected = false;
class SrvCB : public BLEServerCallbacks {
  void onConnect(BLEServer*)    { bleConnected = true; }
  void onDisconnect(BLEServer* s){ bleConnected = false; s->getAdvertising()->start(); }
};

void muxSelect(int ch){ for(int i=0;i<4;i++) digitalWrite(MUX_S[i],(ch>>i)&1); }
int  readFSR(int ch){ muxSelect(ch); delayMicroseconds(6); return analogRead(MUX_SIG); }

void setupBLE(){
  BLEDevice::init("SmartInsole");
  BLEServer* s = BLEDevice::createServer();
  s->setCallbacks(new SrvCB());
  BLEService* svc = s->createService(NUS_SVC);
  txChar = svc->createCharacteristic(NUS_TX, BLECharacteristic::PROPERTY_NOTIFY);
  txChar->addDescriptor(new BLE2902());
  svc->start();
  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(NUS_SVC);
  adv->start();
}

void openNewLog(){
  char name[32];
  int idx = 0;
  do { snprintf(name,sizeof(name),"/log_%03d.csv", idx++); } while (SD.exists(name) && idx < 1000);
  logFile = SD.open(name, FILE_WRITE);
  if (logFile){
    logFile.println("t_ms,activity,fsr0,fsr1,fsr2,fsr3,fsr4,fsr5,fsr6,fsr7,qw,qx,qy,qz,ax,ay,az");
    Serial.printf("Recording -> %s (activity=%s)\n", name, ACTIVITIES[activity]);
  } else Serial.println("!! SD open failed");
  t0_ms = millis(); sampleCount = 0;
}

void handleButton(){
  static uint32_t downAt = 0; static bool wasDown = false;
  bool down = (digitalRead(PIN_BTN) == LOW);
  if (down && !wasDown){ downAt = millis(); wasDown = true; }
  if (!down && wasDown){
    uint32_t held = millis() - downAt; wasDown = false;
    if (held > 800){                                   // long: cycle activity
      activity = (activity + 1) % NUM_ACT;
      Serial.printf("Activity -> %s\n", ACTIVITIES[activity]);
    } else {                                           // short: start/stop
      recording = !recording;
      if (recording) openNewLog();
      else if (logFile){ logFile.flush(); logFile.close(); Serial.println("Stopped."); }
    }
  }
}

void readIMU(){
  if (bno.getSensorEvent(&sv)){
    switch (sv.sensorId){
      case SH2_ROTATION_VECTOR:
        qw=sv.un.rotationVector.real; qx=sv.un.rotationVector.i;
        qy=sv.un.rotationVector.j;    qz=sv.un.rotationVector.k; break;
      case SH2_LINEAR_ACCELERATION:
        ax=sv.un.linearAcceleration.x; ay=sv.un.linearAcceleration.y;
        az=sv.un.linearAcceleration.z; break;
    }
  }
}

void setup(){
  Serial.begin(115200);
  pinMode(PIN_BTN, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT);
  for(int i=0;i<4;i++) pinMode(MUX_S[i], OUTPUT);
  analogReadResolution(12); analogSetAttenuation(ADC_11db);   // 0..~3.3V

  Wire.begin(I2C_SDA, I2C_SCL);
  if (!bno.begin_I2C()) Serial.println("!! BNO085 not found");
  else { bno.enableReport(SH2_ROTATION_VECTOR, 5000); bno.enableReport(SH2_LINEAR_ACCELERATION, 5000); }

  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  if (!SD.begin(SD_CS)) Serial.println("!! SD init failed (BLE stream still works)");

  setupBLE();
  Serial.println("Ready. Short press = start/stop, long press = change activity.");
}

void loop(){
  static uint32_t nextUs = micros();
  handleButton();
  readIMU();

  if ((int32_t)(micros() - nextUs) >= 0){
    nextUs += SAMPLE_US;
    if (recording){
      uint32_t t = millis() - t0_ms;
      int f[NUM_FSR]; for (int i=0;i<NUM_FSR;i++) f[i]=readFSR(i);

      char row[192];
      int n = snprintf(row,sizeof(row),
        "%lu,%s,%d,%d,%d,%d,%d,%d,%d,%d,%.4f,%.4f,%.4f,%.4f,%.3f,%.3f,%.3f",
        (unsigned long)t, ACTIVITIES[activity],
        f[0],f[1],f[2],f[3],f[4],f[5],f[6],f[7], qw,qx,qy,qz, ax,ay,az);

      if (logFile) logFile.println(row);
      if (bleConnected && txChar && (sampleCount % BLE_DECIMATE == 0)){
        row[n++]='\n'; row[n]=0; txChar->setValue((uint8_t*)row, n); txChar->notify();
      }
      if ((sampleCount & 0x7F)==0 && logFile) logFile.flush();   // periodic flush
      sampleCount++;
      digitalWrite(PIN_LED, HIGH);
    } else {
      digitalWrite(PIN_LED, (millis()/500)&1);                   // idle blink
    }
  }
}
