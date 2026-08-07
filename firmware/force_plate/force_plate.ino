/*
 * force_plate.ino — pressure/force acquisition for biomech-pressure-lab.
 * ============================================================================
 * Load cells (HX711) + FSR pucks -> calibrated newtons -> condition-tagged CSV
 * on Serial and (when a card reader exists) on microSD.
 *
 * Board:  ESP32-WROOM-32 DevKitC  (Elegoo ESP-32 3-pack)   esp32:esp32:esp32
 *         The ESP32-C6 Feather is NOT used here — SENSING_DEVICES_PLAN.md:587
 *         assigns the Feather to the worn insole+ankle pod (N1). The force
 *         plate gets a plain devkit, per FIRMWARE_SCOPE.md's board assignment.
 *
 * ----------------------------------------------------------------------------
 * WHAT THIS IS NOT, AND WHY THAT IS IN THE FIRMWARE AND NOT JUST THE DOCS
 * ----------------------------------------------------------------------------
 * hardware/BENCH_NEXT_STEPS.md §0 established two things about the parts that
 * are physically on the desk today:
 *
 *   - `force_plate.stl` is ONE `foot()` bracket (19.0 x 26.0 x 21.0 mm), not a
 *     plate. The rig needs 4 feet + 4 top_bosses + a top. You have 1 / 0 / 0.
 *   - That foot printed in plain PETG at <=52 % effective density, against a
 *     PRINT_CARD spec of PA-CF/PETG-CF at 100 % infill. It is a dimensional
 *     fit-check coupon.
 *
 * So NOBODY STANDS ON THIS. That is not a disclaimer, it is enforced below by
 * MAX_BENCH_N: any total above 250 N latches an overload fault, stops logging,
 * and requires an explicit CLEAR. 250 N is ~25 kg — comfortably above any
 * hand-press or bench mass you would legitimately use, and far below the ~779 N
 * a single sole sees. Reduced protective sensation (T1DM) means the operator
 * may not feel a corner bracket digging in or a rig starting to fail, so the
 * ceiling lives in code where it does not depend on being felt.
 *
 * ----------------------------------------------------------------------------
 * SAFETY POSTURE — hEDS + T1DM as firmware constraints
 * ----------------------------------------------------------------------------
 *  * NOTHING HERE HEATS, VIBRATES OR MOVES. This subsystem drives no motor, no
 *    heater, no servo, no haptic. The only output pin is the 3 mA status LED.
 *    There is therefore no duty-cycle bound to state, because there is no duty
 *    to bound — that is the honest answer, not an omission.
 *  * HARD INPUT LIMIT: MAX_BENCH_N (250 N), latching. See above.
 *  * SESSION CAP: MAX_SESSION_MS (20 min), auto-stop. An unattended rig pressing
 *    on an insensate foot is the failure this bounds.
 *  * TASK WATCHDOG: 8 s, panic-on-timeout, fed once per loop. Every HX711 read
 *    is timeout-guarded (hx711_lite.h), so an absent or miswired amp reports
 *    #FAULT hx711_timeout instead of hanging in a way that looks like "no load".
 *  * The HX711 excites the bridge at ~4.3 V through ~1 k, i.e. ~4 mA. No thermal
 *    path to skin exists in this circuit at all.
 *
 * ----------------------------------------------------------------------------
 * CONDITIONS ARE COORDINATES — enforced, not requested
 * ----------------------------------------------------------------------------
 * A force trace with no posture / load / footwear attached is not data, it is a
 * number. START is REFUSED until all five condition fields are set, every row
 * carries a cond_id, and changing any field mid-session increments cond_id and
 * rolls to a new SD file. Bring-up without a condition is still possible via
 * RAW, which is prefixed #RAW, is never written to SD, and is not CSV.
 *
 * ----------------------------------------------------------------------------
 * BUGS FIXED FROM THE PREVIOUS REVISION OF THIS FILE (all real, all silent)
 * ----------------------------------------------------------------------------
 *  B1. `#include "HX711.h"` — library not installed on this machine, so this
 *      sketch did not compile at all. Replaced by hx711_lite.h (no dependency).
 *  B2. DOUT_PIN was GPIO5 — an ESP32 STRAPPING pin. HX711 DOUT is pulled LOW
 *      whenever a conversion is ready, so a powered amp can hold GPIO5 low
 *      across reset and change the boot mode.
 *  B3. The COP_MODE pin map was DOUT[4] = {5, 6, 7, 15}. GPIO6 and GPIO7 are
 *      bonded to the WROOM-32's internal SPI FLASH — driving them crashes the
 *      chip. GPIO15 is a second strapping pin. Three of those four pins were
 *      unusable, which is what happens to a code path nobody could build.
 *  B4. `const float BODY_N = 700.0` hard-coded a body weight and divided every
 *      reported value by it. analysis/balance.py already refuses to scale by an
 *      unsourced body constant (see its FOOT_L_MM enforcement note). Body mass
 *      is now UNSET by default; bw_ratio is emitted empty until BW <kg> is given
 *      and the value is recorded in the file header.
 *  B5. No read timeout anywhere -> indefinite hang on a missing amp.
 *  B6. Calibration lived in a source constant, so it was lost on every reflash.
 *      Offsets and scale factors now persist in NVS.
 *
 * ----------------------------------------------------------------------------
 * UNTESTED ON HARDWARE. Compiles clean (see README §7 for the exact command and
 * byte count). It has never been flashed, no serial port has been opened, and
 * no HX711, load cell or FSR has been connected. Treat every number it prints
 * as unverified until the bench procedure in README §6 has been run.
 * ============================================================================
 */

