"""Tests for bridge_runner hardening: stdout isolation and resource limits."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from harness.plugins.sandbox import SubprocessExecutor


@pytest.mark.integration
@pytest.mark.asyncio
class TestBridgeHardening:
    async def test_stdout_poisoning_isolation(self, tmp_path: Path) -> None:
        """Verify that print() calls in plugin code go to stderr and do not corrupt JSON-RPC."""
        script = tmp_path / "noisy_plugin.py"
        script.write_text(
            """
import sys

# Top-level print during module import
print("POISON_IMPORT_STDOUT")

def noisy_method(x: int) -> int:
    # Print during RPC method execution
    print(f"POISON_METHOD_STDOUT: {x}")
    sys.stdout.write("POISON_DIRECT_STDOUT\\n")
    return x * 2
""",
            encoding="utf-8",
        )

        executor = SubprocessExecutor(script)
        await executor.start()
        try:
            assert executor.is_running
            # Invoke method - this must succeed without JSONDecodeError
            res = await executor.execute("noisy_method", {"x": 21})
            assert res == {"status": "ok", "result": 42}

            # Verify that the poison was redirected to stderr
            stderr_content = "\n".join(executor.transport.stderr_lines)
            assert "POISON_IMPORT_STDOUT" in stderr_content
            assert "POISON_METHOD_STDOUT: 21" in stderr_content
            assert "POISON_DIRECT_STDOUT" in stderr_content
        finally:
            await executor.stop()
            assert not executor.is_running

    async def test_subprocess_resource_limits_env(self, tmp_path: Path) -> None:
        """Verify that HARNESS_MEM_LIMIT_MB and HARNESS_CPU_LIMIT_S do not crash startup."""
        script = tmp_path / "resource_plugin.py"
        script.write_text(
            """
def echo(val: str) -> str:
    return f"echo:{val}"
""",
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["HARNESS_MEM_LIMIT_MB"] = "256"
        env["HARNESS_CPU_LIMIT_S"] = "30"

        executor = SubprocessExecutor(script, env=env)
        await executor.start()
        try:
            assert executor.is_running
            res = await executor.execute("echo", {"val": "bound"})
            assert res == {"status": "ok", "result": "echo:bound"}
        finally:
            await executor.stop()
            assert not executor.is_running
