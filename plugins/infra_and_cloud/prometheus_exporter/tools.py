"""Tool functions for Prometheus Exporter plugin."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.services.prometheus import (
    DefaultPrometheusExporterService,
    resolve_prometheus_exporter,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.prometheus_exporter")
_EXPORTER = resolve_prometheus_exporter()


def prometheus_record_metric(
    metric_type: str,
    name: str,
    value: float,
    labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Record metric observation into Prometheus registry."""
    try:
        if metric_type == "counter":
            _EXPORTER.increment(name, labels=labels, value=value)
        elif metric_type == "gauge":
            _EXPORTER.set_gauge(name, labels=labels, value=value)
        elif metric_type == "histogram":
            _EXPORTER.observe(name, labels=labels, value=value)
        else:
            return {"status": "error", "error": f"Invalid metric_type: {metric_type}"}

        return {"status": "ok", "name": name, "metric_type": metric_type, "value": value}
    except Exception as e:
        logger.error("prometheus_record_metric_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def prometheus_get_text_metrics() -> dict[str, Any]:
    """Export formatted Prometheus text export."""
    try:
        text = _EXPORTER.generate_text_export()
        return {"status": "ok", "metrics_text": text}
    except Exception as e:
        logger.error("prometheus_get_text_metrics_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def prometheus_reset_metrics() -> dict[str, Any]:
    """Reset all registered metrics."""
    try:
        _EXPORTER.clear_metrics()
        return {"status": "ok", "cleared": True}
    except Exception as e:
        logger.error("prometheus_reset_metrics_failed", error=str(e))
        return {"status": "error", "error": str(e)}
