"""Hermetic execution trial for Rank #1 emergent macro-capability: cap_context_anti_rot_governance.

Trial Specification (Brief 1 §1.5):
1. Step 1 (Pre-Audit & Triage): codebase-context-governor (ContextGovernor.run_govern)
2. Step 2 (Anti-Rot Prune & Rule 11 Enforcement): context-anti-rot-sync + agent-instruction-architect
3. Step 3 (Downstream SSOT Synchronization): codebase-context-architect (ContextSynchronizer.run_sync)
4. Step 4 (CI Linter & Post-Governance Gate): ContextLinter.run_lint + ContextGovernor.run_govern
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.services.codebase_context.governor import ContextGovernor
from harness.services.codebase_context.linter import ContextLinter
from harness.services.codebase_context.synchronizer import ContextSynchronizer

# Import context sync engine from the skill script
import sys
skill_scripts = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "context-anti-rot-sync" / "scripts"
if str(skill_scripts) not in sys.path:
    sys.path.insert(0, str(skill_scripts))
from context_sync_engine import ContextSyncEngine


@pytest.mark.unit
def test_cap_context_anti_rot_governance_trial(tmp_path: Path) -> None:
    """Execute end-to-end hermetic trial for cap_context_anti_rot_governance in tmp_path."""
    repo_dir = tmp_path / "trial_repo"
    repo_dir.mkdir(parents=True)

    # -------------------------------------------------------------------------
    # Fixture Setup: Seeded repository with deliberate context rot & defects
    # -------------------------------------------------------------------------
    # 1. src/app.py (valid empty module)
    src_dir = repo_dir / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "app.py").write_text('"""App module."""\n', encoding="utf-8")

    # 2. package.json defining {"scripts": {"test": "pytest"}}
    pkg_json = {"name": "trial-repo", "scripts": {"test": "pytest"}}
    (repo_dir / "package.json").write_text(json.dumps(pkg_json, indent=2), encoding="utf-8")

    # 3. docs/guide.md mentioning a non-existent script: `npm run build`
    docs_dir = repo_dir / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "guide.md").write_text(
        "# Developer Guide\n\nRun `npm run build` to compile assets.\n",
        encoding="utf-8",
    )

    # 4. AGENTS.md: 155 lines (> 150 budget), 1 lint leakage line, 1 valid path `src/app.py`, 1 broken path `src/ghost_module.py`
    agents_lines = [
        "# Constitution and Guidelines",
        "",
        "## Execution Seams",
        "- Run tests via `pytest`",
        "",
        "## Negative Boundaries",
        "- Do not touch production credentials or sensitive env files.",
        "",
        "## Path References",
        "- Reference valid: `src/app.py`",
        "- Reference broken: `src/ghost_module.py`",
        "",
        "## Lint Leakage",
        "ERROR: E501 line too long in compiler output",
        "",
        "## Additional Rules",
    ]
    # Pad to exactly 155 lines with consecutive blank lines (demonstrating whitespace rot)
    while len(agents_lines) < 150:
        agents_lines.append(f"- Rule {len(agents_lines)}: General guideline.")
    # Add consecutive blank lines to reach 155 lines
    while len(agents_lines) < 155:
        agents_lines.append("")
    agents_lines = agents_lines[:155]
    assert len(agents_lines) == 155, f"Seeded lines must be 155, got {len(agents_lines)}"
    (repo_dir / "AGENTS.md").write_text("\n".join(agents_lines) + "\n", encoding="utf-8")

    # 5. CLAUDE.md: stale header without @AGENTS.md pointer
    (repo_dir / "CLAUDE.md").write_text(
        "# CLAUDE Instructions\nGenerated from AGENTS.md\nStale instructions body.\n",
        encoding="utf-8",
    )

    # 6. .github/copilot-instructions.md: stale body text that does not match AGENTS.md
    github_dir = repo_dir / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "copilot-instructions.md").write_text(
        "<!-- Generated from AGENTS.md by `python scripts/sync_context.py`. Edit AGENTS.md instead. -->\n\nStale Copilot content.\n",
        encoding="utf-8",
    )

    # =========================================================================
    # Step 1: Pre-Audit & Triage (codebase-context-governor)
    # =========================================================================
    gov_report_step1 = ContextGovernor.run_govern(
        root=repo_dir,
        target_file=None,
        complexity_score=0.80,
        config={},
    )

    assert gov_report_step1.passed is False, "Step 1 pre-audit must fail on un-governed seeded repository"
    assert gov_report_step1.recommended_tier == "High", "Complexity 0.80 must route to High compute tier"

    # Stage 1: Line budget overflow (> 150 lines) and lint leakage detected
    stage1 = gov_report_step1.stages[0]
    assert stage1.passed is False, "Stage 1 (Smell Auditing) must fail"
    rule_names = {v.rule_name for v in gov_report_step1.violations}
    assert "Instruction Line Budget" in rule_names, "Must detect line budget overflow (> 150)"
    assert "Lint Leakage Guard" in rule_names, "Must detect lint leakage pattern"

    # Stage 3: SSOT sync drift detected
    stage3 = gov_report_step1.stages[2]
    assert stage3.passed is False, "Stage 3 (SSOT Sync) must detect drift"
    assert "Sync drift detected" in stage3.message

    # Stage 4: CI Linter problems detected (src/ghost_module.py and npm run build)
    stage4 = gov_report_step1.stages[3]
    assert stage4.passed is False, "Stage 4 (CI Lint) must detect path and script problems"
    assert stage4.details.get("problems_count", 0) >= 2

    # =========================================================================
    # Step 2: Anti-Rot Pruning & Rule 11 Enforcement (context-anti-rot-sync)
    # =========================================================================
    # Prune redundant whitespace, eliminate lint leakage, fix broken path & script spans
    sync_engine = ContextSyncEngine(workspace_root=repo_dir)

    # 1. Clean whitespace on AGENTS.md
    clean_res = sync_engine.clean_file("AGENTS.md", "AGENTS.md")
    assert clean_res.cleaned_lines < clean_res.original_lines

    # 2. Compress bloated rules into concise standards, eliminate lint leakage and broken ghost module
    cleaned_agents_lines = [
        "# Constitution and Guidelines",
        "",
        "## Execution Seams",
        "- Run unit tests via `pytest -v`",
        "- Build package via `python -m build`",
        "",
        "## Negative Boundaries",
        "- Do not touch production credentials or sensitive env files.",
        "- Do not modify host configuration outside test scope.",
        "",
        "## Path References",
        "- Reference valid: `src/app.py`",
        "",
        "## Core Architectural Guidelines",
        "- Rule 1: Maintain modular single-responsibility plugins.",
        "- Rule 2: Keep context files concise and strictly budgeted.",
        "- Rule 3: Use typed ServiceKey for all IoC registrations.",
        "- Rule 4: Subprocess isolation for external plugins.",
    ]
    (repo_dir / "AGENTS.md").write_text("\n".join(cleaned_agents_lines) + "\n", encoding="utf-8")

    # 3. Fix the broken npm script reference in docs/guide.md
    (docs_dir / "guide.md").write_text(
        "# Developer Guide\n\nRun `npm test` to execute test suite.\n",
        encoding="utf-8",
    )

    # 4. Audit via context-anti-rot-sync engine
    audit_res = sync_engine.audit_file("AGENTS.md", max_lines=150)
    assert audit_res.passed is True, f"Cleaned AGENTS.md must pass audit: {audit_res.violations}"
    assert audit_res.total_lines < 150, f"Cleaned AGENTS.md must be < 150 lines, got {audit_res.total_lines}"
    assert audit_res.has_negative_boundaries is True
    assert audit_res.has_execution_seams is True

    # =========================================================================
    # Step 3: Downstream SSOT Synchronization (codebase-context-architect)
    # =========================================================================
    sync_res = ContextSynchronizer.run_sync(root=repo_dir, source_rel="AGENTS.md", dry_run=False)
    assert "[UPDATED] Synchronized CLAUDE.md from AGENTS.md" in sync_res.actions
    assert "[UPDATED] Synchronized .github/copilot-instructions.md from AGENTS.md" in sync_res.actions

    # Verify CLAUDE.md contains @AGENTS.md pointer
    claude_content = (repo_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "@AGENTS.md" in claude_content
    assert "Claude Code specific" in claude_content

    # Verify .github/copilot-instructions.md mirrors AGENTS.md with banner
    copilot_content = (repo_dir / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert "Generated from AGENTS.md" in copilot_content
    assert "## Negative Boundaries" in copilot_content

    # Confirm idempotence: second sync run reports in_sync == True
    sync_res_idempotent = ContextSynchronizer.run_sync(root=repo_dir, source_rel="AGENTS.md", dry_run=True)
    assert sync_res_idempotent.in_sync is True

    # =========================================================================
    # Step 4: CI Linter & Post-Governance Verification Gate
    # =========================================================================
    lint_report_step4 = ContextLinter.run_lint(root=repo_dir, config={})
    assert lint_report_step4.passed is True, f"Lint report must pass: {lint_report_step4.problems}"
    assert lint_report_step4.problems_count == 0

    gov_report_step4 = ContextGovernor.run_govern(
        root=repo_dir,
        target_file=None,
        complexity_score=0.80,
        config={},
    )
    assert gov_report_step4.passed is True, "Post-governance report must pass all 5 stages"
    assert gov_report_step4.passed_stages_count == 5
    assert len(gov_report_step4.violations) == 0
