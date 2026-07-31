# PRINT_CARD — biomech-pressure-lab hardware

All printable STLs in this repo live in this one `hardware/` folder, so this is one card,
grouped by the three sub-projects: **the relief insole**, **the ankle pod**, and **gait /
DIY-lab sensing**. Print only the parts for the rig you're actually building (some parts are
alternative revisions — see notes).

Material choices follow the repo's intent *and* the shop policy: **PLA is prototype-only**;
functional parts use the high-grade owned stock (**PA-CF / PETG-CF / PC / ASA**); **TPU is for
soft/flex parts** (insole, sensor carriers) and always runs from the **external spool, never the
AMS**. Owned filament: plenty of TPU + the H2D AMS high-grade set (PC / ASA / PA-CF / CF).

## Slice recipe

| Part (.stl) | Material | Nozzle | Layer | Walls | Infill | Supports | Brim | Plate |
|---|---|---|---|---|---|---|---|---|
| `relief_insole.stl` | **TPU dual** — soft/foaming cushion 85–90A (VarioShore) + firm shell TPU 95A HF | 0.4 (0.6 High-Flow ok for cushion) | 0.20 | 2–3 | cushion 12–18% honeycomb · shell 35–45% | No | No (glue stick to release) | **P1 — insole (H2D dual-nozzle, EXTERNAL spool for soft)** |
| `barefoot_sole.stl` | **soft TPU 85A** | 0.4 (or 0.6 HF) | 0.20 | 3 | ~15% gyroid | No | No (glue stick) | **P2 — TPU carriers (EXTERNAL spool)** |
| `insole_fsr_layout.stl` | **TPU** (6-zone FSR carrier) | 0.4 | 0.20–0.24 | 2–3 | ~15% gyroid | No | No | **P2 — TPU carriers (EXTERNAL spool)** |
| `ankle_pod.stl` | **ASA** (body-worn, tough; PA-CF/PETG-CF for stiffer base) | 0.4 (hardened if CF) | 0.20 | 3 | 20% | No | Yes (ASA warps) | **P3 — ankle pod (AMS, enclosure warm)** |
| `ankle_pod_enclosure.stl` | **ASA** base+lid (or PA-CF base for shin-strap rigidity + ASA/PETG lid for snap flex) | 0.4 (hardened if CF) | 0.20 | 3–4 | 20–25% | No | Yes | **P3 — ankle pod (AMS, enclosure warm)** |
| `pressure_mat.stl` | **ASA** or PETG-CF (non-load electrode comb) | 0.4 (hardened if CF) | 0.20 | 3 | 15–20% | No | Yes (thin comb teeth) | **P4 — DIY-lab frames (AMS)** |
| `force_plate.stl` | **PA-CF / PETG-CF** — STRUCTURAL (bears bodyweight → 4 load cells); DRY the filament | 0.4 **hardened** | 0.20 | 4 | 40–100% (repo wants solid platform) | No | Yes (recommended) | **P5 — force plate (AMS, DRY, hardened)** |
| `fsr_puck.stl` ×6–8 | **PETG** rigid — *part says NO CF* (grinds the fine nozzle); PLA ok as proto | **0.2 stainless** (fine dome) — *fallback: 0.4 + 0.12mm layer if no 0.2 nozzle* | 0.12 | 3–4 | 100% (tiny/solid) | No | No | **P6 — pucks (fine-detail nozzle, batch all)** |

**How to slice:** open the STLs in Bambu Studio (H2D profile already set), assign each part's
material to an AMS slot — **except the TPU parts (P1/P2), which must feed from the external
spool, not the AMS** — arrange on the indicated plate, Slice, Print. Print **one** ankle-pod
revision (`ankle_pod` = older ESP32-S3/mux rig · `ankle_pod_enclosure` = current ESP32-C6
STEMMA-QT rig) and **one** FSR carrier (`barefoot_sole` = 8-zone · `insole_fsr_layout` = 6-zone)
to match your electronics. The force plate is a **structural draft — proof-load it before
standing full weight** (FEA/proof-load gated). The STLs are pre-rendered at default params; only
open the `.scad` in OpenSCAD if you want to re-parameterize (measure your board/foot) and
re-export.

## Software & measurement

**Insole (relief_insole) — measurement + regen (no electronics):**
- Phone: **iPhone LiDAR → Scaniverse or Polycam**. Scan your **existing orthotic, not a bare
  foot** — matte it first (baby powder / matte spray), include a ruler/coin for scale, export
  **STL**, clean watertight in Blender/Fusion.
- Feed it to `hardware/build_insole.py` (Python): `--scan my_orthotic.stl` (best fit), or caliper
  measurements `--length --forefoot-width --heel-width --arch-height` (mm). It places the relief
  window/met pad/arch from `insole_spec.json` and re-emits `relief_insole.stl` fitted to you.
- No PC software beyond Python + the `analysis/` pipeline (calibrate → interpret → `hotspot.json`
  → `insole_spec.json`). Runs on the committed sample with `--demo` if you have no sensor data.

**Ankle pod + FSR carriers — sensor-rig firmware/flashing:**
- **Arduino IDE** (or arduino-cli/PlatformIO) with the **esp32 board package** (Espressif, via
  Boards Manager). Board = *ESP32-S3 Dev Module* (older rig) or *Adafruit ESP32-C6 Feather*
  (STEMMA-QT rig).
- Libraries by sketch: `all_day_logger`/`smart_insole` → **Adafruit BNO08x** (IMU) + built-in
  `SD`/`SPI`/`Wire` (smart_insole also uses the ESP32 built-in `BLEDevice` stack). STEMMA-QT
  C6 rig → **Adafruit MPU6050** + **Adafruit VCNL4200** (+ their deps **Adafruit Unified
  Sensor**, **Adafruit BusIO**). `i2c_scanner` → `Wire` only (verify MPU 0x68 / VCNL 0x51).
  FSRs are analog reads — no library. The 8-zone rig also needs a **CD74HC4067 mux** (GPIO, no
  lib); the 6-zone C6 rig drops the mux (6 FSRs → A0–A5).
- **C6 STEMMA gotcha:** firmware must drive **IO20 HIGH** to power the STEMMA-QT bus or both
  I2C breakouts read as "not found." Flash + smoke-test with the lid off (confirm all FSR
  channels + both I2C devices enumerate).
- **Calibrate** each FSR: flash `firmware/fsr_calibrate`, record known weights, fit with
  `analysis/calibrate.py` (power-law ADC→kPa). Caliper-measure your actual board's hole spacing
  against the `.scad` standoff params before printing the enclosure final.

**DIY-lab sensing (force plate + pressure mat):**
- **force_plate:** 4× load cells + **HX711** ADC(s); flash `firmware/force_plate` (needs the
  **HX711** Arduino library — 1 HX711 = total vertical GRF; 4-HX711 CoP upgrade is in-sketch).
  Calibrate against known weights.
- **pressure_mat:** Velostat sheet + copper-tape electrode matrix (the printed comb aligns them);
  flash `firmware/pressure_mat` (matrix scan, anti-ghosting — no external lib); render with
  `analysis/mat_heatmap.py`.
- **fsr_puck:** no software — pure-print force-concentrator, one per FSR zone.
