# BUILD_PLAN — STEMMA-QT ankle pod (ESP32-C6 Feather revision)

Stepwise build plan for the **updated Path 2 electronics**: ESP32-C6 Feather + VCNL4200 +
MPU-6050 (all STEMMA QT) + 6× FSR402, replacing the ESP32-S3/mux/BNO085 rig documented in the
main [README](../README.md) Path 2 section with a simpler, no-mux, STEMMA-chained build. Same
loop, same downstream analysis — just a different BOM. Print files:
[`hardware/ankle_pod_enclosure.scad`](../hardware/ankle_pod_enclosure.scad) (2-part shin pod) and
[`hardware/insole_fsr_layout.scad`](../hardware/insole_fsr_layout.scad) (flat FSR carrier); zone
math in [`docs/insole_sensor_layout.md`](insole_sensor_layout.md).

> ⚠️ **Assumptions, stated up front:** the ESP32-C6 Feather's exact GPIO-to-`Ax` mapping is
> inconsistently documented even by Adafruit (their own guide and pinout page disagree on a
> couple of pins) — so all firmware references below use the **symbolic pin names** (`A0`..`A5`,
> `SDA`, `SCL`) that the Arduino board variant resolves for you, never raw GPIO numbers. Also:
> neither the MPU-6050 nor VCNL4200 STEMMA QT breakouts have a confirmed, standardized
> mounting-hole pattern, so the enclosure holds the IMU with a retaining lip + zip-tie rather than
> screws (see the .scad comments). Verify both against your actual boards before printing final.

---

## (a) Print list — H2D settings

No part here needs supports — every overhang in both `.scad` files is a straight extrusion or a
small bridged slot (≤10 mm), both well inside the H2D's unsupported-bridging range.

| Part | Source | Material | Nozzle | Layer height | Supports | Infill | Rough time |
|---|---|---|---|---|---|---|---|
| Ankle pod **base** | `ankle_pod_enclosure.scad` → `base()` | PETG (or PLA-CF for extra shin-strap rigidity) | 0.4 mm hardened | 0.20 mm | No | 20–25% | ~2–2.5 h |
| Ankle pod **lid** | same file → `lid()` | same as base | 0.4 mm hardened | 0.20 mm | No | 20–25% | ~1 h |
| FSR **sensor-carrier plate** | `insole_fsr_layout.scad` | TPU (black, **external dryer spool, not AMS**) | 0.4 mm hardened | 0.20–0.24 mm | No | ~15% gyroid | ~1.5 h |
| FSR **force-concentrator pucks** ×6 | `fsr_puck.scad` (existing, one per zone) | plain PLA or PETG — **not** PLA-CF here | 0.2 mm stainless (fine detail on the small dome) | 0.12 mm | No | 100% (small/solid) | ~10 min ea, ~1 h batched |

