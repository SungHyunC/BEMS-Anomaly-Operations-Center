# BEMS Anomaly Operations Center

**🌐 Language:** **English** · [한국어](README.ko.md)

> ICT Module 4 — Intermediate Project
> **Smart Building Energy Anomaly Detection & Response System**
> Kim Sung-hyun · 2021271250 · Individual Project

A six-stage agent pipeline that simulates multi-zone Building Energy
Management System (BEMS) telemetry, intentionally degrades the network,
recovers lost data with classical ML, classifies severity, and diagnoses
root cause with a deterministic rule engine — all surfaced through a
multi-tab Streamlit operations console.

---

## 🎥  Demo Video

**Watch (unlisted): https://www.youtube.com/watch?v=RMszTL3nexo**

---

## Repository Layout

```
.
├── src/                       all source code
│   ├── config.py              sensor specs, zones, network constraints, pipeline params
│   └── agents/                the 5 backend agents
│       ├── generator.py       Stage 1  ▸ multi-zone synthetic BEMS samples
│       ├── transmitter.py     Stage 2  ▸ network degradation (delay / drop / noise)
│       ├── collector.py       Stage 3  ▸ FastAPI service + SQLite store + background worker
│       ├── ml_processor.py    Stage 4  ▸ interpolation + 3-detector anomaly ensemble
│       ├── decision.py        Stage 5  ▸ deterministic rule engine
│       ├── evaluator.py       MAE + Precision/Recall/F1 against ground truth
│       ├── scenarios.py       preset failure recipes (fire / HVAC / peak load / …)
│       └── store.py           SQLite (WAL) persistence layer
│
├── dashboard/                 web GUI code
│   └── app.py                 Stage 6  ▸ 7-tab Streamlit + Plotly console
│
├── data/                      sample synthetic data
│   ├── generate_samples.py    regenerator script
│   ├── sample_truth.csv       600 ground-truth rows (3 zones × 200 samples)
│   ├── sample_readings.csv    540 rows after 10 % packet drop
│   ├── sample_decisions.csv   599 Decision Agent outputs (50 Critical, 17 Warning, 532 Normal)
│   └── README.md              schema reference
│
├── tests/                     24 pytest cases (including RLock deadlock regression)
├── .streamlit/config.toml     dashboard theme
├── requirements.txt
├── run_all.sh                 one-shot launcher for all stages
├── README.md                  this file
└── TROUBLESHOOTING.md         major bugs hit during development + fixes
```

---

## System Overview

```
[1] Generator  →  [2] Transmitter  →  [3] Collector  →  [4] ML Processor  →  [5] Decision  →  [6] Dashboard
 3 zones,         delay / drop /         FastAPI +          interpolate +          rule-engine        operations
 ground-truth     EM noise               SQLite + worker    Z-score + IForest      root-cause         console
```

Every stage is an independent process. They communicate over REST so any
individual agent can be replaced or moved to a different machine. The
Collector also runs a **background worker** that pushes decisions every
second — the dashboard never has to poll for new alerts.

### The six agents

| # | Stage | Module | Responsibility |
|---|-------|--------|----------------|
| ① | Generator      | `src/agents/generator.py`     | 3 zones × 4 sensors, daily-cycle baseline + Gaussian noise, ground-truth `is_anomaly` and `scenario` labels |
| ② | Transmitter    | `src/agents/transmitter.py`   | Forwards each sample twice — clean to `/truth` (eval), degraded to `/ingest` |
| ③ | Collector      | `src/agents/collector.py`     | FastAPI; SQLite (WAL) persistence; background decision worker; 12 REST endpoints |
| ④ | ML Processor   | `src/agents/ml_processor.py`  | Per-zone reindex, linear interpolation, 3 detectors in parallel |
| ⑤ | Decision       | `src/agents/decision.py`      | Severity classification + nine-rule explainable root-cause engine |
| ⑥ | Dashboard      | `dashboard/app.py`            | Seven tabs — Building, Operations, Telemetry, Pipeline, Alerts, Scenario Lab, Quality Metrics |

### Sensor specs

| Sensor | Normal range | Anomaly threshold |
|--------|--------------|-------------------|
| Power consumption | 0 – 5 kW       | > 8 kW |
| Temperature       | 20 – 26 °C     | > 30 °C or < 15 °C |
| Humidity          | 40 – 60 %      | > 75 % or < 25 % |
| CO₂               | 400 – 800 ppm  | > 1200 ppm |

