"""Thread-safe Prometheus Metric Exporter implementing text exposition format."""

from __future__ import annotations

import sys
import threading
from typing import Any

from harness.services.prometheus.models import (
    DEFAULT_BUCKETS,
    MetricDefinition,
)
from harness.services.prometheus.protocols import PrometheusExporterService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DefaultPrometheusExporterService(PrometheusExporterService):
    """Zero-dependency thread-safe Prometheus text format metric generator."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._definitions: dict[str, MetricDefinition] = {}
        # Stores: (name, label_tuple) -> value
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        # Histograms: (name, label_tuple) -> {"buckets": dict[float, int], "sum": float, "count": int}
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], dict[str, Any]] = {}

    def _labels_to_tuple(self, labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
        if not labels:
            return ()
        return tuple(sorted((str(k), str(v)) for k, v in labels.items()))

    def register_metric(self, metric: MetricDefinition) -> None:
        with self._lock:
            self._definitions[metric.name] = metric

    def increment(
        self, name: str, labels: dict[str, str] | None = None, value: float = 1.0
    ) -> None:
        if value < 0:
            raise ValueError("Counter increments must be non-negative")
        key = (name, self._labels_to_tuple(labels))
        with self._lock:
            if name not in self._definitions:
                self._definitions[name] = MetricDefinition(name=name, help_text=f"Auto-registered {name}", metric_type="counter")
            self._counters[key] = self._counters.get(key, 0.0) + value

    def set_gauge(
        self, name: str, labels: dict[str, str] | None = None, value: float = 0.0
    ) -> None:
        key = (name, self._labels_to_tuple(labels))
        with self._lock:
            if name not in self._definitions:
                self._definitions[name] = MetricDefinition(name=name, help_text=f"Auto-registered {name}", metric_type="gauge")
            self._gauges[key] = float(value)

    def observe(
        self, name: str, labels: dict[str, str] | None = None, value: float = 0.0
    ) -> None:
        key = (name, self._labels_to_tuple(labels))
        with self._lock:
            if name not in self._definitions:
                self._definitions[name] = MetricDefinition(name=name, help_text=f"Auto-registered {name}", metric_type="histogram")
            buckets = self._definitions[name].buckets
            if key not in self._histograms:
                self._histograms[key] = {
                    "buckets": {b: 0 for b in buckets},
                    "sum": 0.0,
                    "count": 0,
                }
            h = self._histograms[key]
            h["sum"] += float(value)
            h["count"] += 1
            for b in buckets:
                if value <= b:
                    h["buckets"][b] += 1

    def _format_labels(self, label_tuples: tuple[tuple[str, str], ...], extra: dict[str, str] | None = None) -> str:
        combined = dict(label_tuples)
        if extra:
            combined.update(extra)
        if not combined:
            return ""
        items = [f'{k}="{v}"' for k, v in sorted(combined.items())]
        return "{" + ",".join(items) + "}"

    def generate_text_export(self) -> str:
        lines: list[str] = []
        with self._lock:
            for name, defn in sorted(self._definitions.items()):
                lines.append(f"# HELP {name} {defn.help_text}")
                lines.append(f"# TYPE {name} {defn.metric_type}")

                if defn.metric_type == "counter":
                    for (m_name, lbls), val in sorted(self._counters.items()):
                        if m_name == name:
                            lines.append(f"{name}{self._format_labels(lbls)} {val}")

                elif defn.metric_type == "gauge":
                    for (m_name, lbls), val in sorted(self._gauges.items()):
                        if m_name == name:
                            lines.append(f"{name}{self._format_labels(lbls)} {val}")

                elif defn.metric_type == "histogram":
                    for (m_name, lbls), h in sorted(self._histograms.items()):
                        if m_name == name:
                            for b, count in sorted(h["buckets"].items()):
                                lines.append(f"{name}_bucket{self._format_labels(lbls, {'le': str(b)})} {count}")
                            lines.append(f"{name}_bucket{self._format_labels(lbls, {'le': '+Inf'})} {h['count']}")
                            lines.append(f"{name}_sum{self._format_labels(lbls)} {h['sum']}")
                            lines.append(f"{name}_count{self._format_labels(lbls)} {h['count']}")

        return "\n".join(lines) + "\n"

    def clear_metrics(self) -> None:
        with self._lock:
            self._definitions.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