#include <Arduino.h>
#include <Preferences.h>
#include <SPI.h>
#include <SD.h>
#include <time.h>
#include <sys/time.h>
#include "esp_task_wdt.h"
#include "hx711_lite.h"

// ===========================================================================
// 1. BUILD CONFIGURATION
// ===========================================================================

#define FW_NAME     "force_plate"
#define FW_VERSION  "2.0.0"
#define FW_DATE     "2026-08-07"

// --- Acquisition mode ------------------------------------------------------
// MODE_TOTAL  1x HX711, channel A. Four 50 kg HALF-bridge cells combined into
//             ONE full Wheatstone bridge (the bathroom-scale topology that the
//             owned ~$8.49 kit actually is). Gives TOTAL vertical force only.
//             *** THIS IS THE ONLY MODE THE OWNED HARDWARE SUPPORTS. ***
//             ergonomics/carts/INVENTORY.md:259 and FIRMWARE_SCOPE.md's parts
//             ledger both record "4x 50 kg load cell + HX711 | 1 set" — ONE
//             amplifier. Not four. That count is what decides total-force vs
//             centre-of-pressure, and it decides total-force.
//
// MODE_AP     1x HX711, channels A AND B. The four half-bridge cells are split
//             into TWO full bridges (front pair, rear pair) instead of one.
//             Yields total force PLUS a 1-D anterior/posterior CoP with zero
//             purchase. Channel B's gain is FIXED at 32 vs A's 128, so the rear
//             line is ~4x coarser — real, but not equivalent to a 4-cell rig.
//             UNTESTED, and it requires rewiring the cell harness.
//
// MODE_COP4   4x HX711 sharing a clock. Full 2-D centre of pressure. Needs
//             3 MORE HX711 amplifiers (~$9 total) -> see README §8 CART. The
//             code is here and compiles; the parts are not on the shelf.
#define MODE_TOTAL 0
#define MODE_AP    1
#define MODE_COP4  2

#ifndef ACQ_MODE
#define ACQ_MODE MODE_TOTAL
#endif

// --- Safety ceilings. These are the hard limits; do not raise them casually. -
static const float    MAX_BENCH_N     = 250.0f;      // latching overload trip
static const uint32_t MAX_SESSION_MS  = 20UL * 60UL * 1000UL;   // 20 min cap
static const uint32_t WDT_TIMEOUT_MS  = 8000;
// Set to 1 ONLY after the rig has been proof-loaded and reprinted to the
// PRINT_CARD structural spec. It gates nothing electrical; it gates the banner
// and the overload ceiling, and it is deliberately awkward to flip.
#define ALLOW_BODY_LOAD 0

// ===========================================================================
// 2. PIN MAP — ESP32-WROOM-32 DevKitC
// ===========================================================================
// Chosen against the WROOM-32 constraints, not by convenience:
//   - GPIO6..11  : bonded to internal SPI flash. NEVER USE. (killed the old B3)
//   - GPIO0,2,12,15 : strapping pins. Avoided for anything an external part drives.
//   - GPIO34..39 : INPUT-ONLY, no pull-ups. Perfect for HX711 DOUT, which is a
//                  push-pull output from the amp and needs no pull-up.
//   - GPIO32..39 : ADC1. Usable with WiFi on; ADC2 is not. FSRs go here.
//   - GPIO5      : VSPI default CS. It IS a strapping pin, but CS idles HIGH,
//                  which is the level the strap wants, so it is safe as CS.

static const int PIN_HX_SCK   = 27;   // shared PD_SCK for every HX711
static const int PIN_HX_DOUT0 = 34;   // amp 0 — the only one the kit provides
static const int PIN_HX_DOUT1 = 35;   // amps 1..3 are MODE_COP4 only (not owned)
static const int PIN_HX_DOUT2 = 36;
static const int PIN_HX_DOUT3 = 39;

static const int PIN_FSR_A    = 32;   // ADC1_CH4 — fsr_puck / FSR402 #1
static const int PIN_FSR_B    = 33;   // ADC1_CH5 — FSR402 #2

static const int PIN_SD_CS    = 5;    // VSPI
static const int PIN_SD_SCK   = 18;
static const int PIN_SD_MOSI  = 23;
static const int PIN_SD_MISO  = 19;

static const int PIN_LED      = 2;    // onboard blue LED, ~3 mA. Only output pin.

#if ACQ_MODE == MODE_COP4
static const int N_CELLS = 4;
#elif ACQ_MODE == MODE_AP
static const int N_CELLS = 2;         // two logical channels on one amp
#else
static const int N_CELLS = 1;
#endif

// ===========================================================================
// 3. STATE
// ===========================================================================

