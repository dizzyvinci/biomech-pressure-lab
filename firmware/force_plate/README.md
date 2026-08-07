# `force_plate` — pressure/force firmware

**Repo:** `biomech-pressure-lab` · **Written:** 2026-08-07 · **Status: COMPILES CLEAN, UNTESTED ON HARDWARE.**

Nothing in this folder has been flashed. No serial port has been opened. No HX711, load cell or FSR
has ever been connected to it. Every number it prints is unverified until §6 has been run.

---

## 0. Read this before you pick anything up

Two things are true at once and both matter:

* The pressure subsystem is the only one in this tree with **printed parts physically on the desk**
  (`BIO-FORCE-PLATE`, `BIO-FSR-PUCK-01`, PETG, job `1148490506`, 2026-08-07).
* **It is not a force plate yet, and the blocker was never firmware.**

`hardware/BENCH_NEXT_STEPS.md` §0 settled the geometry: `force_plate.stl` is **one `foot()`**
(19.0 × 26.0 × 21.0 mm), not a plate. The rig wants 4 feet, 4 `top_boss()` and a top. You have
**1 / 0 / 0**, and `top_boss()` / `top_plate()` are still commented out in `force_plate.scad`, so no
STL exists for them. The one foot also printed in **plain PETG at ≤52 % effective density** against a
`PRINT_CARD.md:40` spec of PA-CF/PETG-CF at 100 % infill.

**So: nobody stands on this.** That is enforced in code, not asked for — `MAX_BENCH_N = 250 N`
latches an overload fault and stops the session. T1DM means reduced protective sensation: the
operator may not feel a corner bracket digging in or a rig beginning to fail, so the ceiling lives
where it does not depend on being felt.

**What you *can* do today, with zero purchases:** bench the HX711 and the FSR puck by hand and by
bench mass, calibrate them, and prove the whole acquisition/logging chain end to end. That is §6.

---

## 1. What was fixed, and the library question

The previous revision of `force_plate.ino` **did not compile**: `fatal error: HX711.h: No such file
or directory`. `FIRMWARE_SCOPE.md` flagged that missing library as handoff **H5** on 2026-08-05 and
it was never actioned — `arduino-cli lib list` still returns the same five libraries it returned
then (BusIO, GFX, MPU6050, SSD1306, Unified Sensor).

**This firmware does not wait on that handoff.** `hx711_lite.h` is a ~130-line inline driver, so the
sketch has **zero external dependencies** and builds on this machine as it stands. That is not just
convenience — the stock library's `wait_ready()` blocks forever on an absent or miswired amp, and a
silent hang is indistinguishable from "no load applied". Every read here takes a timeout.

*(Installing the missing libraries is still worth doing for the other repos' sketches. It is not
needed for anything in this folder, and I did not run it — installs belong to you.)*

Five other real defects fixed, listed with reasons in the header of `force_plate.ino`: a strapping
pin used for HX711 DOUT (**B2**), a 4-channel pin map that used **GPIO6/GPIO7 — bonded to the
WROOM-32's internal SPI flash, so touching them crashes the chip** (**B3**), a hard-coded
`BODY_N = 700.0` dividing every output by an unsourced body weight (**B4**, the same defect
`analysis/balance.py` already refuses for `FOOT_L_MM`), no read timeouts (**B5**), and calibration
stored in a source constant so it died on every reflash (**B6**).

---

## 2. The HX711 count decides everything — and it is ONE

> `ergonomics/carts/INVENTORY.md:259` — *"4× 50 kg load cells + HX711 amp | 8.49"*
> `FIRMWARE_SCOPE.md` parts ledger — *"4× 50 kg load cell + HX711 | **1 set**"*

**One amplifier.** That is the whole answer to the total-force-vs-centre-of-pressure question:

