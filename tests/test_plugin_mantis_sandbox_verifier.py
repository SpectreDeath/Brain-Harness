"""Tests for Google Mantis Sandbox Verifier Plugin."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.mantis_sandbox_verifier.main import (
    MANTIS_SANDBOX_VERIFIER_KEY,
    MantisSandboxEngine,
    MantisSandboxVerifierPlugin,
    MantisSandboxVerifierService,
    mantis_patch_verify,
    mantis_reproduce_crash,
    mantis_sandbox_exec,
)


@pytest.mark.unit
class TestMantisSandboxVerifierPlugin:
    """Unit test suite for Mantis sandbox execution and patch verification."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey into ServiceContext."""
        ctx = ServiceContext()
        plugin = MantisSandboxVerifierPlugin()

        assert plugin.name == "plugin.mantis_sandbox_verifier"
        assert MANTIS_SANDBOX_VERIFIER_KEY in plugin.provides

        await plugin.on_load(ctx)
        svc = ctx.require(MANTIS_SANDBOX_VERIFIER_KEY)
        assert isinstance(svc, MantisSandboxVerifierService)

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    @pytest.mark.asyncio
    async def test_sandbox_exec_pipe_disposal(self) -> None:
        """Verify subprocess execution runs and cleanly disposes stream pipes (Rule 14)."""
        engine = MantisSandboxEngine()
        cmd = f'"{sys.executable}" -c "import sys; sys.stdout.write(\'HELLO_SANDBOX\')"'
        res = await engine.sandbox_exec(command=cmd, timeout_seconds=10)

        assert res["status"] == "ok"
        assert res["exit_code"] == 0
        assert "HELLO_SANDBOX" in res["stdout"]

    def test_reproduce_crash_detection(self) -> None:
        """Verify reproducer detects crashes and handles normal exit codes."""
        # 1. Script that raises an exception / crash
        crashing_script = "raise ValueError('Simulated vulnerability crash!')"
        repro_res = mantis_reproduce_crash(
            reproducer_script=crashing_script,
            target_file="app.py",
            sanitizers=["asan"]
        )
        assert repro_res["status"] == "ok"
        assert repro_res["crashed"] is True
        assert repro_res["verdict"] == "CRASH_REPRODUCED"

        # 2. Script that exits cleanly
        clean_script = "print('All checks pass cleanly'); import sys; sys.exit(0)"
        clean_res = mantis_reproduce_crash(
            reproducer_script=clean_script,
            target_file="app.py"
        )
        assert clean_res["crashed"] is False
        assert clean_res["verdict"] == "CRASH_NOT_REPRODUCED"

    def test_patch_verify_lifecycle(self) -> None:
        """Verify transactional patch verification gate and re-attack checks."""
        diff = """--- app.py
+++ app.py
@@ -1,1 +1,2 @@
-# Unsafe code
+# Safe patched code
"""
        # Reproducer fails to crash after patch is applied
        safe_reproducer = "import sys; sys.exit(0)"
        patch_res = mantis_patch_verify(
            diff_content=diff,
            reproducer_script=safe_reproducer,
            run_bypass_reattack=False
        )

        assert patch_res["status"] == "ok"
        assert patch_res["patch_applied"] is True
        assert patch_res["crashed_after_patch"] is False
        assert patch_res["verified_secure"] is True
        assert patch_res["verdict"] == "VERIFIED_SECURE"
