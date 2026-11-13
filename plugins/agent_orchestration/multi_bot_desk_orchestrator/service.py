"""Subprocess-isolated service implementation for Multi-Bot Desk Orchestrator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from harness.services.multi_bot_desk import (
    BotDeskLease,
    BotHopDispatchOutcome,
    BotHopDispatchRequest,
    McpApprovalOutcome,
    McpApprovalRequest,
    MultiBotDeskEngine,
    MultiBotDeskProtocol,
)


class DefaultMultiBotDeskService(MultiBotDeskProtocol):
    """Service adapter delegating to MultiBotDeskEngine with Rule 14 subprocess runner support."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = MultiBotDeskEngine()

    def evaluate_bot_hop_dispatch(
        self, request: BotHopDispatchRequest
    ) -> BotHopDispatchOutcome:
        return self._engine.evaluate_bot_hop_dispatch(request)

    def evaluate_mcp_tool_approval(
        self, request: McpApprovalRequest
    ) -> McpApprovalOutcome:
        return self._engine.evaluate_mcp_tool_approval(request)

    def allocate_bot_desk_lease(
        self,
        bot_id: str,
        *,
        is_primary: bool = False,
        occupied_displays: tuple[int, ...] = (),
    ) -> BotDeskLease:
        return self._engine.allocate_bot_desk_lease(
            bot_id,
            is_primary=is_primary,
            occupied_displays=occupied_displays,
        )

    async def run_cli_subprocess(
        self, args: list[str], *, timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute the skill CLI script in an isolated subprocess with Rule 14 pipe cleanup."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "multi-bot-desk-orchestrator"
            / "scripts"
            / "multi_bot_desk_engine.py"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                close_fn = getattr(pipe, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        pass