| Mode | Amps | Wiring | Output | Buildable now? |
|---|--:|---|---|---|
| `MODE_TOTAL` **(default)** | 1 | 4 half-bridge cells → **one** full Wheatstone bridge (bathroom-scale topology) | total vertical force only | ✅ **yes** |
| `MODE_AP` | 1 | 4 cells → **two** full bridges → HX711 ch A + ch B | total **+ 1-D anterior/posterior CoP** | ✅ yes, but rewire + untested |
| `MODE_COP4` | 4 | 4 full-bridge cells, one amp each, shared clock | full **2-D CoP** | ❌ needs 3 more HX711 → §8 |

`MODE_AP` is the interesting one and it costs nothing: instead of summing all four half-bridge cells
into a single bridge, pair them front/front and rear/rear into **two** bridges and read them on the
HX711's two channels. **Caveat that must not be glossed:** channel B's gain is **fixed at 32** where
channel A is 128, so the rear line is roughly **4× coarser**. It is a real 1-D CoP, not a substitute
for a 4-cell rig. Marked untested because it is.

All three modes compile (§7). Select with `-DACQ_MODE=0|1|2`.

---

## 3. Wiring

### 3.1 Load cells → HX711

Each 50 kg cell is a **half bridge, 3 wires**: red = centre tap, black and white = bridge ends.
Combining four into one full bridge is the standard SparkFun load-cell-combinator pattern — opposite
corners take tension vs compression, so they sum.

| HX711 pin | Goes to | Conductor |
|---|---|---|
| `E+` | red of cells 1 & 3 | cell pigtail as supplied |
| `E−` | red of cells 2 & 4 | cell pigtail as supplied |
| `A+` | white of 1 & 2, black of 3 & 4 | cell pigtail as supplied |
| `A−` | black of 1 & 2, white of 3 & 4 | cell pigtail as supplied |
| `B+` / `B−` | *unused in `MODE_TOTAL`* — leave open | — |

For **`MODE_AP`**: cells 1+2 form one bridge into `A+/A−`, cells 3+4 form the second into `B+/B−`.

### 3.2 HX711 + SD + FSR → ESP32-WROOM-32 DevKitC

**Board:** `esp32:esp32:esp32` (Elegoo ESP-32 3-pack). The ESP32-C6 Feather is *not* used here —
`SENSING_DEVICES_PLAN.md:587` assigns the Feather to the worn insole/ankle pod.

| Signal | GPIO | Direction | Conductor | Why this pin |
|---|--:|---|---|---|
| HX711 `PD_SCK` | **27** | out | 28 AWG silicone | safe GPIO, not strapping, not flash |
| HX711 #0 `DOUT` | **34** | in | 28 AWG silicone | **input-only pin — ideal**, and DOUT is push-pull so it needs no pull-up (GPIO34-39 have none) |
| HX711 #1–3 `DOUT` | 35 / 36 / 39 | in | 28 AWG silicone | `MODE_COP4` only, amps not owned |
| HX711 `VCC`, `GND` | 3V3, GND | — | 28 AWG silicone | 3.3 V rail; do **not** feed 5 V into a 3.3 V logic pin |
| FSR puck A | **32** | in | 28 AWG bench / **22 AWG in-shoe** | ADC1_CH4 |
| FSR puck B | **33** | in | 28 AWG bench / **22 AWG in-shoe** | ADC1_CH5 |
| SD `CS` | **5** | out | 28 AWG silicone | VSPI CS; it *is* a strapping pin but CS idles HIGH, which is the level the strap wants |
| SD `SCK` / `MOSI` / `MISO` | 18 / 23 / 19 | — | 28 AWG silicone | VSPI defaults |
| Status LED | 2 | out | onboard | ~3 mA. **The only output pin in this firmware.** |

**Pins deliberately avoided:** `GPIO6–11` are bonded to the WROOM-32's internal SPI flash — using
them crashes the chip, and the previous revision used two of them. `GPIO0/12/15` are strapping pins.

