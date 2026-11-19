"""Brain Harness Vault ModelSource adapter for Ontology-Spider.

Implements the ModelSource seam interface defined in ``ontology_spider.seam``,
mapping Brain Harness Knowledge Vault items, canonical ``edges``, ``isnad``
provenance claims, and temporal validity bounds into an ``OntologyModel``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any, Union, cast

from harness.services.storage.isnad_hash import verify_claim_entry

logger = logging.getLogger(__name__)

_NOISE_DIRS = frozenset({".git", "__pycache__", ".venv", "node_modules", "dist", "target"})


def _infer_repo_root(dir_path: Path) -> Path:
    """Infer repository root when scanning canonical .harness/knowledge vaults."""
    resolved = dir_path.resolve()
    if resolved.name == "knowledge" and resolved.parent.name == ".harness":
        return resolved.parent.parent
    return resolved

try:
    from ontology_spider.model import (
        Entity,
        OntologyModel,
        Provenance,
        Relation,
    )
    from ontology_spider.seam import ModelSource

    HAS_ONTOLOGY_SPIDER = True
except ModuleNotFoundError:
    HAS_ONTOLOGY_SPIDER = False
    Entity = None  # type: ignore
    OntologyModel = None  # type: ignore
    Provenance = None  # type: ignore
    Relation = None  # type: ignore
    ModelSource = object  # type: ignore


def _sanitize_identifier(raw: Any) -> str:
    """Normalize arbitrary paths, URIs, or hyphenated IDs into .dialog-safe identifiers."""
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw).strip()).strip("_")
    return cleaned or "unknown"


def _alloc_unique_identifier(
    raw_id: Any,
    raw_to_safe: dict[str, str],
    safe_to_raw: dict[str, str],
) -> str:
    """Allocate a collision-free .dialog-safe identifier preserving raw_id mappings."""
    key = str(raw_id)
    if key in raw_to_safe:
        return raw_to_safe[key]
    base = _sanitize_identifier(key)
    candidate = base
    if candidate in safe_to_raw and safe_to_raw[candidate] != key:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:6]
        candidate = f"{base}_{digest}"
        counter = 2
        while candidate in safe_to_raw and safe_to_raw[candidate] != key:
            candidate = f"{base}_{digest}_{counter}"
            counter += 1
    raw_to_safe[key] = candidate
    safe_to_raw[candidate] = key
    return candidate


def _claim_is_verified(
    entry: dict[str, Any],
    *,
    ki_id: str = "",
    repo_root: Path | None = None,
    source_repo: str = "",
    blob_cache: dict[str, str | None] | None = None,
) -> bool:
    """Return True only when a claim or lineage node carries a verified 64-hex SHA-256 hash."""
    return verify_claim_entry(
        entry,
        ki_id=ki_id,
        repo_root=repo_root,
        source_repo=source_repo,
        blob_cache=blob_cache,
    ).verified


def _summarize_isnad(
    raw_isnad: Any,
    *,
    ki_id: str = "",
    repo_root: Path | None = None,
    source_repo: str = "",
    blob_cache: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """Normalize dict, nested claims dict, or list isnad claims into cryptographic summary fields."""
    if isinstance(raw_isnad, dict) and raw_isnad:
        nested_claims = raw_isnad.get("claims")
        if isinstance(nested_claims, list) and nested_claims:
            claims = [entry for entry in nested_claims if isinstance(entry, dict)]
        elif isinstance(nested_claims, list):
            has_envelope_claim = any(
                k in raw_isnad
                for k in ("verified", "status", "verified_at", "sha256", "sha256_hash", "artifact_sha256")
            )
            claims = [raw_isnad] if has_envelope_claim else []
        else:
            claims = [raw_isnad]
    elif isinstance(raw_isnad, list):
        claims = [entry for entry in raw_isnad if isinstance(entry, dict)]
    else:
        claims = []

    checks = [
        verify_claim_entry(
            claim,
            ki_id=ki_id,
            repo_root=repo_root,
            source_repo=source_repo,
            blob_cache=blob_cache,
        )
        for claim in claims
    ]
    verified_count = sum(1 for check in checks if check.verified)
    flagged_missing_count = sum(1 for check in checks if check.status == "MISSING_HASH_FLAGGED")
    total_count = len(checks)

    conf_vals: list[float] = []
    for claim in claims:
        raw_conf = claim.get("confidence")
        if raw_conf is not None:
            try:
                conf_vals.append(float(raw_conf))
            except (TypeError, ValueError):
                pass
    min_conf = min(conf_vals) if conf_vals else (1.0 if verified_count > 0 else 0.0)
    return {
        "isnad_count": total_count,
        "verified_isnad_count": verified_count,
        "isnad_verified": verified_count > 0,
        "isnad_null_hash_flagged_count": flagged_missing_count,
        "min_isnad_confidence": round(min_conf, 4),
    }


def _canonical_code_module_id(raw_dst: str, *, rel: str, target_kind: str) -> str | None:
    """Derive a canonical underscored module ID from src/*.py, src_*_py, or module applicable_to targets."""
    if rel not in ("references_code", "applicable_to"):
        return None
    raw = raw_dst.strip().replace("\\", "/")
    if raw.startswith("./"):
        raw = raw[2:]
    if not raw:
        return None

    if raw.startswith("src/") and raw.endswith(".py"):
        trimmed = raw[4:]
        if trimmed.endswith("/__init__.py"):
            trimmed = trimmed[: -len("/__init__.py")]
        else:
            trimmed = trimmed[: -len(".py")]
        return _sanitize_identifier(trimmed) if trimmed else None

    if "/" not in raw and "." not in raw and raw.startswith("src_") and raw.endswith("_py"):
        trimmed = raw[4:]
        if trimmed.endswith("___init___py"):
            trimmed = trimmed[: -len("___init___py")]
        elif trimmed.endswith("__init___py"):
            trimmed = trimmed[: -len("__init___py")]
        else:
            trimmed = trimmed[: -len("_py")]
        return _sanitize_identifier(trimmed) if trimmed else None

    if (
        rel == "applicable_to"
        and "/" not in raw
        and (target_kind == "module" or raw.startswith(("harness.", "plugins.")))
    ):
        return _sanitize_identifier(raw)

    return None


def _extract_item_and_edges(
    data: dict[str, Any],
    fallback_id: str,
    min_confidence: float,
    *,
    resolved_id: str | None = None,
    raw_to_safe: dict[str, str] | None = None,
    repo_root: Path | None = None,
    blob_cache: dict[str, str | None] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract normalized item dictionary and edge records from one KI JSON payload."""
    raw_id = str(data.get("id") or fallback_id)
    item_id = resolved_id or _sanitize_identifier(raw_id)
    raw_meta = data.get("metadata")
    meta = dict(raw_meta) if isinstance(raw_meta, dict) else dict(data)
    source_repo = str(data.get("source_repo") or "")
    meta.update(
        _summarize_isnad(
            data.get("isnad"),
            ki_id=item_id,
            repo_root=repo_root,
            source_repo=source_repo,
            blob_cache=blob_cache,
        )
    )
    if raw_id != item_id:
        meta.setdefault("raw_id", raw_id)
    for field in ("status", "category", "updated_at", "created_at", "title"):
        if field in data and data[field] is not None:
            meta.setdefault(field, data[field])
    tags = data.get("tags") or []
    if tags:
        meta["tags"] = list(tags)

    item_type = _sanitize_identifier(data.get("type") or data.get("category") or "concept")
    item_record = {"id": item_id, "type": item_type, "metadata": meta}

    def _target_id(raw_dst: str) -> str:
        if raw_to_safe and raw_dst in raw_to_safe:
            return raw_to_safe[raw_dst]
        return _sanitize_identifier(raw_dst)

    extracted_edges: list[dict[str, Any]] = []
    seen_edge_keys: set[tuple[str, str]] = set()
    for raw_edge in data.get("edges") or []:
        if not isinstance(raw_edge, dict):
            continue
        raw_conf = raw_edge.get("confidence")
        conf = float(raw_conf) if raw_conf is not None else 1.0
        if conf < min_confidence:
            continue
        rel = _sanitize_identifier(
            raw_edge.get("type") or raw_edge.get("rel") or raw_edge.get("predicate") or "related_to"
        )
        raw_dst = str(raw_edge.get("target") or raw_edge.get("to") or raw_edge.get("object") or "")
        if not raw_dst:
            continue
        primary_dst = _target_id(raw_dst)
        target_kind = str(raw_edge.get("target_kind") or "")
        if (rel, primary_dst) not in seen_edge_keys:
            seen_edge_keys.add((rel, primary_dst))
            extracted_edges.append(
                {
                    "from": item_id,
                    "rel": rel,
                    "to": primary_dst,
                    "target_kind": target_kind,
                    "valid_from": raw_edge.get("valid_from"),
                    "valid_until": raw_edge.get("valid_until"),
                    "metadata": {
                        "confidence": conf,
                        "description": raw_edge.get("description") or "",
                        "raw_target": raw_dst,
                        "target_kind": target_kind,
                        "valid_from": raw_edge.get("valid_from"),
                        "valid_until": raw_edge.get("valid_until"),
                    },
                }
            )
        canonical_dst = _canonical_code_module_id(raw_dst, rel=rel, target_kind=target_kind)
        if canonical_dst and ("references_code", canonical_dst) not in seen_edge_keys:
            seen_edge_keys.add(("references_code", canonical_dst))
            canon_kind = target_kind or "module"
            extracted_edges.append(
                {
                    "from": item_id,
                    "rel": "references_code",
                    "to": canonical_dst,
                    "target_kind": canon_kind,
                    "valid_from": raw_edge.get("valid_from"),
                    "valid_until": raw_edge.get("valid_until"),
                    "metadata": {
                        "confidence": conf,
                        "description": raw_edge.get("description") or "",
                        "raw_target": raw_dst,
                        "target_kind": canon_kind,
                        "normalized_from_rel": rel,
                        "valid_from": raw_edge.get("valid_from"),
                        "valid_until": raw_edge.get("valid_until"),
                    },
                }
            )

    for dep in data.get("dependencies") or []:
        dep_target = dep if isinstance(dep, str) else (dep.get("id") if isinstance(dep, dict) else "")
        if dep_target:
            extracted_edges.append(
                {
                    "from": item_id,
                    "rel": "depends_on",
                    "to": _target_id(str(dep_target)),
                    "metadata": {"confidence": 1.0, "raw_target": str(dep_target)},
                }
            )

    return item_record, extracted_edges


class HarnessVaultModelSource(ModelSource):
    """Adapter loading canonical vault items, edges, and isnad claims into OntologyModel."""

    def __init__(
        self,
        source: Union[str, Path, dict[str, Any]],
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
        repo_root: Path | None = None,
    ) -> None:
        if not HAS_ONTOLOGY_SPIDER:
            raise RuntimeError(
                "The 'ontology_spider' engine is not installed. "
                "Install it via: pip install -e <path-to-Ontology-Spider> "
                "or consult plugins/memory_and_epistemics/ontology_spider/README.md"
            )
        self.source = source
        self.as_of = as_of
        self.min_confidence = float(min_confidence)
        self.repo_root = Path(repo_root) if repo_root is not None else None
        self.source_label = str(source) if not isinstance(source, dict) else "memory_dict"

    def _load_data_dict(self) -> dict[str, Any]:
        """Normalize input source into a canonical vault dictionary {vault_id, items, edges}."""
        if isinstance(self.source, dict):
            return self.source
        if isinstance(self.source, Path) or (isinstance(self.source, str) and not self.source.strip().startswith("{")):
            p = Path(self.source)
            if p.is_dir():
                return self._scan_vault_directory(p)
            if p.is_file():
                return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8")))
            raise FileNotFoundError(f"Vault source path does not exist: {p}")
        return cast(dict[str, Any], json.loads(str(self.source)))

    def _scan_vault_directory(self, dir_path: Path) -> dict[str, Any]:
        """Scan dual-file KI subdirectories or standalone JSON files with collision-safe IDs."""
        loaded_entries: list[tuple[dict[str, Any], str]] = []

        for child in sorted(dir_path.iterdir(), key=lambda entry: entry.name):
            if child.name in _NOISE_DIRS or child.name.startswith("."):
                continue
            target_file: Path | None = None
            fallback_id = child.name if child.is_dir() else child.stem
            if child.is_dir():
                for candidate in ("metadata.json", "item.json"):
                    if (child / candidate).exists():
                        target_file = child / candidate
                        break
            elif child.is_file() and child.suffix == ".json":
                target_file = child

            if target_file is None:
                continue
            try:
                data = json.loads(target_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                logger.debug("Skipping unreadable vault entry %s: %s", target_file, exc)
                continue
            if not isinstance(data, dict):
                continue
            if "items" in data:
                return data
            loaded_entries.append((data, fallback_id))

        raw_to_safe: dict[str, str] = {}
        safe_to_raw: dict[str, str] = {}
        # Reserve exact clean identifiers before disambiguating colliding raw names
        for data, fallback_id in loaded_entries:
            raw_id = str(data.get("id") or fallback_id)
            if _sanitize_identifier(raw_id) == raw_id:
                _alloc_unique_identifier(raw_id, raw_to_safe, safe_to_raw)
        for data, fallback_id in loaded_entries:
            raw_id = str(data.get("id") or fallback_id)
            _alloc_unique_identifier(raw_id, raw_to_safe, safe_to_raw)

        repo_root = self.repo_root if self.repo_root is not None else _infer_repo_root(dir_path)
        blob_cache: dict[str, str | None] = {}
        items: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        for data, fallback_id in loaded_entries:
            raw_id = str(data.get("id") or fallback_id)
            resolved_id = raw_to_safe[raw_id]
            item_rec, item_edges = _extract_item_and_edges(
                data,
                fallback_id,
                self.min_confidence,
                resolved_id=resolved_id,
                raw_to_safe=raw_to_safe,
                repo_root=repo_root,
                blob_cache=blob_cache,
            )
            items.append(item_rec)
            edges.extend(item_edges)

        # Auto-declare canonical ontology schema (concept taxonomy + domain/range)
        # for directory vaults so structural & Gruber coherence checks pass cleanly.
        builtin_schema_preds = {
            "instance_of",
            "subclass_of",
            "domain",
            "range",
            "disjoint_with",
            "acyclic",
        }
        schema_edges: list[dict[str, Any]] = []
        seen_subtypes: set[str] = set()
        seen_predicates: set[str] = set()

        for item in items:
            item_type = str(item.get("type") or "")
            if item_type and item_type != "concept" and item_type not in seen_subtypes:
                seen_subtypes.add(item_type)
                schema_edges.append({"from": item_type, "rel": "subclass_of", "to": "concept"})

        for edge in edges:
            target_kind = _sanitize_identifier(edge.get("target_kind") or "")
            if edge.get("target_kind") and target_kind != "concept" and target_kind not in seen_subtypes:
                seen_subtypes.add(target_kind)
                schema_edges.append({"from": target_kind, "rel": "subclass_of", "to": "concept"})
            rel = str(edge.get("rel") or "")
            if rel and rel not in builtin_schema_preds and rel not in seen_predicates:
                seen_predicates.add(rel)
                schema_edges.append({"from": rel, "rel": "domain", "to": "concept"})
                schema_edges.append({"from": rel, "rel": "range", "to": "concept"})

        edges.extend(schema_edges)
        return {"vault_id": dir_path.name, "items": items, "edges": edges}

    def _within_temporal_window(self, edge: dict[str, Any], edge_meta: dict[str, Any]) -> bool:
        if not self.as_of:
            return True
        v_from = edge.get("valid_from") or edge_meta.get("valid_from")
        v_until = edge.get("valid_until") or edge_meta.get("valid_until")
        if v_from and str(v_from) > self.as_of:
            return False
        if v_until and str(v_until) < self.as_of:
            return False
        return True

    def load(self) -> OntologyModel:
        """Construct an OntologyModel from the vault data with temporal & confidence filters."""
        data = self._load_data_dict()
        vault_id = data.get("vault_id", "harness_vault")
        model = OntologyModel(uri=f"urn:vault:{vault_id}")
        declared_item_ids: set[str] = set()

        for item in data.get("items") or []:
            raw_item_id = str(item.get("id") or "")
            if not raw_item_id:
                continue
            item_id = _sanitize_identifier(raw_item_id)
            declared_item_ids.add(item_id)
            meta = dict(item.get("metadata") or {})
            title = str(meta.get("title") or item.get("title") or raw_item_id)
            model.add_entity(Entity(id=item_id, name=title, attributes=meta))

            item_type = item.get("type")
            if item_type:
                norm_type = _sanitize_identifier(item_type)
                ts = str(meta.get("updated_at") or meta.get("updated") or "")
                prov_kwargs: dict[str, Any] = {"source": f"vault:{self.source_label}", "turn_id": "vault_item_type"}
                if ts:
                    prov_kwargs["timestamp"] = ts
                model.add_assertion(
                    relation=Relation(subject=item_id, predicate="instance_of", object=norm_type),
                    provenance=Provenance(**prov_kwargs),
                )

        for edge in data.get("edges") or []:
            edge_meta = dict(edge.get("metadata") or {})
            raw_conf = edge.get("confidence", edge_meta.get("confidence"))
            conf = float(raw_conf) if raw_conf is not None else 1.0
            if conf < self.min_confidence or not self._within_temporal_window(edge, edge_meta):
                continue

            raw_src = edge.get("from") or edge.get("subject") or edge.get("source") or ""
            raw_rel = edge.get("rel") or edge.get("predicate") or edge.get("relation") or edge.get("type") or ""
            raw_dst = edge.get("to") or edge.get("object") or edge.get("target") or ""
            if not (raw_src and raw_rel and raw_dst):
                continue

            src = _sanitize_identifier(raw_src)
            rel = _sanitize_identifier(raw_rel)
            dst = _sanitize_identifier(raw_dst)
            prov = Provenance(source=f"vault:{self.source_label}", turn_id="vault_edge")
            model.add_assertion(
                relation=Relation(subject=src, predicate=rel, object=dst), provenance=prov, attributes=edge_meta
            )

            target_kind = str(edge.get("target_kind") or edge_meta.get("target_kind") or "")
            if target_kind and dst not in declared_item_ids and not model.query(subject=dst, predicate="instance_of"):
                model.add_assertion(
                    relation=Relation(subject=dst, predicate="instance_of", object=_sanitize_identifier(target_kind)),
                    provenance=Provenance(source=f"vault:{self.source_label}", turn_id="vault_target_kind"),
                )

        return model
