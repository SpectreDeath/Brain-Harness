"""Tests for Domain 2: Kubernetes Manifest plugin."""

from __future__ import annotations

import pytest

from plugins.k8s_manifest.main import (
    check_security_context,
    lint_k8s_manifest,
    validate_resource_limits,
)


@pytest.mark.unit
class TestK8sManifestPlugin:
    def test_lint_k8s_manifest(self) -> None:
        manifest = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            "  name: my-app\n"
        )
        res = lint_k8s_manifest(manifest)
        assert res["status"] == "ok"
        assert res["valid"] is False  # Missing explicit namespace
        assert res["issues"][0]["rule"] == "MissingExplicitNamespace"

    def test_validate_resource_limits(self) -> None:
        unlimited_yaml = "apiVersion: v1\nkind: Pod\nmetadata:\n  name: pod\n"
        res = validate_resource_limits(unlimited_yaml)
        assert res["status"] == "ok"
        assert res["compliant"] is False
        assert len(res["missing_declarations"]) == 4

    def test_check_security_context(self) -> None:
        insecure_yaml = "securityContext:\n  privileged: true\n"
        res = check_security_context(insecure_yaml)
        assert res["status"] == "ok"
        assert res["secure"] is False
        checks = [f["check"] for f in res["findings"]]
        assert "PrivilegedContainer" in checks
