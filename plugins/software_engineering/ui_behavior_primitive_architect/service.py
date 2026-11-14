"""Subprocess-isolated service adapter for UI Behavior Primitive Architect."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

from harness.services.ui_behavior_architect import (
    AgentBridgeStepDecision,
    ExpertScopeRoute,
    PrimitiveAuditReport,
    TriModalVerificationReport,
    UIBehaviorArchitectEngine,
    UIBehaviorArchitectProtocol,
)


class DefaultUIBehaviorArchitectService(UIBehaviorArchitectProtocol):
    """Service adapter delegating to UIBehaviorArchitectEngine with Rule 14 subprocess support."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = UIBehaviorArchitectEngine()

    def audit_primitive_definition(
        self,
        name: str,
        *,
        state_keys: tuple[str, ...] = (),
        live_keys: tuple[str, ...] = (),
        controlled_keys: tuple[str, ...] | None = None,
        provided_options: tuple[str, ...] = (),
        api_methods: tuple[str, ...] = (),
        agent_actions: tuple[str, ...] = (),
        has_asleep_predicate: bool = False,
        has_render_as_prop: bool = False,
    ) -> PrimitiveAuditReport:
        return self._engine.audit_primitive_definition(
            name,
            state_keys=state_keys,
            live_keys=live_keys,
            controlled_keys=controlled_keys,
            provided_options=provided_options,
            api_methods=api_methods,
            agent_actions=agent_actions,
            has_asleep_predicate=has_asleep_predicate,
            has_render_as_prop=has_render_as_prop,
        )

    def evaluate_agent_bridge_step(
        self,
        ref: str,
        component: str,
        action: str,
        *,
        available_actions: tuple[str, ...] = (),
        value: Any = None,
        confirm_attr: str | None = None,
        hidden: bool = False,
        secret: bool = False,
        person_approved: bool | None = None,
        tool_name: str = "act",
    ) -> AgentBridgeStepDecision:
        return self._engine.evaluate_agent_bridge_step(
            ref,
            component,
            action,
            available_actions=available_actions,
            value=value,
            confirm_attr=confirm_attr,
            hidden=hidden,
            secret=secret,
            person_approved=person_approved,
            tool_name=tool_name,
        )

    def evaluate_tri_modal_check(
        self,
        pattern: str,
        *,
        aria_violations: tuple[str, ...] = (),
        ssr_globals_accessed: tuple[str, ...] = (),
        ltr_focus: str = "",
        rtl_focus: str = "",
        ltr_state: dict[str, Any] | None = None,
        rtl_state: dict[str, Any] | None = None,
    ) -> TriModalVerificationReport:
        return self._engine.evaluate_tri_modal_check(
            pattern,
            aria_violations=aria_violations,
            ssr_globals_accessed=ssr_globals_accessed,
            ltr_focus=ltr_focus,
            rtl_focus=rtl_focus,
            ltr_state=ltr_state,
            rtl_state=rtl_state,
        )

    def plan_expert_scope(
        self,
        changed_files: tuple[str, ...],
    ) -> tuple[ExpertScopeRoute, ...]:
        return self._engine.plan_expert_scope(changed_files)

    async def run_cli_subprocess(self, args: list[str], *, timeout: float = 30.0) -> dict[str, Any]:
        """Execute the skill CLI script in an isolated subprocess with Rule 14 pipe cleanup."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "ui-behavior-primitive-architect"
            / "scripts"
            / "ui_behavior_architect_engine.py"
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
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
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
