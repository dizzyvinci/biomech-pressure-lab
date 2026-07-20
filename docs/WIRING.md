# Wiring — pin-by-pin solder guide for the STEMMA-QT ankle pod

The one thing [`BUILD_PLAN.md`](BUILD_PLAN.md) step (b)/(c) says and doesn't say: it tells you
to wire "the 6 FSR dividers... to a small stub of perfboard" but not which pad gets which lead.
This doc is that missing layer — pin-by-pin, for the **exact hardware in this build**: an
**Adafruit ESP32-C6 Feather** (STEMMA QT), **MPU-6050** + **VCNL4200** STEMMA QT breakouts, **6×
FSR402**, and a flat 1200 mAh LiPo. Read it alongside
[`BUILD_PLAN.md`](BUILD_PLAN.md) §(b)/(c), [`insole_sensor_layout.md`](insole_sensor_layout.md)
(zone numbering), and [`calibration.md`](calibration.md) (the divider math this doc explains the
*build side* of).

Not a medical device — a build reference, same as the rest of `docs/`.

---

## 0. What needs NO soldering — read this first

**The entire I²C sensor chain is plug-in. Zero solder joints.** This is the single biggest labor
saver in the whole build and it's easy to miss because BUILD_PLAN.md's wiring section is titled
the same as the FSR section:

```
ESP32-C6 Feather (STEMMA QT port) ──cable──▶ MPU-6050 (0x68) ──cable──▶ VCNL4200 (0x51)
```

Every connector in that chain is a keyed **JST-SH 4-pin STEMMA QT** plug — SDA/SCL/3V/GND, push
to seat, no tools. **The only soldering in this entire build is the 6 FSR voltage dividers.**
Everything else below in this doc (§1–§8) is exclusively about that FSR wiring.

**Cable inventory gate (you have 1 of 3 needed cables today):** you're holding **one** STEMMA QT
cable, with two more incoming. The chain above needs **two cable hops** — Feather→MPU-6050 and
MPU-6050→VCNL4200 — so with one cable on hand you can seat the Feather→MPU-6050 hop now and bench
test I²C with just the IMU enumerating; hold the VCNL4200 off the chain until cable #2 arrives.
Don't start soldering FSRs waiting on this — the two jobs are independent and the FSR side is the
long pole anyway.

**The BNO085 upgrade path (×3 incoming) — also zero-solder.** When the BNO085 boards arrive, the
MPU-6050→BNO085 swap is a **cable swap, not a rewire**: unplug the STEMMA cable from the MPU-6050,
plug it into the BNO085, done. Two things to check before you do:
- **I²C address.** Adafruit's BNO08x STEMMA QT breakout defaults to `0x4A` (solder-jumper
  selectable to `0x4B`) — **not** `0x68` — so the firmware's I²C address constant needs updating
  when you swap, even though the physical wiring doesn't change.
- **Enclosure fit.** [`ankle_pod_enclosure.scad`](../hardware/ankle_pod_enclosure.scad)'s
  `imu_bay` pocket is sized to the MPU-6050's footprint (`imu_l=18, imu_w=13`). Adafruit's BNO08x
  STEMMA QT board is a noticeably bigger breakout — measure yours against that pocket before you
  assume it drops in; if it doesn't fit, bump `imu_l`/`imu_w` in the `.scad` and reprint just the
  `base()`. Same "measure your actual board" caveat the file already gives for the Feather and
  MPU-6050.

---

## 1. FSR voltage divider — the theory, briefly

An FSR402's resistance **falls** as force on the pad **rises** (roughly 1 MΩ+ unloaded down to a
few hundred ohms at full body weight). Wired into a divider with a **fixed resistor to ground**,
that resistance swing becomes a voltage swing the ADC can read:

```
3V3 ──[ FSR ]── node ──[ R_fixed ]── GND        ADC pin reads "node"
```

```
Vnode = Vcc × R_fixed / (R_fixed + R_fsr)
```

More force → lower `R_fsr` → **higher** `Vnode` (node voltage rises toward 3V3 as the FSR's
resistance shrinks relative to the fixed resistor).

