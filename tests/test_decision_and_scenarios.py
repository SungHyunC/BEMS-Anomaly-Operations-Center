from __future__ import annotations

from src.agents.decision import decide, _match_rule, _collect_triggers
from src.agents.scenarios import SCENARIOS, apply_scenario
from src.config import SENSOR_NAMES, SENSORS


def _row(**overrides) -> dict:
    base = {
        "zone": "Zone-A", "seq": 0, "ts": 0.0,
        "iforest_anom": False, "iforest_score": 0.0,
    }
    for n in SENSOR_NAMES:
        base[n] = 1.0
        base[f"{n}_z"] = 0.0
        base[f"{n}_z_anom"] = False
        base[f"{n}_hard_anom"] = False
    base.update(overrides)
    return base


def test_normal_when_nothing_fires():
    res = decide(_row())
    assert res.severity == "Normal"
    assert res.triggered == []
    assert "nominal" in res.alert.lower()
    assert res.action == "No action required."


def test_warning_on_soft_zscore():
    res = decide(_row(power=6.0, power_z=3.0, power_z_anom=True))
    assert res.severity == "Warning"
    assert any(t["sensor"] == "power" for t in res.triggered)


def test_critical_on_hard_breach():
    res = decide(_row(power=12.0, power_hard_anom=True, power_z=2.0))
    assert res.severity == "Critical"
    assert res.triggered[0]["hard_breach"] is True


def test_critical_on_extreme_zscore():
    res = decide(_row(temperature=99.0, temperature_z=5.5, temperature_z_anom=True))
    assert res.severity == "Critical"


def test_iforest_only_yields_warning_and_pattern_diagnosis():
    res = decide(_row(iforest_anom=True, iforest_score=0.42))
    assert res.severity == "Warning"
    assert "IsolationForest" in res.diagnosis
    assert res.detector == "iforest"


def test_root_cause_inference_fire_risk():
    """Temperature high + CO₂ high (without humidity high) → fire risk rule."""
    row = _row(
        temperature=42.0, temperature_hard_anom=True, temperature_z=5.0,
        co2=1500, co2_hard_anom=True, co2_z=6.0,
    )
    res = decide(row)
    assert res.severity == "Critical"
    assert "fire" in res.diagnosis.lower() or "thermal" in res.diagnosis.lower()
    assert "evacuat" in res.action.lower() or "detector" in res.action.lower()


def test_root_cause_inference_hvac_failure():
    """Temperature + humidity + CO₂ all high together → HVAC failure rule."""
    row = _row(
        temperature=33.0, temperature_hard_anom=True, temperature_z=3.0,
        humidity=82.0, humidity_hard_anom=True, humidity_z=3.5,
        co2=1400, co2_hard_anom=True, co2_z=5.0,
    )
    res = decide(row)
    assert "hvac" in res.diagnosis.lower()
    assert "chiller" in res.action.lower() or "cool" in res.action.lower()


def test_root_cause_inference_peak_load():
    """Power high alone → peak load rule (NOT fire risk)."""
    row = _row(power=12.0, power_hard_anom=True, power_z=8.0)
    res = decide(row)
    assert "peak" in res.diagnosis.lower() or "load" in res.diagnosis.lower()
    assert "load shedding" in res.action.lower() or "circuit" in res.action.lower()


def test_root_cause_inference_cold_snap():
    """Temperature low → cold snap / heating loss."""
    row = _row(temperature=10.0, temperature_hard_anom=True, temperature_z=-4.0)
    res = decide(row)
    assert "heating" in res.diagnosis.lower() or "ventilation" in res.diagnosis.lower()


def test_every_scenario_produces_at_least_one_breach():
    baseline = {"power": 2.0, "temperature": 22.0, "humidity": 50.0, "co2": 600.0}
    for tag, scenario in SCENARIOS.items():
        out = scenario.apply(dict(baseline))
        breached = False
        for n, v in out.items():
            spec = SENSORS[n]
            if spec.anomaly_high is not None and v > spec.anomaly_high: breached = True
            if spec.anomaly_low is not None and v < spec.anomaly_low: breached = True
        assert breached, f"scenario {tag} did not produce a hard breach"


def test_apply_scenario_rejects_unknown():
    import pytest
    with pytest.raises(KeyError):
        apply_scenario("does_not_exist", {})


def test_decide_ignores_legacy_use_claude_kwarg():
    """Backwards-compat: callers that still pass use_claude= must not break."""
    res = decide(_row(), use_claude=True)
    assert res.severity == "Normal"