HX711Lite  hx[4];
Preferences prefs;

// --- Calibration, persisted in NVS -----------------------------------------
struct CellCal {
  int32_t offset;      // raw counts at zero load (tare)
  float   scale_cpn;   // counts per NEWTON. 0 => uncalibrated.
};
CellCal cal[4] = {{0, 0.0f}, {0, 0.0f}, {0, 0.0f}, {0, 0.0f}};

float plate_ap_mm = 240.0f;   // front-line to rear-line spacing (force_plate.scad PLATE)
float plate_ml_mm = 240.0f;
float body_kg     = 0.0f;     // 0 => UNSET. bw_ratio stays blank. See B4.

// --- Condition. Conditions are coordinates: none of these may be empty. -----
struct Condition {
  char posture[24];   // stand_2ft | stand_1ft_L | stand_1ft_R | seated | press_hand
  char load[24];      // bw_full | bw_partial | mass_only | hand
  char footwear[24];  // barefoot | sock | shoe_<name> | orthotic_<name>
  char side[8];       // L | R | both | na
  char surface[24];   // hard | foam | carpet | plate_bare
  char note[48];
};
Condition cond = {"", "", "", "", "", ""};
uint16_t cond_id = 0;

// --- Session ---------------------------------------------------------------
uint32_t session_no   = 0;
bool     streaming    = false;
bool     raw_mode     = false;
uint32_t session_t0   = 0;
uint16_t sample_win   = 5;      // median-trim window, 1..15
uint32_t row_count    = 0;

bool  sd_present      = false;
File  logfile;
char  logpath[40]     = "";

// --- Fault flags emitted on every row --------------------------------------
static const uint16_t F_HX_TIMEOUT   = 0x0001;
static const uint16_t F_HX_SAT       = 0x0002;
static const uint16_t F_OVERLOAD     = 0x0004;
static const uint16_t F_NOT_TARED    = 0x0008;
static const uint16_t F_NOT_CAL      = 0x0010;
static const uint16_t F_COND_UNSET   = 0x0020;
static const uint16_t F_SD_FAIL      = 0x0040;
static const uint16_t F_EPOCH_UNSET  = 0x0080;
static const uint16_t F_SESSION_CAP  = 0x0100;

uint16_t sticky_flags = 0;
bool     overload_latched = false;
bool     epoch_set = false;

// ===========================================================================
// 4. HELPERS
// ===========================================================================

static float trimmedMean(float *b, int n) {
  // maker hack, docs/maker_hacks.md: median-then-trimmed-mean. A plain average
  // SMEARS the HX711's impulse spikes across the window; sorting and dropping
  // the outer quartiles rejects them first. Kept from the previous revision
  // because it is the right filter — only the plumbing around it changed.
  for (int i = 1; i < n; i++) {
    float k = b[i]; int j = i - 1;
    while (j >= 0 && b[j] > k) { b[j + 1] = b[j]; j--; }
    b[j + 1] = k;
  }
  int lo = n / 4, hi = n - n / 4;
  if (hi <= lo) { lo = 0; hi = n; }
  float s = 0;
  for (int i = lo; i < hi; i++) s += b[i];
  return s / (float)(hi - lo);
}

// Read one logical channel as RAW counts, averaged over `n` conversions.
// Returns false and sets flags if the amp does not answer.
static bool readCellRaw(int ch, int n, float &outRaw, uint16_t &flags) {
  if (n < 1) n = 1;
  if (n > 15) n = 15;
  float buf[15];
  int got = 0;

  for (int i = 0; i < n; i++) {
#if ACQ_MODE == MODE_AP
    // One amp, two channels: A = front pair, B = rear pair. switchGain() burns
    // one conversion because the HX711 applies gain to the NEXT sample.
    HX711Lite::Gain want = (ch == 0) ? HX711Lite::GAIN_A_128 : HX711Lite::GAIN_B_32;
    if (hx[0].gain() != want) {
      if (!hx[0].switchGain(want)) { flags |= F_HX_TIMEOUT; break; }
    }
    int amp = 0;
#else
    int amp = ch;
#endif
    int32_t r;
    if (!hx[amp].readRaw(r)) { flags |= F_HX_TIMEOUT; break; }
    if (HX711Lite::saturated(r)) flags |= F_HX_SAT;
    buf[got++] = (float)r;
  }

  if (got == 0) return false;
  outRaw = trimmedMean(buf, got);
  return true;
}

static bool conditionComplete() {
  return cond.posture[0] && cond.load[0] && cond.footwear[0]
      && cond.side[0] && cond.surface[0];
}

static void isoUtc(char *buf, size_t n) {
  if (!epoch_set) { snprintf(buf, n, ""); return; }
  time_t now = time(nullptr);
  struct tm tmv;
  gmtime_r(&now, &tmv);
  strftime(buf, n, "%Y-%m-%dT%H:%M:%SZ", &tmv);
}

