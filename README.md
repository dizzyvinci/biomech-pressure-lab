# Personal Biomechanics Lab

A DIY toolkit to measure your own foot **geometry**, **plantar pressure**, and **motion across movements**, then feed it into a **3D-printed custom insole** with a targeted relief window under your hot spot — and verify it worked. Built around an iPhone + a Bambu H2D.

> **Part of the biomech-lab family — the hardware pressure side.** Its sibling repo **`biomech-lab`** covers *markerless motion / joint video analysis* (webcam→OpenSim, DICOM/MRI bone geometry). **This** repo is the **build-your-own hardware** side: a **smart insole + pressure plate** you fabricate yourself, plus the analysis that drives a 3D-printed insole. Separate repos, complementary data — **motion + structure + pressure**.

![How the smart-insole rig fits together](docs/system-diagram.svg)

```
  iPhone LiDAR/photo ─┐
   (foot/orthotic)    ├─► foot GEOMETRY (STL)
                      │
  OpenCap (2 iPhones)─┼─► MOTION across movements (joint angles, gait)
                      │
  DIY smart insole ───┴─► dynamic PRESSURE (peak/impulse per zone, COP)
                                  │
                                  ▼
                    Python analysis → HOT SPOT + gait findings
                                  │
                                  ▼
                    H2D prints insole (soft lattice + firm shell + relief window)
                                  │
                                  ▼
                    Re-measure → verify load dropped → iterate
```

## What's in here
| Path | What it is |
|---|---|
| `firmware/smart_insole/smart_insole.ino` | ESP32 firmware: 8× FSR + IMU, logs CSV to SD + streams over BLE |
| `analysis/analyze_pressure.py` | Loads logs → peak/impulse per zone, center-of-pressure, per-activity comparison, hot-spot finder, plots |
| `analysis/requirements.txt` | Python deps |
| `docs/opencap_setup.md` | Step-by-step OpenCap (markerless gait) setup for iPhone |
| `docs/insole_print_spec.md` | The printable insole (density zones + relief window) + sensor-carrier + ESP32 enclosure |

## Build order (recommended)

> **No printer yet? You don't need one to start.** The entire measurement side works with improvised parts. See **[docs/quickstart.md](docs/quickstart.md)** for the **no-printer** and **with-printer** paths.

1. **Scan** your existing orthotic → STL (see `docs/insole_print_spec.md`). *No new pressure gear needed to start.*
2. **Assemble the smart insole** (BOM + wiring below), flash `smart_insole.ino`.
3. **Record** labeled sessions (stand / walk / stairs / pivot), then run `analyze_pressure.py` → find your hot spot.
4. **(Optional) OpenCap** for joint-level gait across movements (`docs/opencap_setup.md`).
5. **Design + print** the insole with the relief window at the hot spot.
6. **Re-record** with the new insole → confirm peak/impulse at the hot zone dropped → iterate.

---

## Smart-insole BOM (~$70–120 basic)

> 🛒 **Ready to order?** [docs/parts_list.md](docs/parts_list.md) lists every part with direct buy links.
> 🧐 **Not sure what a part does?** [docs/what-each-part-is-for.md](docs/what-each-part-is-for.md) explains each one in plain English (and flags cart items that aren't part of this project).
| Part | Qty | ~$ | Notes |
|---|---|---|---|
| ESP32-S3 DevKitC-1 (or **Seeed XIAO ESP32-S3** for wearable) | 1 | 8–15 | BLE + enough ADC/SPI/I2C |
| Interlink **FSR402** force sensors | 8 | ~6 ea | Cheap. Upgrade: **FlexiForce A301** (more linear, ~$25 ea) |
| **CD74HC4067** 16-ch analog mux | 1 | 2 | 8 FSRs → 1 ADC pin |
| **Adafruit BNO085** IMU | 1 | 20 | Fused orientation (pronation, strike timing) |
| microSD SPI module + card | 1 | 8 | Full-rate onboard logging |
| 10 kΩ resistors | 8 | ~2 | FSR voltage dividers |
| LiPo 500 mAh + **TP4056** charger (or small USB power bank) | 1 | 10 | Wearable power |
| Thin insole / EVA sheet, wires, perfboard, tape | — | 10 | Mount the FSRs |

> Start with **6–8 FSR402**. A pro 14× FlexiForce build runs ~$700 — not needed to begin. DIY FSR insoles have validated to **r ≈ 0.87** vs professional systems, which is plenty for *relative* hot-spot mapping and iteration.

## Wiring (ESP32-S3 pin map — matches the firmware)
| Signal | ESP32-S3 GPIO |
|---|---|
| Mux SIG (analog out) | GPIO1 (ADC1_CH0) |
| Mux S0 / S1 / S2 / S3 | GPIO2 / 3 / 4 / 5 |
| Mux EN | GND |
| IMU SDA / SCL (I2C) | GPIO8 / GPIO9 |
| SD CS / MOSI / SCK / MISO (SPI) | GPIO10 / 11 / 12 / 13 |
| Button (start/stop + cycle activity) | GPIO14 → GND (internal pull-up) |
| Status LED | GPIO15 |

**Each FSR** is a voltage divider: `3V3 ── FSR ──●── 10kΩ ── GND`, with the node `●` going to a mux channel (Y0…Y7). Higher force → higher voltage.

### FSR → foot-zone map (default 8-sensor layout)
```
        toes
   hallux   met5
 met1   met3
      midfoot
 heel_med  heel_lat
```
Channel order in firmware/analysis: `0 heel_med, 1 heel_lat, 2 midfoot, 3 met1, 4 met3, 5 met5, 6 hallux, 7 toes`.
Edit `ZONES` / `SENSOR_XY` in `analyze_pressure.py` if you place them differently.

## Data format (CSV, one row per sample ~100 Hz)
```
t_ms,activity,fsr0,fsr1,fsr2,fsr3,fsr4,fsr5,fsr6,fsr7,qw,qx,qy,qz,ax,ay,az
```
`fsrN` = raw 12-bit ADC (0–4095). `q*` = IMU quaternion. `a*` = accel (m/s²). Calibrate FSR→Newtons later (see analysis script).

## Safety / expectations
- FSRs give **relative, repeatable** pressure, not lab-grade absolute kPa. Perfect for "where is highest and how it shifts by movement." Want true kPa? Calibrate each channel against known weights (script has a hook).
- This is a measurement/【design】 aid, not a medical device. You already have custom orthotics — treat this as tuning on top of them.
