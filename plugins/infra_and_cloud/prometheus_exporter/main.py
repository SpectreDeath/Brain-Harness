"""Main entrypoint and plugin registration for Prometheus Exporter."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.prometheus import (
    PROMETHEUS_EXPORTER_SERVICE_KEY,
    DefaultPrometheusExporterService,
    PrometheusExporterService,
)
from plugins.infra_and_cloud.prometheus_exporter.tools import (
    prometheus_get_text_metrics,
    prometheus_record_metric,
    prometheus_reset_metrics,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.prometheus_exporter")


class PrometheusExporterPlugin(HarnessPlugin):
    """Harness Plugin for Prometheus Telemetry Export (Rules 1, 3, 45)."""

    name = "domain.prometheus_exporter"
    version = "1.0.0"
    description = "Prometheus text format metric exporter and runtime telemetry aggregator"
    trusted = True

    def __init__(self, service: PrometheusExporterService | None = None) -> None:
        self._service = service or DefaultPrometheusExporterService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [PROMETHEUS_EXPORTER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(PROMETHEUS_EXPORTER_SERVICE_KEY, self._service, provider=self.name)
        logger.info("PrometheusExporterService registered into IoC context", plugin=self.name)

    async def on_enable(self) -> None:
        logger.info("PrometheusExporterPlugin enabled", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("PrometheusExporterPlugin disabled", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("PrometheusExporterPlugin unloaded", plugin=self.name)


# Authoritative module singleton export (Rule 45)
plugin = PrometheusExporterPlugin()

__all__ = [
    "PROMETHEUS_EXPORTER_SERVICE_KEY",
    "PrometheusExporterPlugin",
    "plugin",
    "prometheus_get_text_metrics",
    "prometheus_record_metric",
    "prometheus_reset_metrics",
]
