"""Test suite for Claude Code Bridge plugin and service."""

from harness.kernel.context import ServiceContext
from harness.services.claude_code import (
    CLAUDE_CODE_BRIDGE_KEY,
    ClaudeCodeBridgeService,
    PromptCompactionResult,
)
from plugins.agent_orchestration.claude_code_bridge.main import (
    ClaudeCodeBridgePlugin,
    plugin,
)


def test_plugin_singleton_and_manifest():
    assert isinstance(plugin, ClaudeCodeBridgePlugin)
    assert plugin.name == "plugin.claude_code_bridge"
    assert CLAUDE_CODE_BRIDGE_KEY in plugin.provides


def test_ioc_registration():
    ctx = ServiceContext()
    p = ClaudeCodeBridgePlugin()
    p.on_load(ctx)

    service = ctx.require(CLAUDE_CODE_BRIDGE_KEY)
    assert isinstance(service, ClaudeCodeBridgeService)


def test_bash_guardrails_evaluation():
    p = ClaudeCodeBridgePlugin()

    # Dangerous commands
    res_push = p.evaluate_bash_guardrails("git push origin main --force")
    assert res_push.is_dangerous is True
    assert res_push.risk_level == "blocked"

    res_reset = p.evaluate_bash_guardrails("git reset --hard HEAD~1")
    assert res_reset.is_dangerous is True
    assert res_reset.risk_level == "blocked"

    res_clean = p.evaluate_bash_guardrails("git clean -fd")
    assert res_clean.is_dangerous is True
    assert res_clean.risk_level == "blocked"

    # Medium risk command
    res_del_branch = p.evaluate_bash_guardrails("git branch -D feature-branch")
    assert res_del_branch.is_dangerous is False
    assert res_del_branch.risk_level == "medium"

    # Safe command
    res_status = p.evaluate_bash_guardrails("git status -s")
    assert res_status.is_dangerous is False
    assert res_status.risk_level == "safe"


def test_prompt_compaction():
    p = ClaudeCodeBridgePlugin()

    # Repeated lines
    text = "line1\nline1\nline1\nline2\nline3"
    res = p.compact_prompt(text, max_lines=10)
    assert isinstance(res, PromptCompactionResult)
    assert res.compacted_text == "line1\nline2\nline3"

    # Long text folding
    long_text = "\n".join([f"line_{i}" for i in range(100)])
    res_fold = p.compact_prompt(long_text, max_lines=20)
    assert "lines folded for context efficiency" in res_fold.compacted_text
    assert res_fold.reduction_pct > 0.0