static void saveCal() {
  prefs.begin("fplate", false);
  for (int i = 0; i < 4; i++) {
    char k[12];
    snprintf(k, sizeof(k), "off%d", i); prefs.putInt(k, cal[i].offset);
    snprintf(k, sizeof(k), "scl%d", i); prefs.putFloat(k, cal[i].scale_cpn);
  }
  prefs.putFloat("ap_mm", plate_ap_mm);
  prefs.putFloat("ml_mm", plate_ml_mm);
  prefs.putFloat("bodykg", body_kg);
  prefs.end();
  Serial.println("#OK cal saved to NVS");
}

static void loadCal() {
  prefs.begin("fplate", true);
  for (int i = 0; i < 4; i++) {
    char k[12];
    snprintf(k, sizeof(k), "off%d", i); cal[i].offset    = prefs.getInt(k, 0);
    snprintf(k, sizeof(k), "scl%d", i); cal[i].scale_cpn = prefs.getFloat(k, 0.0f);
  }
  plate_ap_mm = prefs.getFloat("ap_mm", 240.0f);
  plate_ml_mm = prefs.getFloat("ml_mm", 240.0f);
  body_kg     = prefs.getFloat("bodykg", 0.0f);
  prefs.end();
}

static uint32_t nextSession() {
  prefs.begin("fplate", false);
  uint32_t s = prefs.getUInt("sess", 0) + 1;
  prefs.putUInt("sess", s);
  prefs.end();
  return s;
}

static const char *modeName() {
#if ACQ_MODE == MODE_COP4
  return "COP4";
#elif ACQ_MODE == MODE_AP
  return "AP";
#else
  return "TOTAL";
#endif
}

// ===========================================================================
// 5. CSV / LOG FORMAT
// ===========================================================================
// One header block of '#' comment lines, then one #COLS line, then plain CSV.
// Every consumer in analysis/ already skips '#'. The `activity` column is the
// posture verbatim, which is what analysis/balance.py's group_col() looks for.
//
//   t_ms       ms since boot, monotonic. ALWAYS present, never wrong.
//   iso_utc    wall clock, empty unless TIME <epoch> was sent. There is NO RTC
//              on this machine (ergonomics/carts/INVENTORY.md has no RTC row),
//              so wall time can only come from the host. An empty column is the
//              truthful answer, not a fabricated one.
//   sess       NVS session counter, survives reflash
//   cond_id    increments on ANY condition change; joins a row to its coordinates
//   activity   = cond.posture
//   total_n    calibrated total vertical force, newtons
//   ch0_n..    per-channel force, newtons (MODE_AP: front/rear; COP4: 4 corners)
//   cop_ap_mm  anterior/posterior CoP, blank in MODE_TOTAL (1 channel = no CoP)
//   cop_ml_mm  medial/lateral CoP, MODE_COP4 only
//   bw_ratio   total_n / (body_kg*9.80665); BLANK while body_kg is unset (B4)
//   fsr0_adc   raw 12-bit ADC — the column analysis/calibrate.py expects
//   fsr0_mv    calibrated millivolts from analogReadMilliVolts(); better data,
//              added alongside rather than replacing, so the existing fit still runs
//   flags      hex bitmask, see section 3

static void writeHeader(Print &p) {
  char iso[28]; isoUtc(iso, sizeof(iso));
  p.printf("# %s v%s (%s)  mode=%s  cells=%d\n", FW_NAME, FW_VERSION, FW_DATE, modeName(), N_CELLS);
  p.printf("# session=%lu  boot_ms=%lu  iso_utc=%s\n", (unsigned long)session_no, (unsigned long)millis(), iso);
  p.printf("# cond_id=%u posture=%s load=%s footwear=%s side=%s surface=%s note=%s\n",
           cond_id, cond.posture, cond.load, cond.footwear, cond.side, cond.surface, cond.note);
  p.printf("# body_kg=%s\n", body_kg > 0 ? String(body_kg, 2).c_str() : "UNSET");
  p.printf("# geom_ap_mm=%.1f geom_ml_mm=%.1f win=%u\n", plate_ap_mm, plate_ml_mm, sample_win);
  for (int i = 0; i < N_CELLS; i++)
    p.printf("# cal%d offset=%ld scale_counts_per_N=%.4f\n", i, (long)cal[i].offset, cal[i].scale_cpn);
  p.printf("# max_bench_n=%.1f session_cap_ms=%lu allow_body_load=%d\n",
           MAX_BENCH_N, (unsigned long)MAX_SESSION_MS, ALLOW_BODY_LOAD);
  p.println("# UNVERIFIED: this firmware has never been run against a physical HX711.");
  p.println("#COLS t_ms,iso_utc,sess,cond_id,activity,total_n,ch0_n,ch1_n,ch2_n,ch3_n,"
            "cop_ap_mm,cop_ml_mm,bw_ratio,fsr0_adc,fsr0_mv,fsr1_adc,fsr1_mv,flags");
}

static bool openLogFile() {
  if (!sd_present) return false;
  if (!SD.exists("/plog")) SD.mkdir("/plog");
  snprintf(logpath, sizeof(logpath), "/plog/S%04lu_C%03u.csv",
           (unsigned long)session_no, cond_id);
  logfile = SD.open(logpath, FILE_WRITE);
  if (!logfile) { sticky_flags |= F_SD_FAIL; return false; }
  writeHeader(logfile);
  logfile.flush();
  Serial.printf("#OK logging to %s\n", logpath);
  return true;
}

