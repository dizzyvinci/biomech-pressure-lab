# What each part is for (pre-purchase guide)

Plain-English purpose of every part, so you know what you're buying **before** you check out. Nothing here is jargon-for-its-own-sake — if a part's job isn't obvious, it's explained.

## 🧠 Core electronics — the measuring rig (buy for either path)
| Part | What it does / why you need it |
|---|---|
| **ESP32-S3 DevKitC-1** | The **brain**. Reads all the sensors, timestamps everything, saves to the SD card, and streams over Bluetooth. Everything else plugs into this. |
| **FSR402 ×8** (force sensors) | The **pressure sensors** under your foot. Each measures force at one spot; the 8 together map *where* your foot loads (heel, ball, toes). |
| **CD74HC4067 mux** | A **switchboard**. Lets all 8 sensors share a single input pin on the ESP32 instead of needing 8 separate pins. |
| **BNO085 IMU** | The **motion sensor**. Tracks foot tilt/orientation and step timing (pronation, heel-strike) — synced with the pressure so you see load *and* movement. |
| **microSD module + card** | **Storage.** Writes the pressure + motion data as CSV files ~100×/second. |
| **10 kΩ resistors ×8** | One per FSR — forms the tiny circuit ("voltage divider") that turns *force* into a *voltage* the ESP32 can read. |
| **LiPo 500 mAh battery** | **Portable power** so the rig runs on your foot, no wall plug. |
| **TP4056 charger** | A little USB-C board to **safely recharge** the LiPo. |
| **Jumper wires + perfboard** | The **connections** + a small board to mount the electronics on. |

## 👟 Mounting — no-printer path
| Part | What it does |
|---|---|
| **EVA foam / cheap insoles** | The **sensor bed** — you stick the 8 FSRs to this and slide it into your shoe. |
| **Double-sided tape + small box** | Hold the sensors flat + **house the electronics** on your ankle. |

## 🖨️ 3D-printer path — optional, for the *final custom insole*
| Part | What it does |
|---|---|
| **Bambu Lab H2D** | The **3D printer**. Prints the final insole (soft cushion + firm shell in one part) plus the sensor-carrier and enclosure. |
| **H2D TPU High-Flow Kit** | Special **nozzles for flexible (TPU) filament** — needed to print soft insoles quickly. |
| **Firm TPU 95A** | Prints the **supportive shell** of the insole. |
| **Soft / foaming TPU** (VarioShore) | Prints the **squishy heel-cushion zone** that won't bottom out — the whole point. |
| **PLA / PETG** | Rigid filament for the **electronics enclosure** (and, separately, Cheeq molds). |

---

## ⚠️ Also in your carts — NOT part of this project
Flagging these so you don't think they're required for the insole build — **prune at checkout if you only want the lab:**

- **eBay — Black Panther Heelys (Men's 11):** a personal buy, unrelated to the lab. *(Not this project.)*
- **Adafruit — items from a previous visit** already in your cart: **NeoPixel Stick**, **CYBERDECK HAT for Raspberry Pi 400/500**, **STEMMA QT / Qwiic cables**, and other leftovers. None are needed for the smart insole. *(Not this project.)*
- **Amazon — any pre-existing item(s)** in the cart from before. *(Not this project.)*

**Rule of thumb:** if it's in the tables *above*, it's part of the insole build. If it's in *this* section, it's something else riding along in your cart.

---

## 🧴 CHEEQ — your separate venture (tagged, NOT the foot lab)
> **Cheeq is your own startup**, with its own repo **[dizzyvinci/cheeq](https://github.com/dizzyvinci/cheeq)** (research, product spec, brand, business plan, patent, pitch deck). It has **nothing to do with the insole build** — it's noted here only so its silicone parts don't get mixed into the foot shopping.

**⭐ The real, authoritative BOM lives in the Cheeq repo — buy from there, not this file:**
[`02_product/build-protocol-V1.md`](https://github.com/dizzyvinci/cheeq/blob/main/02_product/build-protocol-V1.md) (full tools + silicone kit, ratios, casting order).

Gist (see that file for specs/quantities):
- **Tools (one-time, ~$300+ — the real cost driver):** vacuum chamber + pump (degassing), 0.1 g gram scale, mixing cups/brushes/mold-release, IR thermometer.
- **Silicones (~$20/puck):** Dragon Skin FX-Pro (skin) · Ecoflex Gel + Slacker (deadened "fat") · **Ecoflex 00-50 / Dragon Skin 10 (firm backing — silicone, *not* PLA)** · Body Double/alginate (lifecast pores) · Silc-Pig pigment · Shin-Etsu KMP-600 (matte powder).
- **Vendors:** Smooth-On / Reynolds Advanced Materials (+ Shin-Etsu, Technogel).

**Correction to an earlier note of mine:** the H2D is **not** needed for Cheeq — the backing is silicone, and the mold is a lifecast, not a 3D print. **Tag: CHEEQ · source of truth = the cheeq repo.**
