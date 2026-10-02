"""Tests for Continuous Background Reflection Daemon and JUnit Test Trajectory Distillation."""

from __future__ import annotations

import asyncio
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main as cli_main
from harness.creator.reflection import (
    HarnessHistoryHarvester,
    HarnessReflectorEngine,
    MemoryPatternPipeline,
    ReflectionScope,
    ReportArtifact,
    TestExecutionPatternExtractor,
)
from harness.services.reflection_worker import ReflectionDaemonWorker
from harness.services.storage import SQLiteStorageService


SAMPLE_JUNIT_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="0" failures="1" skipped="0" tests="3" time="0.852">
    <testcase classname="tests.test_auth" name="test_login_success" time="0.100" />
    <testcase classname="tests.test_auth" name="test_token_expiry" time="0.250">
      <failure message="AssertionError: Token should have expired after 3600 seconds">
Traceback (most recent call last):
  File "tests/test_auth.py", line 42, in test_token_expiry
    assert token.is_expired()
AssertionError: Token should have expired after 3600 seconds
      </failure>
    </testcase>
    <testcase classname="tests.test_storage" name="test_db_lock_timeout" time="0.502">
      <failure message="TimeoutError: Database lock acquisition timed out">
Traceback (most recent call last):
  File "tests/test_storage.py", line 88, in test_db_lock_timeout
    raise TimeoutError("Database lock acquisition timed out")
TimeoutError: Database lock acquisition timed out
      </failure>
    </testcase>
  </testsuite>
</testsuites>
"""


@pytest.mark.unit
class TestReflectionHarvesterAndExtractor:
    """Verify JUnit XML harvesting and pattern extraction."""

    def test_harvest_junit_reports_valid(self, tmp_path: Path) -> None:
        report_file = tmp_path / "test-report.xml"
        report_file.write_text(SAMPLE_JUNIT_XML, encoding="utf-8")

        harvester = HarnessHistoryHarvester(
            temp_dir=tmp_path / "temp",
            app_data_dir=tmp_path / "app_data",
        )
        reports = harvester.harvest_junit_reports(report_file)

        assert len(reports) == 1
        assert reports[0].report_type == "test_report"
        failures = reports[0].metadata.get("failures", [])
        assert len(failures) == 2

        assert failures[0]["test_name"] == "tests.test_auth::test_token_expiry"
        assert failures[0]["test_file"] == "tests.test_auth"
        assert "AssertionError: Token should have expired" in failures[0]["message"]

        assert failures[1]["test_name"] == "tests.test_storage::test_db_lock_timeout"
        assert failures[1]["test_file"] == "tests.test_storage"
        assert "Database lock acquisition timed out" in failures[1]["message"]

    def test_harvest_junit_reports_missing_or_corrupt(self, tmp_path: Path) -> None:
        harvester = HarnessHistoryHarvester(
            temp_dir=tmp_path / "temp",
            app_data_dir=tmp_path / "app_data",
        )
        # Missing file
        assert harvester.harvest_junit_reports(tmp_path / "nonexistent.xml") == []

        # Corrupted file
        corrupt_file = tmp_path / "corrupt.xml"
        corrupt_file.write_text("NOT XML CONTENT <<< >>>", encoding="utf-8")
        assert harvester.harvest_junit_reports(corrupt_file) == []

    def test_pattern_extractor_junit_failures(self) -> None:
        extractor = TestExecutionPatternExtractor()
        report = ReportArtifact(
            file_path=Path("test-report.xml"),
            title="CI Test Run Report (test-report.xml)",
            created_at="2026-10-02T12:00:00Z",
            report_type="test_report",
            content_text="2 failures encountered",
            friction_points=["tests.test_auth::test_token_expiry: failure"],
            metadata={
                "failures": [
                    {
                        "test_name": "tests.test_auth::test_token_expiry",
                        "test_file": "tests/test_auth.py",
                        "line": 42,
                        "message": "AssertionError: Token should have expired",
                    },
                    {
                        "test_name": "tests.test_storage::test_db_lock_timeout",
                        "test_file": "tests/test_storage.py",
                        "line": 88,
                        "message": "TimeoutError: Database lock acquisition timed out",
                    },
                ]
            },
        )

        patterns = extractor.extract(
            reports=[report],
            transcripts=[],
        )

        assert len(patterns) == 2
        assert all(p.category == "error_recovery" for p in patterns)
        assert any("test_token_expiry" in p.title for p in patterns)
        assert any("test_db_lock_timeout" in p.title for p in patterns)
        for p in patterns:
            assert p.confidence >= 0.85
            assert len(p.source_artifacts) >= 1
            assert p.anti_pattern is not None


@pytest.mark.asyncio
class TestReflectionDaemonAndEngine:
    """Verify reflection engine JUnit distillation and background daemon worker."""

    async def test_engine_reflects_junit_report(self, tmp_path: Path) -> None:
        report_file = tmp_path / "junit.xml"
        report_file.write_text(SAMPLE_JUNIT_XML, encoding="utf-8")

        vault_dir = tmp_path / "knowledge_vault"
        vault_dir.mkdir(parents=True)

        storage = SQLiteStorageService(":memory:")
        try:
            pipeline = MemoryPatternPipeline()
            engine = HarnessReflectorEngine(storage=storage, pipeline=pipeline)

            scope = ReflectionScope(min_confidence=0.80)
            report = await engine.reflect(
                scope=scope,
                test_report_path=report_file,
                commit_to_vault=True,
                generate_html_brief=False,
                vault_dir=vault_dir,
            )

            assert len(report.heuristics) >= 2
            assert len(report.knowledge_items) >= 2

            # Check that knowledge items were committed to disk in canonical format
            ki_dirs = list(vault_dir.iterdir())
            assert len(ki_dirs) >= 2
            for ki_dir in ki_dirs:
                assert (ki_dir / "metadata.json").is_file()
                assert (ki_dir / "summary.md").is_file()
        finally:
            storage.close()

    async def test_daemon_worker_step_and_lifecycle(self, tmp_path: Path) -> None:
        report_file = tmp_path / "ci_tests.xml"
        report_file.write_text(SAMPLE_JUNIT_XML, encoding="utf-8")

        vault_dir = tmp_path / "daemon_vault"
        vault_dir.mkdir(parents=True)

        worker = ReflectionDaemonWorker(
            interval_seconds=0.05,
            test_report_path=report_file,
            vault_dir=vault_dir,
            commit_to_vault=True,
            generate_html=False,
            min_confidence=0.80,
        )

        assert not worker.is_running
        assert worker.cycle_count == 0
        assert worker.last_report is None

        # Execute single step
        report = await worker.step()
        assert worker.cycle_count == 1
        assert worker.last_report is report
        assert len(report.knowledge_items) >= 2

        # Verify start/stop lifecycle
        worker.start()
        assert worker.is_running
        await asyncio.sleep(0.12)
        await worker.stop()
        assert not worker.is_running
        assert worker.cycle_count >= 2


@pytest.mark.unit
class TestReflectionCLI:
    """Verify Click CLI invocation with test-report and reflection flags."""

    def test_cli_reflect_with_test_report(self, tmp_path: Path) -> None:
        report_file = tmp_path / "pytest_results.xml"
        report_file.write_text(SAMPLE_JUNIT_XML, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli_main,
            [
                "reflect",
                "--test-report",
                str(report_file),
                "--no-commit",
                "--no-html",
            ],
        )

        assert result.exit_code == 0
        assert "Endogenous Memory Reflection Report" in result.output
        assert "Distilled Heuristics Matrix:" in result.output
