"""Tests for Domain: Vibe Scanner plugin (AI AST Vulnerability Detector)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.security_and_forensics.vibe_scanner.main import (
    VibeScannerService,
    compare_benchmark,
    generate_json_report,
    generate_sarif_report,
    scan_code,
    scan_file,
    scan_project,
)


@pytest.mark.unit
class TestVibeScannerPlugin:
    def test_sql_injection_detection(self) -> None:
        vuln_code = """
import sqlite3
def get_user(username):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    return cursor.fetchall()
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        assert res["clean"] is False
        assert res["critical_count"] >= 1
        detectors = [f["detector"] for f in res["findings"]]
        assert "SQLInjection" in detectors

        # Safe parameterized query should be clean
        safe_code = """
import sqlite3
def get_user(username):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchall()
"""
        safe_res = scan_code(safe_code)
        assert safe_res["status"] == "ok"
        detectors = [f["detector"] for f in safe_res["findings"]]
        assert "SQLInjection" not in detectors

    def test_unsafe_file_access_detection(self) -> None:
        vuln_code = """
from pathlib import Path
BASE_DIR = Path("/app/data")
def read_doc():
    filename = request.args.get("file")
    file_path = BASE_DIR / filename
    with open(file_path, "r") as f:
        return f.read()
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        detectors = [f["detector"] for f in res["findings"]]
        assert "UnsafeFileAccess" in detectors

        # Safe relative_to check
        safe_code = """
from pathlib import Path
BASE_DIR = Path("/app/data")
def read_doc():
    filename = request.args.get("file")
    target = (BASE_DIR / filename).resolve()
    target.relative_to(BASE_DIR.resolve())
    with open(target, "r") as f:
        return f.read()
"""
        safe_res = scan_code(safe_code)
        assert safe_res["status"] == "ok"
        detectors = [f["detector"] for f in safe_res["findings"]]
        assert "UnsafeFileAccess" not in detectors

    def test_hardcoded_secret_detection(self) -> None:
        vuln_code = """
OPENAI_KEY = "sk-proj-abc123456789012345678901234567890"
DB_PASS = "SuperSecretPassword123!"
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        assert res["critical_count"] >= 1
        detectors = [f["detector"] for f in res["findings"]]
        assert "HardcodedSecret" in detectors

        safe_code = """
import os
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
DB_PASS = os.environ.get("DB_PASS")
"""
        safe_res = scan_code(safe_code)
        assert safe_res["status"] == "ok"
        detectors = [f["detector"] for f in safe_res["findings"]]
        assert "HardcodedSecret" not in detectors

    def test_unsafe_deserialization_detection(self) -> None:
        vuln_code = """
import pickle
def load_session(data):
    return pickle.loads(data)
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        assert res["critical_count"] >= 1
        detectors = [f["detector"] for f in res["findings"]]
        assert "UnsafeDeserialise" in detectors

    def test_weak_crypto_detection(self) -> None:
        vuln_code = """
import hashlib
import random

def create_auth_token(username):
    token = hashlib.md5(f"{username}{random.randint(1000, 9999)}".encode()).hexdigest()
    return token
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        detectors = [f["detector"] for f in res["findings"]]
        assert "WeakCrypto" in detectors

        safe_code = """
import secrets
def create_auth_token():
    return secrets.token_hex(32)
"""
        safe_res = scan_code(safe_code)
        assert safe_res["status"] == "ok"
        detectors = [f["detector"] for f in safe_res["findings"]]
        assert "WeakCrypto" not in detectors

    def test_swallowed_exception_detection(self) -> None:
        vuln_code = """
def process_data(item):
    try:
        critical_operation(item)
    except Exception:
        pass
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        assert res["high_count"] >= 1
        detectors = [f["detector"] for f in res["findings"]]
        assert "ExceptionSwallowed" in detectors

        safe_code = """
import logging
def process_data(item):
    try:
        critical_operation(item)
    except Exception as e:
        logging.error("Failed item: %s", e)
        raise
"""
        safe_res = scan_code(safe_code)
        assert safe_res["status"] == "ok"
        detectors = [f["detector"] for f in safe_res["findings"]]
        assert "ExceptionSwallowed" not in detectors

    def test_input_validation_detection(self) -> None:
        vuln_code = """
import os
def handle_cmd():
    cmd = request.args.get("cmd")
    os.system(cmd)
"""
        res = scan_code(vuln_code)
        assert res["status"] == "ok"
        detectors = [f["detector"] for f in res["findings"]]
        assert "InputValidation" in detectors

    def test_compare_benchmark(self) -> None:
        vuln = """
import sqlite3
import pickle

def handle(req):
    cursor.execute(f"SELECT * FROM tbl WHERE x = '{req}'")
    return pickle.loads(req)
"""
        sec = """
import sqlite3
import json

def handle(req):
    cursor.execute("SELECT * FROM tbl WHERE x = ?", (req,))
    return json.loads(req)
"""
        bench = compare_benchmark(vuln, sec)
        assert bench["status"] == "ok"
        assert bench["vulnerable"]["total_findings"] >= 2
        assert bench["secure"]["total_findings"] == 0
        assert bench["fully_remediated"] is True
        assert bench["risk_reduction_pct"] == 100.0

    def test_scan_file_and_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "app.py"
            file1.write_text("""
import pickle
def load(data):
    return pickle.loads(data)
""", encoding="utf-8")

            # Scan individual file
            file_res = scan_file(str(file1))
            assert file_res["status"] == "ok"
            assert file_res["clean"] is False
            assert file_res["critical_count"] == 1

            # Scan project directory
            proj_res = scan_project(tmpdir)
            assert proj_res["status"] == "ok"
            assert proj_res["total_files_scanned"] == 1
            assert proj_res["files_vulnerable"] == 1
            assert proj_res["critical_count"] == 1

            # Export SARIF
            sarif_out = Path(tmpdir) / "results.sarif"
            sarif_res = generate_sarif_report(tmpdir, str(sarif_out))
            assert sarif_res["status"] == "ok"
            assert sarif_out.exists()
            sarif_data = json.loads(sarif_out.read_text(encoding="utf-8"))
            assert sarif_data["version"] == "2.1.0"
            assert len(sarif_data["runs"]) > 0

            # Export JSON
            json_out = Path(tmpdir) / "results.json"
            json_res = generate_json_report(tmpdir, str(json_out))
            assert json_res["status"] == "ok"
            assert json_out.exists()

    def test_service_facade(self) -> None:
        svc = VibeScannerService()
        code = "API_KEY = 'sk-proj-123456789012345678901234567890'"
        res = svc.scan_code(code)
        assert res["status"] == "ok"
        assert res["critical_count"] >= 1

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/security_and_forensics/vibe_scanner")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation failed: {report.errors}"
