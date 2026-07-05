# refs — cited plantar-load reference database

[`plantar_norms.json`](plantar_norms.json) is the **norms** the analysis compares an
athlete against: per foot **zone** (down to the 2nd metatarsal), per **sport/movement**,
the expected **load distribution** and **peak force** — from published sports-medicine
research where possible.

## Why a database (not just estimates)
A rubric is only as good as its reference. "Your met2 is at 21% of load" means nothing
until you know the field's norm is 16% — *then* it's a 1.3× overload and an injury flag.
So we keep the norms in one cited, versioned file that gets **more rigid as sources are
added**. `analysis/zone_load.py` reads it.

## Honesty: every value carries a confidence flag
- **`published`** — the value/range is stated in the cited paper (e.g. gymnastics
  landing **7.1–15.8× BW**).
- **`published_order`** — the *ranking* of zones is from a paper (e.g. running: central
  met heads > 1st met > heel > hallux > lateral); magnitudes are filled to match.
- **`estimated`** — biomechanically reasonable, **no direct source yet** (a TODO to
  replace with data).

"Estimation fine, exact better": the peak-force ranges are mostly `published`; several
per-zone magnitude splits are `published_order` or `estimated` and clearly marked.
**Contributions = add a paper + tighten a distribution + flip a flag to `published`.**

## What's in it (v0.1)
Profiles: `running_rearfoot`, `running_forefoot`, `gymnastics_landing`,
`figure_skating_landing`, `ballet_releve`, `ballet_pointe`. Each has `dist_pct` (10
zones), `peak_force_BW`, `watch_zones`, an `injury` note, and source refs.

Key sourced facts:
| | Finding | Source |
|---|---|---|
| Gymnastics | landing **7.1–15.8× BW** | [Front. Sports Act. Living 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12179790/) |
| Figure skating | single-leg landing **~5× BW** (to ~8×) | [ACSM](https://acsm.org/the-science-of-figure-skating-jumps/) |
| Running | central met heads bear most; forefoot **281–313 kPa** | [PMC5112690](https://pmc.ncbi.nlm.nih.gov/articles/PMC5112690/) |
| Ballet | 1st-MTP pain → **less hallux, more met-head** load | [Children 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9406650/) |
| Injury | **2nd met** = #1 stress-fracture site ("dancer's fracture") | [Physiopedia](https://www.physio-pedia.com/Metatarsal_Stress_Fractures_in_the_Athletic_Population) |

## Roadmap (more rigid)
- Replace `estimated` distributions with per-zone baropodometry from papers/our own captures.
- Add profiles: sprinting, jump-landing (volleyball/basketball, ACL), soccer cut, martial-arts kick, walking-gait clinical norms.
- **Video → force** estimation as a connector: 2D-pose → GRF is now feasible
  ([pose-estimation GRF, PMC11057390](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11057390/));
  it *estimates* the peak force, then this DB gives the *published* range to check it against.
- Our own captures (calibrated insole) feed back in — the DB tightens as we scale.

Not medical advice — a training/screening reference. Values summarize published research;
verify against primary sources for clinical use.
