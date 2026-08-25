"""Data models for MemGraphRAG 3-Layer Memory (Schema, Fact, Passage) and Conflict Groups."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SchemaNode:
    """Schema layer node: stores abstract ontology triple (head_type, relation, tail_type)."""

    idx: int
    content: Tuple[str, str, str]
    frequency: int = 0
    embedding: Optional[List[float]] = None
    fact_indices: List[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "idx": self.idx,
            "content": list(self.content),
            "frequency": self.frequency,
            "embedding": self.embedding,
            "fact_indices": self.fact_indices,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaNode":
        return cls(
            idx=data["idx"],
            content=tuple(data["content"]),  # type: ignore
            frequency=data.get("frequency", 0),
            embedding=data.get("embedding"),
            fact_indices=data.get("fact_indices", []),
        )


@dataclass
class FactNode:
    """Fact layer node: stores concrete relational triple (head, relation, tail)."""

    idx: int
    content: Tuple[str, str, str]
    frequency: int = 0
    embedding: Optional[List[float]] = None
    schema_idx: int = -1
    passage_indices: List[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "idx": self.idx,
            "content": list(self.content),
            "frequency": self.frequency,
            "embedding": self.embedding,
            "schema_idx": self.schema_idx,
            "passage_indices": self.passage_indices,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FactNode":
        return cls(
            idx=data["idx"],
            content=tuple(data["content"]),  # type: ignore
            frequency=data.get("frequency", len(data.get("passage_indices", []))),
            embedding=data.get("embedding"),
            schema_idx=data.get("schema_idx", -1),
            passage_indices=data.get("passage_indices", []),
        )


@dataclass
class PassageNode:
    """Passage layer node: stores original text chunks and citation identifiers."""

    idx: int
    chunk_id: str
    content: str
    embedding: Optional[List[float]] = None
    fact_indices: List[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "idx": self.idx,
            "chunk_id": self.chunk_id,
            "content": self.content,
            "embedding": self.embedding,
            "fact_indices": self.fact_indices,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PassageNode":
        return cls(
            idx=data["idx"],
            chunk_id=data["chunk_id"],
            content=data["content"],
            embedding=data.get("embedding"),
            fact_indices=data.get("fact_indices", []),
        )


class ConflictGroupModel(BaseModel):
    """Pydantic model representing a semantic conflict group."""

    group_id: str = Field(..., description="Unique conflict group ID")
    head: str = Field(..., description="Subject entity name")
    relation: str = Field(..., description="Relation predicate")
    conflicting_tails: list[str] = Field(default_factory=list, description="Contradictory tail entities")
    fact_indices: list[int] = Field(default_factory=list, description="Fact node indices involved")
    supporting_passage_indices: list[int] = Field(default_factory=list, description="Supporting passage indices")
    resolution_status: str = Field(default="pending", description="Resolution status (pending, resolved, discarded)")
    resolved_tail: str | None = Field(default=None, description="Resolved tail entity")
