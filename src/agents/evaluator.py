"""Evaluator — quantitative quality metrics for the pipeline.

Two things we can measure because the Generator labels every sample:

  * Interpolation MAE   — for each sensor, mean |truth - interpolated|
                          taken over the rows whose seq was lost in transit
                          (i.e. dropped by the Transmitter).
  * Detection P/R/F1    — Z-score vs. IsolationForest vs. the union, scored
                          against the ground-truth ``is_anomaly`` label.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.config import SENSOR_NAMES
from src.agents import ml_processor
from src.agents.store import get_store


def _interpolation_metrics(zone: str) -> dict[str, Any]:
    store = get_store()
    joined = store.truth_vs_readings(zone)
    if not joined:
        return {"zone": zone, "n_truth": 0, "n_missing": 0, "per_sensor": {}}

    # Build the same processed frame the dashboard sees.
    readings = store.readings(zone=zone, last_n=10_000)
    proc = ml_processor.process_zone(readings, zone) if readings else pd.DataFrame()

    truth_df = pd.DataFrame(joined).rename(
        columns={f"t_{n}": n for n in SENSOR_NAMES}
    )[["seq", *SENSOR_NAMES]].rename(columns={n: f"truth_{n}" for n in SENSOR_NAMES})

    if proc.empty:
        return {"zone": zone, "n_truth": len(truth_df), "n_missing": 0, "per_sensor": {}}

    merged = proc.merge(truth_df, on="seq", how="inner")
    missing_mask = merged["was_missing"].astype(bool)
    n_missing = int(missing_mask.sum())

    per_sensor: dict[str, dict[str, float]] = {}
    for name in SENSOR_NAMES:
        if name not in merged or f"truth_{name}" not in merged:
            continue
        all_diff = (merged[name] - merged[f"truth_{name}"]).abs()
        gap_diff = all_diff[missing_mask]
        per_sensor[name] = {
            "mae_overall": float(np.round(all_diff.mean(), 4)) if len(all_diff) else 0.0,
            "mae_recovered_only": float(np.round(gap_diff.mean(), 4)) if len(gap_diff) else 0.0,
            "n_gap_samples": int(len(gap_diff)),
        }
    return {
        "zone": zone,
        "n_truth": int(len(truth_df)),
        "n_missing": n_missing,
        "per_sensor": per_sensor,
    }


def _binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = y_true.astype(bool); y_pred = y_pred.astype(bool)
    tp = int(np.sum(y_true & y_pred))
    fp = int(np.sum(~y_true & y_pred))
    fn = int(np.sum(y_true & ~y_pred))
    tn = int(np.sum(~y_true & ~y_pred))
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(prec, 4),
        "recall":    round(rec, 4),
        "f1":        round(f1, 4),
        "support":   int(len(y_true)),
    }


def _detection_metrics(zone: str) -> dict[str, Any]:
    store = get_store()
    readings = store.readings(zone=zone, last_n=10_000)
    truth = store.truth(zone=zone, limit=10_000)
    if not readings or not truth:
        return {"zone": zone, "detectors": {}, "support": 0}
    proc = ml_processor.process_zone(readings, zone)
    if proc.empty:
        return {"zone": zone, "detectors": {}, "support": 0}

    truth_df = pd.DataFrame([
        {"seq": r["seq"], "is_anomaly": bool(r["is_anomaly"])} for r in truth
    ])
    merged = proc.merge(truth_df, on="seq", how="inner")
    if merged.empty:
        return {"zone": zone, "detectors": {}, "support": 0}

    y_true = merged["is_anomaly"].to_numpy()
    zs_pred = merged[[f"{n}_z_anom" for n in SENSOR_NAMES]].any(axis=1).to_numpy()
    hard_pred = merged[[f"{n}_hard_anom" for n in SENSOR_NAMES]].any(axis=1).to_numpy()
    if_pred  = merged["iforest_anom"].to_numpy()
    union_pred = zs_pred | hard_pred | if_pred

    return {
        "zone": zone,
        "support": int(len(y_true)),
        "anomaly_prevalence": round(float(y_true.mean()), 4),
        "detectors": {
            "zscore":        _binary_metrics(y_true, zs_pred),
            "hard_threshold": _binary_metrics(y_true, hard_pred),
            "iforest":       _binary_metrics(y_true, if_pred),
            "union":         _binary_metrics(y_true, union_pred),
        },
    }


def evaluate_zone(zone: str) -> dict[str, Any]:
    return {
        "zone": zone,
        "interpolation": _interpolation_metrics(zone),
        "detection": _detection_metrics(zone),
    }


def evaluate_all() -> dict[str, Any]:
    store = get_store()
    zones = store.zones_seen()
    return {"zones": {z: evaluate_zone(z) for z in zones}}
