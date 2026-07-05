# Build guide — the two DIY instruments that close the biggest gaps

From [lab_scope.md](lab_scope.md): the insole gives *relative* pressure; these two prints
add the **vertical GRF (× body-weight)** and a **full-foot pressure map** the papers use —
for **~$150** of parts + the H2D. We don't hit lab accuracy; we get the important data at
scale, cheaply, to trend and extrapolate.

## 1 · Force plate — vertical GRF in body-weights
**Unlocks:** the ×BW numbers the insole can't (gymnastics 7–16, jump-landing, running
2.5–3). DIY load-cell rigs reach **ICC > 0.94** vs a lab plate. *(Center-of-pressure too,
if you take the 4-HX711 upgrade — the cheap kit gives total force, which is the key number.)*

**Print** ([`hardware/force_plate.scad`](../hardware/force_plate.scad)): 4× `foot()` +
4× `top_boss()` in PETG (100% infill — they carry load). Top: print `top_plate()` **or**
use a 240 mm plywood/acrylic square (stiffer, faster).

**Buy:** 4× bar load cells (**50 kg** each → 200 kg / ~2000 N capacity) + an **HX711**
amp (a "4× 50 kg load cell + HX711" kit is ~$9), M5 bolts, rubber feet.

**Assemble:** one load cell per corner, **fixed end bolted to a `foot`, free end to the
top** with the air gap so it flexes (don't let it bottom out). Wire the **four cells into
one full bridge** → a single **HX711** → ESP32-S3 (the standard "load-cell combinator"
pattern). *CoP upgrade:* swap in 4 **full-bridge** cells on 4 HX711 for per-corner force.

**Firmware** ([`firmware/force_plate/`](../firmware/force_plate/force_plate.ino)): tares on
boot, streams `t_ms,total_N,total_BW` (flip `COP_MODE` to 1 for the 4-HX711 CoP build).

**Calibrate:** put a known mass on each corner, tune `CAL[i]` until grams read true; set
`BODY_N` to your weight. Then a step/jump onto the plate = a real GRF trace (peak ×BW,
loading rate, CoP) — feed it to the landing/balance analysis by timestamp.

## 2 · Velostat pressure mat — a full-foot pressure map
**Unlocks:** a heel/arch/forefoot **pressure map** (platform-style) to complement the
8-zone insole — great for the standing / seated / bounce work. A maker build resolved
~7,000 cells clearly.

**Print** ([`hardware/pressure_mat.scad`](../hardware/pressure_mat.scad)): the `frame()` —
a rigid border + an **alignment comb** that lays the copper strips straight at `PITCH`
(default 10 mm → ~8×11 = 88 cells for a 110×260 mm mat), plus a cable slot.

**Buy:** a **[Velostat/Linqstat sheet](https://www.adafruit.com/product/1361)** (~$4),
**copper foil tape** (rows + columns), and a **CD74HC4067** mux (you already have a 12-pack)
for the columns.

**Assemble:** lay copper-tape **rows** on the bottom (along the comb), Velostat over them,
copper-tape **columns** on top (crossing). Each overlap = a pressure cell. Rows → ESP32
GPIO; columns → mux → ADC.

**Firmware** ([`firmware/pressure_mat/`](../firmware/pressure_mat/pressure_mat.ino)): drives
one row HIGH at a time, reads every column via the mux, streams a frame per line. Pipe to a
Python heatmap (`matplotlib.imshow` of the row×col array). Caveats in the sketch: **ghosting**
(ground inactive columns or add per-cell diodes) and, for a big matrix, drive rows with a
**74HC595 shift register** instead of one GPIO each.

## Honest limits (see [lab_scope.md](lab_scope.md))
Still coarse + resistive (drift → recalibrate); **no shear/6-axis**. But vertical GRF and a
real pressure map, from prints + ~$150, is the data that matters for finding *your* hot
spots and dosing *your* load. r≈0.87, not 1.0 — at scale, that's plenty to extrapolate from.
Not a medical device.
