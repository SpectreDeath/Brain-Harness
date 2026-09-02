"""Tests for Antigravity OTel Telemetry Plugin and Statusline Generation."""

from __future__ import annotations

import pytest
from plugins.data_engineering.antigravity_otel_telemetry.service import (
    AntigravityTelemetryService,
    AntigravityOtelTelemetryPlugin,
    ANTIGRAVITY_TELEMETRY_KEY,
)
from harness.kernel.context import ServiceContext


@pytest.mark.unit
class TestAntigravityOtelTelemetry:
    def test_span_hierarchy_lifecycle(self) -> None:
        service = AntigravityTelemetryService()
        parent = service.start_span("agent_session", span_id="span_p1", attributes={"session_id": "s1"})
        assert parent.span_id == "span_p1"
        assert parent.end_time is None

        child = service.start_span("tool_exec", span_id="span_c1", parent_id="span_p1")
        assert child.parent_span_id == "span_p1"

        closed_child = service.end_span("span_c1", status="OK", extra_attributes={"exit_code": 0})
        assert closed_child is not None
        assert closed_child.end_time is not None
        assert closed_child.attributes["exit_code"] == 0

        spans = service.list_spans()
        assert len(spans) == 2

    def test_token_tracking_and_statusline_payload(self) -> None:
        service = AntigravityTelemetryService()
        service.record_tokens(prompt_tokens=1000, completion_tokens=250)

        payload = service.export_statusline_payload(mode="review")
        assert payload["mode"] == "review"
        assert payload["tokens"]["prompt"] == 1000
        assert payload["tokens"]["completion"] == 250
        assert payload["tokens"]["total"] == 1250
        assert payload["tokens"]["context_fill_ratio"] > 0.0

    @pytest.mark.asyncio
    async def test_plugin_ioc_registration(self) -> None:
        plugin = AntigravityOtelTelemetryPlugin()
        ctx = ServiceContext()
        await plugin.on_load(ctx)
        resolved = ctx.require(ANTIGRAVITY_TELEMETRY_KEY)
        assert resolved is not None
