"""Contract test suite for architecture-deepening-workflow and monolith-decomposition-engine."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import pytest

repo_root = Path(__file__).resolve().parent.parent


def test_frontmatter_description_bounds():
    """Rule 44: Skill frontmatter description must be between 100 and 350 characters."""
    skill_dirs = [
        repo_root / ".agents" / "skills" / "architecture-deepening-workflow",
        repo_root / ".agents" / "skills" / "monolith-decomposition-engine",
    ]

    for sd in skill_dirs:
        skill_md = sd / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md missing in {sd}"
        content = skill_md.read_text(encoding="utf-8")
        assert content.startswith("---"), "Frontmatter missing"
        parts = content.split("---", 2)
        frontmatter = parts[1]

        # Extract description
        desc_line = ""
        for line in frontmatter.splitlines():
            if line.startswith("description:"):
                desc_line = line.replace("description:", "").strip()
                break

        assert desc_line, f"Description not found in {skill_md}"
        desc_len = len(desc_line)
        assert 100 <= desc_len <= 350, f"Description length {desc_len} out of bounds (100-350) in {sd.name}"
        assert "Do not use for" in desc_line, f"Missing negative boundary in {sd.name}"


def test_card_ascii_formatting_and_invariants():
    """Rule 37: CARD.md must use single-pipe borders and declare mandatory invariants."""
    cards = [
        repo_root / ".agents" / "skills" / "architecture-deepening-workflow" / "CARD.md",
        repo_root / ".agents" / "skills" / "monolith-decomposition-engine" / "CARD.md",
    ]

    for card in cards:
        assert card.exists(), f"CARD.md missing: {card}"
        content = card.read_text(encoding="utf-8")
        assert "SKILL:" in content, f"Missing SKILL: header in {card}"
        assert "│" in content, f"Missing single-pipe border in {card}"
        assert "║" not in content, f"Double-pipe border detected in {card}"
        assert "## Mandatory Invariants Checklist" in content, f"Missing checklist in {card}"
        assert "- [ ]" in content, f"Missing checkboxes in {card}"


def test_cli_script_subcommands():
    """Verify scripts/deepen_cycle.py help, scan, and check-lines subcommands."""
    script_p = repo_root / ".agents" / "skills" / "architecture-deepening-workflow" / "scripts" / "deepen_cycle.py"
    assert script_p.exists(), f"CLI script missing: {script_p}"

    # 1. Main help
    res = subprocess.run([sys.executable, str(script_p), "--help"], capture_output=True, text=True, cwd=repo_root)
    assert res.returncode == 0
    assert "scan" in res.stdout
    assert "check-lines" in res.stdout
    assert "verify" in res.stdout
    assert "push" in res.stdout

    # 2. Check-lines on codebase_context (which passed Cycle 70)
    check_dir = repo_root / "src" / "harness" / "services" / "codebase_context"
    res_chk = subprocess.run(
        [sys.executable, str(script_p), "check-lines", "--dir", str(check_dir), "--max-lines", "200"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert res_chk.returncode == 0
    assert "All" in res_chk.stdout
    assert "<= 200 lines" in res_chk.stdout


def test_knowledge_vault_dual_file_format():
    """Rule 40: Persisted knowledge items must adhere to canonical dual-file format."""
    ki_dir = repo_root / ".harness" / "knowledge" / "ki_20261014_70_cycle_deepening_corpus"
    assert ki_dir.is_dir(), f"Knowledge directory missing: {ki_dir}"

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"
    assert meta_file.exists(), f"metadata.json missing in {ki_dir}"
    assert summary_file.exists(), f"summary.md missing in {ki_dir}"

    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["id"] == "ki_20261014_70_cycle_deepening_corpus"
    assert "isnad_claims" in meta
    assert len(meta["isnad_claims"]) >= 3

    summary = summary_file.read_text(encoding="utf-8")
    assert "The 7-Phase State Machine" in summary
    assert "Anti-Pattern Defenses" in summary


def test_context_map_registration():
    """Verify both skills are registered in root CONTEXT-MAP.md."""
    cmap_text = (repo_root / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    assert "architecture-deepening-workflow" in cmap_text
    assert "monolith-decomposition-engine" in cmap_text
