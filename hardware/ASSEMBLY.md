# ASSEMBLY — biomech-pressure-lab hardware

One card, three sub-rigs: **relief insole**, **ankle pod** (+ FSR carrier), and **DIY-lab sensing**
(force plate, pressure mat, FSR puck). Build only the parts for the rig you're assembling. Pins below
are read straight from the committed firmware — verify against your own board revision before power.

---

## 1. After the print
- **relief_insole / barefoot_sole / insole_fsr_layout (TPU):** printed on a glue stick, no supports,
  no brim. Peel off the plate once cool; TPU releases easier warm. Pop the sensor pockets/wire
  channels clear of strings. `relief_insole` is dual-TPU (soft cushion + firm shell) — check the two
  materials fused at the interface.
- **ankle_pod / ankle_pod_enclosure (ASA):** brim used (ASA warps) — peel it off, deburr the mating
  rim flat so the lid seats. Each `.scad` prints **body + lid side-by-side on one plate** (the "2
  shells" the gate reports — expected, not a defect). No supports; USB/STEMMA/FSR slots are
  round-ended and bridge clean.
- **pressure_mat (ASA/PETG-CF):** thin comb teeth — brim on, handle gently, don't snap the teeth off.
- **force_plate (PA-CF/PETG-CF, STRUCTURAL):** dry the filament, brim recommended, 4 walls. `foot()`
  renders x4 — print four. `top_boss()` x4 and `top_plate()` are commented out in the `.scad`;
  uncomment to export if you're not using plywood/acrylic for the top.
- **fsr_puck (rigid PETG) ×6–8:** tiny solid domes, 0.12 mm layer, no supports/brim. Batch them.

## 2. Hardware & assembly
- **Ankle pod (ESP32-C6 STEMMA rig, `ankle_pod_enclosure.scad`):**
  - **Feather standoffs:** four posts drilled for **M2.5**. As-printed they're self-tap pilots
    (2.0 mm); for a lid you'll open often, drill through 2.5 mm and **press an M2.5 brass heat-set
    insert** into each, then screw the Feather down with M2.5 SHCS.
  - **IMU (MPU-6050 / BNO085):** drops into the floor-level lip pocket at the +X end — **no screws**
    (most STEMMA breakouts have no reliable hole pattern). Retain with a **zip-tie** up through one
    floor slot, over the board, down the other, cinch underneath.
  - **LiPo** (1200 mAh flat pouch, 35×20×6) sits UNDER the Feather in the main bay.
  - **Lid:** friction-fit lip + snap ribs (0.2 mm engage into a 0.35 mm groove — a click, not a
    fight). Press to seat. Optional TPU `strap_keeper()` clips into the strap slots; or thread ~25 mm
    elastic through the two under-base slots.
- **Ankle pod (older ESP32-S3 rig, `ankle_pod.scad`):** press-fit lid (0.6 mm lip clearance, no
  snap); strap through the two under-base slots; USB-C / button / sensor-ribbon slots. No inserts.
- **Force plate:** each printed `foot()` clamps the **fixed end** of a 50 kg bar load cell with an
  **M5 bolt** (`LC_hole_d=5.2`); the free end overhangs with a 2 mm air gap — **do not let it bottom
  out**. A `top_boss()` bolts to each cell's free end and presses up on the top (plywood/acrylic, or
  printed `top_plate()`); glue the bosses into the plate pockets. Rubber feet in the underside 10 mm
  pockets.
- **Pressure mat:** the printed comb is an **alignment jig** — lay copper-tape rows/cols against its
  teeth with the Velostat sheet between the two electrode layers. No fasteners; tape + frame.
- **FSR puck:** one rigid puck sits centered on each FSR's active area (funnels load the same way
  every time). It drops into the insole pocket over the sensor — no glue needed, the insole membrane
  holds it.

## 3. Wiring / electronics

### Ankle pod — 6-zone STEMMA-QT rig (ESP32-C6 Feather, `insole_fsr_layout` carrier)
6× FSR402 go straight to the Feather analog pins, **no mux**:
| Zone | FSR | Feather pin |
|---|---|---|
| heel_med | fsr0 | A0 |
| heel_lat | fsr1 | A1 |
| midfoot | fsr2 | A2 |
| met1 | fsr3 | A3 |
| met5 | fsr4 | A4 |
| hallux | fsr5 | A5 |

Each FSR = one leg to 3.3 V, other leg to its Ax pin **and** a fixed pull-down resistor to GND
(voltage divider). I2C on **SDA/SCL = STEMMA-QT bus**; MPU-6050 at **0x68**, VCNL4200 at **0x51**.
⚠️ **Firmware must drive IO20 HIGH** to power the STEMMA-QT bus or both I2C breakouts read as "not
found." Smoke-test with the lid off. Libs: Adafruit MPU6050 + VCNL4200 (+ Unified Sensor, BusIO).