// ===========================================================================
// 6. COMMAND PARSER
// ===========================================================================

static void printHelp() {
  Serial.println(F(
    "# --- commands -------------------------------------------------------\n"
    "# ID                 firmware id, mode, pin map\n"
    "# TIME <epoch_s>     set wall clock (no RTC exists; host must supply it)\n"
    "# COND k=v [k=v...]  posture= load= footwear= side= surface= note=\n"
    "# COND?              show current condition + completeness\n"
    "# BW <kg>            body mass for bw_ratio. Omit and the column stays blank.\n"
    "# GEOM <ap_mm> <ml_mm>   plate geometry for CoP\n"
    "# WIN <1..15>        median-trim window per sample\n"
    "# TARE [n]           zero every channel (n conversions, default 24)\n"
    "# CAL <ch> <kg>      scale factor from a known mass on channel <ch>\n"
    "# SHOW               calibration + fault state\n"
    "# SAVE / RELOAD      persist / re-read calibration in NVS\n"
    "# ZERO               60 s tare-drift check, prints spread in newtons\n"
    "# RAW                stream raw counts for bring-up (NOT data, never on SD)\n"
    "# START / STOP       begin / end a condition-tagged CSV session\n"
    "# CLEAR              clear a latched overload\n"
    "# SD?                card status\n"));
}

static void cmdId() {
  Serial.printf("#ID %s v%s %s mode=%s cells=%d core=esp32\n",
                FW_NAME, FW_VERSION, FW_DATE, modeName(), N_CELLS);
  Serial.printf("#PINS hx_sck=%d hx_dout=[%d,%d,%d,%d] fsr=[%d,%d] sd_cs=%d led=%d\n",
                PIN_HX_SCK, PIN_HX_DOUT0, PIN_HX_DOUT1, PIN_HX_DOUT2, PIN_HX_DOUT3,
                PIN_FSR_A, PIN_FSR_B, PIN_SD_CS, PIN_LED);
}

static void setCondField(const char *k, const char *v) {
  if      (!strcmp(k, "posture"))  strlcpy(cond.posture,  v, sizeof(cond.posture));
  else if (!strcmp(k, "load"))     strlcpy(cond.load,     v, sizeof(cond.load));
  else if (!strcmp(k, "footwear")) strlcpy(cond.footwear, v, sizeof(cond.footwear));
  else if (!strcmp(k, "side"))     strlcpy(cond.side,     v, sizeof(cond.side));
  else if (!strcmp(k, "surface"))  strlcpy(cond.surface,  v, sizeof(cond.surface));
  else if (!strcmp(k, "note"))     strlcpy(cond.note,     v, sizeof(cond.note));
  else { Serial.printf("#ERR unknown condition key '%s'\n", k); return; }
  cond_id++;
}

static void cmdCond(char *args) {
  char *tok = strtok(args, " ");
  while (tok) {
    char *eq = strchr(tok, '=');
    if (eq) { *eq = 0; setCondField(tok, eq + 1); }
    tok = strtok(nullptr, " ");
  }
  Serial.printf("#COND id=%u posture=%s load=%s footwear=%s side=%s surface=%s note=%s complete=%d\n",
                cond_id, cond.posture, cond.load, cond.footwear, cond.side,
                cond.surface, cond.note, conditionComplete() ? 1 : 0);
}

static void cmdTare(int n) {
  if (n < 1) n = 24;
  if (n > 15) n = 15;   // trimmedMean buffer ceiling; 15 conversions ~1.5 s @10 SPS
  bool ok = true;
  for (int c = 0; c < N_CELLS; c++) {
    float raw; uint16_t f = 0;
    if (readCellRaw(c, n, raw, f)) {
      cal[c].offset = (int32_t)raw;
      Serial.printf("#OK tare ch%d offset=%ld\n", c, (long)cal[c].offset);
    } else {
      Serial.printf("#FAULT tare ch%d NO RESPONSE from HX711 (check E+/E-, VCC, DOUT, CLK)\n", c);
      ok = false;
    }
  }
  if (ok) sticky_flags &= ~F_NOT_TARED;
}

static void cmdCal(int ch, float known_kg) {
  if (ch < 0 || ch >= N_CELLS) { Serial.println("#ERR channel out of range"); return; }
  if (known_kg <= 0)           { Serial.println("#ERR known mass must be > 0 kg"); return; }

  float raw; uint16_t f = 0;
  if (!readCellRaw(ch, 15, raw, f)) { Serial.println("#FAULT no HX711 response"); return; }

  float delta = raw - (float)cal[ch].offset;
  if (fabsf(delta) < 1000.0f) {
    // Not a style rule — a resolution one. A 200 kg-capacity rig reading a
    // 200 g reference sits in the noise, and a scale factor fitted there is
    // worthless. Say so and name the fix rather than emitting a bad constant.
    Serial.printf("#ERR delta=%.0f counts is too small to calibrate (need >1000).\n", delta);
    Serial.println("#ERR Use a HEAVIER reference. A 4x 50 kg rig needs kilograms, not grams.");
    Serial.println("#ERR Free option: a sealed 1 US gal jug of water = 3.785 L ~ 3.78 kg at 20 C.");
    Serial.println("#ERR See README section 8 (CART) for the hanging scale / mass set line.");
    return;
  }
  cal[ch].scale_cpn = delta / (known_kg * 9.80665f);
  Serial.printf("#OK cal ch%d scale=%.4f counts/N  (delta=%.0f counts for %.3f kg)\n",
                ch, cal[ch].scale_cpn, delta, known_kg);
  sticky_flags &= ~F_NOT_CAL;
}

