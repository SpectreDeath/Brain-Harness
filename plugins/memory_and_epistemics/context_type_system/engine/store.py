"""ContextStore runtime boundary enforcing provenance, policy barriers, and O(1) indexed lookups."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    PROTECTED_TYPES,
    ContextItem,
    ContextObserver,
    ContextType,
    ContextTypeError,
    transition_allowed,
)


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
