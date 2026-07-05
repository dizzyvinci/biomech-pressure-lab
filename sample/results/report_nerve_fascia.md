# Nerve & fascia load — from the all-day pressure dose
_Which nerves/fascia your day's loading overloads, via **CPTS = PTI × cycles/day** (gait steps + the at-rest bounce dose) and the pressure gradient. Associations published (refs/plantar_norms.json `structures`); zone weights estimated. **SCREENING/EDUCATION, NOT A DIAGNOSIS** — these structures overlap & mimic each other._

**Daily dose (CPTS, MPa·s/day):** forefoot **12783** · heel/mid **4337**   _(diabetic-ulcer healing anchor 140–275; an order-of-magnitude reference for AT-RISK tissue, not a healthy-foot limit — use it to compare zones & track your own trend)._
> ⚡ **55% of the forefoot's daily loading cycles come from the at-rest bounce/tap dose** (40,320/day vs 33,622 gait) — invisible to any step-counter, landing on the same met heads gait already loads.

| structure | kind | load (CPTS) | | driving zones | peak | Δgrad |
|---|---|---|---|---|---|---|
| **plantar_fascia** | fascia | 11688 | ████████████ 🔴 HIGH | heel_med, met1, met2, met3, hallux, toes | heel_med 645 kPa | 556 kPa |
| **morton_neuroma** | nerve | 6584 | ███████ 🟠 elevated | met2, met3, met4 | met3 263 kPa | 174 kPa |
| **tibial_nerve_tarsal_tunnel** | nerve | 5004 | █████ 🟠 elevated | heel_med, midfoot, met1 | heel_med 645 kPa | 556 kPa |
| **baxter_nerve** | nerve | 2395 | ██ 🟢 watch | heel_med | heel_med 645 kPa | 556 kPa |

## What's driving each (mechanism · clue · manage)

### plantar_fascia  ·  fascia  ·  🔴 HIGH
- _aka_ plantar aponeurosis
- **mode:** tension (windlass) + insertional compression
- **driver:** heel-lift + toe/hallux extension tensions it; equinus/tight gastroc forces early forefoot loading and raises met-head pressure -> more fascial tension. Toe-walking/forefoot-loading stacks the dose.
- **tell it apart:** medial calcaneal insertion; classic FIRST-STEP MORNING pain, worse after rest.
- **manage:** offload medial heel AND cushion the forefoot; calf/soleus length work; hallux/windlass load management. Hypermobile: load, don't over-stretch.
- load 11688 MPa·s/day from heel_med, met1, met2, met3, hallux, toes; peak heel_med 645 kPa; steepest gradient 556 kPa. _Sources: [pf_windlass](https://pmc.ncbi.nlm.nih.gov/articles/PMC385265/), [equinus_pf](https://www.michiganfootdoctors.com/gastrocnemius-recession-equinus-contracture-plantar-fasciitis/)._

### morton_neuroma  ·  nerve  ·  🟠 elevated
- _aka_ interdigital / intermetatarsal neuroma (common digital plantar nerve)
- **mode:** compression between met heads + toe-hyperextension tethering under the transverse intermetatarsal ligament
- **driver:** forefoot loading + toe extension. The at-rest forefoot BOUNCE/toe-tap dose (bounce.py) stacks onto gait here -- narrow 2nd/3rd interspaces already run higher pressure.
- **tell it apart:** BURNING / numbness / tingling into adjacent toes, 'pebble in the shoe', Mulder's click; relieved by removing the shoe & splaying the toes.
- **manage:** widen the toe box, a metatarsal pad PROXIMAL to the met heads to splay them, cut forefoot dose / add ball-of-foot rest windows, avoid sustained toe-hyperextension.
- load 6584 MPa·s/day from met2, met3, met4; peak met3 263 kPa; steepest gradient 174 kPa. _Sources: [morton](https://www.ncbi.nlm.nih.gov/books/NBK470249/), [press_grad](https://pmc.ncbi.nlm.nih.gov/articles/PMC2387244/)._

### tibial_nerve_tarsal_tunnel  ·  nerve  ·  🟠 elevated
- _aka_ posterior tibial nerve (tarsal tunnel, medial ankle)
- **mode:** tension/traction with overpronation (medial-column collapse)
- **driver:** an overpronation / medial-loading signature (heel_med >> heel_lat, heavy medial midfoot) puts the nerve under traction at the medial ankle.
- **tell it apart:** medial-ANKLE Tinel; burning/tingling radiating into the sole & toes; worse with activity/standing.
- **manage:** medial-arch support / motion control to reduce pronation traction; if radiating medial-ankle symptoms -> clinician.
- load 5004 MPa·s/day from heel_med, midfoot, met1; peak heel_med 645 kPa; steepest gradient 556 kPa. _Sources: [tarsal_tunnel](https://www.ncbi.nlm.nih.gov/books/NBK513273/)._

### baxter_nerve  ·  nerve  ·  🟢 watch
- _aka_ inferior calcaneal nerve = first branch of the lateral plantar nerve
- **mode:** compression (entrapment under abductor hallucis / thickened fascia / spur)
- **driver:** sustained medial-heel weight-bearing dose through the day; a thickened/inflamed plantar fascia squeezes it.
- **tell it apart:** pain slightly MORE MEDIAL than the fascia insertion; unlike fasciitis it WORSENS THROUGH THE DAY with weight-bearing (an all-day-dose signature), often burning/constant; Tinel over the medial calcaneus radiates to the lateral heel / 4th-5th toes.
- **manage:** the same medial-heel offload helps, but if heel pain is worse-with-the-day (not worse-in-the-morning) and resists fasciitis care, this nerve is the suspect -> clinician for US-guided block / MRI.
- load 2395 MPa·s/day from heel_med; peak heel_med 645 kPa; steepest gradient 556 kPa. _Sources: [baxter](https://radsource.us/baxters-nerve/)._

## Reads
- **Forefoot dominates the day's dose** → interdigital-nerve (Morton) + met-head load is the biggest cumulative exposure. The bounce dose is a big, hidden part of it — dose it, don't just suppress it: metatarsal pad, wider toe box, ball-of-foot rest windows.
- **Medial heel pain? Time-of-day tells fascia from nerve:** plantar fasciitis = worst first steps in the **morning**; Baxter's nerve = worse **as the day's weight-bearing accumulates**. Same spot, different fix — log when it hurts.
- **Steep forefoot pressure gradient at met3 (174 kPa jump)** → concentrated subsurface shear near the digital nerves (gradient discriminates breakdown risk better than peak alone). Smooth it with a met pad / cushioning that spreads the load.

---
_Not a medical device; not medical advice. A screening/education aid to discuss with a clinician — confirming which nerve or fascia is involved usually needs exam + ultrasound/MRI or a diagnostic block. Structures & mechanisms: refs/plantar_norms.json `structures`._