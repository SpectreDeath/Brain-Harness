"""Slotted domain models for Prometheus Metric Exporter (Rule 12)."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

VALID_METRIC_TYPES = {"counter", "gauge", "histogram"}
METRIC_NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


@dataclass(slots=True, frozen=True)
class MetricDefinition:
    """Slotted immutable metric schema definition."""

    name: str
    help_text: str
    metric_type: str = "counter"
    label_names: tuple[str, ...] = field(default_factory=tuple)
    buckets: tuple[float, ...] = field(default_factory=lambda: DEFAULT_BUCKETS)

    def __post_init__(self) -> None:
        if not METRIC_NAME_RE.match(self.name):
            raise ValueError(f"Invalid metric name: {self.name}")
        if self.metric_type not in VALID_METRIC_TYPES:
            raise ValueError(f"metric_type must be one of {sorted(VALID_METRIC_TYPES)}")


@dataclass(slots=True, frozen=True)
class MetricSample:
    """Slotted immutable metric observation sample."""

    name: str
    labels: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    value: float = 0.0
    timestamp_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("metric sample name must be non-empty")
