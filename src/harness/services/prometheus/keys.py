"""Typed service keys for Prometheus Metric Exporter (Rule 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.services.prometheus.protocols import PrometheusExporterService

PROMETHEUS_EXPORTER_SERVICE_KEY = ServiceKey["PrometheusExporterService"]("service.prometheus_exporter")
