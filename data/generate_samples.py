"""Regenerate the sample CSV files in this folder.

Run with:  python data/generate_samples.py
Produces:
  data/sample_truth.csv      — 200 ground-truth Generator samples
  data/sample_readings.csv   — same samples after Transmitter degradation
  data/sample_decisions.csv  — Decision Agent output for every sample
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.agents import ml_processor               # noqa: E402
from src.agents.decision import decide            # noqa: E402
from src.agents.generator import generate_sample  # noqa: E402
from src.config import SENSOR_NAMES, ZONE_NAMES, NETWORK, SENSORS  # noqa: E402

random.seed(42)
N_PER_ZONE = 200
DATA = Path(__file__).resolve().parent


def _degrade(sample: dict) -> dict | None:
    if random.random() < NETWORK.drop_rate:
        return None
    noisy = dict(sample["readings"])
    for name, value in noisy.items():
        spec = SENSORS[name]
        noisy[name] = round(value + random.gauss(0, spec.noise_std * NETWORK.noise_multiplier), 3)
    return {**sample, "readings": noisy}


def main() -> None:
    truth_rows, reading_rows = [], []

    for zone in ZONE_NAMES:
        for seq in range(N_PER_ZONE):
            force = (seq % 25 == 0)  # ~4% anomaly rate
            sample = generate_sample(zone, seq, force_anomaly=force)
            truth_rows.append({
                "zone": sample["zone"], "seq": sample["seq"], "ts": sample["ts"],
                **sample["readings"],
                "is_anomaly": int(sample["is_anomaly"]),
                "scenario": sample["scenario"] or "",
            })
            degraded = _degrade(sample)
            if degraded is not None:
                reading_rows.append({
                    "zone": degraded["zone"], "seq": degraded["seq"], "ts": degraded["ts"],
                    "source": "transmitter",
                    **degraded["readings"],
                })

    pd.DataFrame(truth_rows).to_csv(DATA / "sample_truth.csv", index=False)
    pd.DataFrame(reading_rows).to_csv(DATA / "sample_readings.csv", index=False)

    # Pipe readings through Stage 4 + 5
    decision_rows = []
    for zone in ZONE_NAMES:
        zone_recs = [
            {"zone": r["zone"], "seq": r["seq"], "ts": r["ts"],
             "readings": {n: r[n] for n in SENSOR_NAMES}}
            for r in reading_rows if r["zone"] == zone
        ]
        df = ml_processor.process(zone_recs)
        if df.empty:
            continue
        df = df[df["zone"] == zone]
        for _, row in df.iterrows():
            res = decide(row.to_dict())
            decision_rows.append({
                "zone": res.zone, "seq": res.seq, "ts": res.ts,
                "severity": res.severity, "detector": res.detector,
                "diagnosis": res.diagnosis, "action": res.action,
                "n_triggered": len(res.triggered),
                "trigger_sensors": ",".join(t["sensor"] for t in res.triggered),
            })

    pd.DataFrame(decision_rows).to_csv(DATA / "sample_decisions.csv", index=False)

    print(f"truth     rows: {len(truth_rows):,}")
    print(f"readings  rows: {len(reading_rows):,}  (drop rate "
          f"{(1 - len(reading_rows)/len(truth_rows))*100:.1f}%)")
    print(f"decisions rows: {len(decision_rows):,}")
    sev_counts = pd.DataFrame(decision_rows)["severity"].value_counts().to_dict()
    print(f"severity mix:   {sev_counts}")


if __name__ == "__main__":
    main()