Notes:
- **Puck nozzle choice:** the puck's revolved dome/rim profile is small enough that the 0.2 mm
  stainless nozzle gives a visibly cleaner result. If you do print pucks in **PLA-CF instead**
  (you don't need to — plain PLA/PETG is plenty rigid for a puck), swap to the **0.4 mm hardened**
  nozzle; carbon fiber will grind through the stainless one.
- **PETG vs PLA-CF for the pod:** PETG is the safer default — it takes the shin-strap flex and
  the lid's snap ribs better without cracking. PLA-CF (210–240 °C) is stiffer but more brittle at
  thin snap features; fine for the base, use PETG for the lid if you'll open it often.
- **H2D dual-nozzle option:** the H2D's two independent nozzles can, in principle, run two
  different jobs (e.g., PETG pod parts on one side, TPU carrier on the other) concurrently if your
  Bambu Studio profile supports independent-nozzle mode for the plate layout you have — worth
  checking before you rely on it. If not, just queue the four print jobs sequentially; see (d).

---

## (b) Electronics wiring

**STEMMA QT I2C chain** (JST-SH 4-pin cables, daisy-chained — order doesn't matter electrically):

```
ESP32-C6 Feather (STEMMA QT port)
   │ cable
   ▼
MPU-6050 breakout (0x68)         — lives INSIDE the ankle pod's IMU bay
   │ cable, continues out the pod's STEMMA-exit slot
   ▼
VCNL4200 breakout (0x51)         — worn OUTSIDE the pod (see placement note below)
```

No address conflict (`0x68` vs `0x51`), so this chains safely on one bus.
[Sources: MPU-6050 STEMMA QT breakout default address](https://learn.adafruit.com/mpu6050-6-dof-accelerometer-and-gyro/pinouts) ·
[VCNL4200 STEMMA QT breakout default address](https://learn.adafruit.com/adafruit-vcnl4200-long-distance-ir-proximity-and-light-sensor).

**⚠️ C6-specific gotcha:** the Feather's STEMMA QT connector shares the board's main I2C pins
(`SDA`=IO19, `SCL`=IO18), but the connector's **power** is switched through a separate pin
(IO20) that firmware must drive **HIGH** before anything on the chain will respond — otherwise
both breakouts read as "not found" even though the wiring is correct.
[Source: Adafruit ESP32-C6 Feather I2C guide](https://learn.adafruit.com/adafruit-esp32-c6-feather/i2c).

**VCNL4200 placement (your call, one reasonable option):** mounted facing down/forward — either
on the front of the ankle pod itself or clipped near the toe box — it can read **ground
clearance during the swing phase** (toe-drag / foot-drop risk), a natural complement to the
pressure + IMU data given this repo already tracks equinus/AFO-adjacent conditions. This is a
suggestion, not a spec — any STEMMA-chained placement works electrically.

**FSR wiring** — unchanged divider model from
[`docs/calibration.md`](calibration.md)/[`analysis/calibrate.py`](../analysis/calibrate.py):
`3V3 — FSR — node — 10 kΩ — GND`, node → ADC pin. With 6 zones and 6 analog pins, **no mux** —
each FSR lands directly on its own Feather pin:

| Zone | Feather pin |
|---|---|
| `heel_med` | `A0` |
| `heel_lat` | `A1` |
| `midfoot`  | `A2` |
| `met1`     | `A3` |
| `met5`     | `A4` |
| `hallux`   | `A5` |

(Full zone coordinates: [`docs/insole_sensor_layout.md`](insole_sensor_layout.md).)

**Full pin-by-pin solder guide** (which pad gets which lead, perfboard layout, divider theory,
solder order, and pre-power multimeter checks): [`docs/WIRING.md`](WIRING.md).

**Power:** the LiPo 2500 mAh plugs directly into the Feather's onboard 2-pin JST-PH battery
connector — it lives inside the case, stacked under the board, no external wiring. Charges +
programs through the same USB-C port the pod exposes.

---

## (c) In-person assembly order & timing

Do this after both prints are done and the Micro Center parts are in hand (~45–75 min first
time through):

1. **Dry-fit** the Feather onto the base's four standoff posts — confirm the 2.5 mm holes line
   up before committing (measure your actual board against `feather_hole_dx`/`dy` first; adjust
   and reprint the base if they're off).
2. **Wire the 6 FSR dividers** — resistor + FSR leads to a small stub of perfboard or straight to
   the Feather's `A0`–`A5` pins and a shared `GND`. Do this **before** seating the board in the
   case; it's much easier on the bench. Pin-by-pin detail (which pad gets which lead, solder
   order, pre-power checks): [`docs/WIRING.md`](WIRING.md).
3. **Seat the LiPo** in the base first (floor of the main bay), then the wired Feather on top,
   screw into the standoffs (self-tap or heat-set insert — see (e)).
4. **Plug the battery** into the Feather's onboard JST-PH connector.
5. **Seat the MPU-6050** in the IMU-bay lip pocket, loop a zip tie up through one floor slot,
   over the board, down through the other, cinch from underneath.
6. **STEMMA-chain** Feather → MPU-6050 → (cable out the STEMMA-exit slot) → VCNL4200.
7. **Route the FSR lead bundle** out the sensor-exit slot toward where the insole carrier will sit.
8. **Dry-fit the lid** — press until the snap ribs click into the base's groove notches. If it's
   too tight/loose, see (e) for the `tol` reprint tweak.
9. **Thread the ~25 mm strap** through both strap-slot bosses; mount to the lower shin/ankle.
10. **Flash + smoke-test** before closing anything up for good — confirm all 6 FSR channels read
    and both I2C devices enumerate (see the gotcha in (b)) with the lid off.

---

## (d) Parallel/overnight prints vs. what needs the Micro Center trip first

**Blocking on the store trip (do this first, or at least in parallel with printing):** the FSR
402 10-pack, 10 kΩ resistors, an M2.5 screw or two (or a heat-set insert kit), and the elastic
strap material are the only items that gate final assembly — everything else (ESP32-C6 Feather,
LiPo, VCNL4200/MPU-6050 STEMMA breakouts, STEMMA QT cables) is presumably already inbound per the
shared BOM.

**Prints — no supports, so all four can run unattended overnight,** in whatever order fits your
plate/bed-clearing schedule:
1. Ankle pod base + lid (PETG/PLA-CF) — can share a plate.
2. FSR carrier plate (TPU, external spool) — run separately if the AMS/dryer feed setup doesn't
   like sharing a plate with the PETG job; check nozzle assignment either way.
3. Six FSR pucks (PLA/PETG, 0.2 mm nozzle) — fast, batch these together, good "one more job before
   bed" print.

**The in-person, attended step is electronics assembly (c)** — do this only after both prints
*and* the parts-store items are on hand; there's no point starting wiring with only half the BOM.

---

## (e) Cleaning / post-processing

- **No supports = minimal cleanup.** Light deburr of the drain holes and cutout edges with a
  hobby knife or a fine file — printed round holes through a wall often have a small lip.
- **IPA wipe** the PETG/PLA-CF shell (base + lid) before handling the electronics — clears
  bed-release residue/oils off the surface, standard habit before boards go in.
- **TPU carrier:** no acetone/IPA needed (won't dissolve TPU and doesn't need it). Trim any
  wire-channel stringing with flush cutters.
- **Heat-set inserts (optional, recommended if you'll open the case often):** rather than
  self-tapping an M2.5 screw straight into the post's 2.0 mm pilot hole every time, drill the
  pilot out to ~2.5 mm and press an M2.5 heat-set insert into each standoff post with a soldering
  iron (~200–220 °C for PETG; check your insert's spec if you went PLA-CF). Do this before final
  assembly — much easier with the case empty.
- **Lid fit-check:** press the lid on dry before wiring anything permanently. Too tight → bump
  `tol` up by 0.05–0.1 mm and reprint just the `lid()` half; too loose to click → drop it by the
  same amount. Standard FDM press-fit tuning, same idea as any other snap part in the repo.

---

## (f) Calibration → the existing analysis scripts

Nothing new to build here — this rig reuses the repo's existing pipeline, with one adaptation:

1. **Calibrate** exactly per [`docs/calibration.md`](calibration.md): flash
   [`firmware/fsr_calibrate/`](../firmware/fsr_calibrate/fsr_calibrate.ino) (or your own C6
   equivalent reading `A0`–`A5`), record known weights per sensor, fit with
   [`analysis/calibrate.py`](../analysis/calibrate.py) — same power-law model, same
   `pad_area_mm2` default (122.7 mm² for a 12.5 mm round FSR402 pad), just **6 channels instead
   of 8**.
2. **Zone-count adaptation (the one real code change):** `analyze_pressure.py`, `zone_load.py`,
   `day_summary.py`, and `nerve_fascia.py` all expect 8 FSR columns. Either zero-fill the missing
   `met3`/`toes` columns before feeding a 6-zone log in, or edit each script's `ZONES` list to the
   6-zone set — spelled out with the exact table in
   [`docs/insole_sensor_layout.md`](insole_sensor_layout.md#compatibility-note-for-the-analysis-scripts).
   This mirrors the same kind of small, flagged adaptation `path2_tracking_build.md` already notes
   for its `mode` column — not done yet, just documented so it isn't a surprise.
3. **Run it:**
   ```powershell
   python analysis/analyze_pressure.py "day_*.csv" --calibration calibration.json --out results/
   ```
   Everything downstream (hot-spot detection, the all-day dose, `build_insole.py`'s relief-window
   placement) works unchanged once the 6-zone adaptation above is in — it only reads zone names
   and pressures, not sensor count.

---

**Not a medical device.** FSRs give relative, repeatable pressure — calibrate, read trends,
recalibrate as they drift. Same honest-limits framing as the rest of `docs/`.