### 3.3 Conductor gauge — this is a medical constraint, not a preference

* **28 AWG silicone stranded (Adafruit 3890, 10-way ribbon, 1 m) is OWNED** and is correct for every
  run in the table above. It is also the *only* correct choice for anything on the head or crossing a
  hypermobile joint: 22 AWG there adds mass and bending stiffness against a structure that cannot
  resist it.
* **⚠️ The owned metre of 3890 is committed to the rib-follower→mux loom.** Do not consume it on this
  bench rig without deciding that trade explicitly.
* **22 AWG silicone stranded is the right spec for the in-shoe FSR run** (`docs/WIRING.md:199` — it is
  a longer, more abused, non-worn-on-head path) **and is NOT ON HAND** (`INVENTORY.md:156`). It is
  already **in the active cart, not ordered** (TUOFENG `B07G2JWYDW`, $15.69, carted 2026-08-07).
  `INVENTORY.md:577` names its scope precisely: *"unblocks the bed mat + force plate only, and is the
  wrong conductor for HUD temples / exo §4.1 / ribs Track C."* This subsystem is one of the two things
  it is genuinely for. → §8.
* Everything on this bench is currently **solderless-or-nothing**: breadboards and jumpers are
  explicitly not owned (`INVENTORY.md:162`). Perfboard *is* owned but requires solder *and* wire.

### 3.4 FSR divider

`3V3 ──[ FSR ]── node ──[ 10 kΩ ]── GND`, node → ADC pin. The 25× 10 kΩ pack (Adafruit 2784) arrived
with order #3716034 (delivered ~07-28, packing slip photographed IMG_0765). The printed
`fsr_puck` is the load-spreading cap that sits on the pad.

---

## 4. Calibration — a procedure you can actually run

Commands over serial at **115200**. Type `HELP` for the full list.

1. **Power up and leave it alone for two minutes.** HX711 + strain gauges drift while warming.
   Taring cold and then measuring produces a slow ramp that reads exactly like material creep.
2. `ID` — confirm mode and pin map.
3. `RAW` — you should see `ch0=` with counts moving when you press the rig. `TIMEOUT` means the amp
   is not answering: check `VCC`, `E+`/`E−`, `DOUT`, `CLK`.
4. `ZERO` — 60-second drift check with nothing touching the rig. It prints the spread in newtons.
   **A spread above ~2 N means it is still warming up — wait and repeat.** Do not skip this.
5. `TARE` — zeroes every channel.
6. Put a **known mass** on the rig, then `CAL 0 <kg>`.
   * **The mass has to be big enough.** A 200 kg-capacity rig reading a 200 g reference sits in the
     noise, and a scale factor fitted there is worthless. The firmware **refuses** any calibration
     where the reading moved less than 1000 counts and tells you why.
   * **Free reference that works:** a sealed **1 US gallon jug of water = 3.785 L ≈ 3.78 kg** at 20 °C.
     Water's density is the reference — you do not need to weigh it.
   * The owned 0.01 g pocket scale is excellent for weighing an FSR-scale reference (grams) and
     useless for a load-cell-scale one (kilograms). Both statements are true; use the right one for
     the right sensor.
   * A proper set of masses or a hanging scale is the real fix → §8.
7. `SAVE` — writes offsets and scale factors to NVS so they survive a reflash. (**B6**.)
8. Optional: `BW <kg>` to enable the `bw_ratio` column, and `GEOM <ap_mm> <ml_mm>` for CoP geometry.
   **If you skip `BW`, `bw_ratio` stays blank** — the firmware will not divide your data by a body
   weight nobody sourced.

**FSR calibration** is a different curve (power-law, not linear): use `firmware/fsr_calibrate`, log
`sensor,force_N,adc` rows into `cal_points.csv`, and fit with `python analysis/calibrate.py`.

---

## 5. Output format

### 5.1 Conditions are coordinates — and `START` enforces it

