"""UDP telemetry link — the realistic field/sensor plane.

Real building-automation networks carry device telemetry over **connectionless
UDP datagrams** (BACnet/IP uses UDP port 47808; CoAP also runs on UDP). Unlike
TCP/HTTP, UDP gives no delivery guarantee — datagrams can simply not arrive,
which is exactly the lossy behaviour we want to model for the field plane.

This module provides:
  * ``UDPTelemetryServer`` — a background listener the Collector runs to receive
    sensor datagrams and persist them to the store (mirrors POST /ingest).
  * ``send_datagram``      — fire-and-forget sender used by the Transmitter.

The management/API plane (dashboard queries, evaluation, manual injection)
stays on HTTP/REST — exactly how production platforms separate a lightweight
telemetry plane from a reliable control/management plane.
"""
from __future__ import annotations

import json
import socket
import threading

from src.config import PIPELINE


class UDPTelemetryServer:
    """Receives JSON sensor datagrams on a UDP port and ingests them."""

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self.host = host or PIPELINE.udp_host
        self.port = port or PIPELINE.udp_port
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sock: socket.socket | None = None
        self.received = 0
        self.last_error: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="udp-telemetry")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._sock is not None:
                self._sock.close()
        except OSError:
            pass
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        # import here to avoid a circular import at module load
        from src.agents.store import get_store
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.host, self.port))
            self._sock.settimeout(1.0)
        except OSError as exc:
            self.last_error = f"bind failed on {self.host}:{self.port}: {exc}"
            return

        store = get_store()
        while not self._stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                pkt = json.loads(data.decode("utf-8"))
                store.insert_reading(pkt, source="udp")
                self.received += 1
            except Exception as exc:  # noqa: BLE001 — never let one bad datagram kill the listener
                self.last_error = f"{exc.__class__.__name__}: {exc}"
                continue


def send_datagram(pkt: dict, sock: socket.socket | None = None,
                  host: str | None = None, port: int | None = None) -> None:
    """Fire-and-forget UDP send. Pass a reused socket for efficiency."""
    host = host or PIPELINE.udp_host
    port = port or PIPELINE.udp_port
    own = sock is None
    s = sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(json.dumps(pkt).encode("utf-8"), (host, port))
    finally:
        if own:
            s.close()
