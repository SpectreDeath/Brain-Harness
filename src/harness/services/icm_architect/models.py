"""Slotted and frozen domain models for Interpretable Context Methodology (ICM) architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IcmWorkspaceRole(str, Enum):
    """Five-role taxonomy for files in an ICM workspace."""

    CATALOG = "catalog"    # Identity & routing (AGENTS.md, index files, pointers)
    CONTRACT = "contract"  # Step contracts (CONTEXT.md)
    FACTORY = "factory"    # Stable references, schemas, tools (_shared/, _tools/, _templates/)
    PRODUCT = "product"    # Run-specific artifacts (stages/*/output/, records/)
    DEAD = "dead"          # Stale, unreferenced, superseded (_archive/)


class IcmFormType(str, Enum):
    """Five canonical ICM forms composing the 3 primitives (sequence, shelf, catalog)."""

    PIPELINE = "pipeline"                  # Sequential production line with handoffs
    RECORD_LIBRARY = "record_library"      # Shelf of uniform records accumulating status
    KNOWLEDGE_BUNDLE = "knowledge_bundle"  # Concepts, claims, sources, and verified quotes
    CONTEXT_MAP = "context_map"            # Organizational graph of teams and processes
    SYSTEM_MAP = "system_map"              # Codebase audit impact index (nouns, verbs)


@dataclass(slots=True, frozen=True)
class IcmInventoryItem:
    """Classified file in an ICM workspace inventory."""

    path: str
    role: str
    byte_size: int
    line_count: int
    last_modified: str
    referrers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path, "role": self.role, "byte_size": self.byte_size,
            "line_count": self.line_count, "last_modified": self.last_modified,
            "referrers": list(self.referrers),
        }


@dataclass(slots=True, frozen=True)
class IcmInvariantViolation:
    """Violation of one of the 10 ICM mandatory invariants."""

    invariant_number: int
    name: str
    description: str
    path: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "invariant_number": self.invariant_number, "name": self.name,
            "description": self.description, "path": self.path, "severity": self.severity,
        }


@dataclass(slots=True, frozen=True)
class IcmWorkspaceAuditReport:
    """Comprehensive diagnostic audit report of an ICM workspace."""

    root: str
    form_detected: str
    total_files: int
    files_by_role: dict[str, int]
    invariants_passed: int
    invariants_total: int
    violations: list[IcmInvariantViolation] = field(default_factory=list)
    estimated_step_tokens: dict[str, int] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return len([v for v in self.violations if v.severity == "error"]) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root, "form_detected": self.form_detected,
            "total_files": self.total_files, "files_by_role": dict(self.files_by_role),
            "invariants_passed": self.invariants_passed, "invariants_total": self.invariants_total,
            "valid": self.valid, "violations": [v.to_dict() for v in self.violations],
            "estimated_step_tokens": dict(self.estimated_step_tokens),
        }


@dataclass(slots=True, frozen=True)
class IcmLinkCheckReport:
    """Report of relative links and contract inputs verification."""

    total_links: int
    resolved_links: int
    broken_links: list[dict[str, str]] = field(default_factory=list)
    graph_nodes: int = 0
    graph_edges: int = 0

    @property
    def valid(self) -> bool:
        return len(self.broken_links) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_links": self.total_links, "resolved_links": self.resolved_links,
            "broken_links": [dict(b) for b in self.broken_links],
            "graph_nodes": self.graph_nodes, "graph_edges": self.graph_edges,
            "valid": self.valid,
        }


@dataclass(slots=True, frozen=True)
class IcmQuoteCheckReport:
    """Report of verbatim quote checking against raw sources and keep-out lists."""

    total_quotes: int
    verified_quotes: int
    broken_quotes: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    keep_out_violations: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.broken_quotes) == 0 and len(self.keep_out_violations) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_quotes": self.total_quotes, "verified_quotes": self.verified_quotes,
            "broken_quotes": [dict(b) for b in self.broken_quotes],
            "warnings": list(self.warnings), "keep_out_violations": list(self.keep_out_violations),
            "valid": self.valid,
        }


@dataclass(slots=True, frozen=True)
class IcmIndexReport:
    """Report of frontmatter index generation across records and shelves."""

    folders_indexed: list[str]
    total_notes: int
    index_files_written: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "folders_indexed": list(self.folders_indexed),
            "total_notes": self.total_notes,
            "index_files_written": list(self.index_files_written),
        }


@dataclass(slots=True, frozen=True)
class IcmScaffoldResult:
    """Result of scaffolding a new ICM workspace or stage."""

    target_dir: str
    form: str
    created_files: list[str]
    status: str = "ok"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_dir": self.target_dir, "form": self.form,
            "created_files": list(self.created_files), "status": self.status,
            "error": self.error,
        }


@dataclass(slots=True, frozen=True)
class IcmTemplateInterpolateResult:
    """Result of interpolating a template with variables (arXiv:2603.16021)."""

    output_path: str
    variables_applied: dict[str, str] = field(default_factory=dict)
    unresolved_placeholders: list[str] = field(default_factory=list)
    status: str = "ok"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": self.output_path,
            "variables_applied": dict(self.variables_applied),
            "unresolved_placeholders": list(self.unresolved_placeholders),
            "status": self.status, "error": self.error,
        }
