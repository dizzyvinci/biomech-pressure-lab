# OpenCap setup — markerless gait across movements (iPhone)

[OpenCap](https://www.opencap.ai/) (Stanford) turns **2 iPhones/iPads** into a 3D markerless motion-capture lab: joint angles, gait speed, stride length, cadence — even estimated joint moments via an OpenSim backend. Free, cloud-processed. 2026 studies report **good-to-excellent within-device reliability** for gait metrics (best when averaging 3 trials).

## You need
- **2 iOS devices** (iPhone/iPad). Any modern iPhone works — LiDAR not required (OpenCap uses the RGB cameras + pose estimation). If you only have one, use **Kinovea** (free desktop 2D) until you borrow a second.
- **2 tripods** (or lean/mount at ~waist height, ~1.5–2 m apart, both aimed at the capture zone).
- The **OpenCap iOS app** (App Store) + a free account at app.opencap.ai.
- A printed **checkerboard** (the app links the PDF) for calibration — tape it to stiff card.

## Capture workflow
1. **Create a session** at app.opencap.ai → it shows a QR/session code.
2. **Connect both iPhones** by scanning the session in the OpenCap app. Mount them ~60–90° apart covering the walkway.
3. **Calibrate**: place the checkerboard in view of both cameras; capture the calibration frame.
4. **Neutral pose**: one static A-pose/T-pose trial (defines your body model + scaling).
5. **Record movements** — one trial each, 3 reps is ideal for reliability:
   - level walk (slow + self-selected + fast)
   - stairs up / down
   - pivot / cut
   - single-leg stance / mini-squat
6. Trials auto-upload → OpenSim processing → download **joint kinematics** (and kinetics) as CSV/`.mot`.

## What to pull out (feeds the insole)
- **Ankle/subtalar angle** through stance → pronation/supination tendency (informs any medial/lateral **posting**).
- **Foot progression + strike pattern** (heel vs mid/forefoot) → where along the foot load lands.
- **Stance-time & loading asymmetry** L vs R → whether one side needs more cushioning.
- **How all of the above change by activity** → so the insole is tuned for your real movements, not just standing.

## Syncing with the smart insole
Start an insole recording (`smart_insole.ino`, short button press) and clap/stomp once at the start of each OpenCap trial — the stomp is a spike in both the insole accel (`ax/ay/az`) and the OpenCap kinematics, so you can time-align the two streams in `analyze_pressure.py` later.

## Fallbacks / alternatives
- **Kinovea** (free, Windows) — 2D sagittal video: quick heel-strike/toe-off, joint angle overlays, one camera.
- **OnForm / Plask** — phone 2D quick looks.
- OpenCap remains the only free route to **3D joint-level** data across movements.
