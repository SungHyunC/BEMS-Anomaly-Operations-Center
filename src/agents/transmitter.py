"""Stage 2 — Transmitter Agent.

Reads samples from the Generator and forwards each one twice:

  * POST /truth  — the *clean* sample, used only for evaluation. Always sent.
  * POST /ingest — the *degraded* sample (delay + drop + extra noise),
                   subject to the same constraints a building IoT link suffers.

If a packet is dropped, only the ingest call is skipped; the truth row is
still recorded so we can later measure interpolation error on that gap.
"""
from __future__ import annotations

import random
import sys
import time

import httpx

from src.config import NETWORK, PIPELINE, SENSORS
from src.agents.generator import stream


def _degrade(sample: dict) -> dict | None:
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
    ingest_url = f"{PIPELINE.collector_url}/ingest"
    truth_url = f"{PIPELINE.collector_url}/truth"
    sent = dropped = failed = truthed = 0
    print(f"[transmitter] -> {ingest_url}", flush=True)

    with httpx.Client(timeout=5.0) as client:
        for sample in stream():
            try:
                client.post(truth_url, json=sample)
                truthed += 1
            except httpx.HTTPError as exc:
                print(f"[transmitter] truth post failed: {exc}", flush=True)

            degraded = _degrade(sample)
            if degraded is None:
                dropped += 1
                continue
            try:
                client.post(ingest_url, json=degraded)
                sent += 1
            except httpx.HTTPError as exc:
                failed += 1
                print(f"[transmitter] ingest failed: {exc}", flush=True)

            if sample["seq"] % 10 == 0 and sample["zone"] == "Zone-A":
                print(
                    f"[transmitter] truth={truthed} sent={sent} "
                    f"dropped={dropped} failed={failed}",
                    flush=True,
                )


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
