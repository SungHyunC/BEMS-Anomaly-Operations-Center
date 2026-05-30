"""Smoke test: feed the store a deterministic truth/readings pair and check
that the evaluator returns sensible MAE and F1 numbers."""
from __future__ import annotations

import time

from src.agents import evaluator


def _truth(zone: str, seq: int, power: float, is_anomaly: bool, scenario: str | None = None):
    return {
        "zone": zone, "seq": seq, "ts": float(seq),
        "readings": {"power": power, "temperature": 22.0, "humidity": 50.0, "co2": 600.0},
        "is_anomaly": is_anomaly, "scenario": scenario,
    }


def _reading(zone: str, seq: int, power: float):
    return {
        "zone": zone, "seq": seq, "ts": float(seq),
        "readings": {"power": power, "temperature": 22.0, "humidity": 50.0, "co2": 600.0},
        "transmitted_at": float(seq) + 0.01,
    }


def test_evaluation_produces_metrics(tmp_db):
    zone = "Zone-A"

    # 40 nominal samples, with seq=15 being a true anomaly (huge power spike).
    for s in range(40):
        is_anom = (s == 15)
        truth_power = 12.0 if is_anom else 2.5
        tmp_db.insert_truth(_truth(zone, s, truth_power, is_anom, "peak_load" if is_anom else None))
        if s != 20:  # drop seq=20 to exercise interpolation MAE
            reading_power = truth_power + (0.05 if s % 2 == 0 else -0.05)  # tiny network noise
            tmp_db.insert_reading(_reading(zone, s, reading_power))

    out = evaluator.evaluate_zone(zone)
    interp = out["interpolation"]
    det = out["detection"]

    assert interp["n_truth"] == 40
    assert interp["n_missing"] == 1
    # Interpolation error on a gap of one between near-identical neighbours is tiny.
    assert interp["per_sensor"]["power"]["mae_recovered_only"] < 0.5

    detectors = det["detectors"]
    # The hard-threshold detector must catch the 12 kW spike with no false positives.
    assert detectors["hard_threshold"]["recall"] == 1.0
    assert detectors["hard_threshold"]["precision"] == 1.0
    # Union recall must be at least as high as any single detector.
    assert detectors["union"]["recall"] >= detectors["zscore"]["recall"]
