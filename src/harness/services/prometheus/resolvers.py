"""Single-seam resolver for PrometheusExporterService."""

from __future__ import annotations

from harness.kernel.context import ServiceContext
from harness.services.prometheus.keys import PROMETHEUS_EXPORTER_SERVICE_KEY
from harness.services.prometheus.protocols import PrometheusExporterService
from harness.services.prometheus.service import DefaultPrometheusExporterService

_GLOBAL_EXPORTER = DefaultPrometheusExporterService()


def resolve_prometheus_exporter(
    context: ServiceContext | None = None,
) -> PrometheusExporterService:
    """Resolve PrometheusExporterService from context or return process-wide singleton."""
    if context is not None and hasattr(context, "has") and context.has(PROMETHEUS_EXPORTER_SERVICE_KEY):
        return context.require(PROMETHEUS_EXPORTER_SERVICE_KEY)
    return _GLOBAL_EXPORTER
