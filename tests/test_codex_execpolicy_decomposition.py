"""Contract verification test suite for Codex ExecPolicy Decomposition (Cycle 44).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted dataclass contracts on PrefixRule, slotted & frozen on AstToken (Rule 12 & Rule 43).
3. 100% backward-compatible facade re-exports across codex_execpolicy.
4. Typed service key EXEC_POLICY_KEY (Rule 2).
5. Module singleton plugin export (Rule 45).
6. AST tokenization, bash subshell parsing, and policy evaluation.
7. Prefix rule amendment and sandbox requirement checks.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.kimi_bridge import BashAstNode
from plugins.security_and_forensics.codex_execpolicy.main import (
    AstToken,
    CodexExecPolicyPlugin,
    CodexExecPolicyService,
    EXEC_POLICY_KEY,
    PrefixRule,
    amend_prefix_rule,
    check_sandbox_requirements,
    evaluate_command_policy,
    get_active_rules,
    parse_bash_ast,
    plugin,
    reset_active_rules,
    tokenize_shell_ast,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestCodexExecPolicyDecompositionArchitecture:
    """Architectural and structural invariants for codex_execpolicy subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = (
            Path(__file__).parent.parent
            / "plugins"
            / "security_and_forensics"
            / "codex_execpolicy"
        )
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        # Check main.py
        main_py = pkg_dir / "main.py"
        assert main_py.is_file()
        main_lines = len(main_py.read_text(encoding="utf-8").splitlines())
        assert main_lines <= 200, f"main.py has {main_lines} lines (> 200)"

        engine_dir = pkg_dir / "engine"
        assert engine_dir.is_dir()

        expected_engine_modules = {
            "__init__.py",
            "models.py",
            "ast_core.py",
            "tokenizer.py",
            "ast_parser.py",
            "rules.py",
            "evaluator.py",
            "sandbox.py",
            "service.py",
        }

        found_modules = {p.name for p in engine_dir.glob("*.py")}
        assert expected_engine_modules.issubset(found_modules)

        for mod_name in expected_engine_modules:
            mod_path = engine_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_and_frozen_dataclass_invariants(self) -> None:
        """Rule 12 & Rule 43: PrefixRule slotted; AstToken slotted and frozen."""
        rule = PrefixRule(pattern=["git", "commit"], action="allow", comment="safe")
        assert hasattr(rule, "__slots__")
        assert not hasattr(rule, "__dict__")

        token = AstToken(raw="curl", is_operator=False, is_redirection=False)
        assert hasattr(token, "__slots__")
        assert not hasattr(token, "__dict__")

        # Verify immutability of frozen dataclass (Rule 43: direct attribute assignment raises)
        with pytest.raises((AttributeError, TypeError)):
            token.raw = "wget"

    def test_typed_service_key_and_plugin_singleton(self) -> None:
        """Rule 2 & Rule 45: EXEC_POLICY_KEY must be typed ServiceKey, and plugin must be singleton."""
        assert isinstance(EXEC_POLICY_KEY, ServiceKey)
        assert EXEC_POLICY_KEY.name == "security.codex_execpolicy"

        assert isinstance(plugin, CodexExecPolicyPlugin)
        assert EXEC_POLICY_KEY in plugin.provides

    def test_ast_tokenization_and_bash_subshell_extraction(self) -> None:
        """Verify AST decomposition tokenizer and parser functions."""
        cmd = "echo $(whoami) && cat `pwd`/test.txt"
        tokens = tokenize_shell_ast(cmd)
        assert tokens["status"] == "ok"
        assert tokens["is_compound"] is True
        assert "&&" in tokens["operators"]

        ast = parse_bash_ast("echo $(whoami)")
        assert isinstance(ast, BashAstNode)
        assert len(ast.children) >= 1
        assert any(c.node_type == "subshell" for c in ast.children)

    def test_policy_evaluator_and_rule_amendment(self) -> None:
        """Verify policy evaluation, default allow/deny, and runtime amendment."""
        try:
            reset_active_rules()
            res_safe = evaluate_command_policy("git status")
            assert res_safe["decision"] == "allow"

            res_deny = evaluate_command_policy("rm -rf /")
            assert res_deny["decision"] == "deny"

            # Initially an unknown tool requires prompt
            res_before = evaluate_command_policy("mycustomtool run")
            assert res_before["decision"] == "prompt"

            # Amend prefix rule to allow
            amend_res = amend_prefix_rule("mycustomtool run", "allow", comment="Allowed internal tool")
            assert amend_res["status"] == "ok"

            res_after = evaluate_command_policy("mycustomtool run --fast")
            assert res_after["decision"] == "allow"

            active = get_active_rules()
            assert any(r.pattern == ["mycustomtool", "run"] for r in active)
        finally:
            reset_active_rules()

    def test_sandbox_requirements(self) -> None:
        """Verify sandbox requirements checker."""
        reqs = check_sandbox_requirements("cargo build", target_platform="linux")
        assert reqs["sandbox_type"] == "linux_landlock_bwrap"
        assert reqs["requires_sandbox"] is True
        assert "." in reqs["recommended_write_paths"]

    @pytest.mark.asyncio
    async def test_ioc_lifecycle_and_service_execution(self) -> None:
        """Verify plugin lifecycle in IoC container."""
        ctx = ServiceContext()
        p = CodexExecPolicyPlugin()
        await p.on_enable(ctx)

        assert ctx.has(EXEC_POLICY_KEY)
        service = ctx.require(EXEC_POLICY_KEY)
        assert isinstance(service, CodexExecPolicyService)

        decision = service.evaluate("ls -la")
        assert decision["decision"] == "allow"

        ast_node = service.parse_ast("cat file.txt | grep match")
        assert ast_node.node_type == "pipeline"

        await p.on_disable(ctx)
