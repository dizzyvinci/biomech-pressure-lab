# Prior art — open DIY smart-insole projects

Yes, plenty of people build their own — the space is well-trodden but **fragmented** (lots of individual repos, Hackster builds, and open-access papers; no single dominant polished project like OpenCap is for motion). Good news: we can borrow freely from these. This repo's angle = tie the insole to **OpenCap motion + a 3D-printed relief-window insole + a measure→print→re-measure loop**, which the references below mostly don't.

## Open repos / builds worth mining
| Source | What it gives us |
|---|---|
| [fuzzylabs/wearable-my-foot](https://github.com/fuzzylabs/wearable-my-foot) | Arduino-based pressure insole for gait/posture; wiring + data pipeline ideas |
| [ahmed-elsarta/insole-pressure-monitor-using-arduino](https://github.com/ahmed-elsarta/insole-pressure-monitor-using-arduino) | Simple FSR insole for gait; good starter reference |
| [Hackster: DIY Smart Insole (Juliette)](https://www.hackster.io/Juliette/a-diy-smart-insole-to-check-your-pressure-distribution-a5ceae) | Full build write-up + Thinger.io visualization |
| [HardwareX: low-cost force insoles](https://www.hardware-x.com/article/S2468-0672(24)00083-X/fulltext) | Open-hardware, peer-reviewed; ground-reaction-force estimation; validated method |
| [MDPI: low-cost smart insole + CNN](https://www.mdpi.com/2227-7080/14/6/362) | Piezoresistive sensor layout + ML classification approach |

## On "buy an open one"
- **Moticon OpenGo / ReGo** — the name says "Open," but the *hardware is proprietary*; "open" refers to **open data access** (plain-text export, real-time UDP, SDK), not open-source. Research/clinic grade, **quote-based pricing in the thousands** — available, just not a consumer checkout. If you ever want turnkey raw data and budget isn't a constraint, it's the buy option; otherwise this repo is the ~$100 path to the same *data ownership*.
- **Nurvv / Arion** — affordable (~$300–500) but **closed data** (their app only), so they can't feed a custom-insole workflow.
