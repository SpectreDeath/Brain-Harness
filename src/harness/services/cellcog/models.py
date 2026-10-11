"""Slotted and frozen data models and constants for CellCog multimodal subsystem."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Constants and Environment
ENV_CELLCOG_API_KEY = "CELLCOG_API_KEY"
DEFAULT_AGENT_PROVIDER = "harness"
DEFAULT_CHAT_MODE = "agent"
DEFAULT_CHAT_TIER = "flash"
DEFAULT_TIMEOUT_SEC = 1800
DEFAULT_RESEARCH_TIMEOUT_SEC = 3600
MAX_ATTACHMENT_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB safety threshold

# Sensitive file path patterns that must never be attached in <SHOW_FILE> tags
SENSITIVE_FILE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|[/\\])\.env($|\..*)", re.IGNORECASE),
    re.compile(r"(^|[/\\])\.git([/\\]|$)", re.IGNORECASE),
    re.compile(r"(^|[/\\])id_rsa(\.pub)?$", re.IGNORECASE),
    re.compile(r"(^|[/\\])id_ed25519(\.pub)?$", re.IGNORECASE),
    re.compile(r"(^|[/\\])\.ssh([/\\]|$)", re.IGNORECASE),
    re.compile(r"(^|[/\\])credentials(\.json|\.xml|\.ini)?$", re.IGNORECASE),
    re.compile(r"(^|[/\\])secrets?(\.json|\.yaml|\.yml)?$", re.IGNORECASE),
    re.compile(r"\.pem$", re.IGNORECASE),
    re.compile(r"\.key$", re.IGNORECASE),
)

# Tag Regular Expressions
SHOW_FILE_REGEX = re.compile(r"<SHOW_FILE>(.*?)</SHOW_FILE>", re.DOTALL | re.IGNORECASE)
GENERATE_FILE_REGEX = re.compile(r"<GENERATE_FILE>(.*?)</GENERATE_FILE>", re.DOTALL | re.IGNORECASE)

_CUSTOM_MIMES: dict[str, str] = {
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
    ".obj": "model/obj",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".pdf": "application/pdf",
    ".csv": "text/csv",
}


def infer_mime_type(path_or_str: str | Path) -> str:
    """Infer MIME type from file extension or path with custom multimodal extensions."""
    mime, _ = mimetypes.guess_type(str(path_or_str))
    if mime:
        return mime
    ext = Path(path_or_str).suffix.lower()
    return _CUSTOM_MIMES.get(ext, "application/octet-stream")


@dataclass(slots=True, frozen=True)
class CellCogArtifact:
    """Slotted and frozen model representing a verified deliverable or input artifact."""

    path: str
    filename: str
    mime_type: str = "application/octet-stream"
    size_bytes: int = 0
    checksum_sha256: str = ""

    @classmethod
    def from_path(cls, file_path: Path | str) -> CellCogArtifact:
        """Construct a CellCogArtifact with verified disk stats and SHA256 checksum if present."""
        p = Path(file_path)
        mime_type = infer_mime_type(p)
        filename = p.name

        if not p.exists() or not p.is_file():
            return cls(
                path=str(p),
                filename=filename,
                mime_type=mime_type,
                size_bytes=0,
                checksum_sha256="",
            )

        try:
            stat = p.stat()
            size = stat.st_size
            h = hashlib.sha256()
            with p.open("rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            sha = h.hexdigest()
            return cls(
                path=str(p),
                filename=filename,
                mime_type=mime_type,
                size_bytes=size,
                checksum_sha256=sha,
            )
        except OSError:
            return cls(
                path=str(p),
                filename=filename,
                mime_type=mime_type,
                size_bytes=0,
                checksum_sha256="",
            )


@dataclass(slots=True, frozen=True)
class MultimodalCompilationResult:
    """Result of multimodal prompt compilation, tag extraction, and security sanitization."""

    sanitized_prompt: str
    valid_inputs: tuple[str, ...] = field(default_factory=tuple)
    rejected_inputs: tuple[str, ...] = field(default_factory=tuple)
    output_destinations: tuple[str, ...] = field(default_factory=tuple)
    missing_files: tuple[str, ...] = field(default_factory=tuple)
    oversized_files: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class CellCogRunResult:
    """Result of an any-to-any CellCog sub-agent execution."""

    success: bool
    message: str
    chat_id: str = ""
    chat_mode: str = DEFAULT_CHAT_MODE
    chat_tier: str = DEFAULT_CHAT_TIER
    attached_files: tuple[str, ...] = field(default_factory=tuple)
    generated_files: tuple[str, ...] = field(default_factory=tuple)
    downloaded_files: tuple[str, ...] = field(default_factory=tuple)
    artifacts: tuple[CellCogArtifact, ...] = field(default_factory=tuple)
    raw_response: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(slots=True, frozen=True)
class CellCogResearchResult:
    """Result of a deep multi-source research task via CellCog."""

    success: bool
    summary: str
    sources_count: int = 0
    chat_id: str = ""
    chat_tier: str = DEFAULT_CHAT_TIER
    attached_files: tuple[str, ...] = field(default_factory=tuple)
    generated_files: tuple[str, ...] = field(default_factory=tuple)
    artifacts: tuple[CellCogArtifact, ...] = field(default_factory=tuple)
    findings: tuple[str, ...] = field(default_factory=tuple)
    raw_response: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(slots=True, frozen=True)
class CellCogCapabilityItem:
    """Single modality skill or capability description in the CellCog catalog."""

    name: str
    category: str
    description: str
    recommended_mode: str = "agent"
    recommended_tier: str = "flash"


@dataclass(slots=True, frozen=True)
class CellCogCapabilitiesResult:
    """Full capability catalog of CellCog modalities."""

    total_capabilities: int
    categories: tuple[str, ...]
    capabilities: tuple[CellCogCapabilityItem, ...]
