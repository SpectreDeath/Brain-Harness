"""Three-Layer Hierarchical Memory holding Schemas, Facts, and Passages."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .models import FactNode, PassageNode, SchemaNode


class ThreeLayerMemory:
    """Three-layer hierarchical memory holding Schemas, Facts, and Passages."""

    def __init__(self) -> None:
        self.schema_layer: List[SchemaNode] = []
        self.fact_layer: List[FactNode] = []
        self.passage_layer: List[PassageNode] = []

        self._schema_to_idx: Dict[Tuple[str, str, str], int] = {}
        self._fact_to_idx: Dict[Tuple[str, str, str], int] = {}
        self._chunk_id_to_idx: Dict[str, int] = {}

    def get_or_create_schema(self, ontology: Tuple[str, str, str]) -> int:
        if ontology in self._schema_to_idx:
            return self._schema_to_idx[ontology]
        idx = len(self.schema_layer)
        node = SchemaNode(idx=idx, content=ontology)
        self.schema_layer.append(node)
        self._schema_to_idx[ontology] = idx
        return idx

    def get_or_create_fact(self, triple: Tuple[str, str, str], schema_idx: int = -1) -> int:
        if triple in self._fact_to_idx:
            idx = self._fact_to_idx[triple]
            if schema_idx != -1 and self.fact_layer[idx].schema_idx == -1:
                self.fact_layer[idx].schema_idx = schema_idx
            return idx
        idx = len(self.fact_layer)
        node = FactNode(idx=idx, content=triple, schema_idx=schema_idx)
        self.fact_layer.append(node)
        self._fact_to_idx[triple] = idx
        return idx

    def get_or_create_passage(self, chunk_id: str, content: str) -> int:
        if chunk_id in self._chunk_id_to_idx:
            return self._chunk_id_to_idx[chunk_id]
        idx = len(self.passage_layer)
        node = PassageNode(idx=idx, chunk_id=chunk_id, content=content)
        self.passage_layer.append(node)
        self._chunk_id_to_idx[chunk_id] = idx
        return idx

    def link_passage_and_fact(self, passage_idx: int, fact_idx: int) -> None:
        if 0 <= passage_idx < len(self.passage_layer) and 0 <= fact_idx < len(self.fact_layer):
            p_node = self.passage_layer[passage_idx]
            f_node = self.fact_layer[fact_idx]
            if fact_idx not in p_node.fact_indices:
                p_node.fact_indices.append(fact_idx)
            if passage_idx not in f_node.passage_indices:
                f_node.passage_indices.append(passage_idx)
            f_node.frequency = len(f_node.passage_indices)

    def link_fact_and_schema(self, fact_idx: int, schema_idx: int) -> None:
        if 0 <= fact_idx < len(self.fact_layer) and 0 <= schema_idx < len(self.schema_layer):
            f_node = self.fact_layer[fact_idx]
            s_node = self.schema_layer[schema_idx]
            f_node.schema_idx = schema_idx
            if fact_idx not in s_node.fact_indices:
                s_node.fact_indices.append(fact_idx)
            s_node.frequency = len(s_node.fact_indices)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_layer": [s.to_dict() for s in self.schema_layer],
            "fact_layer": [f.to_dict() for f in self.fact_layer],
            "passage_layer": [p.to_dict() for p in self.passage_layer],
            "stats": {
                "num_schemas": len(self.schema_layer),
                "num_facts": len(self.fact_layer),
                "num_passages": len(self.passage_layer),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThreeLayerMemory":
        mem = cls()
        for s_data in data.get("schema_layer", []):
            node = SchemaNode.from_dict(s_data)
            mem.schema_layer.append(node)
            mem._schema_to_idx[node.content] = node.idx

        for f_data in data.get("fact_layer", []):
            node = FactNode.from_dict(f_data)
            mem.fact_layer.append(node)
            mem._fact_to_idx[node.content] = node.idx

        for p_data in data.get("passage_layer", []):
            node = PassageNode.from_dict(p_data)
            mem.passage_layer.append(node)
            mem._chunk_id_to_idx[node.chunk_id] = node.idx

        return mem
