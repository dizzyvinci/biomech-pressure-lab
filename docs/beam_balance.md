# Beam / athlete balance (specialized)

Clinical balance asks *"are you safe?"*. Elite balance asks *"how clean was that?"*.
On a **10 cm beam**, **mediolateral (side-to-side) sway is what makes you fall off**,
and the signature score is the **landing "stick"** — judges deduct for wobbles and
steps. [`analysis/beam_balance.py`](../analysis/beam_balance.py) scores exactly that,
from the same insole COP + IMU.

![beam / athlete balance](beam_balance.svg)

## What it scores
| | From | Metric |
|---|---|---|
| **Static hold** (scale / relevé / arabesque) | COP | **ML sway** (mm) + grade, area, velocity, hold time |
| **Landing stick** | force + COP | detect impact → **settle time**, post-landing sway, **wobble count**, **step** detection → a **0–10 stick score** |
| **Relevé load** | FSR | forefoot vs heel share (beam lives on the ball of the foot) |
| **Vision independence** | eyes-open/closed | **athlete Romberg** — here a *low* eyes-closed sway is elite (they spot; inverse of the clinical read) |

## The stick score
Detect the landing impact (steepest force onset), then over the next ~3 s:
- **settle time** = time until COP speed stays < 25 mm/s,
- **wobbles** = COP-speed corrections,
- **step** = a big ML shift or a re-unweight (hop),
- deductions in judge points (wobble ~0.1, step ~0.5) → `stick = 10 − deductions`.

**Worked demo** ([report](../sample/results/report_beam_balance.md)):
```bash
python beam_balance.py --demo --out sample/results
```
> `landing_clean` → **stick 10.0/10 (STUCK)** — settles at once, 0 wobbles.
> `landing_wobble` → **9.2/10** — 0.94 s settle, 2 wobbles, a step.
> `releve_hold` → **ML sway 0.42 mm (elite)**, 92 % forefoot (on the ball).

Label each element in the log (`releve_hold`, `landing_1`, `landing_2`, …); the module
picks the right analysis per label.

## Why this fits the strategy
This is the **niche**: we own the **foot-pressure + center-of-pressure** layer a
coach's camera can't see — objective ML control and stick quality, per rep. **Sync each
landing to your existing video review by timestamp** (and to any wearable you already
train with) so the sensor *adds* to the tools you have rather than replacing them.

Not a medical device — a training/performance aid; work with your coach.
