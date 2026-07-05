# Quickstart — two ways to build

You do **not** need a 3D printer to build the measurement lab. Printing only matters for the *final* tuned insole (and even that can be outsourced). Pick your path.

## Path A — No 3D printer (start here, ~$100, zero printing)
Build the whole **measurement** rig and find your hot spot with nothing printed.

1. **Sensor mount** — peel-and-stick the 8 FSRs onto a **cheap store-bought insole or 3–4 mm EVA foam** at the zone positions (see the foot-zone map in the [README](../README.md)). Tape a thin cover layer over them so they sit flat under your foot.
2. **Wiring** — route the ribbon up to the instep; strain-relieve with tape.
3. **Electronics** — ESP32 + CD74HC4067 mux + BNO085 + microSD on a small perfboard, tucked in **any small box** (project box, Altoids tin, a pouch on the laces).
4. **Flash** `firmware/smart_insole/smart_insole.ino`, record labeled clips (stand / walk / stairs / pivot).
5. **Analyze** — `python analysis/analyze_pressure.py "logs/*.csv" --out results/` → your hot zone + `hotspot.json`.
6. **Final insole** — send the STL to a **TPU print service** (⚠️ confirm they do *flexible/foaming* TPU, not just rigid) or a local maker. Or come back to Path B later.

**You can complete steps 1–5 today with zero printing** and decide on the printer afterward.

## Path B — With a 3D printer (Bambu H2D)
Everything in Path A, plus the printed payoff:

1. Print the **sensor-carrier insole** (thin TPU with FSR pockets) and the **ESP32 enclosure** (PLA/PETG) — see [insole_print_spec.md](insole_print_spec.md) §6–7. Nicer than the improvised mount, not required.
2. Print the **final custom insole** in TPU: soft cushion + firm shell + **relief window** at your hot spot (§1–5).
3. **Iterate** — after re-measuring with the insole in, reprint with a tweaked window/density.

## Which do I actually need?
| Goal | Printer? |
|---|---|
| Measure pressure/motion, find the hot spot | ❌ No |
| Fabricate the tuned insole | ✅ FDM TPU — own printer **or** a print service |
| Sensor-carrier insole + enclosure | ➖ Optional (improvise otherwise) |

See **"Which 3D-printing process makes a TPU insole?"** in [insole_print_spec.md](insole_print_spec.md) for FDM vs SLS vs resin.
