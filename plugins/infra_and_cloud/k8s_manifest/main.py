"""Kubernetes manifest linter, resource limit validator, and security auditor plugin."""

from __future__ import annotations

import re
from typing import Any


def lint_k8s_manifest(manifest_yaml: str) -> dict[str, Any]:
    """Lint basic Kubernetes YAML manifest structure."""
    issues: list[dict[str, Any]] = []

    if "apiVersion:" not in manifest_yaml:
        issues.append({
            "rule": "MissingApiVersion",
            "severity": "critical",
            "detail": "Manifest is missing required 'apiVersion' field.",
        })

    if "kind:" not in manifest_yaml:
        issues.append({
            "rule": "MissingKind",
            "severity": "critical",
            "detail": "Manifest is missing required 'kind' field.",
        })

    if "metadata:" not in manifest_yaml or "name:" not in manifest_yaml:
        issues.append({
            "rule": "MissingMetadataName",
            "severity": "high",
            "detail": "Manifest metadata must declare a resource 'name'.",
        })

    if "namespace:" not in manifest_yaml:
        issues.append({
            "rule": "MissingExplicitNamespace",
            "severity": "medium",
            "detail": "No explicit namespace declared; resource will deploy to 'default'.",
        })

    return {
        "status": "ok",
        "valid": len(issues) == 0,
        "issues_count": len(issues),
        "issues": issues,
    }


def validate_resource_limits(manifest_yaml: str) -> dict[str, Any]:
    """Check for CPU and memory resource requests & limits."""
    missing: list[str] = []

    if "resources:" not in manifest_yaml:
        missing.extend(["requests.cpu", "requests.memory", "limits.cpu", "limits.memory"])
    else:
        if "requests:" not in manifest_yaml:
            missing.extend(["requests.cpu", "requests.memory"])
        if "limits:" not in manifest_yaml:
            missing.extend(["limits.cpu", "limits.memory"])

    return {
        "status": "ok",
        "has_resource_declarations": len(missing) == 0,
        "missing_declarations": missing,
        "compliant": len(missing) == 0,
    }


def check_security_context(manifest_yaml: str) -> dict[str, Any]:
    """Audit pod and container securityContext settings."""
    findings: list[dict[str, Any]] = []

    if "securityContext:" not in manifest_yaml:
        findings.append({
            "check": "MissingSecurityContext",
            "severity": "high",
            "detail": "No securityContext declared on pod or container spec.",
        })
    else:
        if "runAsNonRoot: true" not in manifest_yaml:
            findings.append({
                "check": "RunAsNonRootNotEnforced",
                "severity": "high",
                "detail": "'runAsNonRoot: true' not explicitly enabled.",
            })

        if "allowPrivilegeEscalation: false" not in manifest_yaml:
            findings.append({
                "check": "PrivilegeEscalationNotBlocked",
                "severity": "medium",
                "detail": "'allowPrivilegeEscalation: false' should be enforced.",
            })

    if re.search(r"privileged:\s*true", manifest_yaml, re.IGNORECASE):
        findings.append({
            "check": "PrivilegedContainer",
            "severity": "critical",
            "detail": "Container explicitly sets 'privileged: true'.",
        })

    return {
        "status": "ok",
        "secure": len(findings) == 0,
        "findings_count": len(findings),
        "findings": findings,
    }
