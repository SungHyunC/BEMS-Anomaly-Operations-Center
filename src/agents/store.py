"""SQLite-backed store shared by the Collector and the Evaluator.

Three tables:

  * truth     — what the Generator actually produced (pre-degradation, with the
                ground-truth anomaly label and scenario tag). The Transmitter
                forwards this so evaluation can run later.
  * readings  — what the Collector received from the Transmitter (post-network
                degradation, with potentially missing seqs and noise). Manual
                injections also land here with source='manual'.
  * decisions — Stage 5 outputs (severity, alert, trigger sensors, detector
                used, whether Claude was called).

A composite primary key of (zone, seq) lets every zone keep its own sequence.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterable

from src.config import PIPELINE, SENSOR_NAMES, ZONE_NAMES


_SCHEMA = """
CREATE TABLE IF NOT EXISTS truth (
    zone           TEXT    NOT NULL,
    seq            INTEGER NOT NULL,
    ts             REAL    NOT NULL,
    power          REAL,
    temperature    REAL,
    humidity       REAL,
    co2            REAL,
    is_anomaly     INTEGER NOT NULL DEFAULT 0,
    scenario       TEXT,
    PRIMARY KEY (zone, seq)
);
CREATE INDEX IF NOT EXISTS idx_truth_zone_ts ON truth(zone, ts);

CREATE TABLE IF NOT EXISTS readings (
    zone           TEXT    NOT NULL,
    seq            INTEGER NOT NULL,
    ts             REAL    NOT NULL,
    transmitted_at REAL,
    received_at    REAL    NOT NULL,
    power          REAL,
    temperature    REAL,
    humidity       REAL,
    co2            REAL,
    source         TEXT    NOT NULL DEFAULT 'transmitter',
    PRIMARY KEY (zone, seq)
);
CREATE INDEX IF NOT EXISTS idx_readings_zone_seq ON readings(zone, seq);

