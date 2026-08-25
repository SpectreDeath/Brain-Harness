"""Internal domain models for Graphiti Memory Plugin."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EpisodicNode(BaseModel):
    """Represents a raw interaction, turn, document, or temporal event."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str = Field(default="default")
    content: str = Field(...)
    source_description: str = Field(default="interaction")
    created_at: datetime = Field(default_factory=_utc_now)
    extracted_entities: list[str] = Field(default_factory=list)
    extracted_edges: list[str] = Field(default_factory=list)


class EntityNode(BaseModel):
    """Represents a resolved semantic concept, agent, or domain object."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str = Field(default="default")
    name: str = Field(...)
    entity_type: str = Field(default="CONCEPT")
    summary: str = Field(default="")
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    episodes: list[str] = Field(default_factory=list)


class EntityEdge(BaseModel):
    """Represents a bi-temporal relational fact connecting two entities."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str = Field(default="default")
    source_node_uuid: str = Field(...)
    source_name: str = Field(...)
    target_node_uuid: str = Field(...)
    target_name: str = Field(...)
    relation_name: str = Field(...)
    fact: str = Field(...)
    episodes: list[str] = Field(default_factory=list)
    valid_at: datetime = Field(default_factory=_utc_now)
    invalid_at: datetime | None = Field(default=None)
    expired_at: datetime | None = Field(default=None)
    weight: float = Field(default=1.0)
