"""Stage 1 — Generator Agent.

Multi-zone BEMS simulator. Each tick yields one sample per zone with:

  * zone, seq (per-zone monotonic), ts
  * 4 sensor readings drawn from a daily-cycle baseline + Gaussian noise
  * is_anomaly  : ground-truth label (True iff a scenario was applied)
  * scenario    : tag of the scenario that produced the anomaly (or None)

The baseline curve loosely follows the ASHRAE Great Energy Predictor III
shape: a smooth sinusoidal occupancy cycle that lifts power & CO₂ during
the day and dampens at night.
"""
from __future__ import annotations

import math
import random
import time
from itertools import count
from typing import Iterator

from src.config import PIPELINE, SENSORS, ZONES, SENSOR_NAMES
from src.agents.scenarios import random_scenario, SCENARIOS


_PERIOD_S = 600.0  # short cycle so the live demo shows variation within a minute


def _daily_cycle(t: float, offset: float) -> float:
    phase = ((t / _PERIOD_S) + offset) * 2.0 * math.pi
    return 0.5 * (1.0 + math.sin(phase))


def _baseline_value(name: str, t: float, zone_meta: dict) -> float:
    spec = SENSORS[name]
    cycle = _daily_cycle(t, zone_meta.get("cycle_offset", 0.0))
    if name == "power":
        value = (spec.base + 1.8 * cycle) * zone_meta.get("power_scale", 1.0)
        value += random.gauss(0, spec.noise_std)
    elif name == "temperature":
        value = spec.base + 1.5 * (cycle - 0.5) + random.gauss(0, spec.noise_std)
    elif name == "humidity":
        value = spec.base - 4.0 * (cycle - 0.5) + random.gauss(0, spec.noise_std)
    else:  # co2
        value = spec.base + 180.0 * cycle + random.gauss(0, spec.noise_std)
    return round(value, 3)


def baseline_reading(zone: str, t: float | None = None) -> dict:
    """One clean (no scenario applied) reading for a zone."""
    t = t if t is not None else time.time()
    zone_meta = ZONES[zone]
    return {name: _baseline_value(name, t, zone_meta) for name in SENSOR_NAMES}


def generate_sample(
    zone: str,
    seq: int,
    *,
    scenario_tag: str | None = None,
    force_anomaly: bool = False,
) -> dict:
    """Produce one labelled sample for ``zone``.

    If ``scenario_tag`` is given it is applied verbatim. Otherwise, with
    probability ``PIPELINE.anomaly_injection_rate`` (or unconditionally when
    ``force_anomaly`` is True), a random scenario is picked.
    """
    t = time.time()
    readings = baseline_reading(zone, t)

    chosen: str | None = None
    if scenario_tag:
        readings = SCENARIOS[scenario_tag].apply(readings)
        chosen = scenario_tag
    elif force_anomaly or random.random() < PIPELINE.anomaly_injection_rate:
        scenario = random_scenario()
        readings = scenario.apply(readings)
        chosen = scenario.tag

    return {
        "zone": zone,
        "seq": seq,
        "ts": t,
        "readings": readings,
        "is_anomaly": chosen is not None,
        "scenario": chosen,
    }


def stream(interval_s: float | None = None) -> Iterator[dict]:
    """Round-robin samples across every configured zone."""
    interval = interval_s if interval_s is not None else PIPELINE.sample_interval_s
    seqs = {zone: count(0) for zone in ZONES}
    while True:
        for zone in ZONES:
            yield generate_sample(zone, next(seqs[zone]))
        time.sleep(interval)


if __name__ == "__main__":
    for sample in stream():
        print(sample)
