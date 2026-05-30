"""Shared configuration for the BEMS pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Project root = the folder *above* src/. The live SQLite store lives in
# <project_root>/data/ so it sits next to the sample CSVs, not inside src/.
ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class SensorSpec:
    name: str
    unit: str
    normal_min: float
    normal_max: float
    anomaly_low: float | None
    anomaly_high: float | None
    base: float
    noise_std: float


SENSORS: dict[str, SensorSpec] = {
    "power":       SensorSpec("power",       "kW",  0.0,   5.0,  None,  8.0,    2.5,   0.6),
    "temperature": SensorSpec("temperature", "°C",  20.0,  26.0, 15.0,  30.0,  23.0,   0.4),
    "humidity":    SensorSpec("humidity",    "%",   40.0,  60.0, 25.0,  75.0,  50.0,   2.0),
    "co2":         SensorSpec("co2",         "ppm", 400.0, 800.0, None, 1200.0, 600.0, 25.0),
}

SENSOR_NAMES: list[str] = list(SENSORS.keys())


# Each zone has its own occupancy cycle offset so they don't move in lockstep.
ZONES: dict[str, dict] = {
    "Zone-A": {"label": "Office Floor", "cycle_offset": 0.0,  "power_scale": 1.0},
    "Zone-B": {"label": "Server Room",  "cycle_offset": 0.25, "power_scale": 1.6},
    "Zone-C": {"label": "Lobby",        "cycle_offset": 0.5,  "power_scale": 0.7},
}
ZONE_NAMES: list[str] = list(ZONES.keys())


@dataclass(frozen=True)
class NetworkConfig:
    delay_min_s: float = 0.2
    delay_max_s: float = 1.5
    drop_rate: float = 0.10
    noise_multiplier: float = 1.2


@dataclass(frozen=True)
class PipelineConfig:
    collector_host: str = "127.0.0.1"
    collector_port: int = 8000
    sample_interval_s: float = 1.0
    window_size: int = 120
    zscore_threshold: float = 2.5
    iforest_contamination: float = 0.05
    iforest_min_samples: int = 30
    anomaly_injection_rate: float = 0.04
    decision_worker_interval_s: float = 1.0
    db_path: str = str(ROOT / "data" / "bems.sqlite3")
    # Telemetry transport for the field/sensor plane:
    #   "udp"  = connectionless datagrams on BACnet/IP's port (realistic; lossy)
    #   "rest" = HTTP POST /ingest (reliable fallback)
    # The management/API plane (dashboard, evaluation, inject) always stays REST.
    transport: str = "udp"
    udp_host: str = "127.0.0.1"
    udp_port: int = 47808            # BACnet/IP standard UDP port

    @property
    def collector_url(self) -> str:
        return f"http://{self.collector_host}:{self.collector_port}"


NETWORK = NetworkConfig()
PIPELINE = PipelineConfig()

# Make sure the data directory exists before anyone opens a sqlite file.
Path(PIPELINE.db_path).parent.mkdir(parents=True, exist_ok=True)
