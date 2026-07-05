# Balance-assist ecosystem — Apple Watch, Parkinson's cue glasses, smart walkers

The balance module doesn't have to stand alone. These three [`integrations/`](../integrations/README.md)
close the loop with devices people already use — **sense** with more inputs, **assist**
with real-time cues.

![balance-assist ecosystem](balance_assist.svg)

## 1 · Parkinson's cueing glasses — [`gait_cue.py`](../integrations/gait_cue.py)
Freezing of gait ("feet glued to the floor") is a top fall cause in Parkinson's, and
the evidence-based fix is an **external cue**: **visual floor-lines** (the AR/laser
"lines" you step over), an **auditory metronome**, or a **haptic** buzz.

The module detects freezes from the ankle IMU with the classic **Freeze Index**
(freeze-band 3–8 Hz power ÷ locomotor-band 0.5–3 Hz power) and emits a **cue-event
stream** a paired device plays. Worked demo: **2 freezes → 10 cue events** (lines on +
metronome @110 bpm + buzz at each freeze, off on resume).
```bash
python integrations/gait_cue.py --demo --out sample/results
```

## 2 · Apple Watch — [`apple_watch.py`](../integrations/apple_watch.py)
Apple Watch + iPhone already compute **Walking Steadiness** (a validated fall-risk
score) plus walking asymmetry, double-support, speed, and step length. The adapter
reads an **Apple Health export** and **cross-references** the insole — two independent
systems corroborating each other. Worked demo:
> Apple **Steadiness Low (42%)** + insole **mCTSIB vestibular ×7.9** → independent
> fall-risk agreement; Apple asymmetry 14% + insole single-leg **51% (left)** → both
> flag the same side.
```bash
python integrations/apple_watch.py sample/apple_health_export_sample.xml \
    --balance sample/results/balance_positions.json --out sample/results
```

## 3 · Smart walker / rollator — [`walker.py`](../integrations/walker.py)
A sensorized walker measures load through the **handles**; the insole measures load
through the **feet**. Together → **% weight through the walker** (a rehab-progress
number that should fall over time), left/right lean, and a **grab detector** (a spike
onto the handles + drop of foot load = a near-fall) that fires an **adaptive-brake +
alert** command a robotic walker consumes. Worked demo: **16% weight through the
walker, 3 grabs → 3 brake+alert commands.**
```bash
python integrations/walker.py --demo --out sample/results
```

## What's real, what needs the device
Each module implements the **algorithm + the data contract** (cue-event / telemetry
JSON — schemas in [integrations/README](../integrations/README.md)). The final hop is a
thin transport the target hardware defines: **BLE/serial** to cue glasses, laser-shoes,
or a robotic walker; a small **HealthKit companion iOS app** for live Watch streaming.

Freezing-of-gait cueing and walker braking are **assistive prototypes — not a medical
device.** Pair with neurology / PT / audiology.
