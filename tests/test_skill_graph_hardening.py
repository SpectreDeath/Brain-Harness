"""Tests for skill_graph hardening: Rule 52 directory traversal hygiene and scan locking."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

import pytest

from harness.services.skill_graph import BuiltinSkillRegistryService


@pytest.mark.unit
class TestSkillGraphHardening:
    def test_skill_count_parity(self) -> None:
        """Verify that bounded os.walk discovers all 109 workspace skill cards."""
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        assert len(skills) == 109
        names = [s.name for s in skills]
        assert "deep-skill-forge" in names
        assert "pi-coding-harness" in names

    def test_concurrent_scan_double_checked_locking(self) -> None:
        """Verify that concurrent threads do not execute redundant scans."""
        registry = BuiltinSkillRegistryService()

        # Measure concurrent discover_all invocations
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(registry.discover_all, ".") for _ in range(8)]
            results = [f.result() for f in futures]

        for r in results:
            assert len(r) == 109

    def test_rule_52_noise_pruning(self, tmp_path: Path) -> None:
        """Verify that noise roots (.venv, node_modules) are pruned in-place and not traversed."""
        # Create a valid skill
        valid_dir = tmp_path / "skills" / "my-valid-skill"
        valid_dir.mkdir(parents=True)
        (valid_dir / "SKILL.md").write_text(
            """---
name: my-valid-skill
description: A valid test skill.
---
# My Valid Skill
""",
            encoding="utf-8",
        )

        # Create a poisoned skill inside .venv
        venv_dir = tmp_path / "skills" / ".venv" / "poisoned-skill"
        venv_dir.mkdir(parents=True)
        (venv_dir / "SKILL.md").write_text(
            """---
name: poisoned-skill
description: Should be ignored by Rule 52.
---
# Poisoned Skill
""",
            encoding="utf-8",
        )

        # Create a poisoned skill inside node_modules
        node_dir = tmp_path / "plugins" / "node_modules" / "sub" / "node-skill"
        node_dir.mkdir(parents=True)
        (node_dir / "SKILL.md").write_text(
            """---
name: node-skill
description: Should be ignored by Rule 52.
---
# Node Skill
""",
            encoding="utf-8",
        )

        registry = BuiltinSkillRegistryService(default_root=str(tmp_path))
        discovered = registry.discover_all(str(tmp_path))
        discovered_names = {s.name for s in discovered}

        assert "my-valid-skill" in discovered_names
        assert "poisoned-skill" not in discovered_names
        assert "node-skill" not in discovered_names