static void cmdShow() {
  Serial.printf("#SHOW mode=%s cells=%d win=%u body_kg=%s geom_ap=%.1f geom_ml=%.1f\n",
                modeName(), N_CELLS, sample_win,
                body_kg > 0 ? String(body_kg, 2).c_str() : "UNSET",
                plate_ap_mm, plate_ml_mm);
  for (int i = 0; i < N_CELLS; i++)
    Serial.printf("#SHOW ch%d offset=%ld scale=%.4f counts/N %s\n",
                  i, (long)cal[i].offset, cal[i].scale_cpn,
                  cal[i].scale_cpn == 0.0f ? "<-- UNCALIBRATED" : "");
  Serial.printf("#SHOW flags=0x%04X overload_latched=%d sd=%d epoch=%d cond_complete=%d\n",
                sticky_flags, overload_latched, sd_present, epoch_set, conditionComplete());
  Serial.printf("#SHOW hx0 reads=%lu timeouts=%lu\n",
                (unsigned long)hx[0].reads(), (unsigned long)hx[0].timeouts());
}

static void cmdZeroDrift() {
  // The single most useful bring-up test: is the rig thermally settled?
  // HX711 + strain gauges drift for 1-2 minutes after power-up. Anyone who
  // tares cold and then measures gets a slow ramp they will read as creep.
  Serial.println("#ZERO 60 s drift check, do not touch the rig");
  float lo = 1e9, hi = -1e9;
  uint32_t t0 = millis();
  while (millis() - t0 < 60000UL) {
    esp_task_wdt_reset();
    float raw; uint16_t f = 0;
    if (!readCellRaw(0, 3, raw, f)) { Serial.println("#FAULT no HX711 response"); return; }
    float n = (cal[0].scale_cpn != 0.0f)
              ? (raw - cal[0].offset) / cal[0].scale_cpn : 0.0f;
    if (n < lo) lo = n;
    if (n > hi) hi = n;
    if (((millis() - t0) / 1000) % 10 == 0) Serial.printf("#ZERO t=%lus n=%.2f\n",
                                                          (unsigned long)((millis() - t0) / 1000), n);
    delay(500);
  }
  Serial.printf("#ZERO spread=%.2f N (lo=%.2f hi=%.2f). >2 N means it is still warming up.\n",
                hi - lo, lo, hi);
}

static void cmdStart() {
  if (!conditionComplete()) {
    Serial.println("#REFUSED condition incomplete. Conditions are coordinates: a force");
    Serial.println("#REFUSED trace with no posture/load/footwear/side/surface is not data.");
    Serial.println("#REFUSED e.g. COND posture=stand_2ft load=mass_only footwear=barefoot side=both surface=hard");
    Serial.println("#REFUSED (use RAW if you only want bring-up counts.)");
    return;
  }
  if (overload_latched) { Serial.println("#REFUSED overload latched, send CLEAR"); return; }
  for (int i = 0; i < N_CELLS; i++) if (cal[i].scale_cpn == 0.0f) sticky_flags |= F_NOT_CAL;

  session_no = nextSession();
  session_t0 = millis();
  row_count  = 0;
  raw_mode   = false;
  streaming  = true;
  writeHeader(Serial);
  openLogFile();
}

static void cmdStop() {
  streaming = false; raw_mode = false;
  if (logfile) { logfile.flush(); logfile.close(); }
  Serial.printf("#STOP session=%lu rows=%lu dur_ms=%lu file=%s\n",
                (unsigned long)session_no, (unsigned long)row_count,
                (unsigned long)(millis() - session_t0), logpath[0] ? logpath : "none");
}

