"""Google Antigravity OpenTelemetry Distributed Tracing & Statusline IPC Service Implementation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


@dataclass(slots=True)
class SpanRecord:
    span_id: str
    name: str
    parent_span_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "OK"


class AntigravityTelemetryService:
    """Authoritative distributed tracing and CLI statusline telemetry service."""

    def __init__(self) -> None:
        self._spans: dict[str, SpanRecord] = {}
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._context_window_limit = 1_000_000

    def start_span(self, name: str, span_id: str, parent_id: str | None = None, attributes: dict[str, Any] | None = None) -> SpanRecord:
        """Start a new hierarchical telemetry span."""
        span = SpanRecord(
            span_id=span_id,
            name=name,
            parent_span_id=parent_id,
            attributes=attributes or {},
        )
        self._spans[span_id] = span
        return span

    def end_span(self, span_id: str, status: str = "OK", extra_attributes: dict[str, Any] | None = None) -> SpanRecord | None:
        """Close an active telemetry span with duration calculation."""
        span = self._spans.get(span_id)
        if not span:
            return None
        span.end_time = time.time()
        span.status = status
        if extra_attributes:
            span.attributes.update(extra_attributes)
        return span

    def record_tokens(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Accumulate token consumption."""
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

    def export_statusline_payload(self, mode: str = "idle") -> dict[str, Any]:
        """Generate Antigravity dynamic statusline IPC payload."""
        total = self._total_prompt_tokens + self._total_completion_tokens
        fill_ratio = round(total / self._context_window_limit, 4)
        return {
            "mode": mode,
            "tokens": {
                "prompt": self._total_prompt_tokens,
                "completion": self._total_completion_tokens,
                "total": total,
                "context_fill_ratio": fill_ratio,
            },
            "active_spans_count": len([s for s in self._spans.values() if s.end_time is None]),
            "completed_spans_count": len([s for s in self._spans.values() if s.end_time is not None]),
        }

    def list_spans(self) -> list[SpanRecord]:
        return list(self._spans.values())


ANTIGRAVITY_TELEMETRY_KEY: ServiceKey[AntigravityTelemetryService] = ServiceKey("service.antigravity.telemetry")


class AntigravityOtelTelemetryPlugin(HarnessPlugin):
    """In-process Harness plugin providing Antigravity telemetry service."""

    name = "antigravity_otel_telemetry"
    version = "1.0.0"
    description = "Google Antigravity OpenTelemetry Telemetry"
    trusted = True

    def __init__(self) -> None:
        self._service = AntigravityTelemetryService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ANTIGRAVITY_TELEMETRY_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(ANTIGRAVITY_TELEMETRY_KEY, self._service)

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass
