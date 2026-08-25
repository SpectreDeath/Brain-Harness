"""Core engine for Context Type System provenance, ledger verification, token budgeting, and prompt assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
import time
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple
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


@dataclass
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


@dataclass
class BudgetConfig:
    """Configuration for token budgeting across context channels."""

    max_tokens: Optional[int] = None
    channel_quotas: Optional[Dict[ContextType, float]] = None
    char_per_token: float = 4.0


SECTION_ORDER = [
    ContextType.INSTRUCTION,
    ContextType.MEMORY,
    ContextType.EVIDENCE,
    ContextType.TOOL_OUTPUT,
]

SECTION_LABELS = {
    ContextType.INSTRUCTION: "Instructions",
    ContextType.MEMORY: "Memory",
    ContextType.EVIDENCE: "Evidence",
    ContextType.TOOL_OUTPUT: "Tool Output",
}


class ContextAssembler:
    """Groups typed context items by channel into a structured, token-budgeted prompt."""

    def assemble(
        self,
        items: List[ContextItem],
        section_order: Optional[List[str | ContextType]] = None,
        custom_labels: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None,
        channel_quotas: Optional[Dict[str | ContextType, float]] = None,
    ) -> str:
        res = self.assemble_detailed(
            items=items,
            section_order=section_order,
            custom_labels=custom_labels,
            max_tokens=max_tokens,
            channel_quotas=channel_quotas,
        )
        return res["prompt"]

    def assemble_detailed(
        self,
        items: List[ContextItem],
        section_order: Optional[List[str | ContextType]] = None,
        custom_labels: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None,
        channel_quotas: Optional[Dict[str | ContextType, float]] = None,
        char_per_token: float = 4.0,
    ) -> dict[str, Any]:
        """Assemble prompt with token budgeting, channel allocation quotas, and pruning telemetry."""
        order = SECTION_ORDER
        if section_order:
            order = [ContextType(s) if isinstance(s, str) else s for s in section_order]

        labels = dict(SECTION_LABELS)
        if custom_labels:
            for k, v in custom_labels.items():
                labels[ContextType(k)] = v

        parsed_quotas: Dict[ContextType, float] = {}
        if channel_quotas:
            for k, v in channel_quotas.items():
                ct = ContextType(k) if isinstance(k, str) else k
                parsed_quotas[ct] = v

        sections: List[str] = []
        channel_breakdown: Dict[str, int] = {}
        total_used_tokens = 0
        total_dropped_items = 0
        rendered_item_count = 0

        for context_type in order:
            matching = [i for i in items if i.context_type == context_type]
            if not matching:
                continue

            # Sort descending by priority, then ascending by creation time
            sorted_items = sorted(matching, key=lambda i: (-i.priority, i.created))

            # Determine channel token budget limit
            channel_token_limit: Optional[int] = None
            if max_tokens is not None:
                if parsed_quotas and context_type in parsed_quotas:
                    channel_token_limit = max(1, int(max_tokens * parsed_quotas[context_type]))
                else:
                    channel_token_limit = max_tokens - total_used_tokens

            retained_items: List[ContextItem] = []
            channel_tokens = 0

            for item in sorted_items:
                item_tokens = item.estimate_tokens(char_per_token=char_per_token)
                if channel_token_limit is not None and (channel_tokens + item_tokens > channel_token_limit):
                    total_dropped_items += 1
                    continue
                if max_tokens is not None and (total_used_tokens + item_tokens > max_tokens):
                    total_dropped_items += 1
                    continue

                retained_items.append(item)
                channel_tokens += item_tokens
                total_used_tokens += item_tokens

            if not retained_items:
                continue

            label = labels.get(context_type, context_type.value.capitalize())
            lines = [f"{label}:"]
            for item in retained_items:
                lines.append(f"- {item.content}")

            sections.append("\n".join(lines))
            channel_breakdown[context_type.value] = len(retained_items)
            rendered_item_count += len(retained_items)

        prompt_str = "\n\n".join(sections)
        estimated_prompt_tokens = max(1, math.ceil(len(prompt_str) / char_per_token)) if prompt_str else 0

        return {
            "prompt": prompt_str,
            "used_tokens": estimated_prompt_tokens,
            "dropped_items_count": total_dropped_items,
            "channel_breakdown": channel_breakdown,
            "item_count": rendered_item_count,
        }


class ContextStore:
    """Runtime boundary enforcing provenance, type channel protection, and O(1) indexed lookups."""

    def __init__(self) -> None:
        self._items: List[ContextItem] = []
        self._by_id: Dict[str, ContextItem] = {}
        # content (normalized) -> (original ContextType, request_id)
        self._ledger: Dict[str, Tuple[ContextType, str]] = {}
        self._observers: List[ContextObserver] = []

    @staticmethod
    def _key(content: str) -> str:
        return " ".join(content.split()).lower()

    def add_observer(self, observer: ContextObserver) -> None:
        """Register a lifecycle observer."""
        self._observers.append(observer)

    def _notify_added(self, item: ContextItem) -> None:
        for obs in self._observers:
            try:
                obs.on_item_added(item)
            except Exception:
                pass

    def _notify_transformed(self, old_item: ContextItem, new_item: ContextItem) -> None:
        for obs in self._observers:
            try:
                obs.on_item_transformed(old_item, new_item)
            except Exception:
                pass

    def _notify_rejected(self, context_type: ContextType, content: str, reason: str) -> None:
        for obs in self._observers:
            try:
                obs.on_rejection(context_type, content, reason)
            except Exception:
                pass

    def add_context(
        self,
        context_type: str | ContextType,
        content: str,
        source: Optional[str] = None,
        priority: int = 0,
        _via_transform: bool = False,
        _derived_from: Optional[str] = None,
    ) -> ContextItem:
        context_type = ContextType(context_type)
        key = self._key(content)

        existing = self._ledger.get(key)
        if existing is not None:
            origin_type, origin_id = existing
            if origin_type != context_type:
                if context_type in PROTECTED_TYPES and not _via_transform:
                    err_msg = (
                        f"{origin_type.value} cannot be inserted into "
                        f"{context_type.value} context "
                        f"(content first registered as {origin_type.value}, id={origin_id})"
                    )
                    self._notify_rejected(context_type, content, err_msg)
                    raise ContextTypeError(err_msg)

        item = ContextItem(
            context_type=context_type,
            content=content,
            source=source,
            priority=priority,
            derived_from=_derived_from,
        )

        if existing is None:
            # First time this content has been seen — record permanent origin in ledger
            self._ledger[key] = (context_type, item.request_id)

        self._items.append(item)
        self._by_id[item.request_id] = item
        self._notify_added(item)
        return item

    def transform(
        self,
        item: ContextItem,
        to_type: str | ContextType,
        source: Optional[str] = None,
    ) -> ContextItem:
        """Explicitly move content across an allowed boundary."""
        to_type = ContextType(to_type)
        if not transition_allowed(item.context_type, to_type):
            err_msg = (
                f"transition {item.context_type.value} -> {to_type.value} "
                f"is not permitted by policy"
            )
            self._notify_rejected(to_type, item.content, err_msg)
            raise ContextTypeError(err_msg)

        new_item = self.add_context(
            context_type=to_type,
            content=item.content,
            source=source or item.source,
            priority=item.priority,
            _via_transform=True,
            _derived_from=item.request_id,
        )
        self._notify_transformed(item, new_item)
        return new_item

    def get_item(self, request_id: str) -> Optional[ContextItem]:
        """O(1) indexed item lookup."""
        return self._by_id.get(request_id)

    def get_lineage(self, request_id: str) -> List[ContextItem]:
        """Trace the full multi-hop derivation chain back to the root observation (Isnad audit)."""
        chain: List[ContextItem] = []
        visited: Set[str] = set()
        curr_id: Optional[str] = request_id

        while curr_id is not None:
            if curr_id in visited:
                break  # Cycle protection
            visited.add(curr_id)
            item = self.get_item(curr_id)
            if item is None:
                break
            chain.append(item)
            curr_id = item.derived_from

        chain.reverse()
        return chain

    def items(self) -> List[ContextItem]:
        return list(self._items)

    def items_of_type(self, context_type: str | ContextType) -> List[ContextItem]:
        context_type = ContextType(context_type)
        return [i for i in self._items if i.context_type == context_type]

    def get_ledger(self) -> List[dict[str, str]]:
        return [
            {"key": k, "origin_type": v[0].value, "origin_id": v[1]}
            for k, v in self._ledger.items()
        ]

    def export_state(self) -> dict[str, Any]:
        """Export internal state to a serializable dictionary."""
        return {
            "items": [item.to_dict() for item in self._items],
            "ledger": [
                {"key": k, "origin_type": v[0].value, "origin_id": v[1]}
                for k, v in self._ledger.items()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextStore:
        """Construct a ContextStore from a serialized snapshot."""
        store = cls()
        items_data = data.get("items", [])
        ledger_data = data.get("ledger", [])

        for item_dict in items_data:
            item = ContextItem.from_dict(item_dict)
            store._items.append(item)
            store._by_id[item.request_id] = item

        for led in ledger_data:
            store._ledger[led["key"]] = (ContextType(led["origin_type"]), led["origin_id"])

        return store


def validate_tool_result(
    store: ContextStore,
    tool_item: ContextItem,
    strict_mode: bool = False,
) -> ContextItem:
    """Promote a TOOL_OUTPUT item to EVIDENCE with validation checking."""
    content_lower = tool_item.content.lower()
    if "error" in content_lower or "failed" in content_lower:
        raise ContextTypeError(
            f"tool output from '{tool_item.source}' failed validation "
            f"and cannot become evidence: {tool_item.content!r}"
        )
    if strict_mode:
        if "exception" in content_lower or "timeout" in content_lower or "unauthorized" in content_lower:
            raise ContextTypeError(
                f"tool output failed strict validation: {tool_item.content!r}"
            )
    return store.transform(tool_item, to_type=ContextType.EVIDENCE, source=tool_item.source)


class ContextSessionManager:
    """Manages independent ContextStore sessions by session_id with snapshot persistence."""

    def __init__(self) -> None:
        self._sessions: Dict[str, ContextStore] = {}

    def get_session(self, session_id: str) -> ContextStore:
        if session_id not in self._sessions:
            self._sessions[session_id] = ContextStore()
        return self._sessions[session_id]

    def reset_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def export_session(self, session_id: str) -> dict[str, Any]:
        """Export session state as a portable snapshot."""
        store = self.get_session(session_id)
        return {
            "session_id": session_id,
            "exported_at": time.time(),
            "state": store.export_state(),
        }

    def import_session(self, session_id: str, data: dict[str, Any]) -> None:
        """Restore a session from a snapshot dictionary."""
        state = data.get("state", data)
        self._sessions[session_id] = ContextStore.from_dict(state)
