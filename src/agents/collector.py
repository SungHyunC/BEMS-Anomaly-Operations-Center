"""Stage 3 — Collector Agent.

FastAPI service that:
  * Receives *clean* samples at POST /truth (used for evaluation only)
  * Receives *degraded* packets at POST /ingest from the Transmitter
  * Receives *manual* injections at POST /inject from the Dashboard
  * Persists everything to a SQLite store
  * Runs Stage 5 (Decision) in a background worker thread that *pushes*
    decisions into the store as new rows arrive — independent of any
    dashboard polling.

GET endpoints expose raw, processed, decisions, evaluation and stats
to the Dashboard and to anyone else who wants to plug in.
"""
from __future__ import annotations

import threading
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import PIPELINE, SENSOR_NAMES, ZONES, ZONE_NAMES
from src.agents import ml_processor
from src.agents.decision import decide
from src.agents.evaluator import evaluate_all, evaluate_zone
from src.agents.generator import baseline_reading
from src.agents.scenarios import SCENARIOS, apply_scenario
from src.agents.store import Store, get_store


# ---------------------------------------------------------------------- models
class Reading(BaseModel):
    power: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    co2: float | None = None


class Packet(BaseModel):
    zone: str = "Zone-A"
    seq: int
    ts: float
    readings: dict[str, float]
    transmitted_at: float | None = None


class TruthPacket(BaseModel):
    zone: str = "Zone-A"
    seq: int
    ts: float
    readings: dict[str, float]
    is_anomaly: bool = False
    scenario: str | None = None


class ManualInjection(BaseModel):
    """User-driven scenario test. Either pick a preset (``scenario``) and we
    auto-fill nominal values + perturbation, or send explicit ``readings``."""
    zone: str = "Zone-A"
    scenario: str | None = None
    readings: dict[str, float] | None = None
    label_as_anomaly: bool = True
    note: str | None = None