`START` is **refused** until all five condition fields are set:

```
COND posture=stand_2ft load=mass_only footwear=barefoot side=both surface=hard note=warmup_2min
START
```

`posture` · `load` · `footwear` · `side` · `surface` (+ optional `note`). Every row carries a
`cond_id`; changing any field increments it and rolls to a new SD file, so **no row can ever be
orphaned from the conditions it was taken under.** For bring-up without a condition there is `RAW`,
which is prefixed `#RAW`, is never written to SD, and is not CSV.

### 5.2 Timestamps — and the honest gap

There is **no RTC anywhere in this inventory**. Wall-clock time can therefore only come from the host:

```
TIME 1754582400        # unix seconds; sets the clock via settimeofday()
```

Every row carries `t_ms` (monotonic since boot, always correct). `iso_utc` is **empty** until `TIME`
is sent, and flag `0x0080` says so. An empty column is the truthful answer; a fabricated timestamp
is not.

### 5.3 CSV

`#`-prefixed header block (firmware version, session, full condition set, calibration constants,
safety ceilings), then `#COLS`, then rows. Everything in `analysis/` already skips `#`.

```
t_ms,iso_utc,sess,cond_id,activity,total_n,ch0_n,ch1_n,ch2_n,ch3_n,
cop_ap_mm,cop_ml_mm,bw_ratio,fsr0_adc,fsr0_mv,fsr1_adc,fsr1_mv,flags
```

`activity` = the posture verbatim, which is the column `analysis/balance.py`'s `group_col()` looks
for. `fsr*_adc` is raw 12-bit, the column `analysis/calibrate.py` expects; `fsr*_mv` is
`analogReadMilliVolts()` — better linearity, added *alongside* rather than replacing, so the existing
fit still runs unchanged.

SD path: `/plog/S<session>_C<cond_id>.csv`, flushed every 20 rows so a yanked card loses ≤20 rows.

**⚠️ microSD does not work today and that is a parts gap, not a code gap.** A 32 GB SanDisk card is
on hand (`INVENTORY.md:554`) but **no microSD breakout / card socket is owned** — there is no such
row anywhere in the inventory, which is exactly what `POST_RESTART_CART.md:382` logged as **T1-05,
~$3.50, "cheapest structural unblock in the file."** The firmware detects this and prints
`#WARN no microSD ... serial only`, then runs normally on serial. Piping serial to a file works today.

### 5.4 `flags` bitmask

| Bit | Meaning |
|---|---|
| `0x0001` | HX711 read timeout |
| `0x0002` | HX711 saturated (rails at ±0x7FFFFF → usually a disconnected cell or no excitation) |
| `0x0004` | **overload trip** |
| `0x0008` | not tared |
| `0x0010` | not calibrated (scale factor still 0) |
| `0x0020` | condition incomplete |
| `0x0040` | SD write failure |
| `0x0080` | wall clock never set |
| `0x0100` | session cap reached |

---

## 6. Bench test — prove it works BEFORE anything is worn or loaded

Run in order. Any step that fails stops the sequence.

