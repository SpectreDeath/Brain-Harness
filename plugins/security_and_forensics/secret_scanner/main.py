"""Secret Scanner & Credential Leak Detection Plugin for Brain Harness.

Performs static regex pattern matching and Shannon entropy analysis to detect
hardcoded API keys, private keys, access tokens, and credentials in source code.
"""

from __future__ import annotations

import math
from pathlib import Path
import re
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

SECRET_SCANNER_KEY: ServiceKey[SecretScannerService] = ServiceKey("security.secret_scanner")

_SECRET_PATTERNS: list[tuple[str, str, float]] = [
    # (Pattern, Label, Minimum Confidence)
    (r"-----BEGIN (RSA|OPENSSH|DSA|EC|PGP)? ?PRIVATE KEY-----", "Private Key Header", 0.99),
    (r"gh[pousr]_[A-Za-z0-9_]{36,255}", "GitHub Token", 0.95),
    (r"sk-[a-zA-Z0-9]{32,64}", "OpenAI API Key", 0.90),
    (r"sk-ant-[a-zA-Z0-9_-]{32,128}", "Anthropic API Key", 0.95),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID", 0.95),
    (r"(?:aws_secret_access_key|secret_key)\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]", "AWS Secret Access Key", 0.92),
    (r"xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Token", 0.95),
    (r"sq0atp-[0-9A-Za-z\-_]{22}", "Square Access Token", 0.90),
    (r"AIza[0-9A-Za-z-_]{35}", "Google API Key", 0.90),
    (r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", "JSON Web Token (JWT)", 0.80),
]


def _shannon_entropy(data: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


def _mask_secret(secret: str) -> str:
    """Mask sensitive string leaving only small prefix and suffix."""
    if len(secret) <= 8:
        return "****"
    return f"{secret[:4]}...{secret[-4:]}"


def scan_text(text: str) -> dict[str, Any]:
    """Scan raw text or code string for potential credentials, tokens, and private keys."""
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        # 1. Regex checks
        for pattern, label, conf in _SECRET_PATTERNS:
            for match in re.finditer(pattern, line):
                matched_str = match.group(0)
                findings.append({
                    "line_number": idx,
                    "rule": label,
                    "matched_preview": _mask_secret(matched_str),
                    "confidence": conf,
                    "category": "pattern_match",
                })

        # 2. High entropy token detection on key-value assignments
        kv_match = re.search(r"(?:api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]([^'\"]{16,})['\"]", line, re.IGNORECASE)
        if kv_match:
            candidate = kv_match.group(1)
            entropy = _shannon_entropy(candidate)
            if entropy > 4.2:
                findings.append({
                    "line_number": idx,
                    "rule": "High Entropy Credential Assignment",
                    "matched_preview": _mask_secret(candidate),
                    "confidence": min(0.95, round(0.5 + (entropy - 4.0) * 0.25, 2)),
                    "category": "entropy_analysis",
                    "entropy": round(entropy, 2),
                })

    is_clean = len(findings) == 0
    return {
        "status": "ok",
        "clean": is_clean,
        "findings_count": len(findings),
        "findings": findings,
    }


def scan_file(file_path: str) -> dict[str, Any]:
    """Scan a specific file on disk for credentials."""
    p = Path(file_path).resolve()
    if not p.exists() or not p.is_file():
        return {"status": "error", "error": f"File not found: {file_path}", "clean": False, "findings": []}

    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
        result = scan_text(content)
        result["file"] = str(p)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e), "clean": False, "findings": []}


def scan_directory(dir_path: str = ".", max_depth: int = 5) -> dict[str, Any]:
    """Recursively scan a directory for leaked credentials."""
    root = Path(dir_path).resolve()
    if not root.exists() or not root.is_dir():
        return {"status": "error", "error": f"Directory not found: {dir_path}", "scanned_files": 0, "findings": []}

    skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
    all_findings: list[dict[str, Any]] = []
    scanned_count = 0

    for path in root.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_file() and path.stat().st_size < 1_000_000:  # < 1MB text limit
            try:
                rel = str(path.relative_to(root))
                content = path.read_text(encoding="utf-8", errors="ignore")
                res = scan_text(content)
                scanned_count += 1
                if not res["clean"]:
                    for f in res["findings"]:
                        f["file"] = rel
                        all_findings.append(f)
            except Exception:
                pass

    return {
        "status": "ok",
        "scanned_files": scanned_count,
        "clean": len(all_findings) == 0,
        "findings_count": len(all_findings),
        "findings": all_findings,
    }


class SecretScannerService:
    """Service facade for credential & secret scanning."""

    def scan_text(self, text: str) -> dict[str, Any]:
        return scan_text(text)

    def scan_file(self, file_path: str) -> dict[str, Any]:
        return scan_file(file_path)

    def scan_directory(self, dir_path: str = ".", max_depth: int = 5) -> dict[str, Any]:
        return scan_directory(dir_path, max_depth=max_depth)


class SecretScannerPlugin(HarnessPlugin):
    """Plugin providing secret scanning capabilities to the Harness kernel."""

    @property
    def name(self) -> str:
        return "plugin.secret_scanner"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Pre-ingestion and on-demand credential & API key scanner with Shannon entropy analysis"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SECRET_SCANNER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SECRET_SCANNER_KEY, SecretScannerService(), provider=self.name)
        logger.info("SecretScannerService provided", plugin=self.name)
