"""Tests for Antigravity Trigger Runtime Plugin and Reactive Scheduling."""

from __future__ import annotations

import pytest
from plugins.agent_orchestration.antigravity_trigger_runtime.service import (
    AntigravityTriggerService,
    AntigravityTriggerRuntimePlugin,
    ANTIGRAVITY_TRIGGER_KEY,
)
from harness.kernel.context import ServiceContext


@pytest.mark.unit
class TestAntigravityTriggerRuntime:
    def test_register_interval_and_file_watcher(self) -> None:
        service = AntigravityTriggerService()
        t1 = service.register_interval("cron_5m", interval_seconds=300.0)
        assert t1.trigger_id == "cron_5m"
        assert t1.trigger_type == "interval"
        assert t1.interval_seconds == 300.0

        t2 = service.register_file_watcher("watch_src", file_path="src/harness/kernel")
        assert t2.trigger_id == "watch_src"
        assert t2.trigger_type == "file_change"

        triggers = service.list_triggers()
        assert len(triggers) == 2

    @pytest.mark.asyncio
    async def test_fire_trigger_and_notification(self) -> None:
        service = AntigravityTriggerService()
        service.register_interval("pulse", interval_seconds=60.0)

        fired = await service.fire_trigger("pulse", payload={"metric": "cpu", "value": 12})
        assert fired

        fired_invalid = await service.fire_trigger("non_existent")
        assert not fired_invalid

        notifications = service.get_notifications()
        assert len(notifications) == 1
        assert notifications[0]["trigger_id"] == "pulse"
        assert notifications[0]["payload"]["metric"] == "cpu"

    @pytest.mark.asyncio
    async def test_plugin_ioc_registration(self) -> None:
        plugin = AntigravityTriggerRuntimePlugin()
        ctx = ServiceContext()
        await plugin.on_load(ctx)
        resolved = ctx.require(ANTIGRAVITY_TRIGGER_KEY)
        assert resolved is not None
