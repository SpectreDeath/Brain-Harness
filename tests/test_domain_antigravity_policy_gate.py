"""Tests for Antigravity Policy Gate Plugin and Declarative Policy Engine."""

from __future__ import annotations

import pytest
from plugins.security_and_forensics.antigravity_policy_gate.service import (
    AntigravityPolicyService,
    AntigravityPolicyGatePlugin,
    ANTIGRAVITY_POLICY_KEY,
    Decision,
)
from harness.kernel.context import ServiceContext


@pytest.mark.unit
class TestAntigravityPolicyGate:
    def test_default_permissive_evaluation(self) -> None:
        service = AntigravityPolicyService()
        decision, rationale = service.evaluate("view_file", {"AbsolutePath": "/workspace/file.py"})
        assert decision == Decision.ALLOW
        assert "Default" in rationale

    def test_deny_rule_evaluation(self) -> None:
        service = AntigravityPolicyService()
        service.add_rule(
            tool_pattern=r"run_command",
            decision=Decision.DENY,
            arg_patterns={"CommandLine": r"rm\s+-rf"},
            rationale="Disallow destructive deletion",
        )

        decision, rationale = service.evaluate("run_command", {"CommandLine": "rm -rf /root"})
        assert decision == Decision.DENY
        assert "destructive" in rationale

        # Permissive command passes
        decision, _ = service.evaluate("run_command", {"CommandLine": "ls -la"})
        assert decision == Decision.ALLOW

    def test_ask_user_rule_evaluation(self) -> None:
        service = AntigravityPolicyService()
        service.add_rule(
            tool_pattern=r"run_command",
            decision=Decision.ASK_USER,
            arg_patterns={"CommandLine": r"git\s+push\s+--force"},
            rationale="Confirm force push",
        )

        decision, rationale = service.evaluate("run_command", {"CommandLine": "git push --force origin main"})
        assert decision == Decision.ASK_USER
        assert "Confirm" in rationale

    def test_audit_trail_logging(self) -> None:
        service = AntigravityPolicyService()
        service.evaluate("list_dir", {"DirectoryPath": "/tmp"})
        service.evaluate("run_command", {"CommandLine": "echo hello"})

        audit = service.get_audit_trail()
        assert len(audit) == 2
        assert audit[0]["tool"] == "list_dir"
        assert audit[1]["tool"] == "run_command"

    @pytest.mark.asyncio
    async def test_plugin_ioc_and_safety_baseline(self) -> None:
        plugin = AntigravityPolicyGatePlugin()
        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(ANTIGRAVITY_POLICY_KEY)
        decision, _ = service.evaluate("run_command", {"CommandLine": "rm -rf /"})
        assert decision == Decision.DENY

        decision, _ = service.evaluate("run_command", {"CommandLine": "git push --force"})
        assert decision == Decision.ASK_USER
