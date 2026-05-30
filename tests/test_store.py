"""Sanity tests for the SQLite store. Includes a regression test for the
RLock deadlock we hit in v1 — /stats nesting calls into missing_seqs()."""
from __future__ import annotations

import threading
import time

from src.config import SENSOR_NAMES


def _mk(zone: str, seq: int, missing_sensor: str | None = None) -> dict:
    readings = {"power": 2.0, "temperature": 22.0, "humidity": 50.0, "co2": 600.0}
    if missing_sensor:
        readings.pop(missing_sensor, None)
    return {"zone": zone, "seq": seq, "ts": time.time(), "readings": readings}


def test_insert_and_read(tmp_db):
    for s in range(5):
        tmp_db.insert_reading(_mk("Zone-A", s))
    out = tmp_db.readings(zone="Zone-A")
    assert [r["seq"] for r in out] == [0, 1, 2, 3, 4]


def test_missing_seqs_detects_gaps(tmp_db):
    for s in [0, 1, 2, 4, 5, 7]:
        tmp_db.insert_reading(_mk("Zone-A", s))
    assert tmp_db.missing_seqs("Zone-A") == [3, 6]


def test_stats_does_not_deadlock(tmp_db):
    """Regression: /stats acquired the store lock and then called missing_seqs()
    which also took the lock — with a plain Lock this deadlocks forever.
    With RLock it must return promptly."""
    for s in [0, 1, 3]:
        tmp_db.insert_reading(_mk("Zone-A", s))

    done: list[dict] = []
    t = threading.Thread(target=lambda: done.append(tmp_db.stats()))
    t.start()
    t.join(timeout=3.0)
    assert not t.is_alive(), "Store.stats() deadlocked"
    assert done and done[0]["zones"]["Zone-A"]["missing"] == 1


def test_truth_and_join(tmp_db):
    tmp_db.insert_truth({
        "zone": "Zone-A", "seq": 0, "ts": 0.0,
        "readings": {"power": 1.0, "temperature": 22.0, "humidity": 50.0, "co2": 600.0},
        "is_anomaly": False, "scenario": None,
    })
    tmp_db.insert_truth({
        "zone": "Zone-A", "seq": 1, "ts": 1.0,
        "readings": {"power": 9.0, "temperature": 22.0, "humidity": 50.0, "co2": 600.0},
        "is_anomaly": True, "scenario": "peak_load",
    })
    tmp_db.insert_reading(_mk("Zone-A", 0))
    # seq 1 intentionally missing — simulates dropped packet
    joined = tmp_db.truth_vs_readings("Zone-A")
    assert len(joined) == 2
    by_seq = {r["seq"]: r for r in joined}
    assert by_seq[0]["r_power"] is not None
    assert by_seq[1]["r_power"] is None     # gap
    assert by_seq[1]["is_anomaly"] == 1


def test_next_seq_advances_across_zones(tmp_db):
    assert tmp_db.next_seq("Zone-A") == 0
    tmp_db.insert_reading(_mk("Zone-A", 0))
    assert tmp_db.next_seq("Zone-A") == 1
    assert tmp_db.next_seq("Zone-B") == 0


def test_decisions_roundtrip(tmp_db):
    tmp_db.insert_decision({
        "zone": "Zone-A", "seq": 4, "ts": 100.0, "severity": "Critical",
        "triggered": [{"sensor": "power", "value": 9.5, "unit": "kW",
                       "z": 5.1, "normal_range": [0, 5], "hard_breach": True}],
        "alert": "[Critical] power spike", "decided_at": 101.0,
        "detector": "hard+zscore",
        "diagnosis": "Peak power load event",
        "action": "Consider load shedding non-critical equipment.",
    })
    items = tmp_db.decisions(zone="Zone-A")
    assert len(items) == 1
    assert items[0]["severity"] == "Critical"
    assert items[0]["triggered"][0]["sensor"] == "power"
    assert items[0]["diagnosis"] == "Peak power load event"
    assert tmp_db.last_decided_seq("Zone-A") == 4
