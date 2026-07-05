# Prototype & pitch status

**Where this is:** the entire **software + design** side is done and verified. What remains is physical assembly once the H2D arrives. This page is the "is it ready to prototype/pitch?" summary.

## ✅ Ready now (software — built & tested)
- Firmware: session logger + **all-day** logger (shoe/barefoot) + calibration collector
- **Pressure** analysis + implications engine → real **kPa** (verified end-to-end)
- **Balance** module (posturography — sway, Romberg, fall-risk flags) — new capability
- Print-ready models ([`ankle_pod.scad`](../hardware/ankle_pod.scad), [`barefoot_sole.scad`](../hardware/barefoot_sole.scad)) + full docs + [diagrams](pipeline.svg)

## 🛒 Ordered vs 🖨️ Printed
| You ORDER (buy) | You PRINT (H2D makes) |
|---|---|
| ESP32-S3, 8× FSR, mux, BNO085 IMU | Ankle pod (PLA/PETG) |
| LiPo (1000–1500 mAh), TP4056, microSD | Barefoot sensor sole (soft TPU) |
| resistors, wires + ribbon | Shoe sensor-carrier (soft TPU) |
| glue stick, filament dryer | **The final relief insole** (soft + firm TPU) |
| **H2D printer + TPU filament** | |
| ~$100 rig + ~$1,800 printer/materials | ~cents of filament per part |

![A day of use](day_in_the_life.svg)

## ⏱️ Lifespans / a day of use
| Piece | Lasts |
|---|---|
| **Battery** (1000–1500 mAh) | **~8–14 h per charge → a waking day**; recharge overnight |
| **microSD** | pull/offload nightly; ~unlimited |
| **Barefoot sole** (soft TPU) | weeks–months of wear; **cheap to reprint** |
| **Ankle pod** (PLA/PETG) | indefinite |
| **FSRs** | drift with heavy use → **recalibrate / replace over months** |
| **Final insole** (TPU) | months; reprint when the relief window needs re-tuning |

## 🎤 Two pitchable capabilities — same ~$100 rig
1. **Custom pressure-relief insole** — measure your hot spot → print a relief-window insole → verify the load dropped.
2. **Balance / fall-risk screen** — posturography (sway area, velocity, Romberg) from the same sensors.
Both are wearable, cheap, and open-source — the pitch is "a $100 wearable that does what a $5k+ pressure plate / posturography lab does, at trend level, all day."

## What's left (physical, ~while the printer ships)
1. (Optional, tracking) order the extras: **1000–1500 mAh LiPo + ribbon cable**.
2. **Print** the pod + sole (OpenSCAD → STL → Bambu Studio).
3. **Assemble** + **calibrate** with known weights (`calibrate.py`).
4. **Record → analyze** (pressure and/or balance).

Everything upstream of "print + solder" is finished. The prototype is buildable and the pitch is presentable **today**.