**`R_fixed` sets *where* the divider is most sensitive**, because the curve is steepest (most
`ΔV` per `ΔR_fsr`) right around the force level where `R_fsr ≈ R_fixed`. Pick `R_fixed` too high
and you lose resolution at heavy loads (the curve saturates near 3V3 early); too low and you lose
resolution on light loads (the curve stays pinned near 0V until real force shows up.

**Start at 10 kΩ** — that's the repo-wide default (`calibrate.py --r-fixed` defaults to `10000`,
`vcc` defaults to `3.3`), it's what [`calibration.md`](calibration.md)'s divider model already
assumes, and it centers sensitivity in the light-to-moderate stance-phase range that matters for
this rig. **Tune it after your first calibration pass** ([`calibration.md`](calibration.md) §Do
it once): if `calibrate.py`'s fitted curve for a channel is bunched into the low or high end of
the 0–4095 ADC range instead of spread across it, that channel's `R_fixed` is off — raise it if
the channel never gets far off 0, lower it if it saturates near 4095 well before max stance force.
The ESP32-C6's ADC is 12-bit (0–4095), which is `calibrate.py`'s `--adc-max` default — no flag
needed at the standard 10 kΩ/3.3V setup.

---

## 2. Pin table — FSR zone → divider node → Feather ADC pin

Matches the `fsr0..fsr5` wiring order in [`insole_sensor_layout.md`](insole_sensor_layout.md) and
the CSV column names the firmware logs.

| # | Zone | Divider node | Feather pin | CSV column |
|---|---|---|---|---|
| 0 | `heel_med` | N0 | `A0` | `fsr0` |
| 1 | `heel_lat` | N1 | `A1` | `fsr1` |
| 2 | `midfoot`  | N2 | `A2` | `fsr2` |
| 3 | `met1`     | N3 | `A3` | `fsr3` |
| 4 | `met5`     | N4 | `A4` | `fsr4` |
| 5 | `hallux`   | N5 | `A5` | `fsr5` |

| Rail | Feather pin | Feeds |
|---|---|---|
| 3V3 | `3V` (silkscreened `3V` on the Feather; called `3V3` throughout this repo) | Top leg of all 6 FSRs (shared) |
| GND | `GND` | Bottom leg of all 6 fixed resistors (shared) |

Each zone is **one FSR + one 10 kΩ resistor**, independent of the other five — no mux, no shared
ADC pin, so a solder mistake on one channel can't cross-talk into another.

**Inventory note:** you have 2 of the 12 FSR402 on hand (10 incoming). The divider/solder process
is identical per channel, so there's no reason to wait for all 12 — wire and bench-test whichever
2 zones you have now (e.g. `heel_med`/`heel_lat`, since they share the perfboard's near edge),
confirm the process, then repeat for the rest as they arrive.

---

## 3. Perfboard layout

BUILD_PLAN.md §(b) gives you two options — "a small stub of perfboard, **or** straight to the
Feather's pins." This section specs the perfboard option, since you're holding ELEGOO perfboard;
skip straight to §5 if you're going pin-direct instead (same solder order still applies, just
without the intermediate board).

