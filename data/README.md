# `/data` — Synthetic Sample Data

Three CSV files produced by the Generator → Transmitter → ML Processor → Decision Agent chain on a fixed random seed (`42`). Regenerate any time with:

```bash
python data/generate_samples.py
```

| File | Rows | What it is |
|------|-----:|------------|
| `sample_truth.csv`     | 600 | Ground-truth samples emitted by the Generator. Carries the `is_anomaly` label and the `scenario` tag (when a scenario was applied). 200 samples per zone × 3 zones. |
| `sample_readings.csv`  | 540 | The same samples *after* the Transmitter degradation (10 % packet drop, extra Gaussian noise). Notice the row count is ~90 % of `sample_truth.csv` — that's the simulated packet loss. |
| `sample_decisions.csv` | 599 | What the Decision Agent produced for each interpolated row. Columns: `severity`, `detector`, `diagnosis`, `action`, `n_triggered`, `trigger_sensors`. |

## Severity mix in `sample_decisions.csv`

| Severity | Count |
|----------|------:|
| Normal   | 532 |
| Critical |  50 |
| Warning  |  17 |

## Live SQLite store

When you run `./run_all.sh`, the system writes a live SQLite database to
`data/bems.sqlite3` (WAL mode). It's `.gitignore`-d. To reset it, click
**Reset operational store** in the dashboard sidebar or hit
`POST /reset` on the Collector.

## Schema (matches `src/agents/store.py`)

```sql
truth(zone, seq, ts, power, temperature, humidity, co2, is_anomaly, scenario)
readings(zone, seq, ts, transmitted_at, received_at,
         power, temperature, humidity, co2, source)
decisions(zone, seq, ts, severity, triggered, alert, decided_at,
          detector, diagnosis, action)
```
