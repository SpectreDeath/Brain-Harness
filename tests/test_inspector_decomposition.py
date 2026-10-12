"""Contract test suite for RepoInspector decomposition per AGENTS.md Rule 11 and Rule 18."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from harness.ingestion.inspector import (
    InspectionError,
    RepoInspector,
    convert_mcp_json,
    extract_function_params,
    extract_python_entrypoints,
    guess_entrypoint,
    parse_skill_frontmatter,
    read_requirements,
    try_mcp_json,
    try_package_json,
    try_plugin_json,
    try_pyproject,
    try_python_ast,
    try_skills_bundle,
)
from harness.plugins.manifest import IsolationMode


@pytest.mark.unit
class TestRepoInspectorDecomposition:
    """Verifies subpackage structure, imports, line count invariants, and strategies."""

    def test_submodule_line_counts(self) -> None:
        """Rule 11: All decomposed submodules in inspector must be <= 200 lines."""
        inspector_dir = Path(__file__).parent.parent / "src" / "harness" / "ingestion" / "inspector"
        assert inspector_dir.exists() and inspector_dir.is_dir()

        py_files = list(inspector_dir.glob("*.py"))
        assert len(py_files) >= 5

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert line_count <= 200, f"{py_file.name} has {line_count} lines (> 200 limit)"

    def test_direct_and_submodule_imports(self) -> None:
        """Verify all public symbols are importable from root and submodules."""
        from harness.ingestion.inspector.ast_extractor import (
            extract_function_params as efp,
            extract_python_entrypoints as epe,
            guess_entrypoint as ge,
            read_requirements as rr,
            try_python_ast as tpa,
        )
        from harness.ingestion.inspector.exceptions import InspectionError as IE
        from harness.ingestion.inspector.inspector import RepoInspector as RI
        from harness.ingestion.inspector.manifest_strategies import (
            convert_mcp_json as cmj,
            try_mcp_json as tmj,
            try_package_json as tpj,
            try_plugin_json as tplj,
            try_pyproject as tpy,
        )
        from harness.ingestion.inspector.skills_bundle import (
            parse_skill_frontmatter as psf,
            try_skills_bundle as tsb,
        )

        assert RI is RepoInspector
        assert IE is InspectionError
        assert efp is extract_function_params
        assert epe is extract_python_entrypoints
        assert ge is guess_entrypoint
        assert rr is read_requirements
        assert tpa is try_python_ast
        assert cmj is convert_mcp_json
        assert tmj is try_mcp_json
        assert tpj is try_package_json
        assert tplj is try_plugin_json
        assert tpy is try_pyproject
        assert psf is parse_skill_frontmatter
        assert tsb is try_skills_bundle

    def test_ast_extractor_function_params(self) -> None:
        """Verify AST parameter extraction from python functions."""
        code = '''
def demo_func(name: str, count: int = 5, extra: dict = None) -> bool:
    return True
'''
        tree = ast.parse(code)
        func_def = tree.body[0]
        params = extract_function_params(func_def)
        assert len(params) == 3

        p_name = params[0]
        assert p_name.name == "name"
        assert p_name.type == "string"
        assert p_name.required is True

        p_count = params[1]
        assert p_count.name == "count"
        assert p_count.type == "integer"
        assert p_count.required is False

        p_extra = params[2]
        assert p_extra.name == "extra"
        assert p_extra.type == "object"
        assert p_extra.required is False

    def test_skills_bundle_discovery_and_entrypoint_generation(self, tmp_path: Path) -> None:
        """Verify Claude plugin and Agent skills bundle discovery strategy."""
        skills_dir = tmp_path / "skills" / "data_cleaner"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            "---\nname: data-cleaner\ndescription: Cleans tabular data\n---\n# Data Cleaner\n",
            encoding="utf-8",
        )

        manifest = try_skills_bundle(tmp_path)
        assert manifest is not None
        assert manifest.name == tmp_path.name
        assert len(manifest.entrypoints) == 1
        assert manifest.entrypoints[0].name == "data-cleaner"
        assert manifest.entrypoints[0].description == "Cleans tabular data"
        assert manifest.isolation == IsolationMode.SUBPROCESS

        # Verify skills_entrypoint.py was written
        ep_file = tmp_path / "skills_entrypoint.py"
        assert ep_file.exists()
        assert "Auto-generated entrypoint runner" in ep_file.read_text(encoding="utf-8")

    def test_backward_compatible_forwarding_methods(self, tmp_path: Path) -> None:
        """Verify legacy protected helper methods on RepoInspector."""
        inspector = RepoInspector()

        # Check parse_skill_frontmatter helper
        frontmatter = "---\nname: test-skill\ndescription: Test description\n---\nBody"
        name, desc = inspector._parse_skill_frontmatter(frontmatter)
        assert name == "test-skill"
        assert desc == "Test description"

        # Check requirements reader
        (tmp_path / "requirements.txt").write_text("pytest>=8.0.0\n# comment\nruff\n", encoding="utf-8")
        deps = inspector._read_requirements(tmp_path)
        assert deps == ["pytest>=8.0.0", "ruff"]

        # Check guess entrypoint
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        assert inspector._guess_entrypoint(tmp_path) == "app.py"

        (tmp_path / "main.py").write_text("pass", encoding="utf-8")
        assert inspector._guess_entrypoint(tmp_path) == "main.py"

        # Check quickstart generation during inspection
        manifest = inspector.inspect(tmp_path)
        quickstart_file = tmp_path / "QUICKSTART.md"
        assert quickstart_file.exists()
        assert manifest.usage_guide != ""
