"""Tests for Domain 2: Docker Container plugin."""

from __future__ import annotations

import pytest

from plugins.docker_container.main import (
    audit_container_security,
    generate_dockerfile,
    lint_dockerfile,
)


@pytest.mark.unit
class TestDockerContainerPlugin:
    def test_lint_dockerfile_issues(self) -> None:
        bad_dockerfile = (
            "FROM python:latest\n"
            "RUN apt-get update && apt-get install -y curl\n"
            "ADD script.sh /script.sh\n"
            "USER root\n"
        )
        res = lint_dockerfile(bad_dockerfile)
        assert res["status"] == "ok"
        assert res["clean"] is False
        rules = [iss["rule"] for iss in res["issues"]]
        assert "AvoidLatestTag" in rules
        assert "AvoidRootUser" in rules

    def test_generate_dockerfile_python(self) -> None:
        res = generate_dockerfile(runtime="python", port=3000)
        assert res["status"] == "ok"
        assert "FROM python:3.12-slim AS builder" in res["dockerfile"]
        assert "EXPOSE 3000" in res["dockerfile"]
        assert "USER appuser" in res["dockerfile"]

    def test_audit_container_security(self) -> None:
        cfg = {"privileged": True, "read_only_rootfs": False, "capabilities_add": ["SYS_ADMIN"]}
        res = audit_container_security(cfg)
        assert res["status"] == "ok"
        assert res["secure"] is False
        assert res["warnings_count"] >= 2