static void handleLine(char *line) {
  while (*line == ' ') line++;
  if (!*line) return;
  char *sp = strchr(line, ' ');
  char *args = sp ? sp + 1 : (char *)"";
  if (sp) *sp = 0;
  for (char *p = line; *p; p++) *p = toupper(*p);

  if      (!strcmp(line, "HELP") || !strcmp(line, "?")) printHelp();
  else if (!strcmp(line, "ID"))     cmdId();
  else if (!strcmp(line, "TIME"))   {
    struct timeval tv = { (time_t)strtoul(args, nullptr, 10), 0 };
    if (tv.tv_sec > 1700000000) { settimeofday(&tv, nullptr); epoch_set = true;
                                  sticky_flags &= ~F_EPOCH_UNSET;
                                  Serial.println("#OK clock set"); }
    else Serial.println("#ERR epoch looks wrong (want unix seconds)");
  }
  else if (!strcmp(line, "COND"))   cmdCond(args);
  else if (!strcmp(line, "COND?"))  cmdCond((char *)"");
  else if (!strcmp(line, "BW"))     { body_kg = atof(args);
                                      Serial.printf("#OK body_kg=%.2f %s\n", body_kg,
                                        body_kg > 0 ? "" : "(UNSET - bw_ratio stays blank)"); }
  else if (!strcmp(line, "GEOM"))   { plate_ap_mm = atof(strtok(args, " "));
                                      char *t = strtok(nullptr, " ");
                                      if (t) plate_ml_mm = atof(t);
                                      Serial.printf("#OK geom ap=%.1f ml=%.1f\n", plate_ap_mm, plate_ml_mm); }
  else if (!strcmp(line, "WIN"))    { int w = atoi(args); if (w >= 1 && w <= 15) sample_win = w;
                                      Serial.printf("#OK win=%u\n", sample_win); }
  else if (!strcmp(line, "TARE"))   cmdTare(atoi(args));
  else if (!strcmp(line, "CAL"))    { char *a = strtok(args, " "); char *b = strtok(nullptr, " ");
                                      cmdCal(a ? atoi(a) : -1, b ? atof(b) : 0.0f); }
  else if (!strcmp(line, "SHOW"))   cmdShow();
  else if (!strcmp(line, "SAVE"))   saveCal();
  else if (!strcmp(line, "RELOAD")) { loadCal(); cmdShow(); }
  else if (!strcmp(line, "ZERO"))   cmdZeroDrift();
  else if (!strcmp(line, "RAW"))    { raw_mode = true; streaming = false;
                                      Serial.println("#RAW bring-up only. Not data. Never written to SD."); }
  else if (!strcmp(line, "START"))  cmdStart();
  else if (!strcmp(line, "STOP"))   cmdStop();
  else if (!strcmp(line, "CLEAR"))  { overload_latched = false; sticky_flags &= ~F_OVERLOAD;
                                      Serial.println("#OK overload cleared"); }
  else if (!strcmp(line, "SD?"))    Serial.printf("#SD present=%d path=%s\n", sd_present,
                                                  logpath[0] ? logpath : "none");
  else Serial.printf("#ERR unknown command '%s' (try HELP)\n", line);
}

static void pollSerial() {
  static char buf[160];
  static size_t n = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[n] = 0; handleLine(buf); n = 0; }
    else if (n < sizeof(buf) - 1) buf[n++] = c;
  }
}

// ===========================================================================
// 7. SETUP
// ===========================================================================

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  esp_task_wdt_config_t wdt_cfg = { WDT_TIMEOUT_MS, 0, true };
  if (esp_task_wdt_init(&wdt_cfg) == ESP_ERR_INVALID_STATE) esp_task_wdt_reconfigure(&wdt_cfg);
  esp_task_wdt_add(nullptr);

  hx[0].begin(PIN_HX_DOUT0, PIN_HX_SCK);
#if ACQ_MODE == MODE_COP4
  hx[1].begin(PIN_HX_DOUT1, PIN_HX_SCK);
  hx[2].begin(PIN_HX_DOUT2, PIN_HX_SCK);
  hx[3].begin(PIN_HX_DOUT3, PIN_HX_SCK);
#endif

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_FSR_A, ADC_11db);
  analogSetPinAttenuation(PIN_FSR_B, ADC_11db);

  loadCal();
  sticky_flags = F_NOT_TARED | F_COND_UNSET | F_EPOCH_UNSET;
  for (int i = 0; i < N_CELLS; i++) if (cal[i].scale_cpn == 0.0f) sticky_flags |= F_NOT_CAL;

  // microSD is OPTIONAL at runtime, and that is deliberate: a 32 GB SanDisk card
  // is on hand (INVENTORY.md:554) but NO microSD BREAKOUT / CARD SOCKET IS OWNED
  // — there is no such row anywhere in the inventory, which POST_RESTART_CART.md
  // logged as line T1-05 (~$3.50). So the card cannot be read yet. Serial-only
  // is the working configuration TODAY; this path lights up when the reader lands.
  SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
  sd_present = SD.begin(PIN_SD_CS, SPI, 10000000);
  if (!sd_present) Serial.println("#WARN no microSD (no card socket is owned yet) - serial only");

  Serial.println();
  Serial.printf("# ============================================================\n");
  Serial.printf("# %s v%s  mode=%s  cells=%d\n", FW_NAME, FW_VERSION, modeName(), N_CELLS);
#if ALLOW_BODY_LOAD == 0
  Serial.println("# BENCH ONLY - DO NOT STAND ON THIS RIG.");
  Serial.println("# The printed foot is a <=52%-dense plain-PETG fit coupon (1 of 4),");
  Serial.println("# there are no top bosses, no top plate and no M5 bolts, and the rig");
  Serial.println("# has never been proof-loaded. Overload trip is armed at 250 N.");
#else
  Serial.println("# ALLOW_BODY_LOAD=1 - only valid AFTER a documented proof load.");
#endif
  Serial.printf("# ============================================================\n");
  cmdId();
  Serial.println("# type HELP");
}

