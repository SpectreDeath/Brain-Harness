"""Tests for code_runner plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.code_runner import (
    CODE_RUNNER_KEY,
    CodeRunnerService,
    PythonEvalResult,
    PythonExecResult,
    ScriptRunResult,
)
from plugins.software_engineering.code_runner.main import (
    CodeRunnerPlugin,
    python_eval,
    python_exec,
    run_temp_script,
)


@pytest.mark.unit
class TestCodeRunnerPlugin:
    def test_python_exec_success(self) -> None:
        code = "for i in range(3): print(f'count_{i}')"
        res = python_exec(code)
        assert res["status"] == "ok"
        assert res["success"] is True
        assert res["returncode"] == 0
        assert "count_0\ncount_1\ncount_2" in res["stdout"]

    def test_python_exec_error(self) -> None:
        code = "raise ValueError('Intentional failure')"
        res = python_exec(code)
        assert res["status"] == "ok"
        assert res["success"] is False
        assert "ValueError: Intentional failure" in res["stderr"]

    def test_python_exec_timeout(self) -> None:
        code = "import time; time.sleep(2)"
        res = python_exec(code, timeout=0.1)
        assert res["status"] == "error"
        assert res["timed_out"] is True

    def test_python_eval(self) -> None:
        res = python_eval("[x ** 2 for x in range(4)]")
        assert res["status"] == "ok"
        assert res["result"] == "[0, 1, 4, 9]"

    def test_run_temp_script_with_args(self) -> None:
        script = """
import sys
print(f"args_received: {len(sys.argv) - 1}")
for a in sys.argv[1:]:
    print(f"arg: {a}")
"""
        res = run_temp_script(script, args=["alpha", "beta"])
        assert res["status"] == "ok"
        assert res["success"] is True
        assert "args_received: 2" in res["stdout"]
        assert "arg: alpha" in res["stdout"]
        assert "arg: beta" in res["stdout"]

    @pytest.mark.asyncio
    async def test_code_runner_plugin_ioc_lifecycle(self) -> None:
        plugin = CodeRunnerPlugin()
        assert plugin.name == "plugin.code_runner"
        assert CODE_RUNNER_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(CODE_RUNNER_KEY)
        assert isinstance(service, CodeRunnerService)

        exec_res = await service.exec_python_async("print('async code runner')")
        assert isinstance(exec_res, PythonExecResult)
        assert exec_res.success is True
        assert "async code runner" in exec_res.stdout

        eval_res = await service.eval_python_async("3 + 7")
        assert isinstance(eval_res, PythonEvalResult)
        assert eval_res.result == "10"

        script_res = await service.run_temp_script_async("import sys; print(sys.version_info.major)")
        assert isinstance(script_res, ScriptRunResult)
        assert script_res.success is True
        assert "3" in script_res.stdout

        await plugin.on_disable()
        await plugin.on_unload()
