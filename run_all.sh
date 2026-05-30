#!/usr/bin/env bash
# Launch the full BEMS pipeline locally.
#
# Usage:   ./run_all.sh
# Ctrl-C stops everything.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

cleanup() {
  echo "[run_all] stopping pipeline..."
  jobs -p | xargs -I {} kill {} 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "[run_all] starting Collector (FastAPI) on 127.0.0.1:8000"
python -m src.agents.collector > "$LOG_DIR/collector.log" 2>&1 &

# wait for the collector to bind the port
for _ in {1..30}; do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.3
done

echo "[run_all] starting Transmitter (Generator + degradation)"
python -m src.agents.transmitter > "$LOG_DIR/transmitter.log" 2>&1 &

echo "[run_all] starting Streamlit Dashboard on http://localhost:8501"
streamlit run dashboard/app.py \
  --server.headless true --server.port 8501 \
  > "$LOG_DIR/dashboard.log" 2>&1 &

echo "[run_all] all stages running. logs -> $LOG_DIR. Ctrl-C to stop."
wait
