# Ready-to-order parts — WITHOUT printer vs WITH printer (kept separate)

Both paths share the same **electronics rig** (you need the sensors either way). What differs is how you make the mounts and the **final insole**. Buy the **Core rig**, then add **only** your path's extras.

---

## 🔩 Core rig — buy for EITHER path (~$90–110)
| # | Part | Qty | ~$ | Buy | Notes |
|---|---|---|---|---|---|
| 1 | **ESP32-S3-DevKitC-1** (N8R8) | 1 | 12 | [Amazon B09MHP42LY](https://www.amazon.com/Espressif-ESP32-S3-DevKitC-1-N8R8-Development-Board/dp/B09MHP42LY) | The brain. |
| 2 | **FSR** force sensors | **8** | ~6 ea | [Adafruit #166](https://www.adafruit.com/product/166) · [Amazon multipack](https://www.amazon.com/s?k=Interlink+FSR402+force+sensitive+resistor) | ⚠️ need **8**. |
| 3 | **CD74HC4067** 16-ch mux | 1 | 2 | [Amazon B07Z45MYP3](https://www.amazon.com/CD74HC4067-16-Channel-Multiplexer-Breakout-Microcontroller/dp/B07Z45MYP3) | 8 FSRs → 1 ADC pin. |
| 4 | **BNO085** 9-DOF IMU | 1 | 20 | [Adafruit #4754](https://www.adafruit.com/product/4754) | Pronation + strike timing. |
| 5 | **microSD SPI module** + card | 1 | 8 | [Amazon module](https://www.amazon.com/s?k=micro+sd+card+module+SPI+arduino) · [card](https://www.amazon.com/s?k=sandisk+microsd+32gb) | Onboard logging. |
| 6 | **10 kΩ resistors** | 8 | ~7 | [Amazon kit](https://www.amazon.com/s?k=10k+ohm+resistor+1%2F4w+assortment) | FSR dividers. |
| 7 | **LiPo 500 mAh** (JST-PH) | 1 | 8 | [Adafruit #1578](https://www.adafruit.com/product/1578) | Wearable power. |
| 8 | **TP4056** USB-C charger | 1 | ~6 | [Amazon](https://www.amazon.com/s?k=TP4056+usb+c+charging+module+protection) | Get the **protected** (DW01) version. |
| 9 | **Jumper wires + perfboard** | 1 | 10 | [Amazon](https://www.amazon.com/s?k=dupont+jumper+wires+kit) | Wiring + protoboard. |

**Core subtotal: ~$90–110.**

---

## 🅰️ WITHOUT a printer — add these (improvise + print service)
| Part | ~$ | Buy | Notes |
|---|---|---|---|
| **EVA foam 3–4 mm** or cheap insoles | 8 | [Amazon EVA](https://www.amazon.com/s?k=eva+foam+sheet+3mm+adhesive) · [insoles](https://www.amazon.com/s?k=cheap+foam+shoe+insoles) | Mount the 8 FSRs on this. |
| **Double-sided tape + small project box** | 8 | [tape](https://www.amazon.com/s?k=double+sided+mounting+tape) · [box](https://www.amazon.com/s?k=small+project+enclosure+box) | Sensor cover + electronics enclosure. |
| **Final insole** | per-print | — | Send your STL to a **TPU print service** (⚠️ confirm *flexible* TPU) or a local maker. |

**Path A total: ~$105–125** + a per-insole print-service fee. **No big purchase.**

---

## 🅱️ WITH a printer (Bambu H2D) — add these
*(Skip the EVA/tape/box — you print the sensor-carrier + enclosure instead.)*
| Part | ~$ | Buy | Notes |
|---|---|---|---|
| **Bambu Lab H2D** | 1,699 | [Bambu store](https://us.store.bambulab.com/products/h2d) | Dual nozzle → soft + firm in one print. Sale ends Jul 15. |
| **H2D TPU High-Flow Kit** | 34 | [Bambu store](https://us.store.bambulab.com/products/h2d-tpu-high-flow-kit) | Footwear-tuned TPU hotends. |
| **Firm TPU — Bambu TPU 95A HF** | ~30 | [Bambu store](https://us.store.bambulab.com/products/tpu-95a-hf) | Support shell. |
| **Soft cushion TPU — Bambu TPU 85A** | ~34 | [Bambu store](https://us.store.bambulab.com/products/tpu-85a-tpu-90a) | The squishy heel layer (won't bottom out). Alt: [ColorFabb VarioShore](https://www.amazon.com/s?k=colorfabb+varioshore+tpu) (foaming, Amazon). |
| **PLA Basic / PETG** | ~25 | [PLA](https://us.store.bambulab.com/products/pla-basic-filament) · [PETG](https://us.store.bambulab.com/collections/petg) | Enclosure + Cheeq molds. |

**Path B total: Core (~$100) + ~$1,830 printer & materials.**

---

## Which path?
- **Just measuring, or a one-off insole** → **Path A** (cheapest start; outsource the print).
- **Want to iterate the insole + reuse the printer** (Cheeq molds, enclosures, everything else) → **Path B**.

You can always **start with Path A** to find your hot spot, then move to Path B only if you decide to fabricate/iterate yourself.

---

## 🧴 CHEEQ project (tagged — SEPARATE, not the foot lab)
> A different project ([dizzyvinci/cheeq](https://github.com/dizzyvinci/cheeq)) — a silicone cheek model. Here only so its parts aren't mixed with the insole shopping. **Not needed for the foot build.**

| Part | Buy | Note |
|---|---|---|
| **Dragon Skin FX-Pro** (skin) | [smooth-on](https://www.smooth-on.com/products/dragon-skin-fx-pro/) | Thin skin layer |
| **Slacker** (deadener) | [smooth-on](https://www.smooth-on.com/products/slacker/) | Softens the gel "fat" |
| **Ecoflex GEL** (soft cushion) | [smooth-on](https://www.smooth-on.com/products/ecoflex-gel/) | Deep gel layer |
| **Body Double** (mold silicone) | [smooth-on](https://www.smooth-on.com/products/body-double-standard/) | Life-cast a real cheek |
| **Silc Pig** pigments | [smooth-on](https://www.smooth-on.com/products/silc-pig/) | Flesh tones |
| Supplies (Ease Release, scale, cups, gloves) | smooth-on / Amazon | Casting basics |
| **PLA/PETG** (optional) | Bambu | Firm backing / printed mold |

Full explanations in [what-each-part-is-for.md](what-each-part-is-for.md) → **CHEEQ** section. **Vendor: Smooth-On (separate order).**
