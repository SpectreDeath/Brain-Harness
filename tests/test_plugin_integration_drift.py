"""Automated drift gate asserting plugin integration invariants, counts, and skills (Track 8).

Verifies:
1. Canonical CLI groups count equals 45 and all integrated subcommands exist in cli.py.
2. Canonical plugin count (134 plugins) excludes .claude-plugin directories.
3. Plugins declare non-empty provides and co-located config.default.yaml (Rule 44).
4. New skills pass deep-module craft validation rules (Rule 37, Rule 44).
5. Documentation cross-links use portable relative paths without raw absolute file:/// URIs (Rule 47).
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import pytest

from harness.cli import main, _CANONICAL_GROUPS
from harness.creator.validator import ValidationContext
from harness.creator.skills.rules import (
    SkillCardRule,
    SkillDirectoryRule,
    SkillFrontmatterRule,
    SkillPillarRule,
)


@pytest.mark.unit
class TestPluginIntegrationDrift:
    """Rigorous drift gate verifying the entire plugin integration surface."""

    def test_canonical_cli_groups_count(self) -> None:
        """Verify that exactly 45 canonical CLI command groups are registered per Rule 6."""
        assert len(_CANONICAL_GROUPS) == 45
        group_names = [name for name, _ in _CANONICAL_GROUPS]
        assert "gev" in group_names
        assert "mantis" in group_names
        assert "memory" in group_names
        assert "context" in group_names
        assert "skills" in group_names
        assert "knowledge" in group_names
        assert "rea" in group_names

    def test_integrated_subcommands_exist(self) -> None:
        """Verify that all newly integrated toolkits and subcommands exist on Click groups."""
        # GEV subcommands
        gev_cmd = main.commands["gev"]
        for sub in ["status", "brief", "flights", "vessels", "hazards", "spatial", "render"]:
            assert sub in gev_cmd.commands, f"Missing gev subcommand: {sub}"

        # Mantis 10-stage subcommands
        mantis_cmd = main.commands["mantis"]
        for sub in [
            "history-scan",
            "dir-summary",
            "plan-review",
            "audit",
            "dedupe",
            "critic-filter",
            "gate",
            "chain-exploits",
            "calibrate-risk",
            "report",
        ]:
            assert sub in mantis_cmd.commands, f"Missing mantis subcommand: {sub}"

        # Context provenance subcommands
        context_cmd = main.commands["context"]
        for sub in ["add", "transform", "validate-tool", "assemble", "ledger", "snapshot"]:
            assert sub in context_cmd.commands, f"Missing context subcommand: {sub}"

        # Memory subcommands
        memory_cmd = main.commands["memory"]
        for sub in ["register", "recall", "step", "working-set", "benchmark", "snapshot", "status", "route"]:
            assert sub in memory_cmd.commands, f"Missing memory subcommand: {sub}"

        # Skills joint-query, bridges, index
        skills_cmd = main.commands["skills"]
        for sub in ["bridges", "index", "joint-query"]:
            assert sub in skills_cmd.commands, f"Missing skills subcommand: {sub}"

        # Knowledge joint-query
        knowledge_cmd = main.commands["knowledge"]
        assert "joint-query" in knowledge_cmd.commands, "Missing knowledge joint-query"

        # Doc wiki subcommands
        doc_cmd = main.commands["doc"]
        assert "wiki-compile" in doc_cmd.commands, "Missing doc wiki-compile"
        assert "wiki-lint" in doc_cmd.commands, "Missing doc wiki-lint"

    def test_canonical_plugin_counts_and_exclusion(self) -> None:
        """Verify canonical count of 134 plugins, 1 external bundle, and .claude-plugin exclusion."""
        repo_root = Path.cwd()
        plugins_root = repo_root / "plugins"

        # 0. Manifest syntax gate (Track 1): verify every plugin.json in the tree parses as valid JSON
        all_manifests = list(plugins_root.rglob("plugin.json"))
        assert len(all_manifests) > 0, "Expected plugin.json manifests in repository"
        for m in all_manifests:
            try:
                json.loads(m.read_text(encoding="utf-8"))
            except Exception as err:
                pytest.fail(f"Manifest failed JSON parse: {m} -> {err}")

        # 1. Canonical internal plugins (Track 0): derived from depth-3 category directories where category != 'external'
        valid_categories = {
            "agent_orchestration",
            "data_engineering",
            "developer_tooling",
            "geospatial_and_osint",
            "infra_and_cloud",
            "integration_and_io",
            "machine_learning",
            "memory_and_epistemics",
            "security_and_forensics",
            "software_engineering",
        }
        canonical_manifests = [
            p for p in sorted(plugins_root.glob("*/*/plugin.json"))
            if p.parent.parent.name != "external" and not p.parent.name.startswith(".")
        ]
        expected_canonical_dirs = [
            d for d in plugins_root.glob("*/*")
            if d.is_dir() and d.parent.name in valid_categories and (d / "plugin.json").exists()
        ]
        # Dynamically derived expectation: canonical manifests must match registered category directories
        assert len(canonical_manifests) == len(expected_canonical_dirs), (
            f"Derived count mismatch: {len(canonical_manifests)} manifests vs {len(expected_canonical_dirs)} dirs"
        )
        assert len(canonical_manifests) >= 134, f"Expected at least 134 canonical plugins, found {len(canonical_manifests)}"
        for cm in canonical_manifests:
            assert cm.parent.parent.name in valid_categories, f"Invalid category {cm.parent.parent.name} for {cm}"

        # 2. External skill bundles: depth 3 where category == 'external'
        external_bundles = [
            p for p in sorted(plugins_root.glob("*/*/plugin.json"))
            if p.parent.parent.name == "external"
        ]
        assert len(external_bundles) == 1, f"Expected 1 external bundle, found {len(external_bundles)}"

        # 3. Verify .claude-plugin nested manifests are excluded from canonical discovery
        claude_manifests = [
            p for p in plugins_root.rglob("plugin.json")
            if ".claude-plugin" in p.parts
        ]
        assert len(claude_manifests) > 0, "Expected nested .claude-plugin files to exist upstream"
        for cm in claude_manifests:
            assert cm not in canonical_manifests
            assert cm not in external_bundles

        # 4. README documentation count alignment gate (Track 4)
        readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
        assert f"**{len(canonical_manifests)} Canonical Harness Plugins**" in readme_text, (
            f"README.md plugin count drifted from discovered canonical manifests ({len(canonical_manifests)})"
        )
        workspace_skills = [s for s in (repo_root / ".agents" / "skills").glob("*/SKILL.md")]
        assert f"**{len(workspace_skills)} Workspace Skills packages" in readme_text, (
            f"README.md skill count drifted from discovered workspace skills ({len(workspace_skills)})"
        )

    def test_target_plugins_provides_and_configs(self) -> None:
        """Verify that target plugins have non-empty 'provides' and valid config.default.yaml."""
        repo_root = Path.cwd()
        targets = [
            ("geospatial_and_osint", "gods_eye_view", "service.gods_eye_view"),
            ("security_and_forensics", "mantis_security_review", "service.mantis_security_review"),
            ("memory_and_epistemics", "context_type_system", "service.context_type_system"),
            ("memory_and_epistemics", "memory_decay_engine", "service.memory_decay"),
            ("memory_and_epistemics", "memgraphrag", "service.memgraphrag"),
            ("memory_and_epistemics", "graphiti_memory", "service.graphiti_memory"),
            ("memory_and_epistemics", "okf_memory", "service.okf_memory"),
            ("data_engineering", "wiki_compiler", "service.wiki_compiler"),
        ]

        for cat, name, expected_key in targets:
            p_dir = repo_root / "plugins" / cat / name
            manifest_file = p_dir / "plugin.json"
            assert manifest_file.exists(), f"Missing plugin.json for {cat}/{name}"
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            provides = data.get("provides") or []
            assert expected_key in provides, f"Expected {expected_key} in {cat}/{name} provides, got {provides}"

            config_file = p_dir / "config.default.yaml"
            assert config_file.exists(), f"Missing config.default.yaml for {cat}/{name} (Rule 44)"
            content = config_file.read_text(encoding="utf-8")
            assert "timeout_seconds:" in content, f"Missing timeout_seconds in {cat}/{name} config"

    def test_new_skills_pass_craft_validation(self) -> None:
        """Verify that newly scaffolded skills pass all deep-module craft validation rules."""
        repo_root = Path.cwd()
        new_skills = ["gods-eye-view", "mantis-security-review", "context-type-system"]
        rules = [SkillDirectoryRule(), SkillFrontmatterRule(), SkillPillarRule(), SkillCardRule()]

        for s_name in new_skills:
            s_dir = repo_root / ".agents" / "skills" / s_name
            assert s_dir.exists(), f"Skill directory missing: {s_dir}"
            ctx = ValidationContext(path=s_dir)
            for r in rules:
                try:
                    gen = r.validate(ctx)
                    gen.send(None)
                except StopIteration:
                    pass
            report = ctx.report
            failed = [c for c in report.checks if not c.passed]
            assert report.valid is True, f"Skill {s_name} failed craft checks: {[f.message for f in failed]}"
            assert len(failed) == 0, f"Skill {s_name} has failing checks: {failed}"

    def test_documentation_relative_links_hygiene(self) -> None:
        """Verify that new documentation files use portable relative links per Rule 47."""
        repo_root = Path.cwd()
        new_docs = [
            repo_root / "docs" / "reference" / "integrated-toolkits.md",
            repo_root / "docs" / "how-to" / "use-gods-eye-view.md",
            repo_root / "docs" / "how-to" / "security-forensics-workflow.md",
            repo_root / "docs" / "explanation" / "knowledge-and-skill-graphs.md",
            repo_root / "docs" / "explanation" / "learning-core-lifecycle.md",
            repo_root / "docs" / "explanation" / "memory-architecture.md",
            repo_root / "docs" / "explanation" / "agent-execution-graphs.md",
        ]

        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        for doc in new_docs:
            assert doc.exists(), f"Documentation file missing: {doc}"
            text = doc.read_text(encoding="utf-8")
            # Assert no workspace-absolute file:/// URIs
            assert "file:///" not in text, f"Found absolute file:/// link in {doc.name}"

            # Validate markdown links point to existing target paths
            for label, target in link_pattern.findall(text):
                if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
                    continue
                clean_target = target.split("#")[0]
                if clean_target:
                    target_path = (doc.parent / clean_target).resolve()
                    assert target_path.exists(), f"Broken relative link in {doc.name}: [{label}]({target})"

