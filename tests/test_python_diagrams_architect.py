# -*- coding: utf-8 -*-
"""Contract verification test suite for python-diagrams-architect skill.

Verifies slotted and frozen dataclass architecture (Rule 12, Rule 43),
code generation, AST linting, canonical architecture presets,
and skill package hygiene (Rule 34, Rule 37, Rule 44).
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import pytest

from harness.creator.skills import SkillValidator
from harness.services.skill_parser import SkillCardParser

SCRIPTS_DIR = Path(__file__).parent.parent / ".agents" / "skills" / "python-diagrams-architect" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pda_diagram_engine import (
    DiagramCluster,
    DiagramEdge,
    DiagramNode,
    DiagramSpec,
    DiagramValidationReport,
    PythonDiagramsEngine,
)


@pytest.fixture
def skill_dir() -> Path:
    """Fixture providing path to python-diagrams-architect skill directory."""
    path = Path(__file__).parent.parent / ".agents" / "skills" / "python-diagrams-architect"
    if not path.exists():
        path = Path(".agents/skills/python-diagrams-architect")
    return path


class TestPythonDiagramsDomainModels:
    """Verify Rule 12 and Rule 43 slotted and frozen dataclass invariants."""

    def test_diagram_node_immutability(self) -> None:
        """Verify DiagramNode is slotted and immutable (Rule 43)."""
        node = DiagramNode(
            provider="aws",
            resource_type="compute",
            class_name="EC2",
            label="api-server",
            var_name="api",
        )
        assert node.provider == "aws"
        assert hasattr(node, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            node.label = "worker"  # type: ignore[misc]

    def test_diagram_edge_immutability_and_validation(self) -> None:
        """Verify DiagramEdge enforces valid directions, styles, and immutability."""
        edge = DiagramEdge(
            source="api",
            target="db",
            direction=">>",
            label="SQL",
            color="red",
            style="dashed",
        )
        assert edge.direction == ">>"
        assert hasattr(edge, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            edge.label = "HTTP"  # type: ignore[misc]

        with pytest.raises(ValueError):
            DiagramEdge("api", "db", direction="->")  # Invalid direction

        with pytest.raises(ValueError):
            DiagramEdge("api", "db", style="wavy")  # Invalid style

    def test_diagram_spec_validation(self) -> None:
        """Verify DiagramSpec validates direction, format, and immutability."""
        spec = DiagramSpec(
            title="Test Architecture",
            filename="test_arch",
            direction="LR",
            outformat="png",
        )
        assert spec.title == "Test Architecture"
        assert hasattr(spec, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            spec.direction = "TB"  # type: ignore[misc]

        with pytest.raises(ValueError):
            DiagramSpec(title="", filename="test")

        with pytest.raises(ValueError):
            DiagramSpec(title="Test", filename="test", direction="UP")

        with pytest.raises(ValueError):
            DiagramSpec(title="Test", filename="test", outformat="bmp")


class TestPythonDiagramsCodeGeneration:
    """Verify code generation syntax, cluster hierarchy, and edge formatting."""

    def test_generate_code_syntax_validity(self) -> None:
        """Verify generated code compiles to valid Python AST."""
        spec = PythonDiagramsEngine.get_canonical_preset("three_tier_web_app")
        code = PythonDiagramsEngine.generate_code(spec)

        assert "with Diagram(" in code
        assert "with Cluster(" in code
        assert "ELB" in code
        assert "EC2" in code
        assert "RDS" in code
        assert "show=False" in code

        # Assert valid Python syntax
        tree = ast.parse(code)
        assert tree is not None

    def test_edge_formatting(self) -> None:
        """Verify edge representation with and without custom properties."""
        plain_edge = DiagramEdge("lb", "api", direction=">>")
        plain_fmt = PythonDiagramsEngine._format_edge(plain_edge)
        assert plain_fmt == "lb >> api"

        custom_edge = DiagramEdge(
            "api",
            "db",
            direction=">>",
            label="SQL queries",
            color="darkgreen",
            style="dashed",
        )
        custom_fmt = PythonDiagramsEngine._format_edge(custom_edge)
        assert 'Edge(label="SQL queries", color="darkgreen", style="dashed")' in custom_fmt

    def test_canonical_presets(self) -> None:
        """Verify all three canonical presets generate valid specs and code."""
        presets = ["three_tier_web_app", "event_driven_microservices", "kubernetes_cluster"]
        for p in presets:
            spec = PythonDiagramsEngine.get_canonical_preset(p)
            assert spec.title is not None
            assert len(spec.nodes) > 0
            assert len(spec.clusters) > 0
            code = PythonDiagramsEngine.generate_code(spec)
            assert ast.parse(code) is not None

        with pytest.raises(KeyError):
            PythonDiagramsEngine.get_canonical_preset("non_existent_preset")


class TestPythonDiagramsLinter:
    """Verify static architectural and AST linting diagnostics."""

    def test_lint_spec_detects_duplicates_and_orphans(self) -> None:
        """Verify spec linting flags duplicate variables and orphan nodes."""
        spec = DiagramSpec(
            title="Flawed Architecture",
            filename="flawed",
            nodes=(
                DiagramNode("aws", "compute", "EC2", "server-1", "srv"),
                DiagramNode("aws", "compute", "EC2", "server-2", "srv"),  # Duplicate var_name
                DiagramNode("aws", "database", "RDS", "lonely-db", "orphan_db"),
            ),
            edges=(
                DiagramEdge("srv", "srv"),
            ),
            show=True,  # Flawed: show=True
        )

        report = PythonDiagramsEngine.lint_spec(spec)
        assert report.valid is False
        assert any("Duplicate node variable name" in err for err in report.errors)
        assert any("Orphan node" in warn for warn in report.warnings)
        assert any("show=True" in warn for warn in report.warnings)

    def test_lint_script_code_ast(self) -> None:
        """Verify AST code linting on Python source strings."""
        good_code = """
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Good Arch", show=False):
    api = EC2("api")
