"""Pre-baked failure scenarios for the BEMS demo.

Each scenario is a small recipe that perturbs one or more sensors of a
baseline reading. The Generator can fire a scenario randomly, the Dashboard
exposes them as a one-click form, and the Evaluator uses the ``tag`` to
trace which scenario caused which decision.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from src.config import SENSORS


@dataclass(frozen=True)
class Scenario:
    tag: str
    label: str
    description: str
    apply: Callable[[dict], dict]  # mutates and returns a readings dict


def _hvac_failure(readings: dict) -> dict:
    out = dict(readings)
    out["temperature"] = round(SENSORS["temperature"].anomaly_high * random.uniform(1.05, 1.20), 3)
    out["humidity"] = round(SENSORS["humidity"].anomaly_high * random.uniform(1.05, 1.15), 3)
    out["co2"] = round(SENSORS["co2"].anomaly_high * random.uniform(1.10, 1.40), 3)
    return out


def _peak_load(readings: dict) -> dict:
    out = dict(readings)
    out["power"] = round(SENSORS["power"].anomaly_high * random.uniform(1.10, 1.60), 3)
    return out


def _fire_risk(readings: dict) -> dict:
    out = dict(readings)
    out["temperature"] = round(SENSORS["temperature"].anomaly_high * random.uniform(1.20, 1.50), 3)
    out["co2"] = round(SENSORS["co2"].anomaly_high * random.uniform(1.30, 1.80), 3)
    out["power"] = round(SENSORS["power"].anomaly_high * random.uniform(0.95, 1.20), 3)
    return out


def _cold_snap(readings: dict) -> dict:
    out = dict(readings)
    out["temperature"] = round(SENSORS["temperature"].anomaly_low * random.uniform(0.55, 0.90), 3)
    out["humidity"] = round(SENSORS["humidity"].anomaly_low * random.uniform(0.50, 0.90), 3)
    return out


def _occupancy_spike(readings: dict) -> dict:
    out = dict(readings)
    out["co2"] = round(SENSORS["co2"].anomaly_high * random.uniform(1.05, 1.30), 3)
    out["humidity"] = round(SENSORS["humidity"].anomaly_high * random.uniform(1.02, 1.15), 3)
    return out


SCENARIOS: dict[str, Scenario] = {
    s.tag: s for s in (
        Scenario("hvac_failure",   "HVAC Failure",
                 "Cooling stops: temperature, humidity and CO₂ all climb together.",
                 _hvac_failure),
        Scenario("peak_load",      "Peak Power Load",
                 "Large appliance/inrush — power spikes well above 8 kW.",
                 _peak_load),
        Scenario("fire_risk",      "Fire Risk",
                 "Temperature and CO₂ shoot up simultaneously — possible fire.",
                 _fire_risk),
        Scenario("cold_snap",      "Cold Snap",
                 "Heating failure or open window — temperature and humidity drop.",
                 _cold_snap),
        Scenario("occupancy_spike", "Occupancy Spike",
                 "Crowded room: CO₂ and humidity rise without power surge.",
                 _occupancy_spike),
    )
}


def random_scenario() -> Scenario:
    return random.choice(list(SCENARIOS.values()))


def apply_scenario(tag: str, readings: dict) -> dict:
    if tag not in SCENARIOS:
        raise KeyError(f"unknown scenario: {tag}")
    return SCENARIOS[tag].apply(readings)
