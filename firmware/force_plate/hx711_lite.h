// hx711_lite.h — minimal, timeout-guarded HX711 driver. NO EXTERNAL LIBRARY.
// ---------------------------------------------------------------------------
// Why this exists instead of `#include "HX711.h"` (Bogdan Necula's library):
//
//   1. That library IS NOT INSTALLED on this machine. `arduino-cli lib list`
//      returns only Adafruit BusIO / GFX / MPU6050 / SSD1306 / Unified Sensor.
//      FIRMWARE_SCOPE.md flagged "install the 6 missing libraries" as handoff H5
//      on 2026-08-05; it was never actioned, so force_plate.ino did not compile
//      ("fatal error: HX711.h: No such file or directory") on the one subsystem
//      whose parts are printed and on the desk. 60 lines of bit-banging removes
//      that dependency permanently instead of waiting on a handoff.
//
//   2. The library's read path is BLOCKING. `wait_ready()` spins forever if the
//      HX711 is absent, unpowered or miswired. On a rig where the operator has
//      reduced protective sensation (T1DM), a silent hang that looks identical
//      to "no load applied" is the wrong failure mode. Every read here takes a
//      timeout and reports the fault instead of hanging.
//
//   3. Channel A/B gain switching needs a discarded conversion after the gain
//      change. Doing it in-driver keeps that correctness detail in one place.
//
// PROTOCOL (HX711 datasheet, Avia Semiconductor, rev 2011):
//   - DOUT idles HIGH; goes LOW when a conversion is ready.
//   - 24 PD_SCK pulses shift out the result MSB-first, 24-bit two's complement.
//   - 1..3 EXTRA pulses select the gain/channel for the NEXT conversion:
//       25 pulses -> ch A gain 128   (datasheet Table 3)
//       26 pulses -> ch B gain 32
//       27 pulses -> ch A gain 64
//   - PD_SCK HIGH for >60 us powers the chip down. Each individual HIGH period
//     must therefore stay under ~50 us -> the shift runs in a critical section
//     so a FreeRTOS tick or ISR cannot stretch one clock phase past that.
//   - Output rate is a HARDWARE pin (RATE, pin 15): LOW = 10 SPS, HIGH = 80 SPS.
//     Firmware CANNOT change it. See README.md "Sample rate" for the board mod.
//
// UNTESTED ON HARDWARE. Written 2026-08-07; compiles clean, never run against a
// physical HX711 on this bench. See README.md §7.

#pragma once
#include <Arduino.h>

class HX711Lite {
 public:
  enum Gain : uint8_t {
    GAIN_A_128 = 1,  // 25 pulses — channel A, gain 128. Default; best resolution.
    GAIN_B_32  = 2,  // 26 pulses — channel B, gain 32. FIXED gain, ~4x coarser.
    GAIN_A_64  = 3   // 27 pulses — channel A, gain 64.
  };

  // Saturation sentinels: the HX711 rails to these when the bridge input is out
  // of range, which in practice means "cell disconnected" or "E+ not powered".
  static const int32_t SAT_MAX = 0x7FFFFFL;
  static const int32_t SAT_MIN = -0x800000L;

  void begin(int doutPin, int sckPin, Gain g = GAIN_A_128) {
    _dout = doutPin;
    _sck  = sckPin;
    _gain = g;
    // DOUT is push-pull driven by the HX711, so no pull-up is required. This
    // matters because GPIO34..39 on the ESP32 are input-only and have NO
    // internal pull-ups at all — using INPUT_PULLUP there would be a silent
    // no-op. Plain INPUT is correct and portable.
    pinMode(_dout, INPUT);
    pinMode(_sck, OUTPUT);
    digitalWrite(_sck, LOW);   // LOW = chip awake
  }

  bool ready() const { return digitalRead(_dout) == LOW; }

  // Blocking-with-a-ceiling. Returns false on timeout instead of spinning.
  bool waitReady(uint32_t timeoutMs) {
    uint32_t t0 = millis();
    while (!ready()) {
      if ((millis() - t0) >= timeoutMs) return false;
      delay(1);                // yields to FreeRTOS; keeps the idle WDT fed
    }
    return true;
  }

  // Read one conversion. Returns false on timeout (out is untouched).
  bool readRaw(int32_t &out, uint32_t timeoutMs = 250) {
    if (!waitReady(timeoutMs)) { _timeouts++; return false; }

    uint32_t v = 0;
    uint8_t extra = (uint8_t)_gain;   // 1, 2 or 3 pulses after the 24 data bits

    portENTER_CRITICAL(&_mux);
    for (uint8_t i = 0; i < 24; i++) {
      digitalWrite(_sck, HIGH);
      delayMicroseconds(1);           // T3 >= 0.2 us, and must stay < 50 us
      v = (v << 1) | (uint32_t)(digitalRead(_dout) & 1);
      digitalWrite(_sck, LOW);
      delayMicroseconds(1);
    }
    for (uint8_t i = 0; i < extra; i++) {
      digitalWrite(_sck, HIGH);
      delayMicroseconds(1);
      digitalWrite(_sck, LOW);
      delayMicroseconds(1);
    }
    portEXIT_CRITICAL(&_mux);

    if (v & 0x800000UL) v |= 0xFF000000UL;   // sign-extend 24 -> 32 bit
    out = (int32_t)v;
    _reads++;
    return true;
  }

  // Change channel/gain. The HX711 applies it to the NEXT conversion, so the
  // one already in flight must be thrown away or it carries the OLD gain.
  // Callers that alternate A/B must use this, not setGain() alone.
  bool switchGain(Gain g, uint32_t timeoutMs = 250) {
    _gain = g;
    int32_t discard;
    return readRaw(discard, timeoutMs);     // this read clocks the new gain in
  }

  void setGain(Gain g) { _gain = g; }
  Gain gain() const { return _gain; }

  static bool saturated(int32_t raw) { return raw >= SAT_MAX || raw <= SAT_MIN; }

  void powerDown() {
    digitalWrite(_sck, LOW);
    digitalWrite(_sck, HIGH);
    delayMicroseconds(70);        // >60 us HIGH -> power-down (datasheet)
  }

  void powerUp() {
    digitalWrite(_sck, LOW);
    delay(1);
    // After power-up the chip resets to channel A gain 128 regardless of the
    // last setting, so re-assert whatever we were using.
    int32_t discard;
    readRaw(discard, 500);
  }

  uint32_t timeouts() const { return _timeouts; }
  uint32_t reads() const { return _reads; }

 private:
  int _dout = -1, _sck = -1;
  Gain _gain = GAIN_A_128;
  uint32_t _timeouts = 0, _reads = 0;
  portMUX_TYPE _mux = portMUX_INITIALIZER_UNLOCKED;
};
