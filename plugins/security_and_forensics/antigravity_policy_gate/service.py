"""Google Antigravity Declarative Policy Gate Service & Plugin Implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


class Decision(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ASK_USER = "ASK_USER"


@dataclass(slots=True)
class PolicyRule:
    tool_name_pattern: str
    decision: Decision
    arg_patterns: dict[str, str] = field(default_factory=dict)
    rationale: str = ""


class AntigravityPolicyService:
    """Authoritative declarative policy evaluation service."""

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []
        self._audit_log: list[dict[str, Any]] = []

    def add_rule(
        self,
        tool_pattern: str,
        decision: Decision,
        arg_patterns: dict[str, str] | None = None,
        rationale: str = "",
    ) -> None:
        """Register a declarative security rule."""
        rule = PolicyRule(
            tool_name_pattern=tool_pattern,
            decision=decision,
            arg_patterns=arg_patterns or {},
            rationale=rationale,
        )
        self._rules.append(rule)

    def evaluate(self, tool_name: str, arguments: dict[str, Any]) -> tuple[Decision, str]:
        """Evaluate incoming tool call against policy rules in registration order."""
        for rule in self._rules:
            if re.match(rule.tool_name_pattern, tool_name):
                # Check arguments
                all_match = True
                for arg_key, pattern in rule.arg_patterns.items():
                    val = str(arguments.get(arg_key, ""))
                    if not re.search(pattern, val):
                        all_match = False
                        break

                if all_match:
                    self._audit_log.append({
                        "tool": tool_name,
                        "args": arguments,
                        "decision": rule.decision.value,
                        "rationale": rule.rationale,
                    })
                    return rule.decision, rule.rationale

        # Default fallback is ALLOW with audit
        self._audit_log.append({
            "tool": tool_name,
            "args": arguments,
            "decision": Decision.ALLOW.value,
            "rationale": "Default permissive rule",
        })
        return Decision.ALLOW, "Default permissive rule"

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Retrieve audit history of evaluated decisions."""
        return list(self._audit_log)


ANTIGRAVITY_POLICY_KEY: ServiceKey[AntigravityPolicyService] = ServiceKey("service.antigravity.policy_gate")


class AntigravityPolicyGatePlugin(HarnessPlugin):
    """In-process Harness plugin providing Antigravity policy evaluation service."""

    name = "antigravity_policy_gate"
    version = "1.0.0"
    description = "Google Antigravity Declarative Policy Gate"
    trusted = True

    def __init__(self) -> None:
        self._service = AntigravityPolicyService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ANTIGRAVITY_POLICY_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(ANTIGRAVITY_POLICY_KEY, self._service)

    async def on_enable(self) -> None:
        # Default safety baseline: deny dangerous shell operations
        self._service.add_rule(
            tool_pattern=r"run_command|bash",
            decision=Decision.DENY,
            arg_patterns={"CommandLine": r"rm\s+-rf\s+/|del\s+/s\s+/q\s+C:\\Windows"},
            rationale="Catastrophic deletion commands blocked",
        )
        self._service.add_rule(
            tool_pattern=r"run_command",
            decision=Decision.ASK_USER,
            arg_patterns={"CommandLine": r"git\s+push\s+--force"},
            rationale="Force push requires interactive human confirmation",
        )

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass
