"""
Capability & SDLC Test Suite for repo-doc-synchronizer.

Verifies:
1. AST Symbol Inspection (classes, callables, type annotations, docstrings)
2. Documentation Coverage Auditing (coverage %, threshold enforcement, missing doc lists)
3. Documentation Drift Detection (broken relative file links with code block isolation Rule 47)
4. Standardized Diátaxis Scaffolding (API reference, README, how-to recipes)
5. Interactive Visual Brief HTML rendering (Mermaid.js topology)
6. CLI Subcommands execution & JSON file output (Rule 4)
7. SkillSDLC & SkillValidator compliance (Rule 34, Rule 37, Rule 44)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure skill scripts directory is on sys.path
SKILL_ROOT = Path(".agents/skills/repo-doc-synchronizer").resolve()
SCRIPTS_DIR = SKILL_ROOT / "scripts"
SRC_DIR = Path("src").resolve()

for p in [SCRIPTS_DIR, SRC_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from doc_ast_inspector import inspect_module_ast
from doc_synchronizer import DocCoverageReport, DocDriftReport, DocSynchronizerEngine

from harness.creator.skills import SkillValidator

CLI_PATH = SCRIPTS_DIR / "doc_synchronizer.py"


def run_cli(*args: str) -> tuple[int, str, str]:
    """Helper to execute doc_synchronizer.py CLI subprocess with UTF-8 encoding."""
    cmd = [sys.executable, str(CLI_PATH)] + list(args)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


@pytest.mark.unit
class TestASTInspector:
    """Verifies AST-level extraction of Python symbols and docstrings."""

    def test_inspect_module_ast_with_classes_and_functions(
        self, tmp_path: Path
    ) -> None:
        """Correctly extracts classes, methods, functions, and docstrings."""
        module_code = '''"""Sample module docstring."""

class Calculator:
    """Performs arithmetic calculations."""

    def add(self, a: int, b: int) -> int:
        """Adds two integers."""
        return a + b

def multiply(x: float, y: float) -> float:
    """Multiplies two numbers."""
    return x * y
'''
        test_file = tmp_path / "calculator.py"
        test_file.write_text(module_code, encoding="utf-8")

        inspection = inspect_module_ast(test_file)
        assert inspection is not None
        assert inspection.has_module_docstring is True
        assert inspection.docstring == "Sample module docstring."
        assert len(inspection.classes) == 1
        assert inspection.classes[0].name == "Calculator"
        assert inspection.classes[0].docstring == "Performs arithmetic calculations."
        assert len(inspection.classes[0].methods) == 1
        assert inspection.classes[0].methods[0].name == "add"
        assert inspection.classes[0].methods[0].docstring == "Adds two integers."

        assert len(inspection.functions) == 1
        assert inspection.functions[0].name == "multiply"
        assert inspection.functions[0].docstring == "Multiplies two numbers."
        assert inspection.total_public_symbols == 2

    def test_inspect_module_ast_missing_or_invalid_file(self, tmp_path: Path) -> None:
        """Gracefully returns None on non-existent or non-Python files."""
        assert inspect_module_ast(tmp_path / "non_existent.py") is None
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("hello", encoding="utf-8")
        assert inspect_module_ast(txt_file) is None


@pytest.mark.unit
class TestDocSynchronizerEngine:
    """Verifies coverage audit, drift detection, and scaffolding logic."""

    @pytest.fixture
    def mock_repo(self, tmp_path: Path) -> Path:
        """Scaffolds a mock repository structure with documented and undocumented modules."""
        repo_dir = tmp_path / "mock_project"
        repo_dir.mkdir(parents=True, exist_ok=True)

        pkg = repo_dir / "mypkg"
        pkg.mkdir(parents=True, exist_ok=True)

        # Well-documented module with sibling README
        mod_a = pkg / "engine.py"
        mod_a.write_text(
            '"""Core engine."""\n\nclass CoreEngine:\n    """Engine class."""\n    def run(self) -> None:\n        """Run engine."""\n        pass\n',
            encoding="utf-8",
        )
        readme_a = pkg / "README.md"
        readme_a.write_text(
            "# Engine Package\n\n[Guide](./engine.md)", encoding="utf-8"
        )

        # Undocumented module
        mod_b = pkg / "helpers.py"
        mod_b.write_text(
            "def do_something(x):\n    return x * 2\n",
            encoding="utf-8",
        )

        return repo_dir

    def test_audit_computes_coverage_and_flags_missing(self, mock_repo: Path) -> None:
        """Audit calculates coverage and identifies undocumented modules."""
        engine = DocSynchronizerEngine(root_dir=mock_repo)
        report = engine.audit(min_coverage=70.0)

        assert isinstance(report, DocCoverageReport)
        assert report.total_modules == 2
        assert report.modules_with_docstring == 1

        # engine.py has module doc + class doc + dedicated README -> ~100%
        # helpers.py has 0% docstring coverage and no dedicated doc -> ~0%
        assert "mypkg/helpers.py" in report.missing_docs

    def test_drift_check_detects_broken_relative_links(self, mock_repo: Path) -> None:
        """Drift check flags non-existent relative links while ignoring code blocks (Rule 47)."""
        docs_dir = mock_repo / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        doc_file = docs_dir / "guide.md"
        doc_content = (
            "# Developer Guide\n\n"
            "See [Valid Link](../mypkg/README.md) for details.\n"
            "See [Broken Link](../non_existent_file.md) for specs.\n\n"
            "```markdown\n"
            "[Fake Link inside codeblock](does_not_exist.md)\n"
            "```\n"
        )
        doc_file.write_text(doc_content, encoding="utf-8")

        engine = DocSynchronizerEngine(root_dir=mock_repo)
        drift_rep = engine.drift_check(docs_dir=docs_dir)

        assert isinstance(drift_rep, DocDriftReport)
        assert drift_rep.has_drift is True
        assert len(drift_rep.broken_links) == 1
        assert drift_rep.broken_links[0].target_link == "../non_existent_file.md"

    def test_scaffold_api_reference(self, mock_repo: Path) -> None:
        """Scaffold generates standardized Diátaxis documentation using AST data."""
        engine = DocSynchronizerEngine(root_dir=mock_repo)
        target_mod = mock_repo / "mypkg" / "engine.py"
        out_doc = mock_repo / "docs" / "engine_api.md"

        res_path = engine.scaffold(
            module_path=target_mod,
            doc_type="api",
            output_path=out_doc,
        )

        assert res_path.exists()
        assert res_path == out_doc
        content = out_doc.read_text(encoding="utf-8")
        assert "engine API Reference" in content
        assert "class CoreEngine" in content
        assert "def run" in content

    def test_visual_brief_generates_interactive_html(self, mock_repo: Path) -> None:
        """Visual brief generates HTML dashboard with dark-mode Mermaid diagram."""
        engine = DocSynchronizerEngine(root_dir=mock_repo)
        out_html = mock_repo / "brief.html"
        res_path = engine.visual_brief(output_path=out_html)

        assert res_path.exists()
        content = out_html.read_text(encoding="utf-8")
        assert "Documentation Coverage Brief & Scorecard" in content
        assert "mermaid" in content
        assert "mypkg/engine.py" in content


@pytest.mark.unit
class TestSkillCraftAndCLI:
    """Verifies CLI execution and SkillValidator compliance."""

    def test_cli_audit_subcommand(self, tmp_path: Path) -> None:
        """CLI audit writes JSON report and exits cleanly."""
        out_json = tmp_path / "coverage.json"
        code, stdout, _ = run_cli(
            "audit",
            "--root",
            ".",
            "--target",
            "src/harness/services",
            "--output",
            str(out_json),
        )

        assert code == 0
        assert "Success! Audit" in stdout
        assert out_json.exists()
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "total_modules" in data
        assert data["total_modules"] > 0

    def test_cli_scaffold_subcommand(self, tmp_path: Path) -> None:
        """CLI scaffold renders API reference to target file."""
        target_mod = Path("src/harness/services/agentwikis.py").resolve()
        out_doc = tmp_path / "agentwikis_api.md"

        code, stdout, _ = run_cli(
            "scaffold",
            "--module",
            str(target_mod),
            "--type",
            "api",
            "--output",
            str(out_doc),
        )

        assert code == 0
        assert "Success! Scaffolded" in stdout
        assert out_doc.exists()
        content = out_doc.read_text(encoding="utf-8")
        assert "AgentWikis" in content or "agentwikis API Reference" in content

    def test_platform_skill_validator_compliance(self) -> None:
        """repo-doc-synchronizer satisfies all SkillValidator rules."""
        report = SkillValidator.validate(SKILL_ROOT)
        assert report.valid is True, (
            f"Skill validation failed: {[c.message for c in report.checks if not c.passed]}"
        )
