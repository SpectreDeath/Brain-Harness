"""Prompt assembly with channel grouping, ordering, and token budget enforcement."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .models import ContextItem, ContextType

SECTION_ORDER: List[ContextType] = [
    ContextType.INSTRUCTION,
    ContextType.MEMORY,
    ContextType.EVIDENCE,
    ContextType.TOOL_OUTPUT,
]

SECTION_LABELS: Dict[ContextType, str] = {
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