# ----------------------------------------------------------- background worker
class DecisionWorker:
    """Periodically runs Stage 4 + 5 on any new readings and writes decisions
    into the store. Survives Claude failures and SQLite contention."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.last_tick: float | None = None
        self.last_error: str | None = None
        self.decisions_made = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="decider")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"{exc.__class__.__name__}: {exc}"
            self._stop.wait(PIPELINE.decision_worker_interval_s)

    def _tick(self) -> None:
        self.last_tick = time.time()
        for zone in self.store.zones_seen():
            recs = self.store.readings(zone=zone, last_n=PIPELINE.window_size)
            if not recs:
                continue
            df = ml_processor.process_zone(recs, zone)
            if df.empty:
                continue
            last_done = self.store.last_decided_seq(zone)
            new = df[df["seq"] > last_done]
            for _, row in new.iterrows():
                result = decide(row.to_dict())
                self.store.insert_decision({
                    "zone": result.zone,
                    "seq": result.seq,
                    "ts": result.ts,
                    "severity": result.severity,
                    "triggered": result.triggered,
                    "alert": result.alert,
                    "decided_at": time.time(),
                    "detector": result.detector,
                    "diagnosis": result.diagnosis,
                    "action": result.action,
                })
                self.decisions_made += 1


# ---------------------------------------------------------------- app & state
worker: DecisionWorker | None = None
udp_server = None  # UDP telemetry listener (BACnet/IP-style field plane)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global worker, udp_server
    store = get_store()
    worker = DecisionWorker(store)
    worker.start()
    # realistic field plane: receive sensor datagrams over UDP
    if PIPELINE.transport == "udp":
        from src.agents.udp_link import UDPTelemetryServer
        udp_server = UDPTelemetryServer()
        udp_server.start()
    try:
        yield
    finally:
        if worker:
            worker.stop()
        if udp_server is not None:
            udp_server.stop()


app = FastAPI(
    title="BEMS Collector",
    version="2.0.0",
    description="Stage 3 hub: ingest → persist → background decide → expose",
    lifespan=_lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ---------------------------------------------------------------- ingest path
@app.post("/truth")
def ingest_truth(packet: TruthPacket) -> dict:
    get_store().insert_truth(packet.model_dump())
    return {"ok": True}


@app.post("/ingest")
def ingest(packet: Packet) -> dict:
    if packet.zone not in ZONE_NAMES:
        # Unknown zone is still accepted — useful for demos with custom zones.
        pass
    get_store().insert_reading(packet.model_dump(), source="transmitter")
    return {"ok": True, "zone": packet.zone, "seq": packet.seq}


@app.post("/inject")
def inject(req: ManualInjection) -> dict:
    """User-driven test. Builds one synthetic sample for ``req.zone`` and
    writes it as BOTH a truth row (with the requested ground-truth label)
    and a reading row tagged source='manual'."""
    if req.zone not in ZONE_NAMES:
        raise HTTPException(400, f"unknown zone: {req.zone}; allowed: {ZONE_NAMES}")
    if req.scenario and req.scenario not in SCENARIOS:
        raise HTTPException(400, f"unknown scenario: {req.scenario}")

    store = get_store()
    seq = store.next_seq(req.zone)
    now = time.time()
    base = baseline_reading(req.zone, now)

    if req.readings:
        merged = {**base, **{k: float(v) for k, v in req.readings.items() if k in SENSOR_NAMES}}
        scenario_tag = req.scenario  # may be None
    elif req.scenario:
        merged = apply_scenario(req.scenario, base)
        scenario_tag = req.scenario
    else:
        merged = base
        scenario_tag = None

    truth_rec = {
        "zone": req.zone, "seq": seq, "ts": now,
        "readings": merged, "is_anomaly": bool(req.label_as_anomaly),
        "scenario": scenario_tag or ("manual" if req.label_as_anomaly else None),
    }
    store.insert_truth(truth_rec)
    store.insert_reading(
        {**truth_rec, "transmitted_at": now},
        source="manual",
        received_at=now,
    )
    return {"ok": True, "zone": req.zone, "seq": seq, "readings": merged, "scenario": scenario_tag}


# ------------------------------------------------------------------- read API
@app.get("/zones")
def zones() -> dict:
    seen = get_store().zones_seen()
    return {
        "configured": [
            {"zone": z, **meta} for z, meta in ZONES.items()
        ],
        "seen": seen,
    }


@app.get("/raw")
def raw(zone: str | None = Query(None), last_n: int = Query(200, ge=1, le=5000)) -> dict:
    store = get_store()
    records = store.readings(zone=zone, last_n=last_n)
    missing = store.missing_seqs(zone) if zone else []
    return {"count": len(records), "missing_seqs": missing, "records": records}


@app.get("/processed")
def processed(zone: str | None = Query(None), last_n: int = Query(200, ge=1, le=5000)) -> dict:
    records = get_store().readings(zone=zone, last_n=last_n)
    df = ml_processor.process(records)
    if df.empty:
        return {"count": 0, "records": []}
    if zone:
        df = df[df["zone"] == zone]
    return {"count": int(len(df)), "records": df.fillna(value="").to_dict(orient="records")}


@app.get("/decisions")
def decisions(zone: str | None = Query(None), last_n: int = Query(100, ge=1, le=1000)) -> dict:
    items = get_store().decisions(zone=zone, last_n=last_n)
    return {"count": len(items), "records": items}


@app.get("/stats")
def stats() -> dict:
    s = get_store().stats()
    s["worker"] = {
        "running": bool(worker and worker._thread and worker._thread.is_alive()),
        "decisions_made": worker.decisions_made if worker else 0,
        "last_tick": worker.last_tick if worker else None,
        "last_error": worker.last_error if worker else None,
    }
    return s


@app.get("/scenarios")
def scenarios() -> dict:
    return {
        "scenarios": [
            {"tag": s.tag, "label": s.label, "description": s.description}
            for s in SCENARIOS.values()
        ]
    }


@app.get("/evaluation")
def evaluation(zone: str | None = Query(None)) -> dict:
    return evaluate_zone(zone) if zone else evaluate_all()


@app.post("/reset")
def reset() -> dict:
    get_store().reset()
    return {"ok": True}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------- entrypoint
def main() -> None:
    import uvicorn
    uvicorn.run(
        "src.agents.collector:app",
        host=PIPELINE.collector_host,
        port=PIPELINE.collector_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