A reading is flagged if (a) it breaches a hard physical threshold,
(b) its **robust Z-score** (MAD-based, \|z\| > 3.2) exceeds the limit,
or (c) **IsolationForest** marks it as a multivariate outlier.
The Decision Agent escalates to *Critical* on a hard breach or
\|z\| > 4; soft-only flags become *Warning*.

### Decision Agent — root-cause rule engine

Nine ordered rules, first match wins. Every diagnosis is auditable.

| Rule | Required signals | Forbidden | Diagnosis |
|------|------------------|-----------|-----------|
| `fire_risk`       | temp ↑, CO₂ ↑                    | humidity ↑     | Possible fire / thermal event |
| `hvac_failure`    | temp ↑, humidity ↑, CO₂ ↑        | —              | HVAC cooling failure |
| `peak_load`       | power ↑                          | temp ↑, CO₂ ↑  | Peak power load event |
| `cold_snap`       | temp ↓                           | —              | Heating loss / open vent |
| `occupancy_spike` | CO₂ ↑, humidity ↑                | power ↑, temp ↑ | Occupancy spike / ventilation insufficient |
| `humidity_anomaly`| humidity ↑                       | —              | Humidity anomaly |
| `low_humidity`    | humidity ↓                       | —              | Low humidity / dry air |
| `co2_only`        | CO₂ ↑                            | —              | Elevated CO₂ — ventilation review |
| `temperature_only`| temp ↑                           | —              | Temperature drift |

Each rule comes with a concrete recommended operator action.

---

## Quick Start

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh
```

* Dashboard: <http://localhost:8501>
* Collector API docs: <http://127.0.0.1:8000/docs>

Logs land in `./logs/`. Ctrl-C stops everything.

## Running stages individually

```bash
export PYTHONPATH=$PWD
python -m src.agents.collector      # Stage 3 + background Stages 4 + 5
python -m src.agents.transmitter    # Stages 1 + 2
streamlit run dashboard/app.py      # Stage 6
```

## Collector REST API

| Method | Path             | Purpose |
|--------|------------------|---------|
| POST   | `/truth`         | Generator's clean sample (evaluation only) |
| POST   | `/ingest`        | Transmitter's degraded packet |
| POST   | `/inject`        | User-driven scenario or custom sample |
| POST   | `/reset`         | Wipe the operational store |
| GET    | `/zones`         | Configured + seen zones |
| GET    | `/scenarios`     | Preset library |
| GET    | `/raw`           | Buffered readings + list of missing seqs |
| GET    | `/processed`     | ML-recovered + anomaly-flagged frame |
| GET    | `/decisions`     | Severity + diagnosis + action history |
| GET    | `/stats`         | Per-zone packet stats + worker state |
| GET    | `/evaluation`    | Interpolation MAE + detection P/R/F1 |
| GET    | `/health`        | Liveness probe |

## Scenario Lab — controlled fault injection

```bash
# preset scenario
curl -X POST http://127.0.0.1:8000/inject \
     -H "Content-Type: application/json" \
     -d '{"zone":"Zone-A","scenario":"fire_risk"}'

# bespoke reading
curl -X POST http://127.0.0.1:8000/inject \
     -H "Content-Type: application/json" \
     -d '{"zone":"Zone-B","readings":{"power":15,"temperature":35,"humidity":85,"co2":1500}}'
```

Presets: `hvac_failure`, `peak_load`, `fire_risk`, `cold_snap`, `occupancy_spike`.

## Tests

```bash
source .venv/bin/activate && python -m pytest tests/ -v
```

24 cases — SQLite store + the RLock deadlock regression, per-zone
interpolation, Z-score / hard-threshold / IsolationForest detectors,
severity classification, every root-cause rule, scenario library, and the
end-to-end evaluator.

---

## Tech Stack

Python 3.11+ · FastAPI · SQLite (WAL) · pandas / NumPy / scikit-learn ·
Streamlit + Plotly. Pure rule-engine decision layer — **no external LLM
dependency**. Tests via pytest.

## Documentation

- `TROUBLESHOOTING.md` — every real bug I hit (RLock deadlock, the
  `0 or -1` integer trap, masking effect on the Z-score detector …) and
  how I fixed it
