# Path 2 — the all-day pressure-TRACKING build (prep + assembly)

This is the "smart insole" that actually **records** your plantar pressure through the day — **barefoot and in-shoe**, so you can compare the two. It's the optional advanced path (the plain printed insole in Path 1 needs none of this).

## How it physically works
```
  in the shoe / on the foot          at the ankle
  ┌───────────────────────┐          ┌──────────────────┐
  │ sensor carrier (TPU)  │ ribbon   │ ANKLE POD        │
  │  8 FSRs in pockets  ──┼──────────┤ ESP32-S3 + LiPo  │
  │  + IMU-free, flat     │  cable   │ + microSD + IMU  │
  └───────────────────────┘          └──────────────────┘
        wearable / thin                 all the bulk lives here
```
The 3D print does **not** wrap the electronics. Only the thin flat FSRs + wiring go on the foot; the ESP32 + battery + SD live in the **ankle pod** (`hardware/ankle_pod.scad`), joined by a thin ribbon cable.

## Barefoot vs shoe
Two sensor carriers, same pod:
- **Barefoot:** `hardware/barefoot_sole.scad` — a thin soft-TPU footbed strapped to the bare foot.
- **In-shoe:** the same FSR-pocket pattern booleaned into your **scanned insole** (Path 1 model), or the barefoot sole slipped into the shoe.
The firmware tags every row `shoe` or `barefoot` (long-press the button to switch) → the analysis compares how footwear changes your loading + hot spot.

## Battery / how long it lasts
Logging 8 FSRs + IMU to SD at **50 Hz**, the ESP32-S3 draws ~80–120 mA:
| LiPo | Runtime |
|---|---|
| 500 mAh (in your Adafruit cart) | ~4 h (sessions) |
| **1000–1500 mAh** (recommended for all-day) | ~8–14 h |
| 2000 mAh | ~16–20 h |
Not literal 24/7, but a **full waking day** is easy with a 1000–1500 mAh cell. Charge overnight via the pod's USB-C.

## What to add to the parts (beyond the Path 1 printer)
The sensor rig from `parts_list.md` **plus**:
- **Bigger LiPo — 1000–1500 mAh** (JST-PH) for all-day runtime (the 500 mAh is fine for sessions).
- **Thin ribbon / flat cable** (~8–10 conductor) insole → ankle pod.
- Optional: a **2:1 resistor divider** on `PIN_VBAT` (2×100 kΩ) to log battery voltage.

## The three prints
| File | Print in | Notes |
|---|---|---|
| `hardware/ankle_pod.scad` | PLA / PETG | Measure your boards, edit params, F6 → STL |
| `hardware/barefoot_sole.scad` | **soft TPU 85A** | Generic footbed; edit `foot_len`/`foot_w` to you |
| (in-shoe carrier) | soft TPU 85A | Boolean the FSR pockets into your scanned insole for true fit |

## Firmware
Flash **`firmware/all_day_logger/all_day_logger.ino`** (not the session logger):
- Auto-starts, 50 Hz, batched SD writes, BLE off, 80 MHz CPU — tuned for battery.
- Button: **short** = drop an event mark; **long** = toggle shoe ↔ barefoot (starts a new file).
- Files: `day_shoe_00N.csv` / `day_bare_00N.csv`, with a `mode` + `vbat` column.

## Assembly order
1. Print the **ankle pod** + a **barefoot sole**.
2. Seat the 8 FSRs in the sole pockets; route wires down the channels to the ribbon.
3. Wire FSR dividers → mux → ESP32; IMU → I²C; microSD → SPI; LiPo → pod (see main [README](../README.md) Path 2 pin map).
4. Ribbon: sole → pod slot. Close the pod lid. Strap the sole + pod on.
5. Flash the firmware, insert a formatted microSD.

## Daily workflow
1. Charge overnight → strap on in the morning.
2. Wear it; **long-press** to switch shoe/barefoot when you change.
3. End of day: pull the SD card → `python analysis/analyze_pressure.py "day_*.csv" --out results/`.
4. Compare `shoe` vs `barefoot` runs → see how your footwear shifts the hot spot.

> **Analysis note:** the logs carry a `mode` column (shoe/barefoot). `analyze_pressure.py` currently groups by `activity`; point it at `mode` (or rename the column) to split the barefoot-vs-shoe comparison — a small tweak, flagged as TODO.

## Reality check
FSRs give **relative, repeatable** pressure (great for "where + how it shifts"), not lab-grade kPa. All-day comfort depends on good strain relief on the ribbon + a snug (not tight) strap. This is a measurement aid, not a medical device.
