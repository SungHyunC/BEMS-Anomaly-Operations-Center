"""Stage 5 — Decision Agent.

Severity classification + deterministic root-cause inference.

Inference logic is rule-based and explainable: we match the pattern of
which sensors fired (and which direction they breached) against a set of
known operational scenarios. Each match yields a structured diagnosis
(probable cause, evidence, recommended action). This is the
production-grade replacement for an LLM-generated alert.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.config import SENSORS, ZONES

Severity = Literal["Normal", "Warning", "Critical"]


@dataclass
class DecisionResult:
    zone: str
    seq: int
    ts: float
    severity: Severity
    triggered: list[dict]
    alert: str
    detector: str
    diagnosis: str
    action: str


# ─────────────────────────────────────────────────────── trigger extraction
def _collect_triggers(row: dict) -> list[dict]:
    triggered = []
    for name, spec in SENSORS.items():
        z_anom = bool(row.get(f"{name}_z_anom"))
        hard = bool(row.get(f"{name}_hard_anom"))
        if not (z_anom or hard):
            continue
        value = row.get(name)
        z = row.get(f"{name}_z", 0.0)
        direction = "high"
        if value is not None:
            if spec.anomaly_low is not None and value < spec.anomaly_low:
                direction = "low"
            elif spec.anomaly_high is not None and value > spec.anomaly_high:
                direction = "high"
            elif z is not None and float(z) < 0:
                direction = "low"
        triggered.append({
            "sensor": name,
            "unit": spec.unit,
            "value": round(float(value), 3) if value is not None else None,
            "z": round(float(z), 3),
            "normal_range": [spec.normal_min, spec.normal_max],
            "hard_breach": hard,
            "direction": direction,
        })
    return triggered


def _classify(triggered: list[dict], iforest_anom: bool) -> Severity:
    if not triggered and not iforest_anom:
        return "Normal"
    for t in triggered:
        if t["hard_breach"] or abs(t["z"]) > 4.0:
            return "Critical"
    if triggered:
        return "Warning"
    return "Warning"


# ─────────────────────────────────── deterministic root-cause inference
# Rules are evaluated top-down; first match wins. Each rule lists which
# (sensor, direction) signals are required (`needs`) and which must be
# absent (`absent`). This makes the decision tree completely auditable.
_RULES: list[dict] = [
    {
        "id": "fire_risk",
        "label": "Possible fire / thermal event",
        "needs":   [("temperature", "high"), ("co2", "high")],
        "absent":  [("humidity", "high")],
        "action":  "Verify smoke and heat detectors; dispatch on-site inspection; "
                   "isolate affected HVAC zone and prepare evacuation protocol if confirmed.",
    },
    {
        "id": "hvac_failure",
        "label": "HVAC cooling failure",
        "needs":   [("temperature", "high"), ("humidity", "high"), ("co2", "high")],
        "absent":  [],
        "action":  "Inspect chiller and cooling tower status; verify supply-air "
                   "temperature set-point; switch to backup AHU if available.",
    },
    {
        "id": "peak_load",
        "label": "Peak power load event",
        "needs":   [("power", "high")],
        "absent":  [("temperature", "high"), ("co2", "high")],
        "action":  "Identify the high-consumption circuit and consider load shedding "
                   "non-critical equipment; verify no inrush from compressor restart.",
    },
    {
        "id": "cold_snap",
        "label": "Heating loss or unintended ventilation",
        "needs":   [("temperature", "low")],
        "absent":  [],
        "action":  "Check heating loop status and damper positions; inspect for an "
                   "open door or window in the zone.",
    },
    {
        "id": "occupancy_spike",
        "label": "Occupancy spike / ventilation insufficient",
        "needs":   [("co2", "high"), ("humidity", "high")],
        "absent":  [("power", "high"), ("temperature", "high")],
        "action":  "Increase fresh-air intake (raise outdoor-air damper set-point) and "
                   "verify supply-fan VFD command.",
    },
    {
        "id": "humidity_anomaly",
        "label": "Humidity anomaly",
        "needs":   [("humidity", "high")],
        "absent":  [],
        "action":  "Check dehumidifier operation and possible water ingress in the zone.",
    },
    {
        "id": "low_humidity",
        "label": "Low humidity / dry-air condition",
        "needs":   [("humidity", "low")],
        "absent":  [],
        "action":  "Engage humidifier; verify steam supply pressure.",
    },
    {
        "id": "co2_only",
        "label": "Elevated CO₂ — ventilation review",
        "needs":   [("co2", "high")],
        "absent":  [],
        "action":  "Raise outdoor-air damper position and verify exhaust-fan status.",
    },
    {
        "id": "temperature_only",
        "label": "Temperature drift",
        "needs":   [("temperature", "high")],
        "absent":  [],
        "action":  "Verify set-point compliance and inspect zone VAV box.",
    },
]


def _signal_set(triggered: list[dict]) -> set[tuple[str, str]]:
    return {(t["sensor"], t["direction"]) for t in triggered}


def _match_rule(triggered: list[dict]) -> dict | None:
    signals = _signal_set(triggered)
    for rule in _RULES:
        if all(req in signals for req in rule["needs"]) and \
           not any(forb in signals for forb in rule["absent"]):
            return rule
    return None


def _diagnose(severity: Severity, triggered: list[dict], iforest_anom: bool) -> tuple[str, str]:
    """Returns (diagnosis_label, recommended_action)."""
    if severity == "Normal":
        return ("All sensors within nominal operating range.",
                "No action required.")
    rule = _match_rule(triggered)
    if rule is not None:
        return rule["label"], rule["action"]
    if iforest_anom and not triggered:
        return ("Multivariate pattern anomaly (IsolationForest)",
                "No single-sensor rule fired. Review zone telemetry for "
                "correlated drift and confirm sensor calibration.")
    return ("Unclassified anomaly",
            "Review the listed sensor trip values and follow zone runbook.")


def _format_alert(severity: Severity, zone: str, triggered: list[dict],
                  diagnosis: str, action: str) -> str:
    zone_label = ZONES.get(zone, {}).get("label", zone)
    header = f"[{severity}] {zone} ({zone_label}) — {diagnosis}"
    if not triggered:
        return f"{header}. Recommended action: {action}"
    evidence = "; ".join(
        f"{t['sensor']}={t['value']}{t['unit']} (z={t['z']}, normal "
        f"{t['normal_range'][0]}–{t['normal_range'][1]}{t['unit']}"
        f"{', HARD BREACH' if t['hard_breach'] else ''})"
        for t in triggered
    )
    return f"{header}. Evidence: {evidence}. Recommended action: {action}"


# ─────────────────────────────────────────────────────────────── public API
def decide(row: dict, **_ignored) -> DecisionResult:
    """The ``**_ignored`` keeps callers from breaking if they still pass old
    flags like ``use_claude=`` — we just drop them."""
    zone = str(row.get("zone", "Zone-A"))
    triggered = _collect_triggers(row)
    iforest_anom = bool(row.get("iforest_anom", False))
    severity: Severity = _classify(triggered, iforest_anom)
    diagnosis, action = _diagnose(severity, triggered, iforest_anom)
    alert = _format_alert(severity, zone, triggered, diagnosis, action)

    detector_bits = []
    if any(t["hard_breach"] for t in triggered): detector_bits.append("hard")
    if any(not t["hard_breach"] for t in triggered): detector_bits.append("zscore")
    if iforest_anom: detector_bits.append("iforest")
    detector = "+".join(detector_bits) or "none"

    return DecisionResult(
        zone=zone,
        seq=int(row["seq"]),
        ts=float(row.get("ts") or 0.0),
        severity=severity,
        triggered=triggered,
        alert=alert,
        detector=detector,
        diagnosis=diagnosis,
        action=action,
    )
