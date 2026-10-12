"""Orca CLI process transport and in-memory mock state store."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

import structlog

from harness.services.orca_bridge import (
    OrcaRunInfo,
    OrcaWorkerDispatchReceipt,
    OrcaWorktreeInfo,
)

logger = structlog.get_logger(__name__)


class OrcaTransportMixin:
    """Manages CLI binary execution and in-memory fallback state stores."""

    def __init__(self, orca_bin: str | None = None) -> None:
        self._orca_bin = (
            orca_bin
            or os.environ.get("ORCA_BIN")
            or shutil.which("orca")
            or shutil.which("orca.cmd")
        )
        self._mock_worktrees: dict[str, OrcaWorktreeInfo] = {}
        self._mock_runs: dict[str, OrcaRunInfo] = {}
        self._mock_dispatches: dict[str, OrcaWorkerDispatchReceipt] = {}
        self._mock_inbox: list[dict[str, Any]] = []

    @property
    def is_cli_available(self) -> bool:
        """Return True if the orca CLI binary is found on PATH or configured."""
        return self._orca_bin is not None

    def _run_cli(self, args: list[str]) -> dict[str, Any]:
        """Execute orca CLI command with JSON formatting and UTF-8 encoding (Rule 23, Rule 14)."""
        if not self._orca_bin:
            raise FileNotFoundError("Orca CLI executable not found on PATH")

        cmd = [self._orca_bin, *args, "--json"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            stdout, stderr = proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            raise TimeoutError(f"Orca command timed out after 60s: {' '.join(cmd)}")
        finally:
            if proc.stdin:
                proc.stdin.close()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()

        if proc.returncode != 0:
            logger.warning(
                "Orca CLI returned non-zero", code=proc.returncode, stderr=stderr
            )
            raise RuntimeError(
                f"Orca command failed ({proc.returncode}): {stderr.strip()}"
            )

        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to parse Orca CLI output as JSON: {stdout}"
            ) from exc
