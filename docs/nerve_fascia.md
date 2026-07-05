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

## Run it

```bash
python analysis/nerve_fascia.py --demo
# or your own day summary:
python analysis/nerve_fascia.py --day my_day.json --out results/
```

`my_day.json`: per-zone `pressure_kPa` + `pti_kPa_s` (per cycle), `gait_steps_per_day`,
`bounce_cycles_per_day`, `heel_strike_fraction`. Emits a ranked structure report + JSON.

---
**Not a medical device; not medical advice.** Associations are published; the zone-weights the
module uses are *estimated* from anatomy + those papers. Confirming which nerve or fascia is
actually involved needs a clinician (exam + ultrasound/MRI, or a diagnostic anesthetic block).
This tells you where your *mechanical dose* is going so you can offload it and ask better questions.