**Cut a small strip** — roughly 6 columns × a few rows is plenty for 6 resistors and two bus
rails; you don't need a full ELEGOO sheet. It's sized to tuck into `board_clear_h` (the 7 mm of
headroom `ankle_pod_enclosure.scad` reserves above the Feather for "the USB-C plug + STEMMA QT
header + any solder"), sitting along the Feather's **analog-pin edge**. That edge isn't arbitrary
— the enclosure's `sensor_w × sensor_h` (9×4 mm) lead-exit slot is deliberately cut into the −Y
wall "near the Feather's analog-pin edge" (see the `.scad` comment on that cutout) specifically so
the FSR bundle's run from insole → divider → ADC pin is as short as possible.

```
                 3V3 rail ───┬────┬────┬────┬────┬────┬───   (bus wire, one long edge)
                              │    │    │    │    │    │
   from insole,          FSR0  FSR1  FSR2  FSR3  FSR4  FSR5   (FSR leads land here —
   via sensor exit slot        │    │    │    │    │    │      through the −Y wall cutout)
                    node ──────●────●────●────●────●────●──── → jumper up to A0..A5
                              │    │    │    │    │    │      on the Feather header
                             10k  10k  10k  10k  10k  10k     (resistor row)
                              │    │    │    │    │    │
                  GND rail ──┴────┴────┴────┴────┴────┴───   (bus wire, other long edge)
```

- **3V3 and GND rails** run the full length of the strip as two bus wires (or two rows of
  through-holes bridged with solder blobs/bus wire) — one shared 3V3 feed and one shared GND
  return for all 6 dividers, rather than 6 separate rail runs.
- **The 6 signal lines** (the divider nodes) leave the *opposite* long edge from the FSR leads,
  as short jumpers straight down onto the Feather's `A0`–`A5` header pins — this is why the strip
  sits piggybacked directly over that edge rather than off to the side.
- **Strain relief / wire-exit path:** the FSR lead bundle (6 signal + 1 shared 3V3 return, or 6+6
  if you don't bus them at the insole) enters through the `sensor_w × sensor_h` slot on the −Y
  wall, at `main_x0 + main_inner_l*0.68` along the case's length — i.e., already positioned by the
  `.scad` file to land right at this strip. **Anchor the bundle before it reaches the solder
  joints**: a dab of hot glue or a small zip-tie on the bundle just inside the exit slot, so any
  tug on the wire outside the case pulls against the anchor point, not against the joints on the
  perfboard. Leave a short service loop (20–30 mm slack) between the anchor and the perfboard so
  the strip isn't rigidly tethered to the wall.
- **Fit check:** six 22 AWG silicone leads bundled round is roughly a 4–5 mm OD bundle — workable
  through the 9×4 mm slot but not loose. Fan the wires flat (side by side) rather than binding them
  into a round bundle if it's tight; the slot already gets a deburr pass per BUILD_PLAN.md §(e),
  which helps here too.
- If you'd rather skip the perfboard entirely, solder the resistors' leads and the FSR leads
  directly onto/at the Feather's own `A0`–`A5`/`3V3`/`GND` header pins — same electrical result,
  no intermediate board, less to mount but messier to rework.

---

## 4. Solder order — and why it's in this order

1. **Tin all pads and wire ends first** — perfboard pads, resistor leads, wire tips, before you
   join anything. Pre-tinning means each joint only needs a quick reflow, not a full fresh melt —
   less total heat into the board and into the wires per joint.
2. **Resistors first.** They're symmetric, non-polarized, and heat-tolerant, and once they're in
   they physically anchor the strip so it's easier to hold steady for everything that follows.
   Doing them first also means the board isn't yet cluttered with dangling wires while you're
   still getting the resistor row square.
3. **Rails second** (3V3 and GND bus wires connecting all 6 resistor legs). With the resistors
   already anchored, the rail wire has fixed tie-points to solder to instead of floating leads —
   fewer things move while you're working.
4. **Sensor (FSR) leads last.** This is the important ordering choice, not just a convenience:
   FSR tails are the one heat- and time-sensitive joint in this build (§7 below). Doing them last
   means you never have to reheat an FSR joint to attach something else afterward — each FSR tail
   gets touched by the iron exactly once, for the shortest possible dwell time, with a clean tip.
   Doing them first (or interleaved) risks re-melting/re-touching that joint later and cooking the
   tail's conductive ink on the second pass.

**Net effect of this order:** every joint gets touched by the iron the fewest possible times, and
the most heat-fragile joints (FSR tails) get touched last and once — less rework, less risk to the
one component in this build that can't tolerate rework.

---

## 5. Wire gauge, length, and strain relief

- **22 AWG silicone stranded** (what you have) is the right call here — more than enough current
  capacity for these microamp-scale ADC lines, and the reason to use it is mechanical, not
  electrical: silicone jacket stays flexible through repeated ankle flex cycles where PVC-jacketed
  wire stiffens and eventually cracks at the joint. One gauge for both signal and rail wiring also
  keeps the BOM simple.
- **Length:** run each FSR lead from the insole's medial-exit slot (per
  [`insole_fsr_layout.scad`](../hardware/insole_fsr_layout.scad)'s `EXIT_X/EXIT_Y` convergence
  point) up to the ankle pod. As a working estimate for a lower-shin mount, budget **300–400 mm**
  per run plus a **30–50 mm service loop** at *both* ends (insole exit and pod entry) — the ankle
  flexes through its full gait range with this rig on, so a taut, straight-line run stresses the
  solder joints at both ends every step; the loops give the bundle somewhere to take up slack
  instead of pulling on a joint.
- **Heat-shrink every FSR tail joint**, no exceptions — this is the connection that sees the most
  flex-fatigue in the whole build (foot strikes, ankle motion), and a bare joint here is the most
  likely point in the rig to eventually crack from repeated flex. A short piece over the joint,
  shrunk down, turns a point flex stress into a distributed one over the shrink tube's length.
- **Bundle strain relief:** in addition to the anchor point at the enclosure's exit slot (§3),
  anchor the bundle again where it exits the insole carrier, and loosely tape/sleeve the run
  between the two anchors at intervals so it moves as one bundle rather than 6+ independent wires
  snagging separately.

---

## 6. Verify with a multimeter BEFORE powering anything

Do this with the battery **unplugged** and USB **disconnected** — resistance measurements on a
powered board will read garbage (or in the worst case, damage the meter on some ranges).

| Check | How | Expect |
|---|---|---|
| **Continuity, each conductor** | Beep/continuity mode, one probe at the insole-side FSR pad, other at the corresponding perfboard node | Beeps (near-0 Ω) — confirms the wire run itself, end to end |
| **No 3V3↔GND short** | Beep/continuity mode, probe the 3V3 rail vs the GND rail directly on the perfboard | **Should NOT beep.** Even an FSR pressed hard is ~200–400 Ω *in series with* the 10 kΩ resistor (≈10.2–10.4 kΩ total) — far above a continuity tester's ~30–50 Ω beep threshold. If it beeps, you have an actual solder bridge, not a "sensitive" FSR reading |
| **Node → GND (= just `R_fixed`)** | Resistance mode, node pad to GND rail | ~10 kΩ (±resistor tolerance), constant regardless of FSR state — this is really a sanity check that the resistor value/placement is right, not a force reading |
| **Node → 3V3 (= the FSR alone)** | Resistance mode, node pad to 3V3 rail, FSR **unloaded** | **>1 MΩ** — many multimeters will just show `OL` (open). That's correct, not a fault |
| **Node → 3V3, FSR pressed firmly** | Same, press the pad hard by hand | Drops sharply — ballpark **1–3 kΩ** at a firm press, **200–400 Ω** at something close to full body weight on that one pad |

If a channel doesn't show this pattern — no drop under pressure, or already near-zero unloaded —
recheck that channel's joints before it goes anywhere near the case; it's far easier to reflow a
joint on the bench than after the lid's snapped on.

---

## 7. Gotchas

- **Never solder directly to an FSR's exposed tail contacts at high heat.** The tail is a
  conductive-ink-on-flex-film contact, not copper — sustained heat delaminates the ink from the
  substrate and kills that channel permanently, often without any visible sign until it stops
  reading. Some FSR402 variants (including some Adafruit-sourced ones) ship with two pins already
  attached to the tail — if yours do, you don't need to touch the tail at all, just wire onto the
  pins. If yours are bare-tail: use a **low iron temp** (~260–270 °C) with a clean, well-tinned
  tip and get in and out in 2–3 seconds per joint — or skip soldering the tail altogether and use
  a crimp connector / screw terminal / pinch-style header instead. Check which variant you actually
  have before you touch iron to tail.
- **Lead-free solder needs more heat and flows worse than 63/37.** If your solder is RoHS
  lead-free (SAC305 or similar — check what shipped in the iFixit kit), expect to run the iron
  noticeably hotter (~350 °C+) and need more flux for a clean joint than 63/37 leaded solder would
  need — relevant here specifically because the FSR tail joints above want the *opposite*
  (minimum heat, minimum dwell). If you have a choice and local regulations allow it, 63/37 leaded
  solder is the easier, lower-temp, better-flowing choice for those particular joints.
- **IO20 must be driven HIGH for the STEMMA QT connector to power up** — this is a firmware step,
  not a wiring one, but it bites people at the *wiring-verification* stage: if you probe the
  STEMMA QT connector's power pin with a multimeter before flashing firmware, you will correctly
  read **0 V there** even though the board and connector are wired fine — IO20 hasn't been told to
  switch it on yet. Don't chase that as a wiring fault; it resolves the moment firmware runs
  (see [`BUILD_PLAN.md`](BUILD_PLAN.md) §(b) for the full note and source link).
