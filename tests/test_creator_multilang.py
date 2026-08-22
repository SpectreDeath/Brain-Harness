"""Unit tests for multi-language archetypes (Python, JS, TS) and AST signature matching."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.creator import PluginCreator
from harness.creator.validator import AstSignatureMatchingRule, ValidationContext
from harness.plugins.manifest import EntrypointSpec, ParameterSpec, PluginManifest


@pytest.mark.unit
class TestMultiLanguageArchetypes:
    @pytest.mark.parametrize("preset", [
        "general",
        "tool",
        "api_wrapper",
        "service",
        "mcp_bridge",
        "agentic_workflow",
        "container",
    ])
    @pytest.mark.parametrize("language", ["python", "javascript", "typescript"])
    def test_scaffold_and_validate_matrix(self, preset: str, language: str, tmp_path: Path) -> None:
        target = tmp_path / f"{preset}_{language}"
        res = PluginCreator.scaffold(
            target,
            name=f"{preset}-{language}",
            preset=preset,
            language=language,
            auto_validate=True,
        )

        assert res.path == target
        assert res.validation_report is not None
        assert res.validation_report.valid is True, f"Failed for {preset} ({language}): {res.validation_report.errors}"
        assert (target / "plugin.json").exists()

        if language == "python":
            assert (target / "main.py").exists()
            assert (target / "requirements.txt").exists()
        elif language == "javascript":
            assert (target / "index.js").exists()
            assert (target / "package.json").exists()
        elif language == "typescript":
            assert (target / "index.ts").exists()
            assert (target / "package.json").exists()
            assert (target / "tsconfig.json").exists()

        if preset == "container":
            assert (target / "Dockerfile").exists()
            dockerfile = (target / "Dockerfile").read_text(encoding="utf-8")
            if language == "python":
                assert "python" in dockerfile
            else:
                assert "node" in dockerfile


@pytest.mark.unit
class TestAstSignatureMatchingExtended:
    @pytest.mark.asyncio
    async def test_kwonly_and_posonly_arguments(self, tmp_path: Path) -> None:
        manifest = PluginManifest(
            name="test_kwonly",
            version="0.1.0",
            description="Test kwonly",
            language="python",
            entrypoint="main.py",
            entrypoints=[
                EntrypointSpec(
                    name="complex_args",
                    description="Test",
                    parameters=[
                        ParameterSpec(name="pos_req", type="string", required=True),
                        ParameterSpec(name="kw_req", type="string", required=True),
                    ],
                )
            ],
        )

        code = (
            "def complex_args(pos_req, /, *, kw_req: str) -> dict:\n"
            "    return {'status': 'ok'}\n"
        )
        (tmp_path / "main.py").write_text(code, encoding="utf-8")
        (tmp_path / "plugin.json").write_text(manifest.model_dump_json(), encoding="utf-8")

        rule = AstSignatureMatchingRule()
        ctx = ValidationContext(path=tmp_path)
        ctx.manifest = manifest
        await rule.validate(ctx)

        assert ctx.report.valid is True
        assert len(ctx.report.warnings) == 0

    @pytest.mark.asyncio
    async def test_kwargs_accepts_extra_parameters(self, tmp_path: Path) -> None:
        manifest = PluginManifest(
            name="test_kwargs",
            version="0.1.0",
            description="Test kwargs",
            language="python",
            entrypoint="main.py",
            entrypoints=[
                EntrypointSpec(
                    name="flexible",
                    description="Test",
                    parameters=[
                        ParameterSpec(name="task", type="string", required=True),
                        ParameterSpec(name="extra_field", type="string", required=True),
                    ],
                )
            ],
        )

        code = (
            "def flexible(task: str, **kwargs) -> dict:\n"
            "    return {'status': 'ok'}\n"
        )
        (tmp_path / "main.py").write_text(code, encoding="utf-8")
        (tmp_path / "plugin.json").write_text(manifest.model_dump_json(), encoding="utf-8")

        rule = AstSignatureMatchingRule()
        ctx = ValidationContext(path=tmp_path)
        ctx.manifest = manifest
        await rule.validate(ctx)

        assert ctx.report.valid is True
        assert len(ctx.report.warnings) == 0
