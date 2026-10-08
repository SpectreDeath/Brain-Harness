"""OKF Agent Memory Plugin for Brain Harness.

Implements the Open Knowledge Framework (OKF v0.2) protocol:
- Git-native plain text knowledge bundle management
- Sub-millisecond BM25 lexical ranking with governance boosting
- Pre-edit governance scoping for target code paths
- Atomic concept mutation with auto-updating parent indexes and audit logs
- Actor trust ordering invariants and normative schema validation
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.okf_memory import (
    OKF_MEMORY_SERVICE_KEY,
    OKFConceptRecord,
    OKFMemoryService,
    OKFSearchResult,
    OKFValidationReport,
)

try:
    from .engine import (
        ALLOWED_TYPES,
        DEFAULT_BUNDLE_DIR,
        OKFMemoryEngine,
        _ensure_within_root,
        _extract_frontmatter,
        _normalize_path,
        _serialize_concept,
        _tokenize,
    )
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    _pkg_dir = Path(__file__).resolve().parent
    if str(_pkg_dir) not in sys.path:
        sys.path.insert(0, str(_pkg_dir))
    from engine import (
        ALLOWED_TYPES,
        DEFAULT_BUNDLE_DIR,
        OKFMemoryEngine,
        _ensure_within_root,
        _extract_frontmatter,
        _normalize_path,
        _serialize_concept,
        _tokenize,
    )

logger = structlog.get_logger(__name__)

# Global default engine instance
_GLOBAL_ENGINE = OKFMemoryEngine()


# -----------------------------------------------------------------------------
# Module Entrypoint Wrappers (Required for AST Inspection & Dynamic Execution)
# -----------------------------------------------------------------------------

def okf_search(
    query: str = "",
    for_path: str | None = None,
    limit: int = 3,
    bundle_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Search knowledge bundle using BM25 lexical ranking or evaluate for-path governance constraints."""
    return _GLOBAL_ENGINE.search(query=query, for_path=for_path, limit=limit, bundle_dir=bundle_dir)


