"""AgentWikis service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class WikiScopeData(BaseModel):
    """Declared scope boundaries and freshness timestamp for a wiki."""

    covers: str = Field(default="", description="Topics and workflows covered by this wiki")
    not_covered: str = Field(default="", description="Explicit negative boundaries and excluded topics")
    current_as: str = Field(default="Unknown", description="Freshness date of the wiki documentation")


class WikiEntityData(BaseModel):
    """Canonical representation of an AgentWikis documentation corpus."""

    slug: str = Field(..., description="Unique wiki slug identifier")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(default="", description="Wiki summary")
    category: str = Field(default="uncategorized", description="Functional category")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    scope: WikiScopeData = Field(default_factory=WikiScopeData, description="Declared scope boundaries")
    document_count: int = Field(default=0, description="Total documents in wiki")
    last_updated: str = Field(default="Unknown", description="Last updated timestamp")
    raw_base: str = Field(default="", description="Raw Markdown URL base")
    html_base: str = Field(default="", description="HTML web documentation URL base")
    xl_document_count: int = Field(default=0, description="Pro XL documents count")


class SearchHitData(BaseModel):
    """Single search hit from AgentWikis full-text or metadata index."""

    wiki_slug: str = Field(..., description="Wiki slug containing document")
    doc_path: str = Field(..., description="Relative document path")
    title: str = Field(..., description="Document title or section")
    score: float = Field(default=0.0, description="Relevance score")
    calibrated_confident: bool = Field(default=False, description="Calibrated confidence flag")
    snippet: str = Field(default="", description="Document context snippet")


class DocumentSliceData(BaseModel):
    """Extracted Markdown document section with isnad provenance."""

    wiki_slug: str = Field(..., description="Wiki slug")
    relative_path: str = Field(..., description="Relative document path")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Extracted Markdown content")
    section: str | None = Field(default=None, description="Extracted sub-section heading")
    is_gated: bool = Field(default=False, description="Whether document requires Pro access")
    source_isnad: str = Field(default="local_llms_full_txt", description="Provenance origin")


class MatchResultData(BaseModel):
    """Intent triage and boundary evaluation result."""

    query: str = Field(..., description="Input query or task prompt")
    in_scope: bool = Field(default=True, description="Whether task is within AgentWikis scope")
    calibrated_confident: bool = Field(default=True, description="Confidence threshold passed")
    confidence: float = Field(default=0.85, description="Calibrated confidence score 0.0-1.0")
    rejection_reason: str | None = Field(default=None, description="Reason if rejected")
    recommended_wikis: list[dict[str, Any]] = Field(default_factory=list, description="Recommended wikis")
    recommended_agentwikis_skills: list[dict[str, Any]] = Field(default_factory=list, description="Recommended skills")
    recommended_local_workspace_skills: list[str] = Field(default_factory=list, description="Workspace skills")
    fallback_recommendation: str = Field(default="none", description="Fallback routing recommendation")


@runtime_checkable
class AgentWikisService(Protocol):
    """Protocol for AgentWikis documentation, boundary triage, and offline slicing."""

    def list_wikis(
        self,
        category: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[Any]:
        """List wikis filtered by category, tag, or text query."""
        ...

    def get_scope(self, wiki_slug: str) -> Any | None:
        """Get declared scope and boundaries for a specific wiki."""
        ...

    def match_intent(self, query: str, limit: int = 3) -> Any:
        """Evaluate task intent against wiki scopes and skills with calibrated abstention."""
        ...

    def search(
        self,
        query: str,
        wiki: str | None = None,
        limit: int = 5,
    ) -> list[Any] | tuple[Any, ...]:
        """Search documentation corpus with calibrated confidence."""
        ...

    def extract_document(
        self,
        doc_path: str,
        section_heading: str | None = None,
        force_remote: bool = False,
    ) -> Any:
        """Extract exact Markdown document section offline or via remote fallback."""
        ...

    def prepare_context_pack(
        self,
        query: str,
        max_tokens: int = 4000,
    ) -> str:
        """One-shot intent triage, document retrieval, and token-bounded context assembly."""
        ...


AGENTWIKIS_SERVICE_KEY: ServiceKey[AgentWikisService] = ServiceKey("service.agentwikis")
