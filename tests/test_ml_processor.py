"""Tests for Stage 4: interpolation, Z-score, IsolationForest, hard thresholds."""
from __future__ import annotations

import time

import numpy as np

from src.agents import ml_processor
from src.config import SENSOR_NAMES


def _gen(zone: str, n: int, skip: set[int] | None = None) -> list[dict]:
    skip = skip or set()
    rng = np.random.default_rng(0)
    rows = []
    for s in range(n):
        if s in skip:
            continue
        rows.append({
            "zone": zone, "seq": s, "ts": float(s),
            "readings": {
                "power":       2.5  + rng.normal(0, 0.1),
                "temperature": 22.0 + rng.normal(0, 0.1),
                "humidity":    50.0 + rng.normal(0, 0.5),
                "co2":         600.0 + rng.normal(0, 5.0),
            },
        })
    return rows


def test_interpolation_fills_dropped_seqs():
    recs = _gen("Zone-A", 10, skip={3, 7})
    df = ml_processor.process(recs)
    assert df["seq"].tolist() == list(range(10))
    # No NaNs in sensor columns after interpolation
    for name in SENSOR_NAMES:
        assert df[name].notna().all()
    # was_missing flag must light up exactly for the dropped seqs
    missing = df[df["was_missing"]]["seq"].tolist()
    assert set(missing) == {3, 7}


def test_zscore_flags_spike():
    recs = _gen("Zone-A", 60)
    # Inject a hard spike in temperature on seq 30
    recs[30]["readings"]["temperature"] = 45.0
    df = ml_processor.process(recs)
    row = df[df["seq"] == 30].iloc[0]
    assert row["temperature_z_anom"] or row["temperature_hard_anom"]
    assert row["anomaly_any"]


def test_hard_threshold_independent_of_zscore():
    # All-equal data → std=0; Z-score won't fire, but hard threshold must.
    recs = _gen("Zone-A", 40)
    for r in recs:
        r["readings"]["power"] = 9.5  # above 8 kW hard limit
    df = ml_processor.process(recs)
    assert df["power_hard_anom"].all()
    assert df["anomaly_any"].all()


def test_iforest_runs_when_enough_samples():
    recs = _gen("Zone-A", 80)
    # Add some clear outliers
    for s in (10, 40, 70):
        recs[s]["readings"]["power"] = 12.0
    df = ml_processor.process(recs)
    # IsolationForest should fire on at least one of the spikes
    spike_rows = df[df["seq"].isin([10, 40, 70])]
    assert spike_rows["iforest_anom"].any()


def test_multi_zone_separation():
    recs = _gen("Zone-A", 30) + _gen("Zone-B", 30, skip={5})
    df = ml_processor.process(recs)
    a = df[df["zone"] == "Zone-A"]
    b = df[df["zone"] == "Zone-B"]
    assert a["seq"].tolist() == list(range(30))
    assert b["seq"].tolist() == list(range(30))
    assert b[b["seq"] == 5]["was_missing"].iloc[0]
    assert not a[a["seq"] == 5]["was_missing"].iloc[0]
