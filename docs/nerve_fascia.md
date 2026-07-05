# From foot pressure → nerve & fascia impact

The insole gives a pressure map. This layer asks the next question: **given the load your foot
takes *all day*, which nerves and fascia are being overloaded — and how would you tell them
apart?** It's the bridge from a number on a sensor to a structure that can hurt.

Module: [`analysis/nerve_fascia.py`](../analysis/nerve_fascia.py) (`--demo`). Structures + citations
live in [`refs/plantar_norms.json`](../refs/plantar_norms.json) under `structures`.
**Screening / education, not a diagnosis** — these structures overlap and mimic each other.

![Nerve & fascia map](nerve_fascia.svg)

## The metric that connects pressure to tissue: CPTS

Peak pressure is *one step*. The pressure-time integral (PTI) is *one step's dose*. **Cumulative
Plantar Tissue Stress** is a whole **day's** dose — and the day's dose is what overloads tissue:

> **CPTS = PTI × loading-cycles-per-day**  (MPa·s/day)

It predicts diabetic-ulcer healing better than pressure or activity alone (healed vs non-healed:
**140 vs 275 MPa·s/day**), and higher CPTS tracks joint pain too. → [CPTS & ulcer healing](https://pubmed.ncbi.nlm.nih.gov/29477099/),
[CPTS & first-MTP pain](https://pmc.ncbi.nlm.nih.gov/articles/PMC5473430/).

The key move for **our** rig: **forefoot cycles/day = gait steps + the at-rest leg-bounce/toe-tap
dose** that [`bounce.py`](../analysis/bounce.py) counts. In the demo that at-rest dose is **~85% of
the forefoot's daily loading cycles** — a habit no step-counter sees, landing on the exact met
heads gait already loads. That's why the forefoot nerve/fascia load dominates the day.

*(Anchor caveat: 140–275 MPa·s/day is a **diabetic-ulcer** figure — an order-of-magnitude
reference for at-risk tissue, not a healthy-foot limit. Use CPTS to compare your zones and track
your own trend, not as a cutoff.)*

## Bonus signal: the pressure gradient

A steep spatial **gradient** (a sharp pressure jump right next to a hot zone) concentrates
*subsurface shear* near nerves and soft tissue — and it discriminates breakdown risk better than
peak pressure alone, especially in the forefoot where shear sits closest to the surface. →
[Pressure gradient & subsurface shear](https://pmc.ncbi.nlm.nih.gov/articles/PMC2387244/). The
module flags forefoot gradient hotspots.

## The structures it maps

| Structure | Kind | Loaded by | Mode | Tell it apart | Source |
|---|---|---|---|---|---|
| **Plantar fascia** | fascia | heel_med + forefoot/hallux (windlass) | **tension** + insertional | first-step **morning** pain, medial calcaneus | [windlass](https://pmc.ncbi.nlm.nih.gov/articles/PMC385265/) · [equinus](https://www.michiganfootdoctors.com/gastrocnemius-recession-equinus-contracture-plantar-fasciitis/) |
| **Baxter's nerve** | nerve | heel_med (medial) | compression / entrapment | worse **through the day**, Tinel → lateral heel | [Baxter](https://radsource.us/baxters-nerve/) |
| **Morton's / interdigital** | nerve | met2·met3·met4 | compression + toe-extension tether | **burning/numb toes**, Mulder's click | [Morton](https://www.ncbi.nlm.nih.gov/books/NBK470249/) |
| **Posterior tibial (tarsal tunnel)** | nerve | heel_med·midfoot·met1 | tension w/ overpronation | medial-**ankle** Tinel, radiating sole | [tarsal tunnel](https://www.ncbi.nlm.nih.gov/books/NBK513273/) |

## Condition-aware reads the module makes

- **The forefoot dose dominates, and the bounce habit is most of it** → interdigital-nerve
  (Morton) + met-head load is the biggest cumulative exposure. Manage the *dose*, don't just
  suppress the movement: metatarsal pad **proximal** to the heads, wider toe box, ball-of-foot
  rest windows.
- **Medial heel pain — let the clock diagnose:** plantar fasciitis is worst on the **first steps
  in the morning**; Baxter's nerve gets worse **as the day's weight-bearing accumulates**. Same
  spot, opposite time-signature, different fix. (Baxter's is up to ~20% of chronic heel pain and
  routinely missed.) Log *when* it hurts.
- **Tight calf / equinus is an amplifier:** it forces early forefoot loading (↑ met-head pressure)
  **and** tensions the fascia via the windlass — equinus carries **~23× the plantar-fasciitis
  risk**. So a forefoot-overload signature and heel-fascia pain travel together.

## Run it — on real captured logs

The honest version runs off your actual day, not a demo. [`analysis/day_summary.py`](../analysis/day_summary.py)
turns raw session CSVs (from [`firmware/all_day_logger`](../firmware/all_day_logger/all_day_logger.ino) —
short-press cycles the `phase` tag walk/stand/**bounce**) into the per-zone **peak, PTI-per-cycle,
and cycles/day**, splitting gait from at-rest bounce. Then `nerve_fascia.py` computes the dose:

```bash
# one command: raw logs -> day summary -> nerve/fascia impact
python analysis/nerve_fascia.py --logs "logs/*.csv" --calibration cal.json \
    --walk-hours 10 --bounce-hours 4 --out results/

# or in two explicit steps
python analysis/day_summary.py "logs/*.csv" --calibration cal.json --walk-hours 10 --bounce-hours 4 --out results/
python analysis/nerve_fascia.py --day results/day.json --out results/

python analysis/nerve_fascia.py --demo    # no hardware — the worked example
```

It runs on the committed sample end-to-end (see [sample/README](../sample/README.md) steps 5b–5c →
[report_nerve_fascia.md](../sample/results/report_nerve_fascia.md)). The **measured** per-zone PTI
already encodes any under-loading (a toe-walker's light heel reads low), so CPTS is
`gait PTI/cycle × gait cycles + bounce PTI/cycle × bounce cycles` — no fudge factor. Emits a ranked
structure report + JSON. `--day` also accepts a hand-written summary (`pressure_kPa` + `pti_kPa_s` +
`gait_steps_per_day` + `bounce_cycles_per_day`).

## It feeds the insole

`interpret.py` writes a `structure_target` into the insole spec, and
[`build_insole.py`](../hardware/build_insole.py) **acts on it**:
- **Morton's** target → a **metatarsal pad** proximal to the met heads (splays met2-4, offloads
  the interdigital nerve), plus a forefoot relief.
- **plantar fascia / tibial** target → auto-enabled **arch support** (windlass unload /
  anti-pronation traction).
- **Baxter's / fascia** medial-heel target → the aggressive medial-heel relief already carried
  by the hot-spot logic.

So the print follows the *structure*, not just the peak-pressure zone.

## Track it over time

The point of a dose model is watching your numbers **move**. [`analysis/trend.py`](../analysis/trend.py)
logs each day's CPTS per structure and charts the trend:

```bash
python analysis/trend.py record results/day.json --date 2026-07-05 --history results/cpts_history.jsonl
python analysis/trend.py chart  --history results/cpts_history.jsonl --out results/
python analysis/trend.py --demo --out results/     # ~6 weeks, forefoot dose falling after an intervention
```

A falling forefoot line after a met pad / rest-window habit is the intervention working; a rising
line says the dose is creeping back ([sample trend](../sample/results/report_trend.md)).

---
**Not a medical device; not medical advice.** Associations are published; the zone-weights the
module uses are *estimated* from anatomy + those papers. Confirming which nerve or fascia is
actually involved needs a clinician (exam + ultrasound/MRI, or a diagnostic anesthetic block).
This tells you where your *mechanical dose* is going so you can offload it and ask better questions.
