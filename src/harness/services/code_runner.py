"""Sandboxed Python Code Runner Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class PythonExecResult(BaseModel):
    """Result of executing a Python code block in subprocess."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    success: bool = Field(default=False, description="True if process returned exit code 0")
    returncode: int = Field(default=0, description="Process return code")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    timed_out: bool = Field(default=False, description="True if execution exceeded timeout limit")
    error: str | None = Field(default=None, description="Error explanation if execution failed")


class PythonEvalResult(BaseModel):
    """Result of evaluating a single Python expression."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    expression: str = Field(default="", description="Evaluated Python expression string")
    result: str = Field(default="", description="String representation of evaluated result")
    error: str | None = Field(default=None, description="Error explanation if evaluation failed")


class ScriptRunResult(BaseModel):
    """Result of running a temporary Python script with arguments."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    success: bool = Field(default=False, description="True if process returned exit code 0")
    returncode: int = Field(default=0, description="Process return code")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    timed_out: bool = Field(default=False, description="True if script timed out")
    error: str | None = Field(default=None, description="Error explanation if execution failed")


@runtime_checkable
class CodeRunnerService(Protocol):
    """Protocol for sandboxed Python code execution and expression evaluation."""

    def exec_python(self, code: str, timeout: float = 10.0) -> PythonExecResult:
        """Execute a block of Python code in an isolated subprocess synchronously."""
        ...

    async def exec_python_async(self, code: str, timeout: float = 10.0) -> PythonExecResult:
        """Execute Python code asynchronously without blocking the event loop."""
        ...

    def eval_python(self, expression: str, timeout: float = 5.0) -> PythonEvalResult:
        """Evaluate a single Python expression and capture output synchronously."""
        ...

    async def eval_python_async(self, expression: str, timeout: float = 5.0) -> PythonEvalResult:
        """Evaluate a single Python expression asynchronously."""
        ...

    def run_temp_script(
        self,
        script_content: str,
        args: list[str] | None = None,
        timeout: float = 15.0,
    ) -> ScriptRunResult:
        """Write script to a temp file, execute with arguments, and clean up."""
        ...

    async def run_temp_script_async(
        self,
        script_content: str,
        args: list[str] | None = None,
        timeout: float = 15.0,
    ) -> ScriptRunResult:
        """Write script to a temp file and execute asynchronously."""
        ...


CODE_RUNNER_KEY: ServiceKey[CodeRunnerService] = ServiceKey("service.code_runner")
