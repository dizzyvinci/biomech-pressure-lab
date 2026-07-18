# Docs index

Guides and specs, grouped. (Start at the [project README](../README.md) for the big picture and
the end-to-end flow.) The `.svg` files here are **code-generated diagrams** — regenerate them with
[`make_graphics.py`](make_graphics.py); they're embedded in the READMEs, not read directly.

### Start here
| Doc | What |
|---|---|
| [quickstart.md](quickstart.md) | Both paths, step by step |
| [prototype_status.md](prototype_status.md) | "Is it ready to build / pitch?" + ordered-vs-printed BOM |
| [prior_art.md](prior_art.md) | How this compares to existing systems |
| [analysis_and_implications.md](analysis_and_implications.md) | What the metrics mean and why |

### Path 1 — the printed insole
| Doc | What |
|---|---|
| [insole_print_spec.md](insole_print_spec.md) | ⭐ The insole design + print settings (relief window, density zones) |
| [fit_to_your_foot.md](fit_to_your_foot.md) | Fit the insole by measurements or a scan of your orthotic |
| [parts_list.md](parts_list.md) | Every part + buy links (printer path + optional rig) |
| [what-each-part-is-for.md](what-each-part-is-for.md) | Plain-English part purposes |

### Path 2 — the sensor rig
| Doc | What |
|---|---|
| [path2_tracking_build.md](path2_tracking_build.md) | The all-day barefoot-and-shoe tracking build, end to end |
| [calibration.md](calibration.md) | Turning raw FSR ADC into real kPa |
| [opencap_setup.md](opencap_setup.md) | Optional markerless motion capture |
| [insole_sensor_layout.md](insole_sensor_layout.md) | FSR zone coordinates for the 6-zone STEMMA-QT (ESP32-C6 Feather) rig |
| [BUILD_PLAN.md](BUILD_PLAN.md) | ⭐ STEMMA-QT ankle-pod build: print list, wiring, assembly order, calibration |

### The analysis — what it measures
| Doc | What |
|---|---|
| [zone_load.md](zone_load.md) | Per-metatarsal over/under-use vs cited sports-med norms |
| [conditions.md](conditions.md) | Condition-aware: toe-walking, equinus, heel pain (+ the bounce dose) |
| [nerve_fascia.md](nerve_fascia.md) | The all-day dose (CPTS) → nerves & fascia + the trend/insole hooks |
| [balance.md](balance.md) · [balance_positions.md](balance_positions.md) · [balance_assist.md](balance_assist.md) | Posturography, mCTSIB, and the assist ecosystem |
| [beam_balance.md](beam_balance.md) · [landing_lab.md](landing_lab.md) | Athlete balance + discipline-scored landings |
| [video_force.md](video_force.md) | Estimating force from video when there's no sensor |

### Build the DIY lab (close the equipment gap)
| Doc | What |
|---|---|
| [lab_scope.md](lab_scope.md) | What the cited papers' gear is vs what we DIY, and the honest gaps |
| [build_lab.md](build_lab.md) | Build guide: load-cell force plate + Velostat pressure mat |
| [maker_hacks.md](maker_hacks.md) | Field-tested tricks to reclaim the accuracy cheap sensors lose |

### Reference data
| [../refs/README.md](../refs/README.md) | The cited norms DB — pressures, thresholds, conditions, nerve/fascia structures |
