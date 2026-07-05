# Quickstart

Two paths. **Path 1 (printer-first) is the recommended start** — it makes a real custom insole with zero electronics. Path 2 is an optional precision upgrade.

## 🖨️ Path 1 — Printer-first (recommended)
Make a custom insole with a relief window, placed **by feel**. No sensors, no wiring, no code.

1. **Scan** your existing orthotic → STL (iPhone: Scaniverse/Polycam, photo mode). [insole_print_spec.md](insole_print_spec.md) §1.
2. **Mark the sore spot** on the model — dead-center / inner / back heel (you already know where it hurts).
3. **Design** the insole: soft-lattice heel cushion + firm shell + a **relief pocket** at that spot. §2–5.
4. **Print** in TPU on the H2D (soft cushion + firm shell in one part). §5 settings.
5. **Wear → adjust → reprint.** Too firm/soft somewhere? Nudge the window size or lattice density and reprint. Iterate by feel.

**Shopping (Path 1):** printer + filament only — Bambu **H2D** + **TPU High-Flow Kit** + **soft/foaming TPU** (cushion) + **firm TPU 95A** (shell). See [parts_list.md](parts_list.md) → *"WITH a printer."*

**No printer of your own?** Send the STL to a **TPU print service** (⚠️ confirm they do *flexible* TPU) instead of buying the H2D. Everything else in Path 1 is unchanged.

---

## 🔬 Path 2 — Optional sensor rig (advanced, later)
Add this **only if** you want to *measure* your pressure objectively instead of placing the relief window by feel — and to prove the new insole actually dropped the load.

1. **Build the smart insole** — ESP32 + 8× FSR + IMU (BOM/wiring in the [README](../README.md) Path 2 section). Mount the FSRs on cheap EVA foam; no printer needed for the rig itself.
2. **Flash** `firmware/smart_insole/smart_insole.ino`, **record** labeled clips (stand / walk / stairs / pivot).
3. **Analyze** — `python analysis/analyze_pressure.py "logs/*.csv" --out results/` → prints your **hot spot** + `hotspot.json`.
4. **(Optional) OpenCap** for joint-level gait across movements — [opencap_setup.md](opencap_setup.md).
5. Feed the measured hot-spot location back into **Path 1 step 2**, print, then **re-record** to confirm the load dropped. Iterate on data.

**Shopping (Path 2 extras):** the electronics rig — see [parts_list.md](parts_list.md) → *"Core rig."*

---

### Which should I do?
- **Just want relief fast / hate wiring** → **Path 1.** You know where it hurts; place the window there.
- **Want objective data + before/after proof** → do Path 1, then add **Path 2** later.
