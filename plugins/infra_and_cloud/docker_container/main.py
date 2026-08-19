"""Docker container linter, multi-stage generator, and security auditor plugin."""

from __future__ import annotations

import re
from typing import Any


def lint_dockerfile(dockerfile_content: str) -> dict[str, Any]:
    """Lint a Dockerfile for security and best practice issues."""
    issues: list[dict[str, Any]] = []
    lines = dockerfile_content.splitlines()

    has_user = False
    has_from = False

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.upper().startswith("FROM"):
            has_from = True
            # Check for latest tag
            if ":latest" in line or (":" not in line.split()[1] and "@" not in line.split()[1]):
                issues.append({
                    "rule": "AvoidLatestTag",
                    "severity": "medium",
                    "line": line_num,
                    "detail": f"Unpinned or :latest base image tag in '{line}'. Use immutable digest or version tag.",
                })

        elif line.upper().startswith("USER"):
            has_user = True
            if "root" in line.lower() or "0" in line:
                issues.append({
                    "rule": "AvoidRootUser",
                    "severity": "high",
                    "line": line_num,
                    "detail": "Explicit switch to root user detected.",
                })

        elif line.upper().startswith("RUN"):
            if "apt-get install" in line and "--no-install-recommends" not in line:
                issues.append({
                    "rule": "AptNoInstallRecommends",
                    "severity": "low",
                    "line": line_num,
                    "detail": "Consider using 'apt-get install --no-install-recommends' to minimize image size.",
                })
            if "pip install" in line and "--no-cache-dir" not in line:
                issues.append({
                    "rule": "PipNoCacheDir",
                    "severity": "low",
                    "line": line_num,
                    "detail": "Consider using 'pip install --no-cache-dir' to keep container lightweight.",
                })
            if re.search(r"curl .* \| (?:ba)?sh", line):
                issues.append({
                    "rule": "AvoidCurlPipeToShell",
                    "severity": "high",
                    "line": line_num,
                    "detail": "Piping unverified curl output directly to shell is dangerous.",
                })

        elif line.upper().startswith("ADD"):
            if not line.endswith(".tar.gz") and not line.endswith(".tar"):
                issues.append({
                    "rule": "PreferCopyOverAdd",
                    "severity": "low",
                    "line": line_num,
                    "detail": "Use COPY instead of ADD for local files.",
                })

    if has_from and not has_user:
        issues.append({
            "rule": "MissingNonRootUser",
            "severity": "high",
            "line": len(lines),
            "detail": "No non-root USER instruction specified. Container may run as root by default.",
        })

    return {
        "status": "ok",
        "clean": len(issues) == 0,
        "issues_count": len(issues),
        "issues": issues,
    }


def generate_dockerfile(
    runtime: str = "python",
    entrypoint_command: str | None = None,
    port: int = 8080,
) -> dict[str, Any]:
    """Generate a hardened multi-stage Dockerfile."""
    rt = runtime.lower().strip()

    if rt == "python":
        cmd = entrypoint_command or "python -m harness.cli"
        dockerfile = (
            "# Stage 1: Build & Dependencies\n"
            "FROM python:3.12-slim AS builder\n"
            "WORKDIR /app\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*\n"
            "COPY pyproject.toml ./\n"
            "RUN pip install --no-cache-dir --prefix=/install .\n\n"
            "# Stage 2: Minimal Runtime\n"
            "FROM python:3.12-slim\n"
            "WORKDIR /app\n"
            "RUN useradd -u 10001 appuser\n"
            "COPY --from=builder /install /usr/local\n"
            "COPY src/ ./src/\n"
            "COPY plugins/ ./plugins/\n"
            "USER appuser\n"
            f"EXPOSE {port}\n"
            f'ENTRYPOINT ["sh", "-c", "{cmd}"]\n'
        )
    elif rt in ("node", "typescript"):
        cmd = entrypoint_command or "npm start"
        dockerfile = (
            "FROM node:20-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm ci\n"
            "COPY . .\n"
            "RUN npm run build\n\n"
            "FROM node:20-alpine\n"
            "WORKDIR /app\n"
            "USER node\n"
            "COPY --from=builder /app/dist ./dist\n"
            "COPY --from=builder /app/node_modules ./node_modules\n"
            f"EXPOSE {port}\n"
            f'CMD ["sh", "-c", "{cmd}"]\n'
        )
    else:
        dockerfile = (
            "FROM alpine:3.19\n"
            "RUN adduser -D appuser\n"
            "WORKDIR /app\n"
            "USER appuser\n"
            f"EXPOSE {port}\n"
            'CMD ["sh"]\n'
        )

    return {
        "status": "ok",
        "runtime": rt,
        "dockerfile": dockerfile,
    }


def audit_container_security(container_config: dict[str, Any]) -> dict[str, Any]:
    """Audit runtime configuration of a container."""
    warnings: list[dict[str, Any]] = []

    if container_config.get("privileged", False):
        warnings.append({
            "check": "PrivilegedMode",
            "severity": "critical",
            "detail": "Container runs in privileged mode, granting full host root capabilities.",
        })

    if not container_config.get("read_only_rootfs", False):
        warnings.append({
            "check": "ReadOnlyRootFilesystem",
            "severity": "medium",
            "detail": "Container filesystem is writable. Consider enabling read_only_rootfs.",
        })

    caps = container_config.get("capabilities_add", [])
    if "ALL" in caps or "SYS_ADMIN" in caps:
        warnings.append({
            "check": "DangerousCapabilities",
            "severity": "high",
            "detail": f"Elevated Linux capabilities {caps} granted to container.",
        })

    return {
        "status": "ok",
        "secure": len(warnings) == 0,
        "warnings_count": len(warnings),
        "warnings": warnings,
    }
