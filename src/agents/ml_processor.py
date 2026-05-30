"""Stage 4 — ML Processor Agent.

Per-zone pipeline:
  1. Build a wide DataFrame indexed by seq.
  2. Reindex against the full [min_seq..max_seq] range so dropped packets show
     up as NaN rows.
  3. Linear-interpolate the NaNs (column-wise).
  4. Run **two** anomaly detectors and combine:
        a. Z-score        — fast, distribution-aware (|z| > 2.5)
        b. IsolationForest — multivariate, sklearn (contamination configured)
     plus the hard physical thresholds from SENSORS.
"""
from __future__ import annotations

import warnings
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.config import PIPELINE, SENSORS, SENSOR_NAMES, ZONE_NAMES


def to_frame(records: Iterable[dict]) -> pd.DataFrame:
    rows = []
    for rec in records:
        row = {
            "zone": rec.get("zone", "Zone-A"),
            "seq": int(rec["seq"]),
            "ts": rec.get("ts") or rec.get("timestamp"),
        }
        for name in SENSOR_NAMES:
            if name in rec:
                row[name] = rec.get(name)
            else:
                readings = rec.get("readings") or {}
                row[name] = readings.get(name, np.nan)
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=["zone", "seq", "ts", *SENSOR_NAMES])
    return pd.DataFrame(rows)


def _per_zone_reindex_and_interp(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    parts: list[pd.DataFrame] = []
    for zone, sub in df.groupby("zone", sort=False):
        sub = sub.sort_values("seq").drop_duplicates(subset=["seq"], keep="last")
        full = pd.RangeIndex(int(sub["seq"].min()), int(sub["seq"].max()) + 1, name="seq")
        sub = sub.set_index("seq").reindex(full).reset_index()
        sub["zone"] = zone
        sub["was_missing"] = sub[SENSOR_NAMES[0]].isna()
        sub[SENSOR_NAMES] = sub[SENSOR_NAMES].interpolate(
            method="linear", limit_direction="both"
        )
        if "ts" in sub.columns:
            sub["ts"] = sub["ts"].interpolate(method="linear", limit_direction="both")
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


def _zscore_flags(df: pd.DataFrame, threshold: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    flags = pd.DataFrame(False, index=df.index, columns=SENSOR_NAMES)
    zs = pd.DataFrame(0.0, index=df.index, columns=SENSOR_NAMES)
    for zone, idx in df.groupby("zone").groups.items():
        sub = df.loc[idx, SENSOR_NAMES].astype(float)
        # Robust-ish: use median & MAD so a single outlier doesn't poison sigma.
        med = sub.median()
        mad = (sub - med).abs().median().replace(0, np.nan)
        sigma = 1.4826 * mad
        sigma = sigma.fillna(sub.std(ddof=0)).replace(0, np.nan)
        z = (sub - med) / sigma
        z = z.fillna(0.0)
        zs.loc[idx, SENSOR_NAMES] = z.round(3).to_numpy()
        flags.loc[idx, SENSOR_NAMES] = (z.abs() > threshold).to_numpy()
    return flags, zs


def _hard_threshold_flags(df: pd.DataFrame) -> pd.DataFrame:
    flags = pd.DataFrame(False, index=df.index, columns=SENSOR_NAMES)
    for name, spec in SENSORS.items():
        s = df[name].astype(float)
        f = pd.Series(False, index=s.index)
        if spec.anomaly_high is not None:
            f |= s > spec.anomaly_high
        if spec.anomaly_low is not None:
            f |= s < spec.anomaly_low
        flags[name] = f
    return flags


def _iforest_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Per-zone IsolationForest. Falls back to all-False if not enough data."""
    flags = pd.Series(False, index=df.index, name="iforest_anom")
    scores = pd.Series(0.0, index=df.index, name="iforest_score")
    min_n = PIPELINE.iforest_min_samples
    for zone, idx in df.groupby("zone").groups.items():
        sub = df.loc[idx, SENSOR_NAMES].astype(float)
        if len(sub) < min_n:
            continue
        try:
            model = IsolationForest(
                n_estimators=80,
                contamination=PIPELINE.iforest_contamination,
                random_state=0,
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(sub.values)
                pred = model.predict(sub.values)        # -1 = outlier
                sc = -model.score_samples(sub.values)   # higher = more anomalous
            flags.loc[idx] = pred == -1
            scores.loc[idx] = np.round(sc, 4)
        except Exception:
            continue
    return pd.concat([flags, scores], axis=1)


def process(records: list[dict]) -> pd.DataFrame:
    """Full Stage 4 pipeline. Returns one wide DataFrame for ALL zones."""
    df = to_frame(records)
    if df.empty:
        return df
    df = _per_zone_reindex_and_interp(df)

    z_flags, z_scores = _zscore_flags(df, PIPELINE.zscore_threshold)
    hard = _hard_threshold_flags(df)
    iforest = _iforest_flags(df)

    out = df.copy()
    for name in SENSOR_NAMES:
        out[f"{name}_z"] = z_scores[name]
        out[f"{name}_z_anom"] = z_flags[name]
        out[f"{name}_hard_anom"] = hard[name]
        out[f"{name}_anom"] = z_flags[name] | hard[name]
    out["iforest_anom"] = iforest["iforest_anom"].astype(bool)
    out["iforest_score"] = iforest["iforest_score"].astype(float)
    out["anomaly_any"] = (
        out[[f"{n}_anom" for n in SENSOR_NAMES]].any(axis=1) | out["iforest_anom"]
    )
    return out


def process_zone(records: list[dict], zone: str) -> pd.DataFrame:
    """Convenience — process all records, then filter to one zone."""
    df = process(records)
    if df.empty:
        return df
    return df[df["zone"] == zone].reset_index(drop=True)