// ===========================================================================
// 8. LOOP
// ===========================================================================

void loop() {
  esp_task_wdt_reset();
  pollSerial();

  if (raw_mode) {
    static uint32_t tr = 0;
    if (millis() - tr >= 200) {
      tr = millis();
      for (int c = 0; c < N_CELLS; c++) {
        float raw; uint16_t f = 0;
        if (readCellRaw(c, 1, raw, f)) Serial.printf("#RAW ch%d=%.0f ", c, raw);
        else                           Serial.printf("#RAW ch%d=TIMEOUT ", c);
      }
      Serial.printf("fsrA=%d fsrB=%d\n", analogRead(PIN_FSR_A), analogRead(PIN_FSR_B));
    }
    return;
  }

  if (!streaming) { digitalWrite(PIN_LED, (millis() / 1000) % 2); return; }

  // --- session cap: an unattended rig on an insensate foot is what this bounds
  if (millis() - session_t0 > MAX_SESSION_MS) {
    sticky_flags |= F_SESSION_CAP;
    Serial.printf("#LIMIT session cap %lu ms reached - auto-stop\n", (unsigned long)MAX_SESSION_MS);
    cmdStop();
    return;
  }

  uint16_t flags = sticky_flags;
  if (!conditionComplete()) flags |= F_COND_UNSET; else flags &= ~F_COND_UNSET;

  float n_ch[4] = {0, 0, 0, 0};
  float total_n = 0;
  bool  any = false;

  for (int c = 0; c < N_CELLS; c++) {
    float raw;
    if (!readCellRaw(c, sample_win, raw, flags)) { n_ch[c] = NAN; continue; }
    any = true;
    n_ch[c] = (cal[c].scale_cpn != 0.0f) ? (raw - (float)cal[c].offset) / cal[c].scale_cpn : NAN;
    if (!isnan(n_ch[c])) total_n += n_ch[c];
  }

  if (!any) {
    Serial.println("#FAULT every HX711 timed out - stopping. Check VCC, E+/E-, DOUT, CLK.");
    cmdStop();
    return;
  }

  // --- HARD LIMIT. Latching, and it stops the session. ----------------------
  if (total_n > MAX_BENCH_N && !overload_latched) {
    overload_latched = true;
    sticky_flags |= F_OVERLOAD;
    flags |= F_OVERLOAD;
    Serial.printf("#ALERT OVERLOAD %.1f N > %.1f N ceiling. LOGGING STOPPED.\n", total_n, MAX_BENCH_N);
    Serial.println("#ALERT This rig is a fit coupon, not a force plate. Take the load off.");
    Serial.println("#ALERT Send CLEAR to reset once the load is removed.");
    digitalWrite(PIN_LED, HIGH);
    cmdStop();
    return;
  }

  // --- CoP -----------------------------------------------------------------
  float cop_ap = NAN, cop_ml = NAN;
#if ACQ_MODE == MODE_AP
  // Two measurement lines: front pair at y=0, rear pair at y=plate_ap_mm.
  if (total_n > 1.0f && !isnan(n_ch[0]) && !isnan(n_ch[1]))
    cop_ap = (n_ch[1] * plate_ap_mm) / total_n;
#elif ACQ_MODE == MODE_COP4
  // Corner order: 0 = front-left, 1 = front-right, 2 = rear-left, 3 = rear-right.
  if (total_n > 1.0f) {
    float fl = n_ch[0], fr = n_ch[1], rl = n_ch[2], rr = n_ch[3];
    if (!isnan(fl) && !isnan(fr) && !isnan(rl) && !isnan(rr)) {
      cop_ap = ((rl + rr) * plate_ap_mm) / total_n;
      cop_ml = ((fr + rr) * plate_ml_mm) / total_n;
    }
  }
#endif

  int   fsr0 = analogRead(PIN_FSR_A);
  int   fsr1 = analogRead(PIN_FSR_B);
  int   mv0  = analogReadMilliVolts(PIN_FSR_A);
  int   mv1  = analogReadMilliVolts(PIN_FSR_B);

  char iso[28]; isoUtc(iso, sizeof(iso));
  char bw[16] = "";
  if (body_kg > 0) snprintf(bw, sizeof(bw), "%.3f", total_n / (body_kg * 9.80665f));

  char row[256];
  int len = snprintf(row, sizeof(row),
    "%lu,%s,%lu,%u,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%s,%s,%s,%d,%d,%d,%d,0x%04X",
    (unsigned long)millis(), iso, (unsigned long)session_no, cond_id, cond.posture,
    total_n, n_ch[0], n_ch[1], n_ch[2], n_ch[3],
    isnan(cop_ap) ? "" : String(cop_ap, 1).c_str(),
    isnan(cop_ml) ? "" : String(cop_ml, 1).c_str(),
    bw, fsr0, mv0, fsr1, mv1, flags);

  Serial.println(row);
  if (logfile) {
    logfile.println(row);
    if ((++row_count % 20) == 0) logfile.flush();   // bounded data loss on a yank
  } else {
    row_count++;
  }

  digitalWrite(PIN_LED, (row_count & 1));
}
