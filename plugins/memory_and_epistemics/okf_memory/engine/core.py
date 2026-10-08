"""OKFMemoryEngine coordinator class for knowledge bundle management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .crud import (
    execute_create,
    execute_relate,
    execute_show,
    execute_update,
    sync_index_and_log,
)
from .search import execute_search
from .utils import (
    DEFAULT_BUNDLE_DIR,
    load_bundle_concepts,
    resolve_bundle,
)
from .validation import execute_validate


class OKFMemoryEngine:
    """In-memory and filesystem engine for OKF v0.2 knowledge bundles."""

    def __init__(self, default_root: str | Path | None = None) -> None:
        self.default_root = Path(default_root) if default_root else Path(DEFAULT_BUNDLE_DIR)

    def _resolve_bundle(self, bundle_dir: str | None = None) -> Path:
        """Resolve bundle root directory safely."""
        return resolve_bundle(self.default_root, bundle_dir)

    def _load_bundle_concepts(self, root: Path) -> dict[str, tuple[dict[str, Any], str, Path]]:
        """Load all valid concept files in bundle root excluding system files."""
        return load_bundle_concepts(root)

    def search(
        self,
        query: str = "",
        for_path: str | None = None,
        limit: int = 3,
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Execute BM25 lexical search or pre-edit governance scoping."""
        root = self._resolve_bundle(bundle_dir)
        concepts = self._load_bundle_concepts(root)
        return execute_search(
            concepts=concepts,
            root=root,
            query=query,
            for_path=for_path,
            limit=limit,
        )

    def show(self, concept_id: str, bundle_dir: str | None = None) -> dict[str, Any] | None:
        """Retrieve full concept record by id."""
        root = self._resolve_bundle(bundle_dir)
        return execute_show(root, concept_id)

    def _sync_index_and_log(
        self,
        root: Path,
        action: str,
        concept_id: str,
        actor: str = "agent:brain-harness",
        details: str = "",
    ) -> None:
        """Auto-update parent index.md table and append audit entry to log.md."""
        sync_index_and_log(
            root=root,
            action=action,
            concept_id=concept_id,
            actor=actor,
            details=details,
        )

    def create(
        self,
        concept_id: str,
        title: str,
        concept_type: str,
        description: str,
        body: str = "",
        governance: list[str] | None = None,
        code_refs: list[str] | None = None,
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Create a new concept document with frontmatter sanitization and auto-sync."""
        root = self._resolve_bundle(bundle_dir)
        return execute_create(
            root=root,
            concept_id=concept_id,
            title=title,
            concept_type=concept_type,
            description=description,
            body=body,
            governance=governance,
            code_refs=code_refs,
        )

    def update(
        self,
        concept_id: str,
        title: str | None = None,
        description: str | None = None,
        body: str | None = None,
        governance: list[str] | None = None,
        code_refs: list[str] | None = None,
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing concept file and sync bookkeeping."""
        root = self._resolve_bundle(bundle_dir)
        return execute_update(
            root=root,
            concept_id=concept_id,
            title=title,
            description=description,
            body=body,
            governance=governance,
            code_refs=code_refs,
        )

    def relate(
        self,
        source_id: str,
        target_id: str,
        description: str = "",
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Bidirectionally relate two concepts in frontmatter."""
        root = self._resolve_bundle(bundle_dir)
        return execute_relate(
            root=root,
            source_id=source_id,
            target_id=target_id,
            description=description,
        )

    def validate(
        self,
        strict: bool = False,
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Validate knowledge bundle against OKF normative schema and trust ordering rules."""
        root = self._resolve_bundle(bundle_dir)
        return execute_validate(root, strict=strict)
