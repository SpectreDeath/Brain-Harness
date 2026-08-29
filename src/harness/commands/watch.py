"""Watch command — autonomous background daemon mode observing file triggers."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable

import structlog

from harness.plugins.watcher import CommentTrigger, CommentTriggerWatcher

logger = structlog.get_logger()


async def start_watch_daemon(
    target_path: str = ".",
    on_trigger: Callable[[CommentTrigger], Any] | None = None,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Run autonomous watch loop monitoring workspace for instruction markers.

    Args:
        target_path: Workspace directory path to observe.
        on_trigger: Callback invoked when a # HARNESS: comment is found.
        stop_event: Optional asyncio Event to terminate the daemon loop.
    """
    p = Path(target_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Target path does not exist: {target_path}")

    processed_triggers: set[tuple[str, int, str]] = set()

    async def default_handler(trigger: CommentTrigger) -> None:
        key = (trigger.file_path, trigger.line_number, trigger.instruction)
        if key in processed_triggers:
            return
        processed_triggers.add(key)
        logger.info(
            "Discovered autonomous comment trigger",
            file=trigger.file_path,
            line=trigger.line_number,
            instruction=trigger.instruction,
        )
        if on_trigger:
            if asyncio.iscoroutinefunction(on_trigger):
                await on_trigger(trigger)
            else:
                on_trigger(trigger)

    loop = asyncio.get_running_loop()
    watcher = CommentTriggerWatcher(p, default_handler)
    watcher.start(loop)
    logger.info("Autonomous watch daemon active", path=str(p))

    try:
        if stop_event:
            await stop_event.wait()
        else:
            while True:
                await asyncio.sleep(1.0)
    finally:
        watcher.stop()
        logger.info("Autonomous watch daemon stopped")


__all__ = ["start_watch_daemon"]
