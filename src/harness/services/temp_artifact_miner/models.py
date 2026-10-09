"""Slotted & Frozen Dataclasses, Constants, and Cryptographic Utilities (Rule 12, Rule 43)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

# Noise directories to actively prune (Rule 52)
PRUNE_NAMES: set[str] = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

# Known prefix patterns for visual brief categorization
KNOWN_BRIEF_PREFIXES: tuple[str, ...] = (
    "architecture-review",
    "book-to-skill-forge",
    "harness-reflection",
    "harness-review",
    "skill-graph",
    "compute-assessor",
    "dynamic-model-router",
    "coding-harness-calibrator",
    "bigquery-augmented-analytics",
    "media-mind-forge",
    "gemini-vercel-streaming",
    "gis-architect",
    "gradio-app-architect",
    "self-eval-brief",
    "data-topology-review",
    "network-forensics",
    "repo-reader",
    "brain-artifact-miner",
    "conversation-trajectory-miner",
    "temp-artifact-miner",
)


@dataclass(slots=True, frozen=True)
class BriefCatalogItem:
    """Slotted and frozen representation of an extracted HTML visual brief (Rule 12)."""

    name: str
    path: str
    category: str
    title: str
    size_bytes: int
    mtime: float
    has_mermaid: bool
    has_scorecard: bool
    has_antipatterns: bool
    is_heavy_topology: bool
    mermaid_dags: tuple[str, ...] = ()
    sha256: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.mermaid_dags, list):
            object.__setattr__(self, "mermaid_dags", tuple(self.mermaid_dags))


@dataclass(slots=True, frozen=True)
class BriefCatalog:
    """Slotted and frozen catalog of extracted visual briefs (Rule 12)."""

    total_scanned: int
    brief_count: int
    total_bytes: int
    heavy_count: int
    items_by_category: dict[str, tuple[BriefCatalogItem, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_scanned < 0 or self.brief_count < 0:
            raise ValueError("Scan and brief counts cannot be negative")
        if self.items_by_category:
            normalized = {
                k: tuple(v) if isinstance(v, list) else v
                for k, v in self.items_by_category.items()
            }
            object.__setattr__(self, "items_by_category", normalized)


@dataclass(slots=True, frozen=True)
class SandboxFixture:
    """Slotted and frozen representation of a pytest sandbox run (Rule 12)."""

    name: str
    path: str
    fixture_count: int
    mock_skills: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.mock_skills, list):
            object.__setattr__(self, "mock_skills", tuple(self.mock_skills))


@dataclass(slots=True, frozen=True)
class SandboxReport:
    """Slotted and frozen summary of ephemeral test sandbox environments (Rule 12, Rule 53)."""

    total_runs: int
    sandbox_path: str
    runs: tuple[SandboxFixture, ...] = ()
    error_snippets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.total_runs < 0:
            raise ValueError("total_runs cannot be negative")
        if isinstance(self.runs, list):
            object.__setattr__(self, "runs", tuple(self.runs))
        if isinstance(self.error_snippets, list):
            object.__setattr__(self, "error_snippets", tuple(self.error_snippets))


@dataclass(slots=True, frozen=True)
class IsnadAttributionRecord:
    """Slotted and frozen record for cryptographic isnad provenance (Rule 12, Rule 41)."""

    brief_name: str
    sha256: str
    mtime: float
    primary_source: str
    test_anchor: str
    confidence: float = 1.0


@dataclass(slots=True, frozen=True)
class VisualSalvageReport:
    """Slotted and frozen summary of salvaged diagrams and documentation (Rule 12)."""

    brief_name: str
    knowledge_vault_path: str
    salvaged_doc_path: str
    extracted_diagrams_count: int
    isnad_claims_count: int


@dataclass(slots=True, frozen=True)
class CognitiveBifurcationReport:
    """Slotted and frozen dual-lens cognitive bifurcation report (Rule 12, Rule 40, Rule 41)."""

    source_name: str
    knowledge_vault_path: str
    salvaged_doc_path: str
    extracted_heuristics: tuple[str, ...] = ()
    procedural_rules: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.extracted_heuristics, list):
            object.__setattr__(self, "extracted_heuristics", tuple(self.extracted_heuristics))
        if isinstance(self.procedural_rules, list):
            object.__setattr__(self, "procedural_rules", tuple(self.procedural_rules))


def detect_brief_category(name: str) -> str:
    """Categorize a visual brief file by standard filename prefix."""
    for prefix in KNOWN_BRIEF_PREFIXES:
        if name.startswith(prefix) or prefix in name:
            return prefix
    if "-" in name:
        return name.split("-")[0]
    return "other"


def compute_file_sha256(path: Path) -> str:
    """Compute cryptographic SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
