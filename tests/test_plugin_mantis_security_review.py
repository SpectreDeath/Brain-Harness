"""Tests for Google Mantis Security Review Plugin."""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.mantis_security_review.main import (
    MANTIS_SECURITY_REVIEW_KEY,
    MantisSecurityReviewPlugin,
    MantisSecurityReviewService,
    compute_stable_signature,
    init_okf_db,
    mantis_calibrate_risk,
    mantis_chain_exploits,
    mantis_critic_filter,
    mantis_dedupe_ladder,
    mantis_directory_summary,
    mantis_generate_report,
    mantis_history_scan,
    mantis_plan_review,
    mantis_research_audit,
    mantis_review_gate,
)


@pytest.mark.unit
class TestMantisSecurityReviewPlugin:
    """Unit test suite for Mantis security review tools and IoC registration."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey into ServiceContext."""
        ctx = ServiceContext()
        plugin = MantisSecurityReviewPlugin()

        assert plugin.name == "plugin.mantis_security_review"
        assert MANTIS_SECURITY_REVIEW_KEY in plugin.provides

        await plugin.on_load(ctx)
        svc = ctx.require(MANTIS_SECURITY_REVIEW_KEY)
        assert isinstance(svc, MantisSecurityReviewService)

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    def test_directory_summary(self, tmp_path: Path) -> None:
        """Verify directory summarization categorizes code and configs."""
        (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
        (tmp_path / "config.json").write_text("{}", encoding="utf-8")
        (tmp_path / "README.md").write_text("# Doc\n", encoding="utf-8")

        res = mantis_directory_summary(str(tmp_path), recursive=True)
        assert res["status"] == "ok"
        assert res["code_files_count"] == 1
        assert res["config_files_count"] == 1
        assert res["doc_files_count"] == 1

    def test_research_audit_and_dedupe(self) -> None:
        """Verify AST static audit detects vulnerabilities and dedupe ladder consolidates them."""
        vulnerable_code = """
import os
import subprocess

def dangerous(user_input):
    eval(user_input)
    subprocess.run("rm -rf " + user_input, shell=True)
    api_key = "AKIA1234567890ABCDEF"
"""
        audit = mantis_research_audit("danger.py", vulnerable_code)
        assert audit["status"] == "ok"
        assert audit["findings_count"] >= 2

        # Check deduplication ladder
        duplicate_findings = audit["findings"] + audit["findings"]
        deduped = mantis_dedupe_ladder(duplicate_findings, mode="syntactic_and_ast")
        assert deduped["status"] == "ok"
        assert deduped["deduped_count"] == audit["findings_count"]
        assert deduped["duplicates_removed"] == audit["findings_count"]

    def test_review_gate_and_critic(self) -> None:
        """Verify independent review gate and production viability critic."""
        code = "line1\neval(cmd)\nline3\n"
        valid_finding = {"line": 2, "cwe": "CWE-95"}
        rev_res = mantis_review_gate(valid_finding, code)
        assert rev_res["verdict"] == "CONFIRMED_VALID"

        invalid_finding = {"line": 99, "cwe": "CWE-95"}
        rev_res2 = mantis_review_gate(invalid_finding, code)
        assert rev_res2["verdict"] == "REJECTED"

        # Critic filter on assertion trap
        assert_finding = {"title": "Assertion Failure Crash", "description": "assert token is not None"}
        critic_res = mantis_critic_filter(assert_finding, check_release_assertions=True)
        assert critic_res["viable_in_production"] is False
        assert critic_res["verdict"] == "DROPPED_ASSERTION_TRAP"

    def test_exploit_chaining_and_calibration(self) -> None:
        """Verify exploit chain construction and risk calibration."""
        findings = [
            {"id": "f1", "title": "Hardcoded Secret", "cwe": "CWE-798", "severity": "medium"},
            {"id": "f2", "title": "Remote Code Execution", "cwe": "CWE-78", "severity": "critical"},
        ]

        chain_res = mantis_chain_exploits(findings, target_objective="Full System Takeover")
        assert chain_res["chains_constructed_count"] == 1
        assert chain_res["exploit_chains"][0]["compound_severity"] == "critical"

        calib_res = mantis_calibrate_risk(findings, asset_criticality="critical")
        assert calib_res["status"] == "ok"
        assert len(calib_res["calibrated_findings"]) == 2
        # Critical multiplier should boost scores
        assert calib_res["calibrated_findings"][0]["calibrated_cvss_score"] > 5.0

    def test_report_generation(self) -> None:
        """Verify executive report compilation generates valid markdown packet."""
        findings = [{"id": "f1", "title": "SQL Injection", "cwe": "CWE-89", "severity": "high", "filepath": "db.py", "line": 10}]
        report = mantis_generate_report(findings, executive_summary="Comprehensive scan complete.")
        assert report["status"] == "ok"
        assert "Google Mantis Security Review Packet" in report["markdown_report"]
        assert "SQL Injection" in report["markdown_report"]

    def test_okf_sqlite_db(self, tmp_path: Path) -> None:
        """Verify SQLite OKF v0.2 database tables and stable signature hashing."""
        db_file = tmp_path / "test_knowledge.db"
        conn = init_okf_db(str(db_file))
        cur = conn.cursor()

        # Check table creation
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "findings" in tables
        assert "okf_concepts" in tables
        assert "execution_logs" in tables
        conn.close()

        sig1 = compute_stable_signature("auth.py", "CWE-89", "login")
        sig2 = compute_stable_signature("auth.py", "CWE-89", "login")
        sig3 = compute_stable_signature("auth.py", "CWE-78", "login")
        assert sig1 == sig2
        assert sig1 != sig3
