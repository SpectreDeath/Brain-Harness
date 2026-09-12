"""AgentWikis Plugin — IoC Micro-Kernel Provider for Documentation, Boundary Triage & Knowledge Slicing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure relocatable path to agentwikis_engine
_scripts_dir = (
    Path(__file__).resolve().parent.parent.parent.parent
    / ".agents"
    / "skills"
    / "agentwikis-router"
    / "scripts"
)
if _scripts_dir.exists() and str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from agentwikis_engine import (
    AgentWikisEngine,
    ContractValidationReport,
    DocumentSlice,
    MatchResult,
    QualityScorecard,
    SearchHit,
    WikiEntity,
    WikiScope,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.agentwikis import AGENTWIKIS_SERVICE_KEY, AgentWikisService

logger = structlog.get_logger(__name__)

# Module-level engine instance
_ENGINE_INSTANCE: AgentWikisEngine | None = None


def get_engine() -> AgentWikisEngine:
    """Returns singleton instance of AgentWikisEngine."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = AgentWikisEngine()
    return _ENGINE_INSTANCE


# ---------------------------------------------------------------------------
# Standalone Tool Entrypoints (Matching plugin.json)
# ---------------------------------------------------------------------------


def agentwikis_list(
    category: str | None = None,
    tag: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """List wikis filtered by category, tag, or text query."""
    engine = get_engine()
    wikis = engine.list_wikis(category=category, tag=tag, query=query)
    return [w.to_dict() for w in wikis]


def agentwikis_scope(wiki: str) -> dict[str, Any] | None:
    """Inspect declared scope boundaries, exclusions, and freshness date for a wiki."""
    engine = get_engine()
    wikis, _ = engine.load_entities()
    w = wikis.get(wiki.strip().lower())
    if not w:
        return None
    return {
        "slug": w.slug,
        "title": w.title,
        "category": w.category,
        "last_updated": w.last_updated,
        "document_count": w.document_count,
        "scope": w.scope.to_dict(),
        "raw_base": w.raw_base,
        "xl_documents": w.xl_document_count,
    }


def agentwikis_match(query: str, limit: int = 3) -> dict[str, Any]:
    """Match user task prompt to in-scope wikis and skills with calibrated abstention."""
    engine = get_engine()
    res = engine.match_intent(query=query, limit=limit)
    return res.to_dict()


def agentwikis_search(
    query: str,
    wiki: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search documentation corpus across documents and metadata with calibrated confidence."""
    engine = get_engine()
    hits = engine.search(query=query, wiki=wiki, limit=limit)
    return [h.to_dict() for h in hits]


def agentwikis_read(
    doc_path: str,
    section: str | None = None,
    remote: bool = False,
) -> dict[str, Any]:
    """Extract exact Markdown document or sub-section slice offline or with remote fallback."""
    engine = get_engine()
    doc_slice = engine.extract_document(
        doc_path=doc_path, section_heading=section, force_remote=remote
    )
    return doc_slice.to_dict()


def agentwikis_pack(query: str, max_tokens: int = 4000) -> str:
    """Prepare a one-shot token-bounded Markdown context pack ready for LLM injection."""
    engine = get_engine()
    return engine.prepare_context_pack(query=query, max_tokens=max_tokens)


# ---------------------------------------------------------------------------
# Rule 1, 2, 3, 45: HarnessPlugin Provider Class
# ---------------------------------------------------------------------------


class AgentWikisPlugin(HarnessPlugin, AgentWikisService):
    """Harness Plugin providing AgentWikis documentation, triage, and offline slicing capabilities."""

    name = "plugin.agentwikis"
    version = "1.0.0"
    description = "AgentWikis knowledge discovery, boundary triage, and offline documentation slicing"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENTWIKIS_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(AGENTWIKIS_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # AgentWikisService Protocol Implementation
    # -------------------------------------------------------------------------

    def list_wikis(
        self,
        category: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[WikiEntity]:
        """List wikis filtered by category, tag, or text query."""
        return get_engine().list_wikis(category=category, tag=tag, query=query)

    def get_scope(self, wiki_slug: str) -> WikiScope | None:
        """Get declared scope and boundaries for a specific wiki."""
        return get_engine().get_scope(wiki_slug=wiki_slug)

    def match_intent(self, query: str, limit: int = 3) -> MatchResult:
        """Evaluate task intent against wiki scopes and skills with calibrated abstention."""
        return get_engine().match_intent(query=query, limit=limit)

    def search(
        self,
        query: str,
        wiki: str | None = None,
        limit: int = 5,
    ) -> tuple[SearchHit, ...]:
        """Search documentation corpus with calibrated confidence."""
        return get_engine().search(query=query, wiki=wiki, limit=limit)

    def extract_document(
        self,
        doc_path: str,
        section_heading: str | None = None,
        force_remote: bool = False,
    ) -> DocumentSlice:
        """Extract exact Markdown document section offline or via remote fallback."""
        return get_engine().extract_document(
            doc_path=doc_path,
            section_heading=section_heading,
            force_remote=force_remote,
        )

    def prepare_context_pack(
        self,
        query: str,
        max_tokens: int = 4000,
    ) -> str:
        """One-shot intent triage, document retrieval, and token-bounded context assembly."""
        return get_engine().prepare_context_pack(query=query, max_tokens=max_tokens)

    def validate_contract(
        self,
        contract_path: str | Path | None = None,
    ) -> ContractValidationReport:
        """Validate corpus against Open Data Contract (ODCS) schema (Stage 2)."""
        engine = get_engine()
        c_path = contract_path or (
            _scripts_dir.parent / "contracts" / "agentwikis_contract.yaml"
        )
        return engine.validate_contract(c_path)

    def generate_visual_brief(
        self,
        output_path: str | Path | None = None,
        query: str | None = None,
        wiki_slug: str | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief with Mermaid DAG and blast radius (Stage 3)."""
        return get_engine().generate_visual_brief(
            output_path=output_path, query=query, wiki_slug=wiki_slug
        )

    def profile_data_quality(
        self,
        min_passing_score: float = 85.0,
    ) -> QualityScorecard:
        """Run DAMA-DMBOK 6-dimension data quality profiling across corpus (Stage 4)."""
        return get_engine().profile_data_quality(min_passing_score=min_passing_score)


# Rule 45: Plugin Module Singleton Export
plugin = AgentWikisPlugin()
