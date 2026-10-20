"""Protocols for Prometheus Metric Exporter Service (Rule 2)."""

from __future__ import annotations

import sys
from typing import Any, Protocol, runtime_checkable

from harness.services.prometheus.models import MetricDefinition

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@runtime_checkable
class PrometheusExporterService(Protocol):
    """Authoritative protocol for application telemetry and Prometheus metric exposition."""

    def register_metric(self, metric: MetricDefinition) -> None:
        """Register a new metric schema."""
        ...

    def increment(
        self, name: str, labels: dict[str, str] | None = None, value: float = 1.0
    ) -> None:
        """Increment a counter metric."""
        ...

    def set_gauge(
        self, name: str, labels: dict[str, str] | None = None, value: float = 0.0
    ) -> None:
        """Set a gauge metric value."""
        ...

    def observe(
        self, name: str, labels: dict[str, str] | None = None, value: float = 0.0
    ) -> None:
        """Record an observation in a histogram."""
        ...

    def generate_text_export(self) -> str:
        """Render metrics in standard Prometheus text exposition format (version 0.0.4)."""
        ...

    def clear_metrics(self) -> None:
        """Reset metric storage."""
        ...