def okf_show(
    concept_id: str,
    bundle_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Retrieve full markdown content, frontmatter metadata, and governance rules for a specific concept."""
    res = _GLOBAL_ENGINE.show(concept_id=concept_id, bundle_dir=bundle_dir)
    if res is None:
        return {"status": "error", "error": f"Concept '{concept_id}' not found"}
    return {"status": "ok", "concept": res}


def okf_create(
    concept_id: str,
    title: str,
    concept_type: str,
    description: str,
    body: str = "",
    governance: list[str] | None = None,
    code_refs: list[str] | None = None,
    bundle_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a new concept document with frontmatter sanitization and automatic parent index updating."""
    try:
        created = _GLOBAL_ENGINE.create(
            concept_id=concept_id,
            title=title,
            concept_type=concept_type,
            description=description,
            body=body,
            governance=governance,
            code_refs=code_refs,
            bundle_dir=bundle_dir,
        )
        return {"status": "ok", "concept": created}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def okf_update(
    concept_id: str,
    title: str | None = None,
    description: str | None = None,
    body: str | None = None,
    governance: list[str] | None = None,
    code_refs: list[str] | None = None,
    bundle_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Update an existing concept document with automatic parent index and audit log synchronization."""
    try:
        updated = _GLOBAL_ENGINE.update(
            concept_id=concept_id,
            title=title,
            description=description,
            body=body,
            governance=governance,
            code_refs=code_refs,
            bundle_dir=bundle_dir,
        )
        return {"status": "ok", "concept": updated}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def okf_relate(
    source_id: str,
    target_id: str,
    description: str = "",
    bundle_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Link two concepts together bidirectionally in frontmatter relations."""
    try:
        return _GLOBAL_ENGINE.relate(
            source_id=source_id,
            target_id=target_id,
            description=description,
            bundle_dir=bundle_dir,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def okf_validate(
    strict: bool = False,
    bundle_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Validate knowledge bundle against OKF normative schema, link consistency, and actor trust ordering."""
    return _GLOBAL_ENGINE.validate(strict=strict, bundle_dir=bundle_dir)


# -----------------------------------------------------------------------------
# Harness Plugin Implementation
# -----------------------------------------------------------------------------

class OKFMemoryPlugin(HarnessPlugin, OKFMemoryService):
    """Harness Plugin providing Open Knowledge Framework (OKF v0.2) memory governance services."""

    name = "plugin.okf_memory"
    version = "1.0.0"
    description = "Git-native agent memory governor providing BM25 search, governance scoping, and trust validation"
    trusted = True

    def __init__(self, engine: OKFMemoryEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OKF_MEMORY_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(OKF_MEMORY_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # OKFMemoryService Protocol Implementation
    # -------------------------------------------------------------------------

    def okf_search(
        self,
        query: str = "",
        for_path: str | None = None,
        limit: int = 3,
        bundle_dir: str | None = None,
    ) -> OKFSearchResult:
        res = self._engine.search(query=query, for_path=for_path, limit=limit, bundle_dir=bundle_dir)
        return OKFSearchResult(
            status=res["status"],
            query=res.get("query", query),
            for_path=res.get("for_path"),
            results_count=res.get("results_count", 0),
            results=res.get("results", []),
            error=res.get("error"),
        )

    async def okf_search_async(
        self,
        query: str = "",
        for_path: str | None = None,
        limit: int = 3,
        bundle_dir: str | None = None,
    ) -> OKFSearchResult:
        return await asyncio.to_thread(self.okf_search, query, for_path, limit, bundle_dir)

    def okf_show(
        self,
        concept_id: str,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord | None:
        rec = self._engine.show(concept_id=concept_id, bundle_dir=bundle_dir)
        if rec is None:
            return None
        return OKFConceptRecord(**rec)

    async def okf_show_async(
        self,
        concept_id: str,
        bundle_dir: str | None = None,
    ) -> OKFConceptRecord | None:
        return await asyncio.to_thread(self.okf_show, concept_id, bundle_dir)

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
        rec = self._engine.create(
            concept_id=concept_id,
            title=title,
            concept_type=concept_type,
            description=description,
            body=body,
            governance=governance,
            code_refs=code_refs,
            bundle_dir=bundle_dir,
        )
        return OKFConceptRecord(**rec)

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
        return await asyncio.to_thread(
            self.okf_create,
            concept_id,
            title,
            concept_type,
            description,
            body,
            governance,
            code_refs,
            bundle_dir,
        )

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
        rec = self._engine.update(
            concept_id=concept_id,
            title=title,
            description=description,
            body=body,
            governance=governance,
            code_refs=code_refs,
            bundle_dir=bundle_dir,
        )
        return OKFConceptRecord(**rec)

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
        return await asyncio.to_thread(
            self.okf_update,
            concept_id,
            title,
            description,
            body,
            governance,
            code_refs,
            bundle_dir,
        )

    def okf_relate(
        self,
        source_id: str,
        target_id: str,
        description: str = "",
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        return self._engine.relate(
            source_id=source_id,
            target_id=target_id,
            description=description,
            bundle_dir=bundle_dir,
        )

    async def okf_relate_async(
        self,
        source_id: str,
        target_id: str,
        description: str = "",
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self.okf_relate, source_id, target_id, description, bundle_dir)

    def okf_validate(
        self,
        strict: bool = False,
        bundle_dir: str | None = None,
    ) -> OKFValidationReport:
        rep = self._engine.validate(strict=strict, bundle_dir=bundle_dir)
        return OKFValidationReport(
            valid=rep["valid"],
            concept_count=rep["concept_count"],
            errors=rep["errors"],
            warnings=rep["warnings"],
        )

    async def okf_validate_async(
        self,
        strict: bool = False,
        bundle_dir: str | None = None,
    ) -> OKFValidationReport:
        return await asyncio.to_thread(self.okf_validate, strict, bundle_dir)


# Module-level singleton (Rule 45)
plugin = OKFMemoryPlugin()

__all__ = [
    "ALLOWED_TYPES",
    "DEFAULT_BUNDLE_DIR",
    "OKFMemoryEngine",
    "OKFMemoryPlugin",
    "_GLOBAL_ENGINE",
    "_ensure_within_root",
    "_extract_frontmatter",
    "_normalize_path",
    "_serialize_concept",
    "_tokenize",
    "okf_create",
    "okf_relate",
    "okf_search",
    "okf_show",
    "okf_update",
    "okf_validate",
    "plugin",
]
