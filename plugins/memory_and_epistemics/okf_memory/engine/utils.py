"""OKF engine utilities, path normalizers, frontmatter handlers, and traversal guards."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger(__name__)

DEFAULT_BUNDLE_DIR = "knowledge"
ALLOWED_TYPES = {"decision", "architecture", "operational", "concept"}


def _normalize_path(p: str | Path) -> str:
    """Normalize file path to forward slashes for deterministic cross-platform comparison."""
    return str(p).replace("\\", "/").strip().lstrip("./")


def _ensure_within_root(root: Path, target: Path) -> Path:
    """Validate that target path resolves within root to prevent traversal attacks."""
    resolved_root = root.resolve()
    resolved_target = target.resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as err:
        raise ValueError(
            f"Path traversal detected: target path '{target}' escapes root '{root}'"
        ) from err
    return resolved_target


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [t for t in tokens if len(t) > 1]


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from Markdown text."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_raw = parts[1]
    body = parts[2].lstrip("\r\n")

    try:
        data = yaml.safe_load(frontmatter_raw) or {}
        if not isinstance(data, dict):
            return {}, content
        return data, body
    except Exception as exc:
        logger.warning("failed_to_parse_frontmatter", error=str(exc))
        return {}, content


def _serialize_concept(data: dict[str, Any], body: str) -> str:
    """Serialize concept dictionary and body into standard OKF markdown format."""
    frontmatter_yaml = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()
    return f"---\n{frontmatter_yaml}\n---\n\n{body.strip()}\n"


def resolve_bundle(default_root: Path, bundle_dir: str | None = None) -> Path:
    """Resolve bundle root directory safely."""
    p = Path(bundle_dir) if bundle_dir else default_root
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


def load_bundle_concepts(root: Path) -> dict[str, tuple[dict[str, Any], str, Path]]:
    """Load all valid concept files in bundle root excluding system files."""
    concepts: dict[str, tuple[dict[str, Any], str, Path]] = {}
    if not root.exists():
        return concepts

    for file_path in root.rglob("*.md"):
        rel_name = file_path.name.lower()
        if rel_name in {"index.md", "log.md", "readme.md"} or file_path.name.startswith("."):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            data, body = _extract_frontmatter(content)
            cid = data.get("id") or file_path.stem
            concepts[str(cid)] = (data, body, file_path)
        except Exception as exc:
            logger.warning("concept_read_error", file=str(file_path), error=str(exc))
    return concepts
