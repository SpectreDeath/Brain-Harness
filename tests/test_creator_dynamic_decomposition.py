"""Characterization test contract for Creator Dynamic decomposed package architecture.

Verifies:
1. Submodule independence and public facade parity.
2. Slotted dataclass architecture for FunctionSignatureMetadata (Rule 12).
3. AST inspector signature extraction and JSONSchema conversion.
4. Isolated module compilation and syntax error safety.
5. In-memory plugin lifecycle, hot-reloading, and manifest inference.
6. DynamicPluginBuilder factory and single-seam resolver (Rule 58).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest

from harness.kernel.context import ServiceContext
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin


@pytest.mark.unit
class TestCreatorDynamicDecompositionParity:
    """Verifies submodule isolation, public export parity, and slotted contracts."""

    def test_submodule_import_isolation(self) -> None:
        """Verify each submodule can be imported independently without circular dependencies."""
        from harness.creator.dynamic import builder, compiler, inspector, models, plugin

        assert hasattr(models, "FunctionSignatureMetadata")
        assert hasattr(inspector, "ASTFunctionInspector")
        assert hasattr(compiler, "_compile_dynamic_module")
        assert hasattr(plugin, "DynamicPythonPlugin")
        assert hasattr(builder, "DynamicPluginBuilder")
        assert hasattr(builder, "resolve_dynamic_builder")

    def test_facade_all_symbol_export_parity(self) -> None:
        """Verify the facade in __init__.py exports all 6 original symbols plus resolver."""
        import harness.creator.dynamic as dyn_pkg

        expected_symbols = [
            "ASTFunctionInspector",
            "DynamicPluginBuilder",
            "DynamicPythonPlugin",
            "FunctionSignatureMetadata",
            "RuntimeIntrospector",
            "_compile_dynamic_module",
        ]
        for sym in expected_symbols:
            assert hasattr(dyn_pkg, sym), f"Facade missing original symbol: {sym}"
            assert sym in dyn_pkg.__all__, f"__all__ missing symbol: {sym}"

    def test_slotted_dataclass_architecture(self) -> None:
        """Verify slotted dataclasses minimize memory footprint (Rule 12)."""
        from harness.creator.dynamic.models import FunctionSignatureMetadata

        assert hasattr(FunctionSignatureMetadata, "__slots__")

        meta = FunctionSignatureMetadata(
            name="multiply",
            docstring="Multiply numbers.",
            parameters={"a": {"type": "integer"}, "b": {"type": "integer", "default": 2}},
            required=["a"],
            return_type="integer",
            is_async=False,
        )
        assert meta.name == "multiply"
        schema = meta.to_parameters_schema()
        assert schema["type"] == "object"
        assert schema["required"] == ["a"]
        assert "b" in schema["properties"]


@pytest.mark.unit
class TestCreatorDynamicCompilerAndInspector:
    """Verifies AST inspection and isolated compilation."""

    def test_ast_inspector_signature_extraction(self) -> None:
        """Verify AST inspector extracts metadata and schemas from Python code."""
        from harness.creator.dynamic.inspector import ASTFunctionInspector

        code = """
def calculate_metric(name: str, value: float = 10.0, tags: list[str] | None = None) -> dict[str, Any]:
    \"\"\"Calculate system metrics.\"\"\"
    return {"metric": name, "val": value}
