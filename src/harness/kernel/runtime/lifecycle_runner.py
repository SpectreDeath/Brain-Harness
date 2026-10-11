"""Runtime start and stop execution routines."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
import structlog

from harness.events.types import EventType, HarnessEvent

if TYPE_CHECKING:
    from harness.kernel.runtime.coordinator import HarnessRuntime

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger()


async def start_runtime(runtime: HarnessRuntime) -> None:
    """Start the runtime: load, validate, and enable all plugins in topological order."""
    if runtime.is_running:
        return

    logger.info("Starting Harness runtime")
    from harness.events.bus import EVENT_BUS_KEY

    runtime.context.provide(
        EVENT_BUS_KEY, runtime.event_bus, provider="harness", allow_override=True
    )

    if runtime._auto_load_user_plugins:
        user_plugins = runtime.loader.discover_all()
        for plugin in user_plugins:
            runtime.register_plugin(plugin)

    if getattr(runtime, "_initial_config_tree", None) is not None:
        await runtime.reconcile(runtime._initial_config_tree)

    results = await runtime.lifecycle.enable_all(
        trusted_only=False, skip_user_plugins=runtime._lazy_external_plugins
    )
    runtime._is_running = True

    await runtime.event_bus.emit(
        HarnessEvent(
            event_type=EventType.HARNESS_STARTED,
            payload={
                "enabled_plugins": [name for name, ok in results.items() if ok],
                "total_plugins": len(results),
                "services": list(runtime.context.list_services().keys()),
            },
        )
    )
    logger.info(
        "Harness runtime started",
        enabled=f"{sum(results.values())}/{len(results)}",
        services=len(runtime.context.list_services()),
    )


async def stop_runtime(runtime: HarnessRuntime) -> None:
    """Stop the runtime: gracefully unload all plugins and close resources."""
    if not runtime.is_running:
        return

    logger.info("Stopping Harness runtime")
    await runtime.lifecycle.unload_all()
    await runtime.context.dispose()
    await runtime.event_bus.emit(HarnessEvent(event_type=EventType.HARNESS_STOPPED))
    await runtime.event_bus.close()
    runtime._is_running = False
    logger.info("Harness runtime stopped")


__all__ = [
    "start_runtime",
    "stop_runtime",
]
