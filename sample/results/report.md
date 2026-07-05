# Pressure analysis — findings & insole directives

_Pressure in kPa (calibrated). A design/measurement aid, not medical advice._


## barefoot

- Highest sustained load (impulse) is at **heel_med** (27% of total) — this is your hot spot.
- Medial load (48%) >> lateral (27%) — a **pronation** tendency; consider mild medial posting / arch support.
- Heel-strike loading rate ~ 11886 rel/s — a hard heel strike; a soft heel cushion helps.
- Cadence ~ 54.5 steps/min.

**Design directives:** `{"relief_window_zone": "heel_med", "relief_window": "standard", "posting": "medial", "cushion_priority": "balanced", "heel_cushion": "soft"}`

## shoe

- Highest sustained load (impulse) is at **heel_med** (40% of total) — this is your hot spot.
- Load is **concentrated** at heel_med (>1.6× the next zone) — a localized overload; offload it aggressively.
- Medial load (56%) >> lateral (25%) — a **pronation** tendency; consider mild medial posting / arch support.
- Heel-dominant (59% at the heel) — prioritize heel cushioning + the relief window.
- Heel-strike loading rate ~ 17788 rel/s — a hard heel strike; a soft heel cushion helps.
- Cadence ~ 54.5 steps/min.

**Design directives:** `{"relief_window_zone": "heel_med", "relief_window": "aggressive (softer + deeper recess)", "posting": "medial", "cushion_priority": "heel", "heel_cushion": "soft"}`

## Barefoot vs shoe

- Your **shoe raises** load at heel_med by 13 pts vs barefoot — the shoe is *adding* to your hot spot. The printed insole should undo that (relief window + softer heel).

## Structure watch — nerves & fascia (screening)

_Screening — which nerves/fascia this loading pattern tends to overload. NOT a diagnosis._
- **plantar_fascia** (fascia) — medial calcaneal insertion; classic FIRST-STEP MORNING pain, worse after rest. → _offload medial heel AND cushion the forefoot; calf/soleus length work; hallux/windlass load management. Hypermobile: load, don't over-stretch._ ([src](https://pmc.ncbi.nlm.nih.gov/articles/PMC385265/))
- **baxter_nerve** (nerve) — pain slightly MORE MEDIAL than the fascia insertion; unlike fasciitis it WORSENS THROUGH THE DAY with weight-bearing (an all-day-dose signature), often burning/constant; Tinel over the medial calcaneus radiates to the lateral heel / 4th-5th toes. → _the same medial-heel offload helps, but if heel pain is worse-with-the-day (not worse-in-the-morning) and resists fasciitis care, this nerve is the suspect -> clinician for US-guided block / MRI._ ([src](https://radsource.us/baxters-nerve/))
- **tibial_nerve_tarsal_tunnel** (nerve) — medial-ANKLE Tinel; burning/tingling radiating into the sole & toes; worse with activity/standing. → _medial-arch support / motion control to reduce pronation traction; if radiating medial-ankle symptoms -> clinician._ ([src](https://www.ncbi.nlm.nih.gov/books/NBK513273/))

→ The relief target should follow the structure(s): **plantar_fascia, baxter_nerve, tibial_nerve_tarsal_tunnel**. Model the all-day dose (CPTS) with `analysis/nerve_fascia.py` — see docs/nerve_fascia.md.

## -> Print these into the insole

- **Relief window** at `heel_med` (aggressive (softer + deeper recess))
- **Posting:** medial · **Cushion priority:** heel
- **Structure target (screening):** plantar_fascia, baxter_nerve, tibial_nerve_tarsal_tunnel