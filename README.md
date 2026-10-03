# BEMS Anomaly Operations Center

**A building-telemetry simulation that turns degraded sensor data into explainable anomaly alerts and an interactive operations dashboard.**

[한국어](README.ko.md) · [Video walkthrough](https://youtu.be/Qljy0q05-nU) · [Sample data](data/README.md) · [Engineering notes](TROUBLESHOOTING.md)

An individual coursework project exploring a complete monitoring pipeline: generate labeled data, simulate packet loss and noise, recover missing readings, detect anomalies, and surface a diagnosis with a suggested operator action. Built with Python, FastAPI, SQLite, scikit-learn, Streamlit, and Plotly.

## What it demonstrates

- **Fault-tolerant data processing:** zone-specific sequence tracking, gap detection, and linear interpolation after simulated network degradation.
- **Multiple detection signals:** physical thresholds, median/MAD-based robust Z-scores, and Isolation Forest combined into an anomaly flag.
- **Explainable decisions:** severity classification and nine ordered rules for possible causes such as HVAC failure, peak load, and heating loss.
- **Persistent monitoring:** SQLite in WAL mode and a collector-owned background worker that produces decisions independently of dashboard refreshes.
- **Operator workflow:** seven dashboard tabs covering the building view, operations, telemetry, pipeline, alerts, scenario injection, and quality metrics, with English/Korean UI labels.
- **Evaluation against known truth:** interpolation MAE and detection precision, recall, and F1 computed from synthetic ground-truth records.

## Architecture

The launcher starts **three processes**, covering six logical stages:

| Process | Modules | Responsibility |
|---|---|---|
| Transmitter | `generator.py`, `transmitter.py` | Generate labeled samples; send clean truth and degraded telemetry |
| Collector | `collector.py`, `store.py`, `ml_processor.py`, `decision.py` | Serve the API, persist data, and run ML processing and decisions in a background thread |
| Dashboard | `dashboard/app.py` | Query REST endpoints and render the operations console |

Telemetry uses HTTP by default. An optional JSON-over-UDP transport is implemented in [`udp_link.py`](src/agents/udp_link.py); select it with `PipelineConfig.transport` in [`src/config.py`](src/config.py). Ground truth and management queries continue to use REST. The UDP format is custom JSON, not a BACnet protocol implementation.

The decision worker checks for new samples every second by default. The dashboard reads those stored decisions via REST, with optional periodic refresh; it does not use server-pushed notifications.

## Run locally

Use Python 3.11 and a macOS/Linux shell with `bash` and `curl` available:

```bash
git clone https://github.com/SungHyunC/BEMS-Anomaly-Operations-Center.git
cd BEMS-Anomaly-Operations-Center
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt 'streamlit>=1.37.0'
./run_all.sh
```

The dashboard uses [`st.fragment`](https://docs.streamlit.io/develop/concepts/architecture/fragments), which requires Streamlit 1.37 or later; the command above accounts for the older lower bound in `requirements.txt`.

- Dashboard: [localhost:8501](http://localhost:8501)
- Collector API docs: [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Runtime logs: `logs/`; persistent data: `data/bems.sqlite3`

Press **Ctrl+C** in the launcher terminal to stop the processes. In the dashboard, enable **Auto-refresh** to watch new readings, then use **Scenario Lab** to inject a known fault and inspect its diagnosis.

To run components separately, activate the environment and run `export PYTHONPATH="$PWD"` in each terminal before one of these commands:

```bash
python -m src.agents.collector
python -m src.agents.transmitter
streamlit run dashboard/app.py
```

## Try a controlled anomaly

With the collector running:

```bash
curl -X POST http://127.0.0.1:8000/inject \
  -H 'Content-Type: application/json' \
  -d '{"zone":"Zone-A","scenario":"fire_risk"}'
```

Available presets are `hvac_failure`, `peak_load`, `fire_risk`, `cold_snap`, and `occupancy_spike`. The injection endpoint also accepts custom sensor readings. Labels and diagnoses are simulated examples, not validated building-safety determinations.

### Data and detector configuration

The default simulation has three zones and four sensors:

| Sensor | Nominal range | Hard anomaly threshold |
|---|---|---|
| Power | 0–5 kW | >8 kW |
| Temperature | 20–26 °C | <15 °C or >30 °C |
| Humidity | 40–60% | <25% or >75% |
| CO₂ | 400–800 ppm | >1,200 ppm |

Defaults include a 10% packet-drop probability, 0.2–1.5 seconds of simulated transmission delay, and additional Gaussian sensor noise. The robust Z-score threshold is 3.2; Isolation Forest starts at 30 samples per zone with contamination set to 0.02. Edit [`src/config.py`](src/config.py) to explore different conditions.

## API reference

| Method | Path | Purpose |
|---|---|---|
| POST | `/truth` | Store clean labeled samples for evaluation |
| POST | `/ingest` | Store degraded telemetry |
| POST | `/inject` | Inject a preset or custom sample |
| GET | `/zones`, `/scenarios` | Inspect configured zones and failure presets |
| GET | `/raw`, `/processed` | Retrieve received or interpolated/flagged readings |
| GET | `/decisions` | Inspect severity, diagnosis, and action history |
| GET | `/stats`, `/evaluation` | Inspect packet statistics, worker state, and quality metrics |
| GET | `/health` | Check collector liveness |
| POST | `/reset` | Clear the local operational store |

## Tests and sample data

```bash
# Run the existing test suite
python -m pytest tests/ -v

# Regenerate the checked-in synthetic CSV examples
PYTHONPATH=. python data/generate_samples.py
```

The tests cover SQLite persistence and a nested-lock deadlock regression, per-zone interpolation, detector behavior, severity and diagnosis rules, scenario injection recipes, and evaluation metrics. See [`tests/`](tests/) for the assertions and [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) for the implementation issues behind them.

The checked-in CSVs contain 600 truth records, 540 received readings, and 599 processed decisions. These are synthetic examples, not measured production performance. Schema details are in [`data/README.md`](data/README.md).

## Current limitations

- This is a local simulation with synthetic sensors, not an integration with an operating building or physical BEMS devices.
- Interpolation estimates missing values; it cannot reconstruct an unseen fault reliably. Detector results depend on the configured window and thresholds.
- Diagnoses are deterministic pattern matches and suggested actions, not proven root causes or automatic equipment control.
- The API has no authentication layer. The prototype has not established production availability, throughput, or detection accuracy on real telemetry.
- Runtime dependencies use lower bounds rather than a lockfile, so installations can resolve different versions.

## Explore the code

Start with [`collector.py`](src/agents/collector.py) for orchestration, [`ml_processor.py`](src/agents/ml_processor.py) for interpolation and detectors, and [`decision.py`](src/agents/decision.py) for the rule engine. The [Korean documentation](README.ko.md) includes the detailed diagnosis-rule table.
