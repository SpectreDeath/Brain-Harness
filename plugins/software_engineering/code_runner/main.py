"""Sandboxed Python code runner and REPL plugin for Brain Harness."""

from __future__ import annotations

import asyncio
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.code_runner import (
    CODE_RUNNER_KEY,
    CodeRunnerService,
    PythonEvalResult,
    PythonExecResult,
    ScriptRunResult,
)

logger = structlog.get_logger(__name__)


def python_exec(code: str, timeout: float = 10.0) -> dict[str, Any]:
    """Execute a block of Python code in an isolated subprocess."""
    try:
        res = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "status": "ok",
            "success": res.returncode == 0,
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": f"Execution timed out after {timeout} seconds.",
            "timed_out": True,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def python_eval(expression: str, timeout: float = 5.0) -> dict[str, Any]:
    """Evaluate a single Python expression and capture the output."""
    wrapper = f"import reprlib; res = ({expression}); print(repr(res))"
    res = python_exec(wrapper, timeout=timeout)
    if res.get("status") != "ok":
        return res

    if not res.get("success"):
        return {
            "status": "error",
            "error": res.get("stderr", "Evaluation failed").strip(),
        }

    return {
        "status": "ok",
        "expression": expression,
        "result": str(res.get("stdout", "")).strip(),
    }


def run_temp_script(
    script_content: str,
    args: list[str] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Write script to a temp file, execute it with arguments, and clean up."""
    temp_dir = tempfile.mkdtemp(prefix="harness_runner_")
    script_file = Path(temp_dir) / "runner_script.py"

    try:
        script_file.write_text(script_content, encoding="utf-8")
        cmd = [sys.executable, str(script_file)]
        if args:
            cmd.extend(args)

        res = subprocess.run(
            cmd,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "status": "ok",
            "success": res.returncode == 0,
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": f"Script execution timed out after {timeout} seconds.",
            "timed_out": True,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        try:
            if script_file.exists():
                script_file.unlink()
            Path(temp_dir).rmdir()
        except Exception:
            pass


class CodeRunnerPlugin(HarnessPlugin, CodeRunnerService):
    """Harness Plugin providing sandboxed Python code execution and expression evaluation."""

    name = "plugin.code_runner"
    version = "1.0.0"
    description = "Sandboxed Python code runner, dynamic REPL expression evaluator, and temp script runner"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CODE_RUNNER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(CODE_RUNNER_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # CodeRunnerService Protocol Implementation
    # -------------------------------------------------------------------------

    def exec_python(self, code: str, timeout: float = 10.0) -> PythonExecResult:
        res = python_exec(code=code, timeout=timeout)
        return PythonExecResult(
            status=res["status"],
            success=res.get("success", False),
            returncode=res.get("returncode", 0),
            stdout=res.get("stdout", ""),
            stderr=res.get("stderr", ""),
            timed_out=res.get("timed_out", False),
            error=res.get("error"),
        )

    async def exec_python_async(self, code: str, timeout: float = 10.0) -> PythonExecResult:
        return await asyncio.to_thread(self.exec_python, code, timeout)

    def eval_python(self, expression: str, timeout: float = 5.0) -> PythonEvalResult:
        res = python_eval(expression=expression, timeout=timeout)
        return PythonEvalResult(
            status=res["status"],
            expression=res.get("expression", expression),
            result=res.get("result", ""),
            error=res.get("error"),
        )

    async def eval_python_async(self, expression: str, timeout: float = 5.0) -> PythonEvalResult:
        return await asyncio.to_thread(self.eval_python, expression, timeout)

    def run_temp_script(
        self,
        script_content: str,
        args: list[str] | None = None,
        timeout: float = 15.0,
    ) -> ScriptRunResult:
        res = run_temp_script(script_content=script_content, args=args, timeout=timeout)
        return ScriptRunResult(
            status=res["status"],
            success=res.get("success", False),
            returncode=res.get("returncode", 0),
            stdout=res.get("stdout", ""),
            stderr=res.get("stderr", ""),
            timed_out=res.get("timed_out", False),
            error=res.get("error"),
        )

    async def run_temp_script_async(
        self,
        script_content: str,
        args: list[str] | None = None,
        timeout: float = 15.0,
    ) -> ScriptRunResult:
        return await asyncio.to_thread(self.run_temp_script, script_content, args, timeout)
