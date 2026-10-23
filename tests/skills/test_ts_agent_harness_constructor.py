"""Contract verification test suite for ts-agent-harness-constructor skill.

Tests slotted domain models, construction assertions, atomic batch budgeting,
workspace confinement, context windowing, TypeScript scaffolding, and skill hygiene.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Prepend skill scripts directory to sys.path per Rule 50 & 57
workspace_root = Path(__file__).parents[2]
skill_scripts = (
    workspace_root
    / ".agents"
    / "skills"
    / "ts-agent-harness-constructor"
    / "scripts"
)
sys.path.insert(0, str(skill_scripts))
sys.path.insert(0, str(workspace_root / "src"))
sys.path.insert(0, str(workspace_root))

from harness.creator.skills import SkillValidator
from ts_harness_constructor import cli
from ts_harness_engine import (
    AtomicBudgetEvaluator,
    BatchBudgetVerdict,
    BudgetVerdictStatus,
    CommandPresetDefinition,
    ContextTurnGroup,
    ContextWindowManager,
    ContextWindowPlan,
    DiagnosticAuditReport,
    ErrorBifurcationMode,
    HarnessBudgetConfig,
    ObserverDispatchResult,
    PRNGBatchSimulator,
    ToolContractDefinition,
    TypeScriptHarnessScaffolder,
    WorkspaceSandboxPolicy,
)


# ---------------------------------------------------------------------------
# 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


def test_harness_budget_config_immutability() -> None:
    """Verify HarnessBudgetConfig is slotted and strictly immutable (Rule 12 & 43)."""
    cfg = HarnessBudgetConfig(max_steps=20, max_tool_calls=50)
    assert cfg.max_steps == 20
    assert cfg.max_tool_calls == 50

    with pytest.raises((AttributeError, TypeError)):
        cfg.max_steps = 30  # type: ignore


def test_tool_contract_immutability() -> None:
    """Verify ToolContractDefinition is slotted and strictly immutable."""
    tool = ToolContractDefinition(
        name="read_file",
        schema={"properties": {"path": {"type": "string"}}, "required": ["path"]},
    )
    assert tool.name == "read_file"

    with pytest.raises((AttributeError, TypeError)):
        tool.name = "write_file"  # type: ignore


def test_command_preset_immutability() -> None:
    """Verify CommandPresetDefinition is slotted and immutable."""
    preset = CommandPresetDefinition(
        name="test",
        executable="npm",
        args=("test", "--silent"),
        timeout_ms=5000,
        shell=False,
    )
    assert preset.name == "test"
    assert preset.shell is False

    with pytest.raises((AttributeError, TypeError)):
        preset.shell = True  # type: ignore


def test_batch_budget_verdict_immutability() -> None:
    """Verify BatchBudgetVerdict is slotted and immutable."""
    verdict = BatchBudgetVerdict(
        batch_size=3,
        remaining_budget=10,
        admitted=True,
        unanswered_calls_count=0,
        status=BudgetVerdictStatus.ADMITTED,
    )
    assert verdict.admitted is True

    with pytest.raises((AttributeError, TypeError)):
        verdict.admitted = False  # type: ignore


# ---------------------------------------------------------------------------
# 2. Construction Invariants & Mathematical Assertions
# ---------------------------------------------------------------------------


def test_budget_config_construction_assertions() -> None:
    """Assert non-positive budgets are rejected during construction."""
    with pytest.raises(AssertionError, match="max_steps must be a positive integer"):
        HarnessBudgetConfig(max_steps=0)

    with pytest.raises(AssertionError, match="max_tool_calls must be a positive integer"):
        HarnessBudgetConfig(max_tool_calls=-5)


def test_tool_contract_name_validation() -> None:
    """Assert invalid tool names are rejected during construction."""
    with pytest.raises(AssertionError, match="Invalid tool name"):
        ToolContractDefinition(name="123-invalid", schema={})

    with pytest.raises(AssertionError, match="Invalid tool name"):
        ToolContractDefinition(name="has space", schema={})

    # Valid names
    t1 = ToolContractDefinition(name="read_file", schema={})
    assert t1.name == "read_file"
    t2 = ToolContractDefinition(name="executeCommand", schema={})
    assert t2.name == "executeCommand"


def test_command_preset_shell_rejection() -> None:
    """Assert command presets reject shell=True (shell injection defense)."""
    with pytest.raises(AssertionError, match="shell=False"):
        CommandPresetDefinition(name="test", executable="node", shell=True)  # type: ignore


# ---------------------------------------------------------------------------
# 3. Tool Schema Validation & Error Bifurcation
# ---------------------------------------------------------------------------


def test_tool_schema_validation() -> None:
    """Test schema validator against JSON Schema subset."""
    tool = ToolContractDefinition(
        name="fetch_url",
        schema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "retries": {"type": "integer"},
                "mode": {"enum": ["fast", "deep"]},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    )

    # Valid arguments
    valid, err = tool.validate_args({"url": "https://example.com", "retries": 3, "mode": "fast"})
    assert valid is True
    assert err is None

    # Missing required field
    valid, err = tool.validate_args({"retries": 2})
    assert valid is False
    assert "Missing required property: $.url" in err

    # Unexpected additional property
    valid, err = tool.validate_args({"url": "https://example.com", "extra": 123})
    assert valid is False
    assert "Unexpected additional property: $.extra" in err

    # Wrong type
    valid, err = tool.validate_args({"url": 12345})
    assert valid is False
    assert "Property $.url must be a string" in err

    # Enum violation
    valid, err = tool.validate_args({"url": "https://example.com", "mode": "unsupported"})
    assert valid is False
    assert "not in allowed enum" in err


# ---------------------------------------------------------------------------
# 4. Workspace Sandboxing & Ancestor Symlink Traversal
# ---------------------------------------------------------------------------


def test_workspace_lexical_confinement(tmp_path: Path) -> None:
    """Test that path traversal attempts are rejected."""
    workspace = WorkspaceSandboxPolicy(root=tmp_path)

    # Normal relative path
    valid, err = workspace.validate_path("src/index.ts")
    assert valid is True

    # Escape attempt via dot-dot
    valid, err = workspace.validate_path("../../etc/passwd")
    assert valid is False
    assert "Path traversal escape detected" in err


def test_workspace_ancestor_symlink_rejection(tmp_path: Path) -> None:
    """Test that symlinks in parent directories are detected and rejected."""
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    # Create a symlinked directory inside workspace pointing outside
    sym_dir = ws_root / "linked_parent"
    try:
        sym_dir.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not supported in this test environment")

    workspace = WorkspaceSandboxPolicy(root=ws_root, allow_ancestor_symlinks=False)
    valid, err = workspace.validate_path("linked_parent/secret.txt")
    assert valid is False
    assert "Ancestor directory is a symbolic link" in err


# ---------------------------------------------------------------------------
# 5. Atomic Batch Budget Invariant & Seeded PRNG Simulation
# ---------------------------------------------------------------------------


def test_atomic_batch_budget_evaluator() -> None:
    """Test atomic batch budget evaluation before transcript mutation."""
    # Scenario A: Batch fits within budget
    verdict = AtomicBudgetEvaluator.evaluate_batch(
        batch_size=3, cumulative_calls=10, max_tool_calls=15
    )
    assert verdict.admitted is True
    assert verdict.remaining_budget == 2
    assert verdict.unanswered_calls_count == 0
    assert verdict.status == BudgetVerdictStatus.ADMITTED

    # Scenario B: Batch exceeds budget -> rejected atomically with zero unanswered calls
    verdict = AtomicBudgetEvaluator.evaluate_batch(
        batch_size=6, cumulative_calls=12, max_tool_calls=15
    )
    assert verdict.admitted is False
    assert verdict.unanswered_calls_count == 0
    assert verdict.status == BudgetVerdictStatus.TOOL_LIMIT


def test_prng_batch_simulation_150_runs() -> None:
    """Run 150 seeded property tests proving zero-orphan invariant."""
    sim = PRNGBatchSimulator.run_simulation(seed=0x12345678, iterations=150)
    assert sim["iterations"] == 150
    assert sim["zero_orphan_asserted"] is True
    assert sim["success"] is True
    assert sim["admitted_runs"] > 0
    assert sim["rejected_runs"] > 0


# ---------------------------------------------------------------------------
# 6. Context Window Group Indivisibility
# ---------------------------------------------------------------------------


def test_context_window_atomic_grouping() -> None:
    """Verify assistant tool calls and corresponding tool results form indivisible groups."""
    messages = [
        {"role": "user", "content": "Fetch data and calculate"},
        {
            "role": "assistant",
            "tool_calls": [
                {"id": "call_1", "name": "fetch", "arguments": {}},
                {"id": "call_2", "name": "calc", "arguments": {}},
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "data_1"},
        {"role": "tool", "tool_call_id": "call_2", "content": "data_2"},
        {"role": "assistant", "content": "Final result calculated"},
    ]

    plan = ContextWindowManager.select_context(messages, max_chars=10000)
    assert len(plan.retained_groups) == 3
    assert plan.retained_groups[0].turn_type == "prompt"
    assert plan.retained_groups[1].turn_type == "turn"
    assert len(plan.retained_groups[1].messages) == 3  # Assistant + 2 tool results
    assert plan.retained_groups[2].turn_type == "answer"


def test_context_window_orphan_detection() -> None:
    """Verify orphaned tool results throw ValueError."""
    orphaned_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "tool", "tool_call_id": "call_orphan", "content": "orphan"},
    ]
    with pytest.raises(ValueError, match="Orphaned tool result detected"):
        ContextWindowManager.select_context(orphaned_messages, max_chars=5000)


# ---------------------------------------------------------------------------
# 7. TypeScript Harness Scaffolding
# ---------------------------------------------------------------------------


def test_typescript_scaffolder(tmp_path: Path) -> None:
    """Verify all 7 TypeScript harness files are scaffolded with key interfaces."""
    files = TypeScriptHarnessScaffolder.scaffold_all(tmp_path)
    assert len(files) == 7

    assert "runAgent.ts" in files
    assert "model.ts" in files
    assert "tools.ts" in files
    assert "workspace.ts" in files
    assert "budget.ts" in files
    assert "context.ts" in files
    assert "telemetry.ts" in files

    run_agent_code = files["runAgent.ts"].read_text(encoding="utf-8")
    assert "export async function runAgent" in run_agent_code
    assert "telemetry.emit('model_start'" in run_agent_code

    tools_code = files["tools.ts"].read_text(encoding="utf-8")
    assert "export class ToolRegistry" in tools_code

    workspace_code = files["workspace.ts"].read_text(encoding="utf-8")
    assert "export class Workspace" in workspace_code
    assert "fs.realpath" in workspace_code
    assert "fs.lstat" in workspace_code


# ---------------------------------------------------------------------------
# 8. Skill Hygiene & Craft Standards (SkillValidator)
# ---------------------------------------------------------------------------


def test_skill_craft_standards() -> None:
    """Verify ts-agent-harness-constructor passes SkillValidator craft standards."""
    skill_dir = workspace_root / ".agents" / "skills" / "ts-agent-harness-constructor"
    report = SkillValidator.validate(skill_dir)
    assert report.valid is True
    assert len(report.errors) == 0


# ---------------------------------------------------------------------------
# 9. Canonical Knowledge Vault Dual-File Integrity (Rule 40)
# ---------------------------------------------------------------------------


def test_knowledge_item_canonical_dual_files() -> None:
    """Verify Knowledge Vault item exists in canonical dual-file format (Rule 40)."""
    ki_dir = workspace_root / ".harness" / "knowledge" / "ki_koos_typescript_harness_from_scratch"
    assert ki_dir.is_dir()

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"

    assert meta_file.is_file()
    assert summary_file.is_file()

    metadata = json.loads(meta_file.read_text(encoding="utf-8"))
    assert metadata["id"] == "ki_koos_typescript_harness_from_scratch"
    assert metadata["category"] == "agent_orchestration"
    assert "isnad" in metadata
    assert len(metadata["isnad"]["claims"]) >= 5

    summary_text = summary_file.read_text(encoding="utf-8")
    assert "Ground-Truth Mental Models" in summary_text
    assert "Error Bifurcation Model" in summary_text
    assert "Atomic Batch Budget Invariant" in summary_text


# ---------------------------------------------------------------------------
# 10. Headless Click CLI Seam Execution (Rule 10)
# ---------------------------------------------------------------------------


def test_headless_cli_commands(tmp_path: Path) -> None:
    """Verify CLI simulation, audit, and scaffold subcommands."""
    runner = CliRunner()

    # 1. Simulate
    sim_res = runner.invoke(cli, ["simulate", "--runs", "50", "--json"])
    assert sim_res.exit_code == 0
    sim_data = json.loads(sim_res.output)
    assert sim_data["iterations"] == 50
    assert sim_data["zero_orphan_asserted"] is True

    # 2. Scaffold
    scaffold_res = runner.invoke(cli, ["scaffold", "--output-dir", str(tmp_path / "ts-harness"), "--json"])
    assert scaffold_res.exit_code == 0
    scaffold_data = json.loads(scaffold_res.output)
    assert scaffold_data["count"] == 7

    # 3. Audit scaffolded directory
    audit_res = runner.invoke(cli, ["audit", "--target-dir", str(tmp_path / "ts-harness"), "--json"])
    assert audit_res.exit_code == 0
    audit_data = json.loads(audit_res.output)
    assert audit_data["is_compliant"] is True
    assert audit_data["passed_count"] == 9