| # | Step | Pass criterion |
|--:|---|---|
| 1 | Flash, open serial 115200 | Banner prints, including **BENCH ONLY — DO NOT STAND ON THIS RIG** |
| 2 | `ID` | Pin map matches §3.2 exactly |
| 3 | **Meter before power.** With the AstroAI TRMS: HX711 `VCC` = 3.3 V, `E+`−`E−` ≈ 3.3 V, no continuity `VCC`↔`GND` | as stated |
| 4 | `RAW`, touch nothing | `ch0` counts present and *stable to a few hundred*. `TIMEOUT` = wiring fault, stop |
| 5 | `RAW`, press the rig by hand | counts move **monotonically** with press. If they move backwards, `A+`/`A−` are swapped |
| 6 | `ZERO` (60 s, untouched) | spread **< 2 N**. If not, keep warming up and repeat |
| 7 | `TARE`, then `SHOW` | offset non-zero, flag `0x0008` cleared |
| 8 | `CAL 0 3.78` with a 1 gal water jug | accepted (>1000 counts). If refused, the reference is too light — that refusal is the firmware working |
| 9 | Remove mass, `RAW` | returns to within ~1 N of zero. A large residual = mechanical binding, **not** a code problem |
| 10 | Re-place the same mass **5×**, note the reading | spread **< 2 %** of the value. This is the repeatability number that decides whether the rig is usable at all |
| 11 | `SAVE`, reset the board, `SHOW` | calibration survived the reboot |
| 12 | `START` with **no** condition set | **refused**, with the coordinates message. This test proves the gate works |
| 13 | `COND ...` then `START` | header block + CSV rows stream |
| 14 | Press past ~25 kg | `#ALERT OVERLOAD`, logging stops, LED solid. **This is the safety test — do not skip it.** Send `CLEAR` |
| 15 | Unplug the HX711 mid-session | `#FAULT ... timed out`, clean stop. **No hang.** This is the watchdog/timeout test |
| 16 | Press the `fsr_puck` on FSR A | `fsr0_adc` / `fsr0_mv` rise and return |

Steps **14 and 15 are the ones that matter most** and are the easiest to skip. 14 proves the hard
limit fires; 15 proves a fault presents as a fault rather than as a plausible-looking flat line.

---

## 7. Compile state — measured, 2026-08-07

Compiler: bundled `arduino-cli 1.5.1`
(`AppData\Local\Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe`),
esp32 core **3.3.11**. **No library installs were performed.**

```
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/force_plate
```

| Build | Program storage | RAM |
|---|--:|--:|
| `force_plate` `MODE_TOTAL` (default) | **376,845 B / 28 %** | 24,368 B / 7 % |
| `force_plate` `MODE_AP` (`-DACQ_MODE=1`) | 377,369 B / 28 % | 24,368 B / 7 % |
| `force_plate` `MODE_COP4` (`-DACQ_MODE=2`) | 378,017 B / 28 % | 24,368 B / 7 % |
| `fsr_calibrate` `FSR_DIRECT` (`adafruit_feather_esp32c6`) | 294,110 B / 22 % | 15,500 B / 4 % |
| `fsr_calibrate` `FSR_MUX` (`-DFSR_MODE=1`) | 294,380 B / 22 % | 15,500 B / 4 % |

All five clean, no warnings-as-errors. **All five are UNTESTED ON HARDWARE.**

---

## 8. Parts this needs that are NOT verified on hand → CART

Ordered by what unblocks the most for the least. **Nothing here has been ordered, carted or paid for.**

