"""Tests for Deepened Plugin Creator Subsystem Architecture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from harness.creator.archetypes import (
    AgenticWorkflowArchetype,
    ArchetypeRegistry,
    ContainerArchetype,
)
from harness.creator.dynamic import DynamicPluginBuilder, DynamicPythonPlugin
from harness.creator.scaffold import (
    PluginScaffoldEngine,
    ScaffoldOptions,
    ScaffoldResult,
)
from harness.creator.validator import (
    AstSignatureMatchingRule,
    PluginValidator,
    RuleSeverity,
    ValidationFixer,
)
from harness.kernel.context import ServiceContext
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin


@pytest.mark.unit
class TestDeepenedScaffoldEngine:
    def test_scaffold_result_dataclass_and_path_compatibility(self, tmp_path: Path) -> None:
        target = tmp_path / "scaffold_res_test"
        engine = PluginScaffoldEngine()
        res = engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="test-scaffold-res",
                preset="general",
                tools=["calc_tax", "calc_discount"],
            ),
        )

        assert isinstance(res, ScaffoldResult)
        assert res.path == target
        assert res.files_count >= 5
        assert res.exists() is True
        assert (res / "plugin.json").exists()
        assert Path(res) == target
        assert str(res) == str(target)

        # Test to_dict serialization
        data = res.to_dict()
        assert data["path"] == str(target)
        assert data["files_count"] >= 5
        assert data["manifest"]["name"] == "test-scaffold-res"

    def test_scaffold_agentic_workflow_archetype(self, tmp_path: Path) -> None:
        target = tmp_path / "my_workflow"
        engine = PluginScaffoldEngine()
        res = engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="agent-optimizer",
                preset="agentic_workflow",
                language="python",
            ),
        )

        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()
        assert (target / "README.md").exists()
        assert (target / ".gitignore").exists()
        assert (target / "tests" / "test_plugin.py").exists()

        manifest = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        assert manifest["category"] == "agent"
        ep_names = [ep["name"] for ep in manifest["entrypoints"]]
        assert "plan" in ep_names
        assert "execute_step" in ep_names
        assert "evaluate" in ep_names

        main_py = (target / "main.py").read_text(encoding="utf-8")
        assert "def plan(" in main_py
        assert "def execute_step(" in main_py
        assert "def evaluate(" in main_py

    def test_scaffold_container_archetype(self, tmp_path: Path) -> None:
        target = tmp_path / "container_plugin"
        engine = PluginScaffoldEngine()
        res = engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="sandbox-runner",
                preset="container",
                language="python",
                tools=["run_task"],
            ),
        )

        assert (target / "plugin.json").exists()
        assert (target / "Dockerfile").exists()
        assert (target / ".dockerignore").exists()
        assert (target / "main.py").exists()

        manifest = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        assert manifest["isolation"] == "docker"

        dockerfile = (target / "Dockerfile").read_text(encoding="utf-8")
        assert "FROM python:3.11-slim" in dockerfile

    def test_scaffold_with_template_override(self, tmp_path: Path) -> None:
        templates_dir = tmp_path / "custom_templates"
        templates_dir.mkdir()
        (templates_dir / "entrypoint_general.py").write_text(
            '"""Custom template entrypoint."""\n\ndef execute(): return {"custom": True}\n',
            encoding="utf-8",
        )

        target = tmp_path / "templated_plugin"
        engine = PluginScaffoldEngine(templates_dir=templates_dir)
        engine.scaffold(target, name="templated-plugin")

        main_code = (target / "main.py").read_text(encoding="utf-8")
        assert "Custom template entrypoint" in main_code


@pytest.mark.unit
class TestDeepenedValidatorAndRemediation:
    @pytest.mark.asyncio
    async def test_ast_signature_matching_pass(self, tmp_path: Path) -> None:
        target = tmp_path / "sig_pass"
        engine = PluginScaffoldEngine()
        engine.scaffold(target, name="sig-pass", preset="general", tools=["execute"])

        report = await PluginValidator.validate(target)
        assert report.valid is True
        assert any(c.name == "AST Signature Matching" and c.passed for c in report.checks)

    @pytest.mark.asyncio
    async def test_validation_fixer_remediate_missing_manifest(self, tmp_path: Path) -> None:
        target = tmp_path / "broken_plugin"
        target.mkdir()
        (target / "main.py").write_text('def execute(task=""): return {"status": "ok"}\n', encoding="utf-8")

        # Initial validation should fail
        fail_report = await PluginValidator.validate(target)
        assert fail_report.valid is False

        # Run with auto-remediation
        fixed_report = await ValidationFixer.remediate(target)
        assert fixed_report.valid is True
        assert (target / "plugin.json").exists()
        assert len(fixed_report.remediations) >= 1

    @pytest.mark.asyncio
    async def test_validation_fixer_remediate_missing_functions(self, tmp_path: Path) -> None:
        target = tmp_path / "missing_func_plugin"
        target.mkdir()
        manifest_data = {
            "name": "auto-fix-funcs",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
            "entrypoints": [
                {"name": "func_a", "parameters": []},
                {"name": "func_b", "parameters": []},
            ],
        }
        (target / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (target / "main.py").write_text('"""Entrypoint"""\ndef func_a(): pass\n', encoding="utf-8")

        fixed_report = await ValidationFixer.remediate(target)
        assert fixed_report.valid is True

        main_text = (target / "main.py").read_text(encoding="utf-8")
        assert "def func_b(" in main_text


@pytest.mark.unit
class TestDeepenedDynamicPlugin:
    def test_infer_manifest_from_typed_functions(self) -> None:
        def query_metrics(service_id: str, limit: int = 50, verbose: bool = False) -> dict[str, Any]:
            """Retrieve live telemetry metrics."""
            return {"service": service_id, "limit": limit}

        plugin = DynamicPluginBuilder.from_functions(
            name="telemetry-sampler",
            functions=[query_metrics],
            description="Live telemetry sampler",
        )

        manifest = plugin.infer_manifest()
        assert manifest.name == "telemetry-sampler"
        assert len(manifest.entrypoints) == 1
        ep = manifest.entrypoints[0]
        assert ep.name == "query_metrics"
        assert ep.description == "Retrieve live telemetry metrics."

        params = {p.name: p for p in ep.parameters}
        assert params["service_id"].type == "string"
        assert params["service_id"].required is True
        assert params["limit"].type == "integer"
        assert params["limit"].default == 50
        assert params["verbose"].type == "boolean"

    @pytest.mark.asyncio
    async def test_dynamic_plugin_hot_reload(self) -> None:
        initial_code = """
