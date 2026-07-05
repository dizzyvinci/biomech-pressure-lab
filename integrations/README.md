# integrations — the balance-assist ecosystem

The insole senses; these turn it into a closed loop with the devices people already
use. Three layers:

```
 SENSE                     DECIDE                        ASSIST
 ─────                     ──────                        ──────
 insole (FSR + IMU) ─┐
 Apple Watch (gait) ─┼──►  balance state · fall-risk ──► Parkinson's cue glasses (lines/metronome)
 smart walker (load)─┘     freezing-of-gait (FOG)        smart walker (adaptive brake + alert)
                                                          haptic buzz (pod / watch)
```

| Module | Direction | What it does | Verified with |
|---|---|---|---|
| [`gait_cue.py`](gait_cue.py) | insole → **glasses** | Detects **freezing of gait** (Freeze Index) → emits a **cue-event stream** (visual floor-lines, metronome, haptic) that Parkinson's cueing glasses / laser-shoes act on | `--demo` (2 freezes → 10 cue events) |
| [`apple_watch.py`](apple_watch.py) | **Watch** → insole | Reads an **Apple Health export** (Walking Steadiness, asymmetry, double-support, speed) and cross-references the insole findings for a **two-source fall-risk view** | `sample/apple_health_export_sample.xml` |
| [`walker.py`](walker.py) | walker ↔ insole → **walker** | Fuses **handle load + foot load** → % weight through the walker (rehab trend), lean, and a **grab detector** that fires **brake + alert** on a near-fall | `--demo` (3 grabs → brake commands) |
| [`video_force.py`](video_force.py) | **video** → force | Estimates peak **vGRF from CoM trajectory** (pose) — check vs the cited DB range; flags **L/R asymmetry** (ACL precursor). Fills in when there's no insole | `--demo` (6.8× BW; 20% asym) |

## What's built vs what needs the device
These modules implement the **algorithms + the data contracts**. The last hop to a
physical device is a thin transport the target hardware defines:

- **Cue glasses / laser-shoes** — consume `cue_events.json` events over **BLE** (or the
  ESP32 drives a GPIO to a laser / an audio DAC for the metronome). Many Parkinson's
  cueing products already take a simple on/off + tempo signal.
- **Apple Watch** — the export adapter works today; **live** sync needs a small
  companion **iOS app** using HealthKit (`HKQuantityTypeIdentifierAppleWalkingSteadiness`
  et al.) to stream the same fields. The Watch IMU can also be an extra trunk channel.
- **Smart walker** — consumes `walker_feedback.json` `brake`/`alert` commands over
  **BLE/serial**; robotic rollators with electronic brakes expose exactly this.

## Event & telemetry schemas
**Cue events** (`gait_cue.py` → glasses/laser/metronome/haptic):
```json
{ "t": 13.0, "channel": "visual_lines|metronome|haptic",
  "action": "on|off|start|stop|buzz", "params": { "spacing_cm": 40, "bpm": 110 } }
```
**Walker telemetry in** (CSV): `t_ms, handle_L_N, handle_R_N, speed_mps[, foot_load_N]`
**Walker feedback out** (`walker.py` → robotic walker):
```json
{ "t": 10.0, "channel": "brake|alert", "action": "engage|release|notify",
  "params": { "level": "high", "msg": "steady — weight onto your feet" } }
```

## API — connect any app (two directions)
The engine is exposed as an HTTP API so *anything* can connect — a coaching app, a
clinician dashboard, a phone app driving the cue glasses, a caregiver alert.

**Inbound** — [`api_server.py`](api_server.py) (dependency-free stdlib):
```
GET  /health                              liveness + tool list
GET  /openapi.json                        machine-readable spec (point any client at it)
POST /analyze/{tool}   body = CSV log  -> analysis JSON
GET  /events/{tool}?demo=1             -> cue / feedback event stream
       tool ∈ pressure balance balance_positions beam landing fog walker
```
```bash
python api_server.py --port 8787
curl -s -X POST --data-binary @session.csv "http://localhost:8787/analyze/landing?discipline=dance"
curl -s "http://localhost:8787/events/fog?demo=1"
```

**Outbound** — [`connectors.py`](connectors.py): push events to other services' webhooks.
Register a URL per event-type in a `connectors.json` (see
[`connectors.sample.json`](connectors.sample.json)) — add a service by adding a URL:
```json
{ "events": { "fall_alert": ["https://caregiver.example/webhook"],
              "landing_score": ["https://coach-app.example/hooks/landing"],
              "cue": ["https://glasses.example/cue"] } }
```
```bash
python connectors.py --demo                                   # dry-run the payloads
python connectors.py --config connectors.json --emit fall_alert --data '{"severity":"high"}' --live
```
One event bus in, one event bus out — that's how "connect to other things" scales:
each new partner is a URL, not a rewrite. Production adds auth + a real ASGI server.

---
Everything is a screening / assistive / performance prototype — **not a medical device**.
Pair with a clinician (neurology / PT / audiology) or coach.