CREATE TABLE IF NOT EXISTS decisions (
    zone        TEXT    NOT NULL,
    seq         INTEGER NOT NULL,
    ts          REAL    NOT NULL,
    severity    TEXT    NOT NULL,
    triggered   TEXT    NOT NULL,
    alert       TEXT    NOT NULL,
    decided_at  REAL    NOT NULL,
    detector    TEXT    NOT NULL DEFAULT 'zscore',
    diagnosis   TEXT    NOT NULL DEFAULT '',
    action      TEXT    NOT NULL DEFAULT '',
    PRIMARY KEY (zone, seq)
);
CREATE INDEX IF NOT EXISTS idx_decisions_zone_seq ON decisions(zone, seq);
"""


class Store:
    """Thread-safe SQLite store. One Store per process is enough.

    We open a single shared connection in WAL mode and serialize all writes
    with an RLock. Reads happen on the same connection — fine for this scale
    (single-writer demo) and avoids the cost of per-call connection setup.
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = path or PIPELINE.db_path
        # check_same_thread=False because FastAPI hands sync handlers off to a
        # threadpool. The RLock below serialises actual access.
        self._conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)
        self._lock = threading.RLock()

    # ---------------------------------------------------------------- helpers
    @contextmanager
    def _cursor(self):
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def reset(self) -> None:
        """Wipe all tables — used by tests and by the dashboard 'Reset' button."""
        with self._cursor() as cur:
            cur.execute("DELETE FROM truth")
            cur.execute("DELETE FROM readings")
            cur.execute("DELETE FROM decisions")

    # ------------------------------------------------------------------ truth
    def insert_truth(self, rec: dict) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO truth
                   (zone, seq, ts, power, temperature, humidity, co2, is_anomaly, scenario)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    rec["zone"], rec["seq"], rec["ts"],
                    rec["readings"].get("power"), rec["readings"].get("temperature"),
                    rec["readings"].get("humidity"), rec["readings"].get("co2"),
                    1 if rec.get("is_anomaly") else 0,
                    rec.get("scenario"),
                ),
            )

    def truth(self, zone: str | None = None, limit: int = 500) -> list[dict]:
        q = "SELECT * FROM truth"
        args: tuple = ()
        if zone:
            q += " WHERE zone = ?"; args = (zone,)
        q += " ORDER BY zone, seq DESC LIMIT ?"
        args = (*args, limit)
        with self._cursor() as cur:
            return [dict(r) for r in cur.execute(q, args)]

    # --------------------------------------------------------------- readings
    def insert_reading(
        self,
        rec: dict,
        source: str = "transmitter",
        received_at: float | None = None,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO readings
                   (zone, seq, ts, transmitted_at, received_at,
                    power, temperature, humidity, co2, source)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    rec["zone"], rec["seq"], rec["ts"],
                    rec.get("transmitted_at"),
                    received_at if received_at is not None else time.time(),
                    rec["readings"].get("power"), rec["readings"].get("temperature"),
                    rec["readings"].get("humidity"), rec["readings"].get("co2"),
                    source,
                ),
            )

    def readings(
        self,
        zone: str | None = None,
        last_n: int = 200,
    ) -> list[dict]:
        if zone:
            q = (
                "SELECT * FROM readings WHERE zone = ? "
                "ORDER BY seq DESC LIMIT ?"
            )
            args = (zone, last_n)
        else:
            q = (
                "SELECT * FROM readings ORDER BY zone, seq DESC LIMIT ?"
            )
            args = (last_n * max(1, len(ZONE_NAMES)),)
        with self._cursor() as cur:
            rows = [dict(r) for r in cur.execute(q, args)]
        rows.sort(key=lambda r: (r["zone"], r["seq"]))
        return rows

    def missing_seqs(self, zone: str) -> list[int]:
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT MIN(seq) AS lo, MAX(seq) AS hi FROM readings WHERE zone = ?",
                (zone,),
            ).fetchone()
            if row is None or row["lo"] is None:
                return []
            present = {
                r["seq"]
                for r in cur.execute(
                    "SELECT seq FROM readings WHERE zone = ?", (zone,)
                )
            }
        return [s for s in range(int(row["lo"]), int(row["hi"]) + 1) if s not in present]

    def next_seq(self, zone: str) -> int:
        """Pick a fresh seq number for a manual injection in a given zone."""
        with self._cursor() as cur:
            r = cur.execute(
                "SELECT MAX(seq) AS m FROM readings WHERE zone = ?", (zone,)
            ).fetchone()
            t = cur.execute(
                "SELECT MAX(seq) AS m FROM truth WHERE zone = ?", (zone,)
            ).fetchone()
        # NB: don't use `... or -1` — seq=0 is falsy and would re-collide.
        r_max = r["m"] if r and r["m"] is not None else -1
        t_max = t["m"] if t and t["m"] is not None else -1
        return int(max(r_max, t_max) + 1)

    def zones_seen(self) -> list[str]:
        with self._cursor() as cur:
            rows = cur.execute(
                "SELECT DISTINCT zone FROM readings ORDER BY zone"
            ).fetchall()
        return [r["zone"] for r in rows] or list(ZONE_NAMES)

    def stats(self) -> dict[str, Any]:
        out: dict[str, Any] = {"zones": {}}
        with self._cursor() as cur:
            total = cur.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
            truth_total = cur.execute("SELECT COUNT(*) AS n FROM truth").fetchone()["n"]
        for zone in self.zones_seen():
            missing = self.missing_seqs(zone)
            with self._cursor() as cur:
                row = cur.execute(
                    "SELECT COUNT(*) AS n, MIN(seq) AS lo, MAX(seq) AS hi "
                    "FROM readings WHERE zone = ?",
                    (zone,),
                ).fetchone()
            received = int(row["n"]) if row else 0
            lo = row["lo"]; hi = row["hi"]
            expected = (hi - lo + 1) if lo is not None and hi is not None else 0
            loss = (len(missing) / expected) if expected else 0.0
            out["zones"][zone] = {
                "received": received,
                "expected": expected,
                "missing": len(missing),
                "missing_seqs": missing[-20:],
                "packet_loss_rate": round(loss, 4),
                "first_seq": lo,
                "last_seq": hi,
            }
        out["total_readings"] = int(total)
        out["total_truth"] = int(truth_total)
        return out

    # -------------------------------------------------------------- decisions
    def insert_decision(self, rec: dict) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO decisions
                   (zone, seq, ts, severity, triggered, alert, decided_at,
                    detector, diagnosis, action)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    rec["zone"], rec["seq"], rec["ts"], rec["severity"],
                    json.dumps(rec.get("triggered", []), ensure_ascii=False),
                    rec["alert"], rec["decided_at"],
                    rec.get("detector", "zscore"),
                    rec.get("diagnosis", ""),
                    rec.get("action", ""),
                ),
            )

    def decisions(
        self, zone: str | None = None, last_n: int = 200
    ) -> list[dict]:
        if zone:
            q = "SELECT * FROM decisions WHERE zone = ? ORDER BY seq DESC LIMIT ?"
            args: tuple = (zone, last_n)
        else:
            q = "SELECT * FROM decisions ORDER BY decided_at DESC LIMIT ?"
            args = (last_n,)
        out = []
        with self._cursor() as cur:
            for r in cur.execute(q, args):
                d = dict(r)
                d["triggered"] = json.loads(d["triggered"]) if d.get("triggered") else []
                out.append(d)
        return out

    def last_decided_seq(self, zone: str) -> int:
        with self._cursor() as cur:
            row = cur.execute(
                "SELECT MAX(seq) AS m FROM decisions WHERE zone = ?", (zone,)
            ).fetchone()
        return int(row["m"]) if row and row["m"] is not None else -1

    # ----------------------------------------------------- evaluation helpers
    def truth_vs_readings(self, zone: str) -> list[dict]:
        """Join truth & readings on (zone, seq). Missing readings come back as
        rows with null reading columns, which is exactly what the evaluator
        needs to compute interpolation MAE."""
        with self._cursor() as cur:
            rows = cur.execute(
                """SELECT t.zone, t.seq, t.ts AS truth_ts,
                          t.power AS t_power, t.temperature AS t_temperature,
                          t.humidity AS t_humidity, t.co2 AS t_co2,
                          t.is_anomaly, t.scenario,
                          r.power AS r_power, r.temperature AS r_temperature,
                          r.humidity AS r_humidity, r.co2 AS r_co2,
                          r.source AS r_source
                   FROM truth t LEFT JOIN readings r
                     ON t.zone = r.zone AND t.seq = r.seq
                   WHERE t.zone = ? ORDER BY t.seq""",
                (zone,),
            ).fetchall()
        return [dict(r) for r in rows]


# Process-wide singleton.
_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store
