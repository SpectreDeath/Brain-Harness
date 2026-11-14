"""Top-level unit & contract tests for ShimHarnessGovernorEngine."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services import (
    AGENTS_MD_MAX_BYTES,
    FILE_READ_MAX_BYTES,
    FILE_READ_MAX_LINES,
    SHIM_HARNESS_GOVERNOR_KEY,
    SHELL_OUTPUT_MAX_BYTES,
    SKILL_MAX_BYTES,
    ShimHarnessGovernorEngine,
    ShimHarnessGovernorProtocol,
)


def test_tool_security_modes_schema_and_containment(tmp_path: Path) -> None:
    engine = ShimHarnessGovernorEngine()
    ws = tmp_path / "ws"
    ws.mkdir()

    # read-only permits read inside workspace with closed schema
    ok = engine.audit_tool_execution(
        permission_mode="read-only",
        tool_level="read",
        workspace_root=ws,
        target_path="sub/new_file.txt",
        tool_schema={"type": "object", "additionalProperties": False},
        file_bytes=1024,
        line_count=50,
    )
    assert ok.allowed is True
    assert ok.within_workspace is True
    assert ok.schema_closed is True

    # read-only denies write
    denied = engine.audit_tool_execution(
        permission_mode="read-only",
        tool_level="write",
        workspace_root=ws,
        target_path="file.txt",
    )
    assert denied.allowed is False
    assert any("read-only mode denies" in v for v in denied.violations)

    # ask requires confirmation for non-read tools
    unconfirmed = engine.audit_tool_execution(
        permission_mode="ask",
        tool_level="shell",
        workspace_root=ws,
        target_path=".",
        confirmed=False,
    )
    assert unconfirmed.allowed is False
    assert unconfirmed.requires_confirmation is True

    confirmed = engine.audit_tool_execution(
        permission_mode="ask",
        tool_level="shell",
        workspace_root=ws,
        target_path=".",
        confirmed=True,
    )
    assert confirmed.allowed is True

    # Traversal escape + oversized read + open schema + NUL byte + shell cap
    escaped = engine.audit_tool_execution(
        permission_mode="auto",
        tool_level="read",
        workspace_root=ws,
        target_path="../secret.txt",
        tool_schema={"type": "object", "additionalProperties": True},
        file_bytes=FILE_READ_MAX_BYTES + 1,
        line_count=FILE_READ_MAX_LINES + 1,
        has_nul_bytes=True,
        shell_output_bytes=SHELL_OUTPUT_MAX_BYTES + 1,
    )
    assert escaped.allowed is False
    assert escaped.within_workspace is False
    assert escaped.schema_closed is False
    assert escaped.file_size_ok is False
    assert escaped.line_count_ok is False
    assert len(escaped.violations) >= 5


def test_frozen_report_immutability_rule43(tmp_path: Path) -> None:
    engine = ShimHarnessGovernorEngine()
    report = engine.audit_tool_execution("auto", "read", tmp_path, "a.py")
    with pytest.raises((AttributeError, TypeError)):
        report.allowed = False  # type: ignore[misc]


def test_deterministic_first_and_allowlisted_router() -> None:
    engine = ShimHarnessGovernorEngine()

    det = engine.route_command("use model gpt-4o")
    assert det.matched_deterministically is True
    assert det.resolved_command == "/model use gpt-4o"
    assert det.allowlisted is True
    assert det.mutating is True

    ro = engine.route_command("list mcps")
    assert ro.matched_deterministically is True
    assert ro.resolved_command == "/mcps"
    assert ro.allowlisted is True
    assert ro.mutating is False

    compiled_ok = engine.route_command(
        "show details for python skill",
        llm_compiled_command="```\n/skill show python-dataclass-architect\n```",
    )
    assert compiled_ok.matched_deterministically is False
    assert compiled_ok.allowlisted is True
    assert compiled_ok.mutating is False

    bad = engine.route_command("wipe disk", llm_compiled_command="/rm -rf /", compiler_max_tokens=500)
    assert bad.allowlisted is False
    assert len(bad.reasons) >= 2


def test_mcp_namespacing_collision_and_config_env_indirection() -> None:
    engine = ShimHarnessGovernorEngine()
    clean = engine.audit_mcp_and_discovery(
        server_name="fs.local",
        tool_names=["read file", "write file"],
        config_payload={"version": 1, "permissions": "ask", "api": "anthropic", "api_key_env": "ANTHROPIC_API_KEY"},
        discovered_endpoints=["ollama:http://127.0.0.1:11434", "lmstudio:http://127.0.0.1:1234"],
    )
    assert clean.collisions == ()
    assert clean.violations == ()
    assert clean.normalized_tools == ("mcp_fs_local_read_file", "mcp_fs_local_write_file")
    assert clean.discovered_endpoints == ("lmstudio:http://127.0.0.1:1234", "ollama:http://127.0.0.1:11434")

    colliding = engine.audit_mcp_and_discovery(
        server_name="srv",
        tool_names=["a:b", "a/b"],
        init_timeout_seconds=45.0,
        config_payload={"version": 1, "api_key": "sk-secret", "permissions": "ask", "api": "openai"},
        discovery_timeout_ms=1500,
    )
    assert len(colliding.collisions) == 1
    assert colliding.uses_env_key_only is False
    assert len(colliding.violations) >= 4


def test_session_ids_and_four_tier_skill_precedence() -> None:
    engine = ShimHarnessGovernorEngine()
    report = engine.audit_session_and_skills(
        session_id="20261114-133500-a1b2c3d4",
        agents_md_bytes=AGENTS_MD_MAX_BYTES + 128,
        skill_candidates=[
            {"name": "alpha", "tier": "global", "size_bytes": 512, "has_closed_frontmatter": True},
            {"name": "alpha", "tier": ".agents/skills", "size_bytes": 512, "has_closed_frontmatter": True},
            {"name": "alpha", "tier": ".claude/skills", "size_bytes": 512, "has_closed_frontmatter": True},
            {
                "name": "too-big",
                "tier": ".shim/skills",
                "size_bytes": SKILL_MAX_BYTES + 1,
                "has_closed_frontmatter": True,
            },
            {"name": "broken-fm", "tier": ".shim/skills", "size_bytes": 256, "has_closed_frontmatter": False},
        ],
    )
    assert report.session_id_valid is True
    assert report.agents_md_truncated is True
    assert report.winning_skills == ("alpha@.claude/skills",)
    assert set(report.rejected_skills) == {"too-big", "broken-fm"}
    assert report.total_skill_files == 5

    invalid = engine.audit_session_and_skills(session_id="../escape", dir_mode=0o755, max_agent_steps=99)
    assert invalid.session_id_valid is False
    assert len(invalid.reasons) >= 3


def test_ioc_context_registration() -> None:
    ctx = ServiceContext()
    engine = ShimHarnessGovernorEngine()
    ctx.provide(SHIM_HARNESS_GOVERNOR_KEY, engine, provider="unit")
    assert isinstance(ctx.require(SHIM_HARNESS_GOVERNOR_KEY), ShimHarnessGovernorProtocol)
