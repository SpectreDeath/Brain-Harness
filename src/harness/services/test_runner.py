"""Test Runner and TDD Execution Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class TestDiscoverResult(BaseModel):
    """Result of test discovery across workspace."""

    status: str = Field(default="ok", description="Status indicator")
    total_test_files: int = Field(default=0, description="Count of test files found")
    total_test_functions: int = Field(default=0, description="Count of test functions identified")
    test_files: list[dict[str, Any]] = Field(default_factory=list, description="Details of discovered test files and functions")
    error: str | None = Field(default=None, description="Error details if discovery failed")


class TestRunResult(BaseModel):
    """Result of running tests via pytest."""

    status: str = Field(default="ok", description="Status indicator (ok, failed, timeout, error)")
    success: bool = Field(default=False, description="True if test execution succeeded with 0 exit code")
    exit_code: int = Field(default=0, description="Process exit code")
    passed: int = Field(default=0, description="Count of passed test cases")
    failed: int = Field(default=0, description="Count of failed test cases")
    skipped: int = Field(default=0, description="Count of skipped test cases")
    errors: int = Field(default=0, description="Count of error test cases")
    duration: float = Field(default=0.0, description="Execution duration in seconds")
    failures_count: int = Field(default=0, description="Count of parsed failure summaries")
    failures: list[dict[str, str]] = Field(default_factory=list, description="Parsed failure traces and headers")
    raw_summary: str = Field(default="", description="Raw pytest summary line")
    error: str | None = Field(default=None, description="Error explanation if run failed")


@runtime_checkable
class TestRunnerService(Protocol):
    """Protocol for test discovery and test suite execution."""

    __test__ = False

    def discover(self, root_dir: str = ".") -> dict[str, Any] | TestDiscoverResult:
        """Discover test files and functions across a workspace."""
        ...

    async def run(
        self,
        target_path: str = "tests",
        *,
        markers: str | None = None,
        keyword_filter: str | None = None,
        timeout: float = 60.0,
        root_dir: str = ".",
    ) -> dict[str, Any] | TestRunResult:
        """Execute pytest on target paths and return structured results."""
        ...


TEST_RUNNER_KEY: ServiceKey[TestRunnerService] = ServiceKey("service.test_runner")
