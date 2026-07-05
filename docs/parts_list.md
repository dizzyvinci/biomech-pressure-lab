# Ready-to-order parts list (smart-insole rig, ~$90–120)

Everything for **Path A (no printer)**. Amazon links = fast/one-cart; Adafruit links = the sensor-grade parts done right. Buy **one** of each row (watch the ⚠️ quantity/variant notes).

| # | Part | Qty | ~$ | Buy | Notes |
|---|---|---|---|---|---|
| 1 | **ESP32-S3-DevKitC-1** (N8R8) | 1 | 12 | [Amazon B09MHP42LY](https://www.amazon.com/Espressif-ESP32-S3-DevKitC-1-N8R8-Development-Board/dp/B09MHP42LY) | Official Espressif. Any N8R8/N16R8 is fine. |
| 2 | **FSR** force sensors | **8** | ~6 ea | [Adafruit #166](https://www.adafruit.com/product/166) · [Amazon FSR402 multipack](https://www.amazon.com/s?k=Interlink+FSR402+force+sensitive+resistor) | ⚠️ Need **8**. Adafruit sells singly; Amazon has multipacks (cheaper/faster). |
| 3 | **CD74HC4067** 16-ch analog mux | 1 | 2 | [Amazon B07Z45MYP3](https://www.amazon.com/CD74HC4067-16-Channel-Multiplexer-Breakout-Microcontroller/dp/B07Z45MYP3) · [10-pack](https://www.amazon.com/GalaxyElec-CD74HC4067-16-Channel-Multiplexer-Breakout/dp/B082HSP8CL) · [SparkFun](https://www.sparkfun.com/sparkfun-analog-digital-mux-breakout-cd74hc4067.html) | 8 FSRs → 1 ADC pin. |
| 4 | **BNO085** 9-DOF IMU | 1 | 20 | [Adafruit #4754](https://www.adafruit.com/product/4754) · [DigiKey](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4754/13426653) | Fused orientation (pronation, strike timing). I2C. |
| 5 | **microSD SPI module** + card | 1 | 8 | [Amazon microSD module](https://www.amazon.com/s?k=micro+sd+card+module+SPI+arduino) · card [Amazon](https://www.amazon.com/s?k=sandisk+microsd+32gb) | Onboard full-rate logging. Any 8–32 GB card. |
| 6 | **10 kΩ resistors** (1/4 W) | 8 | ~7 | [Amazon resistor kit](https://www.amazon.com/s?k=10k+ohm+resistor+1%2F4w+assortment) | FSR voltage dividers. A kit covers spares. |
| 7 | **LiPo 500 mAh** (JST-PH) | 1 | 8 | [Adafruit #1578](https://www.adafruit.com/product/1578) · [Amazon](https://www.amazon.com/s?k=500mah+lipo+battery+jst+ph) | Wearable power. |
| 8 | **TP4056** USB-C charge/protect board | 1 | ~6 (5pc) | [Amazon TP4056](https://www.amazon.com/s?k=TP4056+usb+c+charging+module+protection) | Get the version **with protection** (DW01). |
| 9 | **Jumper wires + perfboard/proto** | 1 | 10 | [Amazon jumper kit](https://www.amazon.com/s?k=dupont+jumper+wires+kit) · [perfboard](https://www.amazon.com/s?k=perfboard+prototype+pcb) | For the mount + protoboard. |
| 10 | **EVA foam sheet / cheap insoles** | 1 | 8 | [Amazon EVA foam 3-4mm](https://www.amazon.com/s?k=eva+foam+sheet+3mm+adhesive) · [cheap insoles](https://www.amazon.com/s?k=cheap+foam+shoe+insoles) | Mount the FSRs on this (no printer needed). |

**Rough total: ~$90–120** depending on FSR pack size and what you have on hand.

## Skip-if-you-have
Soldering iron, USB-C cable (ESP32 flashing), double-sided tape.

## After it arrives
1. Wire per the [README](../README.md) pin map (FSR dividers → mux → GPIO1; IMU → I2C; SD → SPI).
2. Mount the 8 FSRs on the EVA/insole at the zone positions.
3. Flash [`firmware/smart_insole/smart_insole.ino`](../firmware/smart_insole/smart_insole.ino).
4. Record → `python analysis/analyze_pressure.py "logs/*.csv" --out results/`.

*(Amazon search-links are used where a specific ASIN isn't critical — pick the top-rated in-stock option. Direct ASINs are given where the exact part matters.)*
