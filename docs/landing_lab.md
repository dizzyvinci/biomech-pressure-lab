# Landing lab — discipline-aware landing scores

The same landing is a different question in each sport. [`analysis/landing_lab.py`](../analysis/landing_lab.py)
detects the impact from the insole, then scores it against the **right rubric** —
because "good" means *stop* in gymnastics, *glide* in skating, and *soft* in dance.

![landing lab — three rubrics](landing_lab.svg)

> **They all land forefoot-first** — then diverge: gymnastics plants the heel and
> *freezes*; dance *rolls* toe→ball→heel softly; skating stays on the ball and *glides*
> out on an edge.

| Discipline | Land on | "Good" = | Scored on | Demo |
|---|---|---|---|---|
| **Gymnastics** (`--discipline gymnastics`) | forefoot → heel, both feet | **stick** — stop dead | settle time · wobbles · step | **9.8 STUCK** |
| **Figure skating** (`figure_skating`) | one foot, ball, **outside edge** | clean **edge check-out** | 1-foot · edge (ML) control · forward flow · absorption | **9.7 clean edge** |
| **Dance / ballet** (`dance`) | toe → ball → heel roll | **soft & quiet** | impact softness · roll (heel-lag) · plié · control | **9.9 soft roll** |

## What it measures (shared primitives)
From the impact onward: **loading rate** (soft plié vs slam), **forefoot/heel roll**
(does the heel engage *after* the forefoot?), **edge** (medial/lateral pressure →
inside/outside edge + chatter), **forward flow** (COP progressing into a glide),
**settle/wobbles/step**. Each rubric weights these differently.

```bash
python landing_lab.py --demo                                   # one clean rep per discipline
python landing_lab.py "session.csv" --discipline figure_skating --calibration cal.json
```
Worked report: [sample/results/report_landing_lab.md](../sample/results/report_landing_lab.md).

## More demographics, same engine
This is the pattern for going beyond foot pain: the **COP + load** engine is
sport-agnostic; each population just needs its own rubric.
- **Volleyball / basketball** — jump-landing knee-safety (loading rate, symmetry) for ACL risk.
- **Running** — footstrike (heel vs mid vs fore), loading rate, pronation over a run.
- **Martial arts / boxing** — stance stability, weight shift, kick base.
- **Older adults** — the [clinical + mCTSIB](balance_positions.md) side.
Add a scorer, reuse the primitives.

Not a medical device — a training / performance aid. Work with your coach; sync each rep
to your existing video by timestamp — the sensor adds the pressure layer the camera can't see.
