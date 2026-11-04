"""Brain Harness Vault ModelSource adapter for Ontology-Spider.

Implements the ModelSource seam interface defined in ontology_spider.seam,
mapping Brain Harness vault items, typed edges, and metadata into OntologyModel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

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


class HarnessVaultModelSource(ModelSource):
    """Adapter loading vault-shaped items and typed edges into an OntologyModel."""

    def __init__(self, source: Union[str, Path, dict[str, Any]]) -> None:
        if not HAS_ONTOLOGY_SPIDER:
            raise RuntimeError(
                "The 'ontology_spider' engine is not installed. "
                "Install it via: pip install -e <path-to-Ontology-Spider> "
                "or consult plugins/memory_and_epistemics/ontology_spider/README.md"
            )
        self.source = source
        self.source_label = str(source) if not isinstance(source, dict) else "memory_dict"

    def _load_data_dict(self) -> dict[str, Any]:
        """Normalize input source into a canonical vault dictionary {vault_id, items, edges}."""
        if isinstance(self.source, dict):
            return self.source

        if isinstance(self.source, Path) or (
            isinstance(self.source, str) and not self.source.strip().startswith("{")
        ):
            p = Path(self.source)
            if p.is_dir():
                return self._scan_vault_directory(p)
            elif p.is_file():
                content = p.read_text(encoding="utf-8")
                return json.loads(content)
            else:
                raise FileNotFoundError(f"Vault source path does not exist: {p}")

        return json.loads(str(self.source))

    def _scan_vault_directory(self, dir_path: Path) -> dict[str, Any]:
        """Scan a directory of knowledge items (dual-file or metadata.json files)."""
        items: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        # Check subdirectories for metadata.json or item.json
        for child in dir_path.iterdir():
            if child.is_dir():
                meta_file = child / "metadata.json"
                if not meta_file.exists():
                    meta_file = child / "item.json"
                if meta_file.exists():
                    try:
                        data = json.loads(meta_file.read_text(encoding="utf-8"))
                        item_id = data.get("id", child.name)
                        items.append({
                            "id": item_id,
                            "type": data.get("type") or data.get("category", "concept"),
                            "metadata": data.get("metadata", data),
                        })
                        for dep in data.get("dependencies", []):
                            edges.append({
                                "from": item_id,
                                "rel": "depends_on",
                                "to": dep if isinstance(dep, str) else dep.get("id"),
                            })
                    except Exception:
                        continue
            elif child.is_file() and child.suffix == ".json":
                try:
                    data = json.loads(child.read_text(encoding="utf-8"))
                    if "items" in data:
                        return data  # It's an exported vault file in the directory
                    item_id = data.get("id", child.stem)
                    items.append({
                        "id": item_id,
                        "type": data.get("type") or data.get("category", "concept"),
                        "metadata": data.get("metadata", data),
                    })
                    for dep in data.get("dependencies", []):
                        edges.append({
                            "from": item_id,
                            "rel": "depends_on",
                            "to": dep if isinstance(dep, str) else dep.get("id"),
                        })
                except Exception:
                    continue

        return {
            "vault_id": dir_path.name,
            "items": items,
            "edges": edges,
        }

    def load(self) -> OntologyModel:
        """Construct an OntologyModel from the vault data."""
        data = self._load_data_dict()
        vault_id = data.get("vault_id", "harness_vault")
        model = OntologyModel(uri=f"urn:vault:{vault_id}")

        # 1. Map Items -> Entities and Class Assertions
        for item in data.get("items", []):
            item_id = str(item.get("id", ""))
            if not item_id:
                continue

            meta = dict(item.get("metadata", {}))
            title = str(meta.get("title") or item.get("title") or item_id)
            entity = Entity(id=item_id, name=title, attributes=meta)
            model.add_entity(entity)

            # Map type -> instance_of assertion
            item_type = item.get("type")
            if item_type:
                prov = Provenance(
                    source=f"vault:{self.source_label}",
                    turn_id="vault_item_type",
                )
                model.add_assertion(
                    relation=Relation(subject=item_id, predicate="instance_of", object=str(item_type)),
                    provenance=prov,
                )

        # 2. Map Edges -> Relations and Assertions
        for edge in data.get("edges", []):
            src = str(edge.get("from") or edge.get("subject") or edge.get("source", ""))
            rel = str(edge.get("rel") or edge.get("predicate") or edge.get("relation", ""))
            dst = str(edge.get("to") or edge.get("object") or edge.get("target", ""))
            if not (src and rel and dst):
                continue

            prov = Provenance(
                source=f"vault:{self.source_label}",
                turn_id="vault_edge",
            )
            model.add_assertion(
                relation=Relation(subject=src, predicate=rel, object=dst),
                provenance=prov,
                attributes=dict(edge.get("metadata", {})),
            )

        return model
