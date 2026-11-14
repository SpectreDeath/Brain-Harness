"""Brain Harness Vault ModelSource adapter for Ontology-Spider.

Implements the ModelSource seam interface defined in ``ontology_spider.seam``,
mapping Brain Harness Knowledge Vault items, canonical ``edges``, ``isnad``
provenance claims, and temporal validity bounds into an ``OntologyModel``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Union, cast

logger = logging.getLogger(__name__)

_NOISE_DIRS = frozenset({".git", "__pycache__", ".venv", "node_modules", "dist", "target"})

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


def _summarize_isnad(raw_isnad: Any) -> dict[str, Any]:
    """Normalize dict or list isnad claims into summary verification fields."""
    if isinstance(raw_isnad, dict) and raw_isnad:
        claims = [raw_isnad]
    elif isinstance(raw_isnad, list):
        claims = [entry for entry in raw_isnad if isinstance(entry, dict)]
    else:
        claims = []

    verified_count = sum(
        1
        for claim in claims
        if bool(
            claim.get("verified_at")
            or claim.get("sha256")
            or claim.get("verified") is True
            or str(claim.get("status", "")).lower() == "verified"
        )
    )
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
        "isnad_count": len(claims),
        "verified_isnad_count": verified_count,
        "isnad_verified": verified_count > 0,
        "min_isnad_confidence": round(min_conf, 4),
    }


def _extract_item_and_edges(
    data: dict[str, Any],
    fallback_id: str,
    min_confidence: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract normalized item dictionary and edge records from one KI JSON payload."""
    raw_id = str(data.get("id") or fallback_id)
    item_id = _sanitize_identifier(raw_id)
    raw_meta = data.get("metadata")
    meta = dict(raw_meta) if isinstance(raw_meta, dict) else dict(data)
    meta.update(_summarize_isnad(data.get("isnad")))
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

    extracted_edges: list[dict[str, Any]] = []
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
        extracted_edges.append(
            {
                "from": item_id,
                "rel": rel,
                "to": _sanitize_identifier(raw_dst),
                "target_kind": str(raw_edge.get("target_kind") or ""),
                "valid_from": raw_edge.get("valid_from"),
                "valid_until": raw_edge.get("valid_until"),
                "metadata": {
                    "confidence": conf,
                    "description": raw_edge.get("description") or "",
                    "raw_target": raw_dst,
                    "target_kind": raw_edge.get("target_kind") or "",
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
                    "to": _sanitize_identifier(dep_target),
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
        """Scan dual-file KI subdirectories or standalone JSON files with noise pruning."""
        items: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

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
            item_rec, item_edges = _extract_item_and_edges(data, fallback_id, self.min_confidence)
            items.append(item_rec)
            edges.extend(item_edges)

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