"""
        rep_good = PythonDiagramsEngine.lint_script_code(good_code)
        assert rep_good.valid is True
        assert len(rep_good.errors) == 0
        assert "aws" in rep_good.providers_used

        bad_code = """
from diagrams import Diagram
with Diagram("Bad Arch", show=True):
    pass
"""
        rep_bad = PythonDiagramsEngine.lint_script_code(bad_code)
        assert rep_bad.valid is True  # valid syntax
        assert any("show=True" in warn for warn in rep_bad.warnings)

        syntax_error_code = "with Diagram('Broken':"
        rep_err = PythonDiagramsEngine.lint_script_code(syntax_error_code)
        assert rep_err.valid is False
        assert len(rep_err.errors) > 0


class TestPythonDiagramsSkillHygiene:
    """Verify package structural hygiene against SkillValidator and SkillCardParser."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        """Assert that SkillValidator passes with zero errors (Rule 34, Rule 38)."""
        assert skill_dir.exists(), f"Skill directory missing: {skill_dir}"
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_parser_complete(self, skill_dir: Path) -> None:
        """Assert that SkillCardParser parses all stages, anti-patterns, and invariants."""
        parsed = SkillCardParser.parse_directory(skill_dir)
        assert parsed is not None
        assert parsed.name == "python-diagrams-architect"

        # Verify 5 stages
        assert len(parsed.stages) >= 5, f"Expected >= 5 stages, found {len(parsed.stages)}"

        # Verify anti-patterns (>= 4)
        assert len(parsed.anti_patterns) >= 4, f"Expected >= 4 anti-patterns, found {len(parsed.anti_patterns)}"

        # Verify invariants (>= 4)
        assert len(parsed.invariants) >= 4, f"Expected >= 4 invariants, found {len(parsed.invariants)}"
        assert all(inv.is_blocking for inv in parsed.invariants)
