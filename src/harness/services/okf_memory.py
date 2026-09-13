"""OKF Agent Memory service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class OKFSearchResult(BaseModel):
    """Result of an OKF lexical BM25 or for-path governance search."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    query: str = Field(default="", description="Queried search terms")
    for_path: str | None = Field(default=None, description="Queried file path for governance scoping")
    results_count: int = Field(default=0, description="Total matching results returned")
    results: list[dict[str, Any]] = Field(default_factory=list, description="Ranked concept headers and scores")
    error: str | None = Field(default=None, description="Error explanation if search failed")


class OKFConceptRecord(BaseModel):
    """Full representation of an OKF concept document."""

    id: str = Field(description="Unique concept identifier (e.g. auth-middleware)")
    title: str = Field(default="", description="Human-readable concept title")
    type: str = Field(default="concept", description="Concept type (decision, architecture, operational, concept)")
    description: str = Field(default="", description="High-density 1-2 sentence summary")
    body: str = Field(default="", description="Markdown body containing concept documentation")
    governance: list[str] = Field(default_factory=list, description="Governance rules or invariants")
    code_refs: list[str] = Field(default_factory=list, description="Related codebase file or directory paths")
    generated: dict[str, Any] = Field(default_factory=dict, description="Provenance metadata (by, at)")
    verified: dict[str, Any] = Field(default_factory=dict, description="Verification metadata (by, at)")
    sources: list[dict[str, Any]] = Field(default_factory=list, description="Source references")
    extra: dict[str, Any] = Field(default_factory=dict, description="Additional custom frontmatter fields")


class OKFValidationReport(BaseModel):
    """Diagnostic validation report for an OKF knowledge bundle."""

    valid: bool = Field(default=True, description="True if no blocking validation errors found")
    concept_count: int = Field(default=0, description="Total valid concepts parsed in bundle")
    errors: list[str] = Field(default_factory=list, description="Critical normative validation failures")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking hygiene and lint warnings")


class OKFGovernanceScope(BaseModel):
    """Pre-edit governance scope result matching concepts to target code paths."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    target_path: str = Field(default="", description="File path evaluated for governance constraints")
    matched_concepts: list[dict[str, Any]] = Field(default_factory=list, description="Concepts governing this path")
    rules: list[str] = Field(default_factory=list, description="Extracted governance rules to enforce")
    error: str | None = Field(default=None, description="Error explanation if scoping failed")


@runtime_checkable
class OKFMemoryService(Protocol):
    """Protocol for interacting with Git-native OKF agent memory bundles."""

    def okf_search(
        self,
        query: str = "",
        for_path: str | None = None,
        limit: int = 3,
        bundle_dir: str | None = None,
    ) -> OKFSearchResult:
        """Search knowledge bundle via BM25 lexical ranking or file path scoping."""
        ...

    async def okf_search_async(
        self,
        query: str = "",
        for_path: str | None = None,
        limit: int = 3,
        bundle_dir: str | None = None,
    ) -> OKFSearchResult:
        """Search knowledge bundle asynchronously."""
        ...

    def okf_show(
        self,
        concept_id: str,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord | None:
        """Retrieve full concept document and frontmatter by identifier."""
        ...

    async def okf_show_async(
        self,
        concept_id: str,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord | None:
        """Retrieve full concept document asynchronously."""
        ...

    def okf_create(
        self,
        concept_id: str,
        title: str,
        concept_type: str,
        description: str,
        body: str = "",
        governance: list[str] | None = None,
        code_refs: list[str] | None = None,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord:
        """Create a new concept document with atomic parent index and log sync."""
        ...

    async def okf_create_async(
        self,
        concept_id: str,
        title: str,
        concept_type: str,
        description: str,
        body: str = "",
        governance: list[str] | None = None,
        code_refs: list[str] | None = None,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord:
        """Create a new concept document asynchronously."""
        ...

    def okf_update(
        self,
        concept_id: str,
        title: str | None = None,
        description: str | None = None,
        body: str | None = None,
        governance: list[str] | None = None,
        code_refs: list[str] | None = None,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord:
        """Update an existing concept document with automatic audit logging."""
        ...

    async def okf_update_async(
        self,
        concept_id: str,
        title: str | None = None,
        description: str | None = None,
        body: str | None = None,
        governance: list[str] | None = None,
        code_refs: list[str] | None = None,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord:
        """Update an existing concept document asynchronously."""
        ...

    def okf_relate(
        self,
        source_id: str,
        target_id: str,
        description: str = "",
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Establish or update relationship between two concepts."""
        ...

    async def okf_relate_async(
        self,
        source_id: str,
        target_id: str,
        description: str = "",
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Establish or update relationship between two concepts asynchronously."""
        ...

    def okf_validate(
        self,
        strict: bool = False,
        bundle_dir: str | None = None,
    ) -> OKFValidationReport:
        """Validate knowledge bundle against OKF normative schema and trust ordering."""
        ...

    async def okf_validate_async(
        self,
        strict: bool = False,
        bundle_dir: str | None = None,
    ) -> OKFValidationReport:
        """Validate knowledge bundle asynchronously."""
        ...


OKF_MEMORY_SERVICE_KEY: ServiceKey[OKFMemoryService] = ServiceKey("service.okf_memory")
