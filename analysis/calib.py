"""
calib.py — shared FSR model: ADC -> resistance -> conductance -> Force(N) -> kPa.

FSRs are nonlinear, so we don't do a naive linear ADC->force. From the voltage
divider (FSR on the high side, R_fixed to GND) we recover FSR resistance, take
its conductance G = 1/R, and use a per-sensor power-law  F = a * G^b  fitted from
known-weight calibration points (see calibrate.py). Pressure = Force / pad area.

Both analyze_pressure.py and interpret.py import this when --calibration is given.
"""
import json
import numpy as np


def load(path):
    with open(path) as f:
        return json.load(f)


def adc_to_conductance(adc, vcc, r_fixed, adc_max):
    """Divider: Vcc—FSR—(node)—R_fixed—GND, ADC reads the node. Higher force -> higher V."""
    adc = np.asarray(adc, float)
    vout = np.clip(adc / adc_max * vcc, 1e-4, vcc - 1e-4)
    r_fsr = r_fixed * (vcc - vout) / vout            # ohms
    return 1.0 / np.clip(r_fsr, 1e-6, None)          # siemens


def adc_to_force(adc, cal, ch):
    g = adc_to_conductance(adc, cal["vcc"], cal["r_fixed"], cal["adc_max"])
    s = cal["sensors"].get(str(ch))
    if s is None:                                    # uncalibrated channel -> fall back to conductance
        return np.clip(g * 1000.0, 0, None)
    f = s["a"] * np.power(np.clip(g, 1e-12, None), s["b"])
    return np.clip(f, 0, None)                       # Newtons


def force_to_kpa(force_n, pad_area_mm2):
    return force_n / (pad_area_mm2 * 1e-6) / 1000.0  # N / m^2 -> kPa


def frame_to_pressure(adc_frame, cal):
    """adc_frame (N, 8) -> pressure kPa (N, 8)."""
    adc_frame = np.asarray(adc_frame, float)
    out = np.zeros_like(adc_frame)
    for ch in range(out.shape[1]):
        out[:, ch] = force_to_kpa(adc_to_force(adc_frame[:, ch], cal, ch), cal["pad_area_mm2"])
    return out