| # | Part | ~$ | Unblocks | Evidence it is missing |
|--:|---|--:|---|---|
| **1** | **microSD breakout / SPI card socket** | 3.50 | on-device logging for this *and* every worn node. The 32 GB card is already owned | **No such row exists anywhere in `INVENTORY.md`.** Logged as T1-05 in `POST_RESTART_CART.md:382`, "cheapest structural unblock in the file" |
| **2** | **Breadboard + jumper wires** | ~8 | *every* "solderless bench" claim in this repo, including step 4 of §6 | `INVENTORY.md:162` — explicitly NOT owned |
| **3** | **22 AWG silicone stranded** — ⚠️ **already carted, not ordered** | 15.69 | the in-shoe FSR run and the force-plate harness. `INVENTORY.md:577` scopes it to *"the bed mat + force plate only"* — this subsystem is one of the two things it is actually for | `:156` NOT owned; TUOFENG `B07G2JWYDW` in the **active cart** since 2026-08-07. Rank **14 of 16** in `CONSTRUCTION_ORDER.json` — do not call it the top blocker |
| **4** | **Reference masses or a hanging/fish scale, ≥10 kg** | ~12 | **turns every reading in this repo from arbitrary units into newtons.** §4 step 6 | `MASTER_REGISTER.md:1001` item 4-6 T2, "a reference force above 200 g" |
| **5** | **HX711 amplifier ×3** | ~9 | `MODE_COP4` — full 2-D centre of pressure. *This is the open $9 question, and the answer is that CoP is not possible without it* | only **1 set** owned (`INVENTORY.md:259`) |
| **6** | **4× full-bridge (4-wire) load cells** | ~15 | `MODE_COP4` needs full bridges; the owned kit is half-bridge | owned kit is the 4×50 kg half-bridge type |
| **7** | **M2–M6 fastener assortment (incl. M5)** | ~8 | mechanically assembling *any* foot to *any* cell — `force_plate.scad` `LC_hole_d = 5.2` is M5 clearance. **This is rank 13 in `CONSTRUCTION_ORDER.json`, the tree's top purchase blocker** | **zero** screw/bolt/nut/washer rows in `INVENTORY.md`; 345 heat-set inserts have nothing to thread into |
| **8** | PA-CF or PETG-CF filament for the structural reprint | — | reprinting 4 feet + 4 bosses to `PRINT_CARD.md:40` spec | plain PETG at ≤52 % density is a fit coupon, not a load path |
| **9** | USDRWAM thin-film FSR ×4 | 9.99 | 6 owned + 4 = 10 = one full single-foot map | **evicted to Saved-for-Later**, `INVENTORY.md:569` — will not arrive unless moved back |

**Cheapest path to a fully working logger today: #1 alone ($3.50).** Everything else in this folder
already runs on serial with what is on the shelf.

### ⚠️ Shelf check owed before any of this is trusted

`INVENTORY.md` contradicts itself about the load cells **right now**: `:157` "NOT owned" (the phantom
$471.94 order that was never placed), `:310` still an open ~$12 buy line, `:344` "force plate ⛔
BLOCKED", against `:563` "on-hand, sensor batch delivered Aug 1–2". The later reconciliation is
probably right — but the **Velostat from that same batch is still in transit (ETA ~Aug 10)**, so the
batch demonstrably did not fully land, and unlike the multimeter and coin motors ("verified on
arrival") the load cells got no arrival check and appear in no photo. `FIRMWARE_SCOPE.md:65` declared
this settled citing `INVENTORY.md:474` — **that citation is now dead** (line 474 is a filament row).

**Opening the box is the cheapest action in this entire tree and it gates §6 step 4 onward.**

---

## 9. Safety, stated plainly

* **Nothing in this subsystem heats, vibrates or moves.** No motor, no heater, no servo, no haptic.
  The only output pin is the 3 mA status LED. There is therefore no duty cycle to bound — that is the
  honest answer, not an omission. The HX711 excites the bridge at ~4.3 V through ~1 kΩ (~4 mA); there
  is no thermal path to skin in this circuit at all.
* **Hard input limit, latching:** `MAX_BENCH_N = 250 N`. Trips → alert, session stops, requires
  `CLEAR`. ~25 kg is far above any legitimate bench mass and far below the ~779 N one sole sees.
* **Session cap:** 20 minutes, auto-stop. Bounds an unattended rig pressing on an insensate foot.
* **Task watchdog:** 8 s, panic on timeout, fed every loop. Every HX711 read is timeout-guarded, so a
  missing amp reports `#FAULT hx711_timeout` instead of hanging in a way that looks like "no load".
* **`ALLOW_BODY_LOAD` is 0** and should stay 0 until the rig is reprinted to structural spec *and*
  proof-loaded. Note the proof load cannot currently be done at all: the owned 4× 50 kg cells sum to
  ~1.96 kN against a ~3.5 kN target (`force_plate.scad`).
* **T1DM + hEDS are why these are in code rather than in prose.** Reduced protective sensation means
  a fault may not be felt; a foot injury here is not a bruise.
