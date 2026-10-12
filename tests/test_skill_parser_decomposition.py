"""Contract test suite for SkillCardParser decomposition per AGENTS.md Rule 11, Rule 18, Rule 37, Rule 52, Rule 58."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.skill_parser import (
    SKILL_PARSER_SERVICE_KEY,
    DefaultSkillCardParserService,
    SkillCardParser,
    SkillCardParserService,
    extract_anti_patterns,
    extract_ascii_card,
    extract_frontmatter,
    extract_invariants,
    extract_references,
    extract_stages_from_card_table,
    extract_stages_from_skill_md,
    resolve_skill_card_parser,
    scan_root,
)


@pytest.mark.unit
class TestSkillCardParserDecomposition:
    """Verifies subpackage architecture, line limits, and parsing invariants."""

    def test_submodule_line_counts(self) -> None:
        """Rule 11: All decomposed submodules in skill_parser must be <= 200 lines."""
        parser_dir = Path(__file__).parent.parent / "src" / "harness" / "services" / "skill_parser"
        assert parser_dir.exists() and parser_dir.is_dir()

        py_files = list(parser_dir.glob("*.py"))
        assert len(py_files) >= 7

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert line_count <= 200, f"{py_file.name} has {line_count} lines (> 200 limit)"

    def test_direct_and_submodule_imports(self) -> None:
        """Verify all symbols can be imported from root package and submodules."""
        from harness.services.skill_parser.card_box import extract_ascii_card as eac
        from harness.services.skill_parser.extractors import (
            extract_anti_patterns as eap,
            extract_invariants as ei,
            extract_references as er,
            extract_stages_from_card_table as esct,
            extract_stages_from_skill_md as essm,
        )
        from harness.services.skill_parser.frontmatter import extract_frontmatter as ef
        from harness.services.skill_parser.parser import SkillCardParser as SCP
        from harness.services.skill_parser.protocols import (
            SKILL_PARSER_SERVICE_KEY as SPSK,
            SkillCardParserService as SCPS,
        )
        from harness.services.skill_parser.resolvers import (
            DefaultSkillCardParserService as DSCPS,
            resolve_skill_card_parser as rscp,
        )
        from harness.services.skill_parser.scanner import scan_root as sr

        assert SCP is SkillCardParser
        assert ef is extract_frontmatter
        assert eac is extract_ascii_card
        assert essm is extract_stages_from_skill_md
        assert esct is extract_stages_from_card_table
        assert eap is extract_anti_patterns
        assert ei is extract_invariants
        assert er is extract_references
        assert sr is scan_root
        assert SPSK is SKILL_PARSER_SERVICE_KEY
        assert SCPS is SkillCardParserService
        assert DSCPS is DefaultSkillCardParserService
        assert rscp is resolve_skill_card_parser

    def test_single_seam_resolver(self) -> None:
        """Rule 58: Single-seam resolver resolves from IoC container if available."""
        ctx = ServiceContext()
        default_svc = resolve_skill_card_parser(ctx)
        assert isinstance(default_svc, DefaultSkillCardParserService)

        custom_svc = DefaultSkillCardParserService()
        ctx.provide(SKILL_PARSER_SERVICE_KEY, custom_svc)
        resolved_custom = resolve_skill_card_parser(ctx)
        assert resolved_custom is custom_svc

    def test_parse_directory_and_extractors(self, tmp_path: Path) -> None:
        """Verify parsing of SKILL.md and CARD.md specifications."""
        skill_dir = tmp_path / "sample-agent-skill"
        skill_dir.mkdir()

        skill_content = """---
name: sample-agent-skill
description: "Sample description"
dependencies: ["other-skill", "another_skill"]
---

# Sample Agent Skill

## 1. Initial Assessment
> **Completion criterion**: Audit complete.
Primary artifact: `audit.md`
Consumes artifact: `input.txt`

## 2. Execution
> **Completion criterion**: Changes verified.

## Anti-Patterns
- **Shallow Module** — Creates useless wrapper without deepening.

Reference: /dependency-skill and [peer-skill].
"""
        (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

        card_content = """# CARD
┌────────────────────────────────────────────────────────┐
│ SKILL: sample-agent-skill                              │
│ Category: architecture                                │
│ Invocation: /sample-agent-skill                       │
│ Version: 1.2.0                                         │
│ Triggers: "audit code", "check architecture"           │
│ Target: Production codebase                            │
│ Requires: "dep-one", "dep-two"                         │
└────────────────────────────────────────────────────────┘

## Mandatory Invariants Checklist
- [ ] Rule 11: Submodules must not exceed 200 lines.
- [ ] Rule 12: Slotted dataclasses required.
"""
        (skill_dir / "CARD.md").write_text(card_content, encoding="utf-8")

        card_def = SkillCardParser.parse_directory(skill_dir)
        assert card_def is not None
        assert card_def.name == "sample-agent-skill"
        assert card_def.version == "1.2.0"
        assert card_def.category == "architecture"
        assert "audit code" in card_def.triggers
        assert len(card_def.stages) == 2
        assert card_def.stages[0].primary_artifact == "audit.md"
        assert len(card_def.anti_patterns) == 1
        assert card_def.anti_patterns[0].name == "Shallow Module"
        assert len(card_def.invariants) == 2
        assert any("Rule 11" in inv.rule for inv in card_def.invariants)
        assert "dep-one" in card_def.dependencies

    def test_legacy_protected_methods_backward_compatibility(self) -> None:
        """Verify protected helper methods on SkillCardParser class."""
        fm, body = SkillCardParser._extract_frontmatter("---\nname: test\n---\nBody")
        assert fm.get("name") == "test"
        assert "Body" in body

        ascii_meta = SkillCardParser._extract_ascii_card("│ Name: test-skill │\n│ Category: core │")
        assert ascii_meta.get("name") == "test-skill"
        assert ascii_meta.get("category") == "core"

        invariants = SkillCardParser._extract_invariants("## Invariants\n- [ ] Must be valid")
        assert len(invariants) == 1
        assert invariants[0].rule == "Must be valid"

        anti_patterns = SkillCardParser._extract_anti_patterns("## Anti-Patterns\n- **Trap** — Avoid this")
        assert len(anti_patterns) == 1
        assert anti_patterns[0].name == "Trap"

    def test_bounded_directory_scanner(self, tmp_path: Path) -> None:
        """Rule 52: Scanner enforces depth limits and ignores noise folders."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()

        # Skill at depth 1
        s1 = skills_root / "s1"
        s1.mkdir()
        (s1 / "SKILL.md").write_text("---\nname: s1\n---\n# S1", encoding="utf-8")

        # Noise directory (.git)
        git_dir = skills_root / ".git" / "fake_skill"
        git_dir.mkdir(parents=True)
        (git_dir / "SKILL.md").write_text("---\nname: fake\n---\n# Fake", encoding="utf-8")

        discovered = SkillCardParser.scan_root(skills_root, max_depth=2)
        assert "s1" in discovered
        assert "fake" not in discovered
