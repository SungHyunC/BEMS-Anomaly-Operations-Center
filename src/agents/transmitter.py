"""Stage 2 — Transmitter Agent (field gateway).

Reads Generator samples and forwards them with realistic building-network
degradation:
  * Transmission delay  — variable WiFi/field latency
  * Packet drop         — ~10% of frames lost on the lossy wireless hop
  * Sensor noise        — Gaussian electromagnetic interference

Transport (set by ``PIPELINE.transport``):
  * ``"udp"``  — degraded telemetry is sent as connectionless **UDP datagrams**
                 to the Collector's BACnet/IP-style port (the realistic field
                 plane; no delivery guarantee).
  * ``"rest"`` — degraded telemetry is POSTed to ``/ingest`` (reliable fallback).

The *clean* copy of every sample is always sent to ``/truth`` over REST so the
evaluator has ground truth even for dropped sequences (management plane).
"""
from __future__ import annotations

import random
import socket
import sys
import time

import httpx

from src.config import NETWORK, PIPELINE, SENSORS
from src.agents.generator import stream
from src.agents.udp_link import send_datagram


def _degrade(sample: dict) -> dict | None:
    """Apply field-network degradation. Returns None if the frame is dropped."""
    if random.random() < NETWORK.drop_rate:
        return None
    noisy = dict(sample["readings"])
    for name, value in noisy.items():
        spec = SENSORS[name]
        noisy[name] = round(
            value + random.gauss(0, spec.noise_std * NETWORK.noise_multiplier), 3
        )
    time.sleep(random.uniform(NETWORK.delay_min_s, NETWORK.delay_max_s))
    return {**sample, "readings": noisy, "transmitted_at": time.time()}


def run() -> None:
    truth_url = f"{PIPELINE.collector_url}/truth"
    ingest_url = f"{PIPELINE.collector_url}/ingest"
    use_udp = (PIPELINE.transport == "udp")
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if use_udp else None

    sent = dropped = failed = truthed = 0
    dest = (f"udp://{PIPELINE.udp_host}:{PIPELINE.udp_port}" if use_udp else ingest_url)
    print(f"[transmitter] transport={PIPELINE.transport} · telemetry -> {dest}", flush=True)

    with httpx.Client(timeout=5.0) as client:
        for sample in stream():
            # clean copy -> evaluation plane (always REST)
            try:
                client.post(truth_url, json=sample)
                truthed += 1
            except httpx.HTTPError as exc:
                print(f"[transmitter] truth post failed: {exc}", flush=True)

            degraded = _degrade(sample)
            if degraded is None:
                dropped += 1
                continue

            if use_udp:
                try:
                    send_datagram(degraded, sock=udp_sock)
                    sent += 1
                except OSError as exc:
                    failed += 1
                    print(f"[transmitter] udp send failed: {exc}", flush=True)
            else:
                try:
                    client.post(ingest_url, json=degraded)
                    sent += 1
                except httpx.HTTPError as exc:
                    failed += 1
                    print(f"[transmitter] ingest failed: {exc}", flush=True)

            if sample["seq"] % 10 == 0 and sample["zone"] == "Zone-A":
                print(f"[transmitter] truth={truthed} sent={sent} "
                      f"dropped={dropped} failed={failed}", flush=True)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
