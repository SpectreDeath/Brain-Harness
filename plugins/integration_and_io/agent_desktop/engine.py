"""Agent Desktop Plugin Engine.

Connects Harness ReAct loops and tools to the underlying AgentDesktopOperatorEngine,
supporting asynchronous CLI execution and simulation fallbacks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Add skill scripts directory to sys.path (Rule 49 & Rule 57)
_SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "agent-desktop-operator" / "scripts"
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from desktop_operator_engine import AgentDesktopOperatorEngine  # type: ignore

logger = structlog.get_logger(__name__)


class AgentDesktopEngine:
    """Plugin engine wrapper around AgentDesktopOperatorEngine."""

    def __init__(self, binary_path: str | None = None) -> None:
        self._operator = AgentDesktopOperatorEngine(binary_path=binary_path)

    @property
    def operator(self) -> AgentDesktopOperatorEngine:
        return self._operator

    async def snapshot(
        self,
        app: str = "",
        root_ref: str = "",
        interactive_only: bool = True,
        skeleton: bool = False,
        compact: bool = True,
        surface: str = "",
        session: str = "default",
    ) -> dict[str, Any]:
        res = await self._operator.snapshot(
            app=app,
            root_ref=root_ref,
            interactive_only=interactive_only,
            skeleton=skeleton,
            compact=compact,
            surface=surface,
            session=session,
        )
        return res.model_dump()

    async def act(
        self,
        action: str,
        ref_id: str,
        value: str = "",
        headed: bool = False,
        interval_ms: int | None = None,
        session: str = "default",
    ) -> dict[str, Any]:
        res = await self._operator.act(
            action=action,
            ref_id=ref_id,
            value=value,
            headed=headed,
            interval_ms=interval_ms,
            session=session,
        )
        return res.model_dump()

    async def find(
        self,
        app: str = "",
        role: str = "",
        name: str = "",
        text: str = "",
        session: str = "default",
    ) -> dict[str, Any]:
        res = await self._operator.find(
            app=app,
            role=role,
            name=name,
            text=text,
            session=session,
        )
        return res.model_dump()

    async def manage_window(
        self,
        operation: str,
        app: str = "",
        window_id: str = "",
        bounds: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        res = await self._operator.manage_window(
            operation=operation,
            app=app,
            window_id=window_id,
            bounds=bounds,
        )
        return res.model_dump()

    async def wait_for(
        self,
        app: str = "",
        element_ref: str = "",
        window_title: str = "",
        text: str = "",
        timeout_ms: int = 5000,
    ) -> dict[str, Any]:
        return await self._operator.wait_for(
            app=app,
            element_ref=element_ref,
            window_title=window_title,
            text=text,
            timeout_ms=timeout_ms,
        )

    async def get_status(
        self,
        check_permissions: bool = True,
    ) -> dict[str, Any]:
        res = await self._operator.get_status(check_permissions=check_permissions)
        return res.model_dump()
