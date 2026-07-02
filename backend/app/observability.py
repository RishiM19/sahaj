"""OpenTelemetry wiring - traces and metrics exported over OTLP to the
collector in infra/otel/collector-config.yaml, which re-exposes them for
Prometheus to scrape (see infra/prometheus.yml, infra/grafana/). FastAPI's
own HTTP-level spans/metrics come free from FastAPIInstrumentor; the two
counters/histogram below are the domain-specific signal worth alerting on -
how the orchestrator itself is behaving, not just HTTP status codes.
"""

from __future__ import annotations

import time
from contextlib import contextmanager

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import get_settings

_turn_counter = None
_turn_duration = None
_agent_counter = None


def setup_observability(app: FastAPI) -> None:
    settings = get_settings()
    resource = Resource.create({SERVICE_NAME: "sahaj-backend"})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=settings.otel_exporter_endpoint, insecure=True),
                export_interval_millis=5000,
            )
        ],
    )
    metrics.set_meter_provider(meter_provider)

    FastAPIInstrumentor.instrument_app(app)

    meter = metrics.get_meter("sahaj.orchestrator")
    global _turn_counter, _turn_duration, _agent_counter
    _turn_counter = meter.create_counter(
        "sahaj_turns_total", description="Orchestrator turns handled, by channel"
    )
    _turn_duration = meter.create_histogram(
        "sahaj_turn_duration_seconds", description="End-to-end turn latency"
    )
    _agent_counter = meter.create_counter(
        "sahaj_agent_dispatches_total", description="Agent invocations, by agent and severity"
    )


@contextmanager
def track_turn(channel: str):
    start = time.monotonic()
    try:
        yield
    finally:
        if _turn_counter is not None:
            _turn_counter.add(1, {"channel": channel})
        if _turn_duration is not None:
            _turn_duration.record(time.monotonic() - start, {"channel": channel})


def record_agent_dispatch(agent: str, severity: str) -> None:
    if _agent_counter is not None:
        _agent_counter.add(1, {"agent": agent, "severity": severity})