def math_add(a: int, b: int) -> int:
    return a + b
"""
        plugin = DynamicPluginBuilder.from_code("dynamic-math", initial_code)

        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        tool_reg = ctx.require(TOOL_REGISTRY_KEY)
        assert "math_add" in tool_reg

        res1 = await tool_reg.invoke("math_add", {"a": 10, "b": 20})
        assert res1 == {"status": "ok", "result": 30}

        # Hot reload with new function
        updated_code = """
def math_add(a: int, b: int) -> int:
    return a + b

def math_mult(a: int, b: int) -> int:
    return a * b
"""
        await plugin.reload_code(updated_code)
        assert "math_mult" in tool_reg

        res2 = await tool_reg.invoke("math_mult", {"a": 6, "b": 7})
        assert res2 == {"status": "ok", "result": 42}

        await plugin.on_disable()

    def test_dynamic_plugin_export_project(self, tmp_path: Path) -> None:
        code = """
def text_summarize(text: str) -> str:
    return text[:20] + "..."
"""
        plugin = DynamicPluginBuilder.from_code("text-summarizer", code)
        target = tmp_path / "exported_text_plugin"

        res = plugin.export_project(target, preset="tool")
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()
        assert (target / "tests" / "test_plugin.py").exists()

        main_content = (target / "main.py").read_text(encoding="utf-8")
        assert "def text_summarize(" in main_content
