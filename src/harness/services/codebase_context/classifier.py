"""Semantic path classifier distinguishing repository paths from URL routes and archetypes."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True, frozen=True)
class SemanticPathClassifier:
    """Classifies inline backtick spans to distinguish real repository paths from URL routes and archetypes."""

    MIME_TYPE_RE = re.compile(
        r"^(?:text|application|image|audio|video|multipart|font|model)/[a-zA-Z0-9.+_-]+$"
    )
    # HTTP / WebSocket API Routes and Endpoints (e.g., /api/health, /ws/events, /v1/chat, /)
    API_ROUTE_RE = re.compile(
        r"^/(?:api|ws|v\d+|graphql|health|metrics|docs|openapi|redoc)(?:/[\w._-]+)*$|^/$"
    )
    # Common foreign repo archetypes, documentation templates, and language build manifests
    ARCHETYPE_FILENAMES = frozenset({
        "CARD.md",
        "SKILL.md",
        "metadata.json",
        "summary.md",
        "config.default.yaml",
        "config.yaml",
        "CONTEXT.md",
        "colors.toml",
        "plugin.json",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "Cargo.toml",
        "Cargo.lock",
        "go.mod",
        "go.sum",
        "Makefile",
        "Dockerfile",
        "docker-compose.yml",
        "main.py",
        "drift.json",
    })

    @classmethod
    def is_mime_type(cls, span: str) -> bool:
        """Check if span matches RFC media/MIME type syntax."""
        return bool(cls.MIME_TYPE_RE.match(span))

    @classmethod
    def is_api_route(cls, span: str) -> bool:
        """Check if span is an HTTP / WebSocket URL endpoint route."""
        return bool(cls.API_ROUTE_RE.match(span))

    @classmethod
    def is_archetype_template(cls, span: str) -> bool:
        """Check if span is a standalone architectural archetype template or build manifest filename."""
        clean = span.split("/")[-1].split("\\")[-1]
        return clean in cls.ARCHETYPE_FILENAMES
