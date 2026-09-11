"""Contract test suite for codebase-context-architect skill."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "codebase-context-architect"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestCodebaseContextArchitectStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "codebase-context-architect"
        assert len(node.stages) >= 5, f"Expected >= 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 5, f"Expected >= 5 invariants, found {len(node.invariants)}"
        assert all(inv.is_blocking for inv in node.invariants), "All invariants must be blocking"

    def test_frontmatter_budget_and_negative_boundary(self, skill_dir: Path) -> None:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists()
        text = skill_file.read_text(encoding="utf-8")
        
        # Rule 44: Description bounded between 100 and 350 chars with action verbs and negative boundary
        frontmatter, _ = SkillCardParser._extract_frontmatter(text)
        desc = frontmatter.get("description", "")
        assert 100 <= len(desc) <= 350, f"Description length {len(desc)} not in [100, 350]"
        assert "Do not use for" in desc, "Description must contain explicit negative boundary ('Do not use for...')"


@pytest.mark.unit
class TestBundledContextLinterAndSyncScripts:
    """Test behavior of bundled Python scripts context_linter.py and sync_context.py."""

    def test_linter_passes_on_clean_repo(self, tmp_path: Path, skill_dir: Path) -> None:
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from context_linter import run_linter

        # Scaffold clean fixture
        (tmp_path / "AGENTS.md").write_text("# Root\nSee `src/api.js` for handlers.\n", encoding="utf-8")
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "api.js").write_text("// API handler\n", encoding="utf-8")
        (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "node --test"}}), encoding="utf-8")

        report = run_linter(tmp_path)
        assert report["passed"] is True
        assert report["problems_count"] == 0

    def test_linter_detects_broken_path_and_missing_script(self, tmp_path: Path, skill_dir: Path) -> None:
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from context_linter import run_linter

        # Reference non-existent path and script
        (tmp_path / "AGENTS.md").write_text(
            "# Root\nRun `npm run dead-script`.\nSee `docs/non_existent.md`.\n",
            encoding="utf-8"
        )
        (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "echo test"}}), encoding="utf-8")

        report = run_linter(tmp_path)
        assert report["passed"] is False
        assert report["problems_count"] >= 2
        messages = [p["message"] for p in report["problems"]]
        assert any("non_existent.md" in m for m in messages)
        assert any("dead-script" in m for m in messages)

    def test_sync_context_generates_vendor_files(self, tmp_path: Path, skill_dir: Path) -> None:
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from sync_context import sync_repository

        # Scaffold canonical AGENTS.md
        (tmp_path / "AGENTS.md").write_text("# Canonical AGENTS\nCommands: `npm test`\n", encoding="utf-8")

        # 1. First sync generates files
        in_sync, messages = sync_repository(tmp_path, dry_run=False)
        assert in_sync is False  # Was not in sync before writing

        claude_file = tmp_path / "CLAUDE.md"
        copilot_file = tmp_path / ".github" / "copilot-instructions.md"
        assert claude_file.exists()
        assert copilot_file.exists()

        assert "@AGENTS.md" in claude_file.read_text(encoding="utf-8")
        assert "Generated from AGENTS.md" in claude_file.read_text(encoding="utf-8")
        assert "Commands: `npm test`" in copilot_file.read_text(encoding="utf-8")

        # 2. Second sync shows already in sync
        in_sync_2, messages_2 = sync_repository(tmp_path, dry_run=True)
        assert in_sync_2 is True


@pytest.mark.unit
class TestCodebaseContextEngineDeepened:
    """Validate deep-module engine, slotted & frozen dataclasses, and polyglot manifests."""

    def test_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from engine import TokenBudgetCheck, ContextLintReport

        check = TokenBudgetCheck(
            file_path="AGENTS.md",
            token_count=100,
            token_ceiling=800,
            passed=True,
            message="OK",
        )

        # Rule 43: Direct attribute assignment raises AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            check.passed = False  # type: ignore

        report = ContextLintReport(
            root_path=".",
            passed=True,
            checks=(check,),
            problems_count=0,
            checks_count=1,
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_polyglot_manifest_inspector(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert manifest inspector handles package.json, pyproject.toml, and Makefile."""
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from engine import ManifestScriptInspector

        # Node package.json
        (tmp_path / "package.json").write_text(json.dumps({"scripts": {"build:prod": "vite build"}}), encoding="utf-8")
        # Python pyproject.toml
        (tmp_path / "pyproject.toml").write_text('[project.scripts]\nmy-cli = "my_pkg:main"\n', encoding="utf-8")
        # Makefile
        (tmp_path / "Makefile").write_text("ci-check:\n\tpytest\nlint-all:\n\truff check .\n", encoding="utf-8")

        scripts = ManifestScriptInspector.extract_available_scripts(tmp_path)
        assert "build:prod" in scripts
        assert "my-cli" in scripts
        assert "pytest" in scripts  # Standard Python tool
        assert "ci-check" in scripts
        assert "lint-all" in scripts

    def test_zero_fork_config_resolution(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert 3-tier zero-fork configuration precedence (Rule 44)."""
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from engine import ConfigResolver

        # Project override config
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "skills.config.yaml").write_text(
            "codebase-context-architect:\n"
            "  chars_per_token: 3\n"
            "  budgets:\n"
            "    AGENTS.md: 600\n",
            encoding="utf-8"
        )

        resolved = ConfigResolver.resolve_config(tmp_path, skill_dir=skill_dir)
        assert resolved["chars_per_token"] == 3
        assert resolved["budgets"]["AGENTS.md"] == 600


@pytest.mark.unit
class TestContextClickCommands:
    """Assert headless Click CLI commands (harness context lint / sync) (Rule 10)."""

    def test_click_context_lint_pass(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Root\nSee `src/server.py`\n", encoding="utf-8")
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "server.py").write_text("# Server\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(main, ["context", "lint", "--root", str(tmp_path)])
        assert result.exit_code == 0
        assert "[PASS]" in result.output

    def test_click_context_lint_fail_on_broken_path(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Root\nSee `src/missing.py`\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(main, ["context", "lint", "--root", str(tmp_path)])
        assert result.exit_code == 1
        assert "[FAIL]" in result.output
        assert "missing.py" in result.output

    def test_click_context_sync_dry_run_drift(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Canonical\n", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["context", "sync", "--root", str(tmp_path), "--dry-run"])
        assert result.exit_code == 1
        assert "[DRIFT]" in result.output

    def test_click_context_sync_generates_files(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Canonical\n", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["context", "sync", "--root", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".github" / "copilot-instructions.md").exists()
