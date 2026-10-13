"""Tool result validation and elevation to evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ContextItem, ContextType, ContextTypeError

if TYPE_CHECKING:
    from .store import ContextStore


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
