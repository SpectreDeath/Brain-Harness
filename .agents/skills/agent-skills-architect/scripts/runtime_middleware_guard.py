#!/usr/bin/env python3
"""
Enterprise Agent Skill Runtime Security & Tool Approval Middleware Guard.
Operationalizes the Microsoft Agent Framework & Google Cloud security standards:
- Defense-in-depth tool call interception
- Auto-approval for read-only inspection tools (load_skill, read_skill_resource)
- Gated approval / sandbox policy for mutating scripts (run_skill_script)
- Dynamic Dependency Injection (IServiceProvider) and runtime kwargs forwarding
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any, Callable

# Rule 23: UTF-8 Stream Codec Entrypoint
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class ToolRiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"      # Safe to auto-approve (e.g. load_skill, read_skill_resource)
    MUTATING = "MUTATING"        # Modifies system state or runs code (e.g. run_skill_script)
    RESTRICTED = "RESTRICTED"    # Network, credentials, or file deletion


@dataclass(slots=True, frozen=True)
class ToolCall:
    """Represents an intercepted agent tool invocation request."""
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    risk_level: ToolRiskLevel = ToolRiskLevel.MUTATING

    def __post_init__(self) -> None:
        assert self.tool_name, "tool_name must not be empty"


@dataclass(slots=True, frozen=True)
class ApprovalDecision:
    """Evaluation result from ToolApprovalMiddleware."""
    approved: bool
    requires_user_prompt: bool
    reason: str
    sandboxed: bool = False


@dataclass(slots=True, frozen=True)
class RuntimeSecurityContext:
    """Context container providing DI application services and runtime kwargs."""
    services: dict[str, Any] = field(default_factory=dict)
    function_invocation_kwargs: dict[str, Any] = field(default_factory=dict)
    auto_approve_read_only: bool = True
    trusted_skills: tuple[str, ...] = ("agent-skills-architect", "crafting-skills")


class ToolApprovalMiddleware:
    """Middleware enforcing tool approval policies and runtime context injection."""

    # Standard read-only skill tools defined in agentskills.io
    READ_ONLY_TOOLS = frozenset({"load_skill", "read_skill_resource", "list_skills", "get_skill_info"})
    MUTATING_SCRIPT_TOOLS = frozenset({"run_skill_script", "execute_command", "run_script"})

    def __init__(
        self,
        approval_callback: Callable[[ToolCall], bool] | None = None,
        sandbox_enabled: bool = True,
    ) -> None:
        self._approval_callback = approval_callback
        self._sandbox_enabled = sandbox_enabled

    def classify_tool(self, tool_name: str) -> ToolRiskLevel:
        """Classify tool risk level based on standard tool registries."""
        if tool_name in self.READ_ONLY_TOOLS:
            return ToolRiskLevel.READ_ONLY
        elif tool_name in self.MUTATING_SCRIPT_TOOLS:
            return ToolRiskLevel.MUTATING
        return ToolRiskLevel.RESTRICTED

    def intercept(self, tool_call: ToolCall, ctx: RuntimeSecurityContext) -> ApprovalDecision:
        """Evaluate whether a tool invocation is permitted, gated, or rejected."""
        risk = tool_call.risk_level or self.classify_tool(tool_call.tool_name)

        # 1. Auto-approve read-only inspection tools
        if risk == ToolRiskLevel.READ_ONLY and ctx.auto_approve_read_only:
            return ApprovalDecision(
                approved=True,
                requires_user_prompt=False,
                reason="Auto-approved: tool is classified as read-only inspection.",
                sandboxed=False,
            )

        # 2. Check if the tool belongs to an explicitly trusted skill
        skill_name = tool_call.arguments.get("skill_name") or tool_call.arguments.get("skill")
        if skill_name and skill_name in ctx.trusted_skills:
            if self._sandbox_enabled:
                return ApprovalDecision(
                    approved=True,
                    requires_user_prompt=False,
                    reason=f"Approved: skill '{skill_name}' is trusted; executing inside isolated sandbox.",
                    sandboxed=True,
                )

        # 3. If explicit approval callback provided, query it
        if self._approval_callback is not None:
            user_approved = self._approval_callback(tool_call)
            return ApprovalDecision(
                approved=user_approved,
                requires_user_prompt=True,
                reason="User approval callback evaluated.",
                sandboxed=self._sandbox_enabled,
            )

        # 4. By default, mutating scripts require explicit human consent
        return ApprovalDecision(
            approved=False,
            requires_user_prompt=True,
            reason="Gated: mutating script calls require explicit user confirmation or sandboxing.",
            sandboxed=self._sandbox_enabled,
        )

    def inject_runtime_context(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        ctx: RuntimeSecurityContext,
    ) -> dict[str, Any]:
        """Inject application services and runtime kwargs into tool call parameters."""
        augmented_args = dict(arguments)
        
        # Inject DI services if requested by the tool
        if "services" not in augmented_args and ctx.services:
            augmented_args["__services__"] = ctx.services

        # Forward runtime keyword arguments
        for k, v in ctx.function_invocation_kwargs.items():
            if k not in augmented_args:
                augmented_args[k] = v

        return augmented_args


def main() -> None:
    parser = argparse.ArgumentParser(description="Demonstrate Runtime Tool Approval Middleware.")
    parser.add_argument("--tool", default="run_skill_script", help="Tool name to evaluate")
    parser.add_argument("--skill", default="custom-skill", help="Target skill name")
    parser.add_argument("--auto-approve-readonly", action="store_true", default=True, help="Auto approve read-only tools")
    args = parser.parse_args()

    middleware = ToolApprovalMiddleware(sandbox_enabled=True)
    ctx = RuntimeSecurityContext(auto_approve_read_only=args.auto_approve_readonly)
    
    risk = middleware.classify_tool(args.tool)
    tool_call = ToolCall(tool_name=args.tool, arguments={"skill_name": args.skill}, risk_level=risk)
    decision = middleware.intercept(tool_call, ctx)

    print("=" * 64)
    print("TOOL APPROVAL MIDDLEWARE EVALUATION")
    print("=" * 64)
    print(f"Tool Name:            {tool_call.tool_name}")
    print(f"Risk Level:           {risk.value}")
    print(f"Approved:             {decision.approved}")
    print(f"Requires User Prompt: {decision.requires_user_prompt}")
    print(f"Sandboxed:            {decision.sandboxed}")
    print(f"Reason:               {decision.reason}")
    print("=" * 64)


if __name__ == "__main__":
    main()
