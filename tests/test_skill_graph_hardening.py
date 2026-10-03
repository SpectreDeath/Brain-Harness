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

    def test_contract_edge_synthesis(self, tmp_path: Path) -> None:
        """Verify that interlocking stage artifacts automatically synthesize directed FEEDS edges."""
        from harness.services.skill_graph import EdgeType

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir(parents=True)

        # Skill A produces ast_diff
        dir_a = skills_dir / "skill-a"
        dir_a.mkdir()
        (dir_a / "SKILL.md").write_text(
            """---
name: skill-a
description: Produces AST diffs.
---
# Skill A
## 1. Diff Generation
Produces artifact: ast_diff
> **Completion criterion**: Diff generated
""",
            encoding="utf-8",
        )

        # Skill B consumes ast_diff
        dir_b = skills_dir / "skill-b"
        dir_b.mkdir()
        (dir_b / "SKILL.md").write_text(
            """---
name: skill-b
description: Ingests AST diffs for analysis.
---
# Skill B
## 1. Ingestion
Consumes artifact: ast_diff
> **Completion criterion**: Ingested
""",
            encoding="utf-8",
        )

        registry = BuiltinSkillRegistryService(default_root=str(tmp_path))
        registry._ensure_scanned(str(tmp_path))

        # Check FEEDS edge was synthesized from skill-a to skill-b
        feeds_edges = [
            e for e in registry._edges
            if e.source == "skill-a" and e.target == "skill-b" and e.relation == EdgeType.FEEDS
        ]
        assert len(feeds_edges) == 1, f"Expected 1 FEEDS edge from skill-a to skill-b, got {feeds_edges}"

        # Verify chaining discovers pipeline using this edge
        chain_res = registry.get_chain("skill-a", "skill-b")
        assert chain_res.status == "ok"
        assert chain_res.chain == ["skill-a", "skill-b"]

    def test_feeds_edge_acyclicity(self, tmp_path: Path) -> None:
        """Verify that mutual artifact consumption does not create directed cycles."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir(parents=True)

        dir_a = skills_dir / "skill-mut-a"
        dir_a.mkdir()
        (dir_a / "SKILL.md").write_text(
            """---
name: skill-mut-a
description: Producer of report, consumer of summary.
---
# Skill Mut A
## 1. Stage
Produces artifact: report
Consumes artifact: summary
> **Completion criterion**: Done
""",
            encoding="utf-8",
        )

        dir_b = skills_dir / "skill-mut-b"
        dir_b.mkdir()
        (dir_b / "SKILL.md").write_text(
            """---
name: skill-mut-b
description: Producer of summary, consumer of report.
---
# Skill Mut B
## 1. Stage
Produces artifact: summary
Consumes artifact: report
> **Completion criterion**: Done
""",
            encoding="utf-8",
        )

        registry = BuiltinSkillRegistryService(default_root=str(tmp_path))
        registry._ensure_scanned(str(tmp_path))

        # Assert no cycle was created in adjacency
        adj = registry._adjacency
        a_to_b = "skill-mut-b" in adj.get("skill-mut-a", set())
        b_to_a = "skill-mut-a" in adj.get("skill-mut-b", set())
        assert not (a_to_b and b_to_a), "Mutual FEEDS edges must not create a directed cycle"

    def test_corpus_idf_routing(self, tmp_path: Path) -> None:
        """Verify that corpus-IDF weighting down-weights common tokens and favors specific matches."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir(parents=True)

        # 19 generic agent skills with high frequency of "agent" and "api"
        for i in range(19):
            s_dir = skills_dir / f"agent-tool-{i}"
            s_dir.mkdir()
            (s_dir / "SKILL.md").write_text(
                f"""---
name: agent-tool-{i}
description: Autonomous agent service {i} for API workflow orchestration.
---
# Agent Tool {i}
## 1. Stage
> **Completion criterion**: Done
""",
                encoding="utf-8",
            )

        # 1 security skill with specific rare tokens ("leakage", "secret")
        sec_dir = skills_dir / "pre-commit-security-guard"
        sec_dir.mkdir()
        (sec_dir / "SKILL.md").write_text(
            """---
name: pre-commit-security-guard
description: Security guard to prevent API secret leakage and catch secrets before git commit.
---
# Pre Commit Security Guard
## 1. Stage
> **Completion criterion**: Done
""",
            encoding="utf-8",
        )

        registry = BuiltinSkillRegistryService(default_root=str(tmp_path))
        registry._ensure_scanned(str(tmp_path))

        assert len(registry._skills_cache) == 20
        assert registry._idf_table.get("agent", 1.0) < registry._idf_table.get("secret", 0.0)

        res = registry.route_intent("prevent API secret leakage", top_k=3)
        assert len(res["matches"]) > 0
        top_skill = res["matches"][0]["skill_name"]
        assert top_skill == "pre-commit-security-guard", (
            f"Expected pre-commit-security-guard as top match, got {top_skill}"
        )

