// i2c_scanner.ino — first bring-up sketch for the ankle-pod sensor chain
//
// WHAT THIS IS FOR
// Before trusting any sensor reading, prove the sensor is physically talking. This sketch pings
// every address on the I2C bus and prints the ones that answer. It is the single best way to
// tell "the sensor is broken" apart from "the STEMMA QT cable isn't seated" -- which, in
// practice, is what it almost always is.
//
// HARDWARE (no soldering -- this is the whole point of the STEMMA QT choice)
//   Adafruit ESP32-C6 Feather  --[STEMMA QT cable]--  MPU-6050
// Plug the cable into the Feather's STEMMA QT port and into either port on the MPU-6050.
// The connectors are keyed; they only go in one way. Power comes over the same cable.
//
// HOW TO RUN
//   1. Arduino IDE -> Tools -> Board -> "Adafruit Feather ESP32-C6"
//        (requires esp32 board core v3.x or newer -- the C6 does NOT exist in core 2.x)
//   2. Tools -> Port -> whichever COM port appears when you plug the Feather in
//   3. Upload
//   4. Tools -> Serial Monitor, set baud to 115200
//
// WHAT YOU SHOULD SEE
//   I2C device found at 0x68   <- MPU-6050 (this is the one you're expecting today)
//
// ADDRESS CHEAT-SHEET for the parts on hand / incoming:
//   0x68  MPU-6050 6-DoF IMU          (on hand)
//   0x4A  BNO085 9-DoF IMU            (incoming -- note: DIFFERENT address from the MPU-6050,
//                                      so firmware that hard-codes 0x68 will not find it)
//   0x51  VCNL4200 proximity/ALS      (on hand)
//   0x70  TCA9548A I2C mux            (on hand)
//   0x5A  DRV2605L haptic driver      (on hand)
//   0x40  PCA9685 PWM driver          (planned -- see balance-exo/docs/HAPTIC_WIRING.md)
//
// TROUBLESHOOTING
//   "No I2C devices found"
//     -> Confirm the sketch you flashed is THIS one. The STEMMA QT port is unpowered at boot and
//        needs IO20 driven HIGH (see the long note above setup()); a sketch that skips that step
//        finds nothing no matter how good the wiring is.
//     -> Reseat BOTH ends of the STEMMA QT cable. This is the cause ~90% of the time.
//     -> Try the sensor's other QT port (they're wired in parallel; either works).
//     -> Confirm the board actually flashed: does the onboard LED/serial banner appear at all?
//        If the sketch itself never ran, this is a board/port problem, not a wiring problem.
//   Sketch won't upload at all
//     -> Wrong board core version. Confirm esp32 core is 3.x, not 2.x.
//     -> Some ESP32 boards need BOOT held while tapping RESET to enter bootloader.
//
// Once you see 0x68, move on to:
//   File -> Examples -> Adafruit MPU6050 -> basic_readings
// which prints live accelerometer + gyro values. That is your first real motion data.

#include <Wire.h>

// ---------------------------------------------------------------------------------------------
// WHAT "DRIVE IO20 HIGH" MEANS, since it is the single most likely reason this sketch finds
// nothing on a rig that is wired perfectly.
//
// IO20 is GPIO pin 20 -- a "general purpose input/output" pin, i.e. one of the chip's own pins
// that firmware can control. Setting it HIGH means driving it to 3.3V (logic 1); LOW means 0V.
//
// On this Feather, IO20 is not a pin you wire anything to. Adafruit wired it to a little
// electronic switch that feeds power to the STEMMA QT connector, so the port can be switched
// off to save battery in deep sleep. The consequence is that the port is UNPOWERED AT BOOT.
// Until these two lines run, the connector has no 3.3V on it, the sensor never starts, and the
// scan below reports "No I2C devices found" -- which looks exactly like a dead sensor or a bad
// cable, and sends you debugging the wrong thing.
//
// This must happen BEFORE Wire.begin(), and the sensor needs a moment to boot once powered.
// ---------------------------------------------------------------------------------------------
#define STEMMA_QT_POWER_PIN 20

void setup() {
  Serial.begin(115200);
  // Wait for the USB serial port to come up. The C6 enumerates over native USB, so without
  // this you'll miss the first few lines of output.
  while (!Serial) delay(10);
  delay(500);

  pinMode(STEMMA_QT_POWER_PIN, OUTPUT);
  digitalWrite(STEMMA_QT_POWER_PIN, HIGH);   // power the STEMMA QT connector
  delay(50);                                  // let the sensor finish its own power-on reset

  Wire.begin();   // uses the board's default STEMMA QT / I2C pins

  Serial.println();
  Serial.println(F("=== I2C scanner -- ankle-pod bring-up ==="));
  Serial.println(F("Expecting 0x68 (MPU-6050) with one STEMMA QT cable attached."));
  Serial.println();
}

void loop() {
  uint8_t found = 0;

  Serial.println(F("Scanning 0x01..0x7E ..."));

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();   // 0 = a device ACKed this address

    if (err == 0) {
      Serial.print(F("  I2C device found at 0x"));
      if (addr < 16) Serial.print('0');
      Serial.print(addr, HEX);

      // Annotate the addresses we actually expect, so the output is self-explaining.
      switch (addr) {
        case 0x68: Serial.print(F("  <- MPU-6050 (6-DoF IMU)"));        break;
        case 0x4A: Serial.print(F("  <- BNO085 (9-DoF IMU)"));          break;
        case 0x51: Serial.print(F("  <- VCNL4200 (proximity/ALS)"));    break;
        case 0x70: Serial.print(F("  <- TCA9548A (I2C mux)"));          break;
        case 0x5A: Serial.print(F("  <- DRV2605L (haptic driver)"));    break;
        case 0x40: Serial.print(F("  <- PCA9685 (PWM driver)"));        break;
        default:                                                        break;
      }
      Serial.println();
      found++;
    }
  }

  if (found == 0) {
    Serial.println(F("  No I2C devices found."));
    Serial.println(F("  -> Reseat BOTH ends of the STEMMA QT cable first; that's usually it."));
  } else {
    Serial.print(F("Done -- "));
    Serial.print(found);
    Serial.println(F(" device(s) responding."));
  }

  Serial.println();
  delay(5000);   // rescan every 5s so you can hot-plug a sensor and watch it appear
}
