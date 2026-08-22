"""Test Runner & TDD Execution Service Plugin for Brain Harness.

Provides autonomous test discovery, test suite execution (pytest/unittest),
and structured failure/traceback extraction for iterative TDD agent loops.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import re
import sys
import time
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

TEST_RUNNER_KEY: ServiceKey[TestRunnerService] = ServiceKey("software.test_runner")


def discover_tests(root_dir: str = ".") -> dict[str, Any]:
    """Discover test files and test functions across a workspace."""
    root = Path(root_dir).resolve()
    if not root.exists():
        return {"status": "error", "error": f"Directory not found: {root_dir}", "test_files": []}

    test_files: list[dict[str, Any]] = []
    skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules"}

    for p in root.rglob("*.py"):
        if any(part in skip_dirs for part in p.parts):
            continue
        if p.name.startswith("test_") or p.name.endswith("_test.py") or "tests" in p.parts:
            try:
                rel = str(p.relative_to(root))
                content = p.read_text(encoding="utf-8", errors="ignore")
                test_funcs = re.findall(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(", content)
                test_classes = re.findall(r"class\s+(Test[a-zA-Z0-9_]+)\s*[:\(]", content)
                test_files.append({
                    "path": rel,
                    "functions_count": len(test_funcs),
                    "functions": test_funcs[:20],
                    "classes": test_classes,
                })
            except Exception:
                pass

    total_funcs = sum(tf["functions_count"] for tf in test_files)
    return {
        "status": "ok",
        "total_test_files": len(test_files),
        "total_test_functions": total_funcs,
        "test_files": test_files,
    }


async def run_tests(
    target_path: str = "tests",
    *,
    markers: str | None = None,
    keyword_filter: str | None = None,
    timeout: float = 60.0,
    root_dir: str = ".",
) -> dict[str, Any]:
    """Execute pytest on target paths and parse results into structured feedback."""
    root = Path(root_dir).resolve()
    start_time = time.time()

    cmd = [sys.executable, "-m", "pytest", target_path, "--tb=short", "-q"]
    if markers:
        cmd.extend(["-m", markers])
    if keyword_filter:
        cmd.extend(["-k", keyword_filter])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = time.time() - start_time
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            _ = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = proc.returncode or 0
        except asyncio.TimeoutError:
            proc.kill()
            return {
                "status": "timeout",
                "passed": 0,
                "failed": 0,
                "duration": round(time.time() - start_time, 2),
                "error": f"Test execution timed out after {timeout}s",
                "success": False,
            }

        # Parse output metrics
        passed_match = re.search(r"(\d+)\s+passed", stdout)
        failed_match = re.search(r"(\d+)\s+failed", stdout)
        skipped_match = re.search(r"(\d+)\s+skipped", stdout)
        error_match = re.search(r"(\d+)\s+error", stdout)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        errors = int(error_match.group(1)) if error_match else 0

        # Extract failure summaries
        failures: list[dict[str, str]] = []
        if failed > 0 or errors > 0:
            for section in re.split(r"_{3,}\s*", stdout):
                if "FAILED" in section or "ERROR" in section:
                    lines = section.strip().splitlines()
                    header = lines[0] if lines else "Unknown test failure"
                    failures.append({
                        "header": header[:100],
                        "details": "\n".join(lines[:15]),
                    })

        return {
            "status": "ok" if exit_code == 0 else "failed",
            "success": exit_code == 0,
            "exit_code": exit_code,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "duration": round(duration, 2),
            "failures_count": len(failures),
            "failures": failures[:10],
            "raw_summary": stdout.splitlines()[-1] if stdout.splitlines() else "",
        }

    except Exception as e:
        return {
            "status": "error",
            "success": False,
            "error": str(e),
            "duration": round(time.time() - start_time, 2),
        }


class TestRunnerService:
    """Service facade for autonomous test running."""

    def discover(self, root_dir: str = ".") -> dict[str, Any]:
        return discover_tests(root_dir)

    async def run(
        self,
        target_path: str = "tests",
        *,
        markers: str | None = None,
        keyword_filter: str | None = None,
        timeout: float = 60.0,
        root_dir: str = ".",
    ) -> dict[str, Any]:
        return await run_tests(
            target_path=target_path,
            markers=markers,
            keyword_filter=keyword_filter,
            timeout=timeout,
            root_dir=root_dir,
        )


class TestRunnerPlugin(HarnessPlugin):
    """Plugin providing test running and TDD capabilities."""

    @property
    def name(self) -> str:
        return "plugin.test_runner"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Autonomous test discovery, test execution, and structured failure parsing for TDD workflows"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [TEST_RUNNER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(TEST_RUNNER_KEY, TestRunnerService(), provider=self.name)
        logger.info("TestRunnerService provided", plugin=self.name)