"""
        meta_map = ASTFunctionInspector.inspect_ast(code)
        assert "calculate_metric" in meta_map
        meta = meta_map["calculate_metric"]
        assert meta.docstring == "Calculate system metrics."
        assert meta.required == ["name"]
        assert meta.parameters["name"]["type"] == "string"
        assert meta.parameters["value"]["type"] == "number"
        assert meta.parameters["value"]["default"] == 10.0

    def test_compile_dynamic_module_success_and_syntax_error(self) -> None:
        """Verify isolated compilation executes code safely and flags syntax errors."""
        from harness.creator.dynamic.compiler import _compile_dynamic_module

        valid_code = "def sample(x: int) -> int:\n    return x + 1\n"
        mod, tools = _compile_dynamic_module("valid_test", valid_code)
        assert "sample" in tools
        assert tools["sample"](5) == 6

        # Syntax error should raise ValueError
        bad_code = "def broken(:\n    pass\n"
        with pytest.raises(ValueError, match="Syntax error in dynamic plugin"):
            _compile_dynamic_module("bad_test", bad_code)


@pytest.mark.unit
class TestCreatorDynamicPluginAndBuilder:
    """Verifies in-memory plugin lifecycle, hot-reloading, and builder factory."""

    @pytest.mark.asyncio
    async def test_dynamic_plugin_lifecycle_and_hot_reload(self) -> None:
        """Verify DynamicPythonPlugin mounting, execution, and hot-reload."""
        from harness.creator.dynamic.builder import DynamicPluginBuilder

        code_v1 = "def ping(msg: str = 'pong') -> str:\n    return f'v1: {msg}'\n"
        plugin = DynamicPluginBuilder.from_code(
            name="live-plugin",
            code=code_v1,
            description="Live testing plugin",
        )

        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        tool_reg = ctx.require(TOOL_REGISTRY_KEY)
        assert "ping" in tool_reg
        res1 = await tool_reg.invoke("ping", {"msg": "hello"})
        assert res1 == {"status": "ok", "result": "v1: hello"}

        # Hot-reload code to v2
        code_v2 = "def ping(msg: str = 'pong') -> str:\n    return f'v2: {msg}'\n"
        await plugin.reload_code(code_v2)

        res2 = await tool_reg.invoke("ping", {"msg": "hello"})
        assert res2 == {"status": "ok", "result": "v2: hello"}

        await plugin.on_disable()
        assert "ping" not in tool_reg
        await plugin.on_unload()

    def test_dynamic_manifest_inference(self) -> None:
        """Verify dynamic plugin manifest inference."""
        from harness.creator.dynamic.builder import DynamicPluginBuilder

        def helper_tool(target: str) -> str:
            """Helpful tool."""
            return target

        plugin = DynamicPluginBuilder.from_functions(
            name="helper-plugin",
            functions=[helper_tool],
        )
        manifest = plugin.infer_manifest()
        assert manifest.name == "helper-plugin"
        assert len(manifest.entrypoints) == 1
        assert manifest.entrypoints[0].name == "helper_tool"

    def test_single_seam_resolver(self) -> None:
        """Verify single-seam resolver function (Rule 58)."""
        from harness.creator.dynamic.builder import (
            DynamicPluginBuilder,
            resolve_dynamic_builder,
        )

        builder_cls = resolve_dynamic_builder(None)
        assert builder_cls is DynamicPluginBuilder or isinstance(builder_cls, DynamicPluginBuilder)

    def test_dynamic_plugin_trusted_isolation_enforcement(self) -> None:
        """Verify dynamic in-process plugins enforce trusted=True and block untrusted code."""
        from harness.creator.dynamic.builder import DynamicPluginBuilder
        from harness.plugins.manifest import IsolationMode

        # Untrusted execution in-process must be rejected loudly
        with pytest.raises(ValueError, match="trusted=False"):
            DynamicPluginBuilder.from_code(
                name="untrusted-plug",
                code="def run(): pass",
                trusted=False,
            )

        # Trusted dynamic plugin succeeds and advertises IN_PROCESS isolation
        trusted_plug = DynamicPluginBuilder.from_code(
            name="trusted-plug",
            code="def run(): return 'ok'",
            trusted=True,
        )
        assert trusted_plug.trusted is True
        assert trusted_plug.isolation == IsolationMode.IN_PROCESS

    def test_sandbox_factory_demotes_untrusted_in_process_request(self, tmp_path: Path) -> None:
        """Verify SandboxExecutorFactory demotes untrusted IN_PROCESS requests to SubprocessExecutor."""
        from harness.plugins.manifest import IsolationMode, PluginManifest
        from harness.plugins.sandbox.factory import SandboxExecutorFactory
        from harness.plugins.sandbox.in_process import InProcessExecutor
        from harness.plugins.sandbox.subprocess import SubprocessExecutor

        ep = tmp_path / "main.py"
        ep.write_text("def run(): return 'hello'")

        manifest = PluginManifest.minimal(name="test_untrusted", entrypoint="main.py")
        manifest.isolation = IsolationMode.IN_PROCESS
        manifest.trusted = False

        executor = SandboxExecutorFactory.create(manifest, tmp_path)
        assert executor is not None
        assert not isinstance(executor, InProcessExecutor)
        assert isinstance(executor, SubprocessExecutor)
