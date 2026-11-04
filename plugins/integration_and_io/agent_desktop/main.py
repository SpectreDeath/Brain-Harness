"""Agent Desktop Plugin Entrypoint & Service Implementation."""

from __future__ import annotations

import asyncio
import concurrent.futures
import sys
from pathlib import Path
from typing import Any, Coroutine, TypeVar

import structlog

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.agent_desktop import (
    AGENT_DESKTOP_KEY,
    ActionDisposition,
    AgentDesktopActResult,
    AgentDesktopService,
    AgentDesktopSnapshotResult,
    AgentDesktopStatusResult,
    AgentDesktopWindowResult,
    DesktopRefToken,
    EvidenceTriState,
)

from .engine import AgentDesktopEngine

logger = structlog.get_logger(__name__)

_GLOBAL_ENGINE = AgentDesktopEngine()

T = TypeVar("T")


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Execute an async coroutine safely across running event loops or sync execution threads."""
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


# -----------------------------------------------------------------------------
# Tool Handlers (Standalone Functions for Tool Registry)
# -----------------------------------------------------------------------------

def desktop_snapshot(
    app: str = "",
    root_ref: str = "",
    interactive_only: bool = True,
    skeleton: bool = False,
    compact: bool = True,
    surface: str = "",
    session: str = "default",
    **kwargs: Any,
) -> dict[str, Any]:
    """Capture application accessibility tree snapshot or drill down into a root ref."""
    return _run_async(
        _GLOBAL_ENGINE.snapshot(
            app=app,
            root_ref=root_ref,
            interactive_only=interactive_only,
            skeleton=skeleton,
            compact=compact,
            surface=surface,
            session=session,
        )
    )


def desktop_act(
    action: str,
    ref_id: str,
    value: str = "",
    headed: bool = False,
    interval_ms: int | None = None,
    session: str = "default",
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a semantic or physical action on a qualified ref (@snapshot_id:eN)."""
    return _run_async(
        _GLOBAL_ENGINE.act(
            action=action,
            ref_id=ref_id,
            value=value,
            headed=headed,
            interval_ms=interval_ms,
            session=session,
        )
    )


def desktop_find(
    app: str = "",
    role: str = "",
    name: str = "",
    text: str = "",
    session: str = "default",
    **kwargs: Any,
) -> dict[str, Any]:
    """Find accessibility nodes matching role, name, or text within an application."""
    return _run_async(
        _GLOBAL_ENGINE.find(
            app=app,
            role=role,
            name=name,
            text=text,
            session=session,
        )
    )


def desktop_manage_window(
    operation: str,
    app: str = "",
    window_id: str = "",
    bounds: dict[str, int] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """List, focus, resize, or reposition application windows and query displays."""
    return _run_async(
        _GLOBAL_ENGINE.manage_window(
            operation=operation,
            app=app,
            window_id=window_id,
            bounds=bounds,
        )
    )


def desktop_wait(
    app: str = "",
    element_ref: str = "",
    window_title: str = "",
    text: str = "",
    timeout_ms: int = 5000,
    **kwargs: Any,
) -> dict[str, Any]:
    """Wait for a desktop element, window, or surface condition without fixed sleep races."""
    return _run_async(
        _GLOBAL_ENGINE.wait_for(
            app=app,
            element_ref=element_ref,
            window_title=window_title,
            text=text,
            timeout_ms=timeout_ms,
        )
    )


def desktop_status(
    check_permissions: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Query host OS accessibility API status, permissions grant, and available surfaces."""
    return _run_async(_GLOBAL_ENGINE.get_status(check_permissions=check_permissions))


# -----------------------------------------------------------------------------
# Plugin Class
# -----------------------------------------------------------------------------

class AgentDesktopPlugin(HarnessPlugin, AgentDesktopService):
    """Brain Harness Plugin providing native accessibility tree desktop operation."""

    name = "plugin.agent_desktop"
    version = "1.1.0"
    description = (
        "Desktop GUI automation & accessibility tree computer-use engine with snapshot maps, "
        "qualified ref allocation, and 2D delivery-retry disposition"
    )
    trusted = False

    def __init__(self, engine: AgentDesktopEngine | None = None) -> None:
        super().__init__()
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENT_DESKTOP_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(AGENT_DESKTOP_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # AgentDesktopService Protocol Implementation
    # -------------------------------------------------------------------------

    async def snapshot(
        self,
        app: str = "",
        root_ref: str = "",
        interactive_only: bool = True,
        skeleton: bool = False,
        compact: bool = True,
        surface: str = "",
        session: str = "default",
    ) -> AgentDesktopSnapshotResult:
        res = await self._engine.snapshot(
            app=app,
            root_ref=root_ref,
            interactive_only=interactive_only,
            skeleton=skeleton,
            compact=compact,
            surface=surface,
            session=session,
        )
        return AgentDesktopSnapshotResult(**res)

    async def act(
        self,
        action: str,
        ref_id: str,
        value: str = "",
        headed: bool = False,
        interval_ms: int | None = None,
        session: str = "default",
    ) -> AgentDesktopActResult:
        res = await self._engine.act(
            action=action,
            ref_id=ref_id,
            value=value,
            headed=headed,
            interval_ms=interval_ms,
            session=session,
        )
        return AgentDesktopActResult(**res)

    async def find(
        self,
        app: str = "",
        role: str = "",
        name: str = "",
        text: str = "",
        session: str = "default",
    ) -> AgentDesktopSnapshotResult:
        res = await self._engine.find(
            app=app,
            role=role,
            name=name,
            text=text,
            session=session,
        )
        return AgentDesktopSnapshotResult(**res)

    async def manage_window(
        self,
        operation: str,
        app: str = "",
        window_id: str = "",
        bounds: dict[str, int] | None = None,
    ) -> AgentDesktopWindowResult:
        res = await self._engine.manage_window(
            operation=operation,
            app=app,
            window_id=window_id,
            bounds=bounds,
        )
        return AgentDesktopWindowResult(**res)

    async def wait_for(
        self,
        app: str = "",
        element_ref: str = "",
        window_title: str = "",
        text: str = "",
        timeout_ms: int = 5000,
    ) -> dict[str, Any]:
        return await self._engine.wait_for(
            app=app,
            element_ref=element_ref,
            window_title=window_title,
            text=text,
            timeout_ms=timeout_ms,
        )

    async def get_status(
        self,
        check_permissions: bool = True,
    ) -> AgentDesktopStatusResult:
        res = await self._engine.get_status(check_permissions=check_permissions)
        return AgentDesktopStatusResult(**res)


# Export module-level singleton per Rule 45
plugin = AgentDesktopPlugin()
