"""Slotted dataclasses, context types, observer protocol, and budget configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
import time
from typing import Any, Dict, Optional, Protocol, Set, Tuple
import uuid


class ContextType(str, Enum):
    """Semantic context channel types."""

    INSTRUCTION = "instruction"
    MEMORY = "memory"
    EVIDENCE = "evidence"
    TOOL_OUTPUT = "tool_output"


class ContextTypeError(Exception):
    """Raised when an illegal context type transition or channel insertion occurs."""
    pass


# Static Policy Boundaries
PROTECTED_TYPES: Set[ContextType] = {
    ContextType.INSTRUCTION,
}

ALLOWED_TRANSITIONS: Set[Tuple[ContextType, ContextType]] = {
    (ContextType.TOOL_OUTPUT, ContextType.EVIDENCE),
    (ContextType.EVIDENCE, ContextType.MEMORY),
}


def transition_allowed(from_type: ContextType, to_type: ContextType) -> bool:
    """Check whether explicit transition between two context channels is allowed."""
    return (from_type, to_type) in ALLOWED_TRANSITIONS


@dataclass(slots=True)
class ContextItem:
    """A typed unit of context with provenance metadata."""

    context_type: ContextType
    content: str
    source: Optional[str] = None
    priority: int = 0
    created: float = field(default_factory=time.time)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    derived_from: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.context_type, ContextType):
            self.context_type = ContextType(self.context_type)
        if not self.content or not self.content.strip():
            raise ValueError("ContextItem content cannot be empty")

    def describe(self) -> str:
        origin = f" <- {self.derived_from}" if self.derived_from else ""
        return (
            f"[{self.context_type.value:<12}] "
            f"source={self.source or 'unknown':<20} "
            f"id={self.request_id}{origin}"
        )

    def estimate_tokens(self, char_per_token: float = 4.0) -> int:
        """Estimate token cost of this item's text content."""
        return max(1, math.ceil(len(self.content) / char_per_token))

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_type": self.context_type.value,
            "content": self.content,
            "source": self.source,
            "priority": self.priority,
            "created": self.created,
            "request_id": self.request_id,
            "derived_from": self.derived_from,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextItem:
        return cls(
            context_type=ContextType(data["context_type"]),
            content=data["content"],
            source=data.get("source"),
            priority=data.get("priority", 0),
            created=data.get("created", time.time()),
            request_id=data.get("request_id", uuid.uuid4().hex[:8]),
            derived_from=data.get("derived_from"),
        )


class ContextObserver(Protocol):
    """Observer protocol for monitoring context lifecycle events."""

    def on_item_added(self, item: ContextItem) -> None:
        ...

    def on_item_transformed(self, old_item: ContextItem, new_item: ContextItem) -> None:
        ...

    def on_rejection(self, context_type: ContextType, content: str, reason: str) -> None:
        ...


@dataclass(slots=True)
class BudgetConfig:
    """Configuration for token budgeting across context channels."""

    max_tokens: Optional[int] = None
    channel_quotas: Optional[Dict[ContextType, float]] = None
    char_per_token: float = 4.0
