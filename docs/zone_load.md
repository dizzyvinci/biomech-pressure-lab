# Zone load vs the field — down to the 2nd metatarsal

Rubrics get *specific*. Not just "your landing was clean," but **which foot regions
you over-use or under-use versus what the research says is normal for that movement** —
and the injury that overload predicts. [`analysis/zone_load.py`](../analysis/zone_load.py)
compares your per-zone distribution against the cited [`refs/plantar_norms.json`](../refs/README.md).

![zone load vs the field](zone_load.svg)

## How it works
1. The 8-FSR rig gives per-zone load; **met2 & met4 are interpolated** from neighbors
   (so we can still flag the injury-critical 2nd metatarsal).
2. Your distribution is compared to the **field's norm** for the chosen movement →
   a ratio per zone. **≥1.3× = over-used, ≤0.7× = under-used.**
3. Overload at a `watch_zone` raises the specific **injury** flag (e.g. central-met →
   stress fracture).
4. If you pass `--calibration` + `--bodyweight-kg`, it also puts your **peak force in
   body-weights** next to the published elite range.

```bash
python zone_load.py --demo --profile ballet_releve
python zone_load.py session.csv --profile running_forefoot --calibration cal.json --bodyweight-kg 62
```

## Worked demo ([report](../sample/results/report_zone_load.md))
A dancer whose load has shifted **off the hallux onto the met heads** (the published
1st-MTP-pain pattern):
> **Over-used:** met3 **1.8×**, met4 **2.2×**, met2 **1.3×** (interp). **Under-used:**
> hallux **0.2×**, toes **0.5×**. → *"central-met (2nd-met) overload is the 'dancer's
> fracture' route — cue big-toe engagement, check the 1st ray."*

Run the **same athlete** against `running_forefoot` and the flags change — because the
norm changes. That's the point: **over/under-use is relative to the field.**

## Grounded in research, honestly flagged
The norms come from sports-medicine literature (gymnastics **7.1–15.8× BW**, skating
**~5–8× BW**, running central-met dominance, ballet hallux↔met-head shift, 2nd-met as
the #1 stress-fracture site). **Every value is flagged** `published` / `published_order`
/ `estimated` — see [refs/README](../refs/README.md). "Estimation is fine; exact is
better," and the DB tightens as sources + our own captures are added.

**More demographics, same engine:** add a `profile` (sprinting, volleyball/basketball
jump-landing for ACL, soccer cut, martial-arts kick, clinical walking) and the whole
over/under-use + injury read comes for free. **Video → force** estimation (2D-pose →
GRF, [PMC11057390](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11057390/)) is a natural
connector: it *estimates* the force; this DB gives the *published* range to check it.

Not a medical device — a training/screening aid; verify against primary sources for clinical use.
