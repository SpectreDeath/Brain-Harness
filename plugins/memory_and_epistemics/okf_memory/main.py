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
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
import yaml

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.okf_memory import (
    OKF_MEMORY_SERVICE_KEY,
    OKFConceptRecord,
    OKFMemoryService,
    OKFSearchResult,
    OKFValidationReport,
)

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


class OKFMemoryEngine:
    """In-memory and filesystem engine for OKF v0.2 knowledge bundles."""

    def __init__(self, default_root: str | Path | None = None) -> None:
        self.default_root = Path(default_root) if default_root else Path(DEFAULT_BUNDLE_DIR)

    def _resolve_bundle(self, bundle_dir: str | None = None) -> Path:
        """Resolve bundle root directory safely."""
        p = Path(bundle_dir) if bundle_dir else self.default_root
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()

    def _load_bundle_concepts(self, root: Path) -> dict[str, tuple[dict[str, Any], str, Path]]:
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

    def search(
        self,
        query: str = "",
        for_path: str | None = None,
        limit: int = 3,
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Search knowledge bundle via BM25 lexical scoring or path-scoped governance matching."""
        root = self._resolve_bundle(bundle_dir)
        concepts = self._load_bundle_concepts(root)

        if not concepts:
            return {
                "status": "ok",
                "query": query,
                "for_path": for_path,
                "results_count": 0,
                "results": [],
            }

        scored: list[dict[str, Any]] = []

        # 1. Path-scoped governance match (Rule 1 / SearchForPath)
        if for_path:
            norm_target = _normalize_path(for_path)
            for cid, (data, body, file_path) in concepts.items():
                code_refs = [
                    _normalize_path(r) for r in (data.get("code_refs") or []) if isinstance(r, str)
                ]
                matched_refs = []
                for ref in code_refs:
                    if ref == norm_target or norm_target.startswith(ref + "/") or ref.startswith(norm_target + "/"):
                        matched_refs.append(ref)

                if matched_refs:
                    score = 100.0 + len(matched_refs) * 10.0
                    gov_rules = data.get("governance") or []
                    scored.append({
                        "id": cid,
                        "title": data.get("title", ""),
                        "type": data.get("type", "concept"),
                        "description": data.get("description", ""),
                        "score": round(score, 2),
                        "governance": gov_rules,
                        "code_refs": code_refs,
                        "matched_refs": matched_refs,
                        "path": _normalize_path(file_path.relative_to(root)),
                    })

            scored.sort(key=lambda x: x["score"], reverse=True)
            results = scored[: max(1, limit)]
            return {
                "status": "ok",
                "query": query,
                "for_path": for_path,
                "results_count": len(results),
                "results": results,
            }

        # 2. BM25 Lexical search (Rule 2 / Search)
        q_tokens = _tokenize(query)
        if not q_tokens:
            # Empty query: return most recent or alphabetically first concepts
            for cid, (data, body, file_path) in list(concepts.items())[:limit]:
                scored.append({
                    "id": cid,
                    "title": data.get("title", ""),
                    "type": data.get("type", "concept"),
                    "description": data.get("description", ""),
                    "score": 1.0,
                    "governance": data.get("governance") or [],
                    "code_refs": data.get("code_refs") or [],
                    "path": _normalize_path(file_path.relative_to(root)),
                })
            return {
                "status": "ok",
                "query": query,
                "for_path": None,
                "results_count": len(scored),
                "results": scored,
            }

        # Document tokenization & corpus stats
        doc_tokens: dict[str, list[str]] = {}
        doc_gov_tokens: dict[str, set[str]] = {}
        df = Counter()
        total_docs = len(concepts)

        for cid, (data, body, _) in concepts.items():
            title_toks = _tokenize(data.get("title", "")) * 3
            desc_toks = _tokenize(data.get("description", "")) * 2
            id_toks = _tokenize(cid) * 2
            gov_texts = [str(g) for g in (data.get("governance") or [])]
            gov_toks = _tokenize(" ".join(gov_texts)) * 3
            body_toks = _tokenize(body)

            all_toks = title_toks + desc_toks + id_toks + gov_toks + body_toks
            doc_tokens[cid] = all_toks
            doc_gov_tokens[cid] = set(gov_toks)

            unique_terms = set(all_toks)
            for t in unique_terms:
                df[t] += 1

        avg_dl = sum(len(toks) for toks in doc_tokens.values()) / max(1, total_docs)
        k1 = 1.2
        b = 0.75

        # Calculate BM25 scores
        for cid, (data, body, file_path) in concepts.items():
            tokens = doc_tokens[cid]
            doc_len = len(tokens)
            term_counts = Counter(tokens)
            score = 0.0

            for qt in q_tokens:
                if qt not in term_counts:
                    continue
                tf = term_counts[qt]
                doc_freq = df.get(qt, 0)
                idf = math.log(1.0 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / avg_dl))
                score += idf * (numerator / denominator)

            # Governance boost bonus
            gov_matches = sum(1 for qt in q_tokens if qt in doc_gov_tokens[cid])
            if gov_matches > 0:
                score += gov_matches * 1.5

            if score > 0.0:
                scored.append({
                    "id": cid,
                    "title": data.get("title", ""),
                    "type": data.get("type", "concept"),
                    "description": data.get("description", ""),
                    "score": round(score, 4),
                    "governance": data.get("governance") or [],
                    "code_refs": data.get("code_refs") or [],
                    "path": _normalize_path(file_path.relative_to(root)),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[: max(1, limit)]
        return {
            "status": "ok",
            "query": query,
            "for_path": None,
            "results_count": len(results),
            "results": results,
        }

    def show(self, concept_id: str, bundle_dir: str | None = None) -> dict[str, Any] | None:
        """Retrieve full concept record by id."""
        root = self._resolve_bundle(bundle_dir)
        concepts = self._load_bundle_concepts(root)
        if concept_id not in concepts:
            return None

        data, body, _file_path = concepts[concept_id]
        return {
            "id": concept_id,
            "title": data.get("title", ""),
            "type": data.get("type", "concept"),
            "description": data.get("description", ""),
            "body": body,
            "governance": data.get("governance") or [],
            "code_refs": data.get("code_refs") or [],
            "generated": data.get("generated") or {},
            "verified": data.get("verified") or {},
            "sources": data.get("sources") or [],
            "extra": {k: v for k, v in data.items() if k not in {
                "id", "title", "type", "description", "governance", "code_refs", "generated", "verified", "sources"
            }},
        }

    def _sync_index_and_log(
        self,
        root: Path,
        action: str,
        concept_id: str,
        actor: str = "agent:brain-harness",
        details: str = "",
    ) -> None:
        """Auto-update parent index.md table and append audit entry to log.md."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # 1. Update log.md
        log_file = root / "log.md"
        log_entry = f"| {now_utc} | {action.upper()} | {concept_id} | {actor} | {details} |\n"
        if not log_file.exists():
            header = "# Knowledge Audit Log\n\n| Timestamp (UTC) | Action | Concept ID | Actor | Details |\n|---|---|---|---|---|\n"
            log_file.write_text(header + log_entry, encoding="utf-8")
        else:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

        # 2. Update index.md
        index_file = root / "index.md"
        concepts = self._load_bundle_concepts(root)
        rows = [
            "# Knowledge Index\n",
            "This table is automatically maintained. Do not edit manually.\n",
            "| ID | Type | Title | Description |",
            "|---|---|---|---|",
        ]
        for cid, (data, _, _) in sorted(concepts.items()):
            title = str(data.get("title", "")).replace("|", "\\|").strip()
            ctype = str(data.get("type", "concept")).replace("|", "\\|").strip()
            desc = str(data.get("description", "")).replace("|", "\\|").replace("\n", " ").strip()
            rows.append(f"| [{cid}]({cid}.md) | {ctype} | {title} | {desc} |")
        rows.append("")
        index_file.write_text("\n".join(rows), encoding="utf-8")

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
        """Create a new concept with sanitized frontmatter and auto-synced bookkeeping."""
        root = self._resolve_bundle(bundle_dir)

        # Validate concept ID (alphanumeric, hyphens, underscores)
        cid = concept_id.strip()
        if not re.match(r"^[a-zA-Z0-9_\-]+$", cid):
            raise ValueError(f"Invalid concept ID '{cid}': must be alphanumeric with hyphens or underscores")

        target_file = root / f"{cid}.md"
        _ensure_within_root(root, target_file)

        if target_file.exists():
            raise FileExistsError(f"Concept '{cid}' already exists at {target_file}")

        # Sanitize scalar fields to eliminate unescaped newlines
        clean_title = title.replace("\r", "").replace("\n", " ").strip()
        clean_type = concept_type.replace("\r", "").replace("\n", "").strip().lower()
        clean_desc = description.replace("\r", "").replace("\n", " ").strip()

        now_iso = datetime.now(timezone.utc).isoformat()
        data: dict[str, Any] = {
            "id": cid,
            "title": clean_title,
            "type": clean_type if clean_type in ALLOWED_TYPES else "concept",
            "description": clean_desc,
            "governance": [str(g).strip() for g in (governance or []) if str(g).strip()],
            "code_refs": [_normalize_path(c) for c in (code_refs or []) if str(c).strip()],
            "generated": {
                "by": "agent:brain-harness",
                "at": now_iso,
            },
        }

        full_content = _serialize_concept(data, body)
        target_file.write_text(full_content, encoding="utf-8")

        # Auto-sync index and audit log (Rule 5 / UpdateParentIndex)
        self._sync_index_and_log(
            root=root,
            action="CREATE",
            concept_id=cid,
            details=f"Created concept: {clean_title}",
        )

        return self.show(cid, bundle_dir=str(root)) or data

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
        concepts = self._load_bundle_concepts(root)
        cid = concept_id.strip()

        if cid not in concepts:
            raise FileNotFoundError(f"Concept '{cid}' not found in bundle at {root}")

        data, old_body, target_file = concepts[cid]
        _ensure_within_root(root, target_file)

        if title is not None:
            data["title"] = title.replace("\r", "").replace("\n", " ").strip()
        if description is not None:
            data["description"] = description.replace("\r", "").replace("\n", " ").strip()
        if governance is not None:
            data["governance"] = [str(g).strip() for g in governance if str(g).strip()]
        if code_refs is not None:
            data["code_refs"] = [_normalize_path(c) for c in code_refs if str(c).strip()]

        new_body = body if body is not None else old_body
        full_content = _serialize_concept(data, new_body)
        target_file.write_text(full_content, encoding="utf-8")

        self._sync_index_and_log(
            root=root,
            action="UPDATE",
            concept_id=cid,
            details="Updated concept properties",
        )

        return self.show(cid, bundle_dir=str(root)) or data

    def relate(
        self,
        source_id: str,
        target_id: str,
        description: str = "",
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Bidirectionally relate two concepts in frontmatter."""
        root = self._resolve_bundle(bundle_dir)
        concepts = self._load_bundle_concepts(root)

        src_id = source_id.strip()
        tgt_id = target_id.strip()

        if src_id not in concepts:
            raise FileNotFoundError(f"Source concept '{src_id}' not found")
        if tgt_id not in concepts:
            raise FileNotFoundError(f"Target concept '{tgt_id}' not found")

        src_data, src_body, src_file = concepts[src_id]
        tgt_data, tgt_body, tgt_file = concepts[tgt_id]

        _ensure_within_root(root, src_file)
        _ensure_within_root(root, tgt_file)

        # Update source relations
        src_relations = src_data.get("relations") or []
        if not any(r.get("target") == tgt_id for r in src_relations if isinstance(r, dict)):
            src_relations.append({"target": tgt_id, "description": description.strip()})
            src_data["relations"] = src_relations
            src_file.write_text(_serialize_concept(src_data, src_body), encoding="utf-8")

        # Update target relations reciprocally
        tgt_relations = tgt_data.get("relations") or []
        if not any(r.get("target") == src_id for r in tgt_relations if isinstance(r, dict)):
            tgt_relations.append({"target": src_id, "description": description.strip()})
            tgt_data["relations"] = tgt_relations
            tgt_file.write_text(_serialize_concept(tgt_data, tgt_body), encoding="utf-8")

        self._sync_index_and_log(
            root=root,
            action="RELATE",
            concept_id=src_id,
            details=f"Linked to {tgt_id}: {description}",
        )

        return {
            "status": "ok",
            "source": src_id,
            "target": tgt_id,
            "description": description,
        }

    def validate(
        self,
        strict: bool = False,
        bundle_dir: str | None = None,
    ) -> dict[str, Any]:
        """Validate knowledge bundle against OKF normative schema and trust ordering rules."""
        root = self._resolve_bundle(bundle_dir)
        concepts = self._load_bundle_concepts(root)

        errors: list[str] = []
        warnings: list[str] = []

        if not concepts:
            warnings.append(f"No concept markdown files found in bundle at {root}")

        known_ids = set(concepts.keys())

        for cid, (data, body, file_path) in concepts.items():
            # 1. Required fields
            for req in ["id", "title", "type", "description"]:
                if not data.get(req):
                    errors.append(f"[{cid}] Missing mandatory field: '{req}'")

            # 2. Type validation
            ctype = str(data.get("type", "")).lower()
            if ctype and ctype not in ALLOWED_TYPES:
                warnings.append(f"[{cid}] Non-standard type '{ctype}'. Expected one of: {sorted(ALLOWED_TYPES)}")

            # 3. Actor trust ordering invariant (Rule 3)
            # If generated by agent/AI, cannot self-attest human verification without human: actor
            generated_by = str((data.get("generated") or {}).get("by", "")).lower()
            verified_by = str((data.get("verified") or {}).get("by", "")).lower()

            if generated_by.startswith(("agent:", "ai:")):
                if verified_by and not verified_by.startswith("human:"):
                    warnings.append(
                        f"[{cid}] Automated verification: '{verified_by}' is not an authoritative human actor"
                    )
                if verified_by == generated_by:
                    errors.append(
                        f"[{cid}] Self-attestation violation: agent '{generated_by}' cannot verify its own output"
                    )

            # 4. Broken relationship links
            relations = data.get("relations") or []
            for rel in relations:
                if isinstance(rel, dict):
                    target = rel.get("target")
                    if target and target not in known_ids:
                        errors.append(f"[{cid}] Broken relation: target '{target}' does not exist in bundle")

            # 5. Non-empty description check
            desc = str(data.get("description", "")).strip()
            if desc and len(desc) < 10:
                warnings.append(f"[{cid}] High-density warning: description is too brief ({len(desc)} chars)")

        is_valid = len(errors) == 0
        if strict and len(warnings) > 0:
            is_valid = False

        return {
            "valid": is_valid,
            "concept_count": len(concepts),
            "errors": errors,
            "warnings": warnings,
        }


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
