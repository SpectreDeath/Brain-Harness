"""Tests for Refactor Engine plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.refactor_engine import (
    REFACTOR_ENGINE_KEY,
    FunctionExtractResult,
    RefactorEngineService,
    UnusedFunctionsResult,
)
from plugins.software_engineering.refactor_engine.main import (
    RefactorEnginePlugin,
    extract_function_preview,
    find_unused_functions,
)


@pytest.mark.unit
class TestRefactorEnginePlugin:
    def test_find_unused_functions(self) -> None:
        code = (
            "def used_func():\n"
            "    return 1\n\n"
            "def dead_func():\n"
            "    return 2\n\n"
            "def main():\n"
            "    used_func()\n"
        )
        res = find_unused_functions(code)
        assert res["status"] == "ok"
        unused_names = [f["name"] for f in res["unused_functions"]]
        assert "dead_func" in unused_names
        assert "used_func" not in unused_names

    def test_extract_function_preview(self) -> None:
        code = (
            "def process():\n"
            "    a = 10\n"
            "    b = 20\n"
            "    c = a + b\n"
        )
        res = extract_function_preview(code, start_line=2, end_line=3, new_func_name="compute_values")
        assert res["status"] == "ok"
        assert "def compute_values():" in res["refactored_preview"]

    @pytest.mark.asyncio
    async def test_refactor_engine_plugin_ioc_lifecycle(self) -> None:
        plugin = RefactorEnginePlugin()
        assert plugin.name == "plugin.refactor_engine"
        assert REFACTOR_ENGINE_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(REFACTOR_ENGINE_KEY)
        assert isinstance(service, RefactorEngineService)

        code = "def alpha(): pass\ndef beta(): alpha()\n"
        unused_res = service.find_unused_functions(code)
        assert isinstance(unused_res, UnusedFunctionsResult)
        assert unused_res.status == "ok"
        assert len(unused_res.unused_functions) == 1
        assert unused_res.unused_functions[0]["name"] == "beta"

        extract_res = service.extract_function_preview(code, start_line=1, end_line=1, new_func_name="new_helper")
        assert isinstance(extract_res, FunctionExtractResult)
        assert extract_res.status == "ok"
        assert "def new_helper():" in extract_res.refactored_preview

        await plugin.on_disable()
        await plugin.on_unload()