### Ankle pod — 8-zone rig (ESP32-S3, `barefoot_sole` carrier, `smart_insole`/`all_day_logger`)
8× FSR402 through a **CD74HC4067 mux**:
| Signal | ESP32-S3 GPIO |
|---|---|
| MUX common SIG → ADC | GPIO1 (ADC1_CH0) |
| MUX select S0/S1/S2/S3 | GPIO2 / 3 / 4 / 5 |
| I2C SDA / SCL (BNO08x IMU) | GPIO8 / GPIO9 |
| microSD CS / MOSI / SCK / MISO | GPIO10 / 11 / 12 / 13 |
| Button / LED | GPIO14 / GPIO15 |
| VBAT sense (2:1 divider, `all_day_logger`) | GPIO16 |

`analogReadResolution(12)`, `ADC_11db` attenuation (0–~3.3 V). BNO08x IMU on I2C (0x4A default). SD
logging + BLE (Nordic UART). Run `i2c_scanner` first to confirm addresses.

### Force plate (`firmware/force_plate`, HX711)
- **Single-HX711 total-force mode (`COP_MODE 0`, default):** HX711 **DOUT = GPIO5, SCK = GPIO4**,
  one HX711 summing all four cells (or one cell). Needs the HX711 Arduino lib.
- **4-HX711 CoP upgrade (`COP_MODE 1`):** shared **SCK = GPIO4**, one data pin per corner
  **DOUT[4] = {5, 6, 7, 15}**.

### Pressure mat (`firmware/pressure_mat`, Velostat matrix, no external lib)
8 rows × 11 cols, anti-ghosting scan:
| Signal | ESP32 GPIO |
|---|---|
| ROW drive (8) | GPIO1–GPIO8 |
| MUX select S0–S3 (columns via CD74HC4067) | GPIO9 / 10 / 11 / 12 |
| MUX common SIG → ADC | GPIO13 |

Discard the first ADC read after each mux switch (settle), 30 µs settle. Render with
`analysis/mat_heatmap.py`.

**Power:** flat-pouch LiPo (JST-PH) for the worn pod; a stationary 18650 or USB is fine for the
force plate / mat. Never put an 18650 in the body-worn pod (design constraint — must be flat pouch).

## 4. Measurement / fitting — REQUIRED (custom-fit rig)

**Relief insole — needs measurement (LiDAR scan preferred, caliper fallback):**
1. **iPhone 15 Pro LiDAR scan** of your **existing orthotic (NOT a bare foot)** — matte it first
   (baby powder / matte spray), include a ruler or coin for scale. App: **Scaniverse or Polycam** →
   export **STL** → clean watertight in **Blender/Fusion**.
2. Feed it to `build_insole.py --scan my_orthotic.stl --name fitted` (best fit). It reads
   `insole_spec.json` and places the relief window / met pad / arch from your data, re-emitting
   `relief_insole.stl`.
3. **Caliper fallback (no scan):** `build_insole.py --length --forefoot-width --heel-width
   --arch-height` in mm (e.g. `--length 262 --forefoot-width 99 --heel-width 64 --arch-height 14`).
4. **Measurement inputs the model expects:** the scan STL passed to `--scan`, or the four caliper
   dims; hotspot placement comes from `analysis/` → `hotspot.json` → `insole_spec.json` (run with
   `--demo` on the committed sample if you have no sensor data yet). Full how-to:
   `../docs/fit_to_your_foot.md`.

**FSR carrier (`insole_fsr_layout`):** set `FOOT_LEN` (mm) to your measured heel→toe length; width
derives from it. Caliper or the scan gives `FOOT_LEN`.

**Ankle pod (body-worn):** caliper your **actual Feather / LiPo / MPU-6050** footprints and correct
`feather_hole_dx/dy` + the IMU pocket in `ankle_pod_enclosure.scad` before the final print (many
STEMMA breakouts vary). The pod straps to the lower shin with ~25 mm elastic — no body scan, but the
board fit **is** a caliper step.

**Force plate / pressure mat / FSR puck:** sized to spec (the load cells / Velostat / FSR402), no
body measurement.

## 5. Calibration & first-power checklist
- **Meter before power:** with the LiPo disconnected, check for shorts across 3V3↔GND. Confirm FSR
  divider pull-downs are present. For the C6 rig, verify IO20 is wired to the STEMMA power enable.
- **I2C enumerate:** flash `i2c_scanner`, lid off — confirm **MPU-6050 0x68 / VCNL4200 0x51** (C6) or
  **BNO08x 0x4A** (S3). If a device is missing on the C6, IO20 isn't HIGH.
- **FSR channels:** confirm all 6 (or 8) channels change with finger pressure before closing the lid.
- **FSR calibration:** flash `firmware/fsr_calibrate`, press **known weights** onto each puck-loaded
  zone, fit with `analysis/calibrate.py` (power-law ADC→kPa).
- **Force plate:** zero (tare) unloaded, then place a **known weight** and set the HX711 cal factor
  until reported force matches. Validated rigs hit ICC>0.94 vs a lab plate.
- **Pressure mat:** run the matrix scan empty (baseline), step on it — `mat_heatmap.py` should show a
  clean foot pressure map with no row/col ghosting.
- **"Working" looks like:** all sensors zero at rest, respond monotonically to load, IMU streams sane
  orientation, and the pod logs to SD / streams over BLE. **⚠️ Force plate is a proof-load-gated
  structural draft — proof-load it before standing full bodyweight.**
