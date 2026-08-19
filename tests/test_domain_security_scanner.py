"""Tests for Domain 1: Security Scanner plugin."""

from __future__ import annotations

import pytest

from plugins.security_and_forensics.security_scanner.main import (
    audit_dependencies,
    scan_code_vulnerabilities,
    scan_secrets,
)


@pytest.mark.unit
class TestSecurityScannerPlugin:
    def test_scan_secrets_detection(self) -> None:
        content = (
            "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\n"
            "OPENAI = 'sk-abcdef1234567890abcdef1234567890'\n"
            "SAFE_LINE = 'hello world'\n"
        )
        res = scan_secrets(content)
        assert res["status"] == "ok"
        assert res["clean"] is False
        assert res["secrets_found_count"] >= 2
        rules = [f["rule"] for f in res["findings"]]
        assert "AWS Access Key" in rules
        assert "OpenAI / Generic API Key" in rules

    def test_scan_code_vulnerabilities_eval_pickle(self) -> None:
        dangerous_code = (
            "import pickle\n"
            "def handle(data):\n"
            "    eval('data * 2')\n"
            "    return pickle.loads(data)\n"
        )
        res = scan_code_vulnerabilities(dangerous_code)
        assert res["status"] == "ok"
        assert res["safe"] is False
        assert res["issues_count"] >= 2
        types = [iss["type"] for iss in res["issues"]]
        assert "Code Injection" in types
        assert "Insecure Deserialization" in types

    def test_audit_dependencies(self) -> None:
        reqs = "requests==2.31.0\npytest\npycrypto==2.6.1\n"
        res = audit_dependencies(reqs)
        assert res["status"] == "ok"
        assert "pytest" in res["unpinned_packages"]
        assert len(res["vulnerabilities"]) >= 1
