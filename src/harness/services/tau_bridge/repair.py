"""Tool history repair engine, stream normalization, and auto-repair (Rule 21)."""

from __future__ import annotations

import json
import re
from typing import Any

from harness.services.tau_bridge.models import HistoryRepairResult


class ToolHistoryRepairEngine:
    """Normalizes message history to guarantee provider tool-call and tool-result parity.

    Prevents 400 Bad Request provider crashes. Auto-repairs argument JSON syntax (trailing commas,
    markdown fences) per Rule 21 and drops orphan tool responses.
    """

    @classmethod
    def sanitize_arguments_json(cls, raw_args: Any) -> str:
        """Auto-repair JSON arguments string (trailing commas, markdown fences) per Rule 21."""
        if isinstance(raw_args, dict):
            return json.dumps(raw_args)
        if not isinstance(raw_args, str) or not raw_args.strip():
            return "{}"

        text = raw_args.strip()
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

        # Try parsing directly
        try:
            parsed = json.loads(text)
            return json.dumps(parsed)
        except Exception:
            pass

        # Auto-repair trailing commas
        cleaned = re.sub(r",\s*([\]}])", r"\1", text)
        try:
            parsed = json.loads(cleaned)
            return json.dumps(parsed)
        except Exception:
            # Fall back to cleaned string
            return cleaned

    @classmethod
    def repair(cls, messages: list[dict[str, Any]]) -> HistoryRepairResult:
        """Execute deterministic multi-pass tool history repair."""
        repaired: list[dict[str, Any]] = []
        repairs_applied: list[str] = []
        dropped_count = 0
        synthesized_count = 0

        # Build index of all declared tool calls in the transcript
        all_call_ids: set[str] = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for call in msg.get("tool_calls") or []:
                    cid = call.get("id")
                    if cid:
                        all_call_ids.add(cid)

        i = 0
        n = len(messages)

        while i < n:
            msg = messages[i]
            role = msg.get("role")

            if role == "tool":
                t_id = msg.get("tool_call_id")
                # Drop orphan tool response if call ID was never declared
                if not t_id or t_id not in all_call_ids:
                    dropped_count += 1
                    repairs_applied.append(
                        f"Dropped orphan tool response message with tool_call_id '{t_id}'"
                    )
                    i += 1
                    continue

                repaired.append(dict(msg))
                i += 1
                continue

            if role == "assistant" and msg.get("tool_calls"):
                repaired_msg = dict(msg)
                cleaned_calls: list[dict[str, Any]] = []
                for call in msg.get("tool_calls") or []:
                    c_dict = dict(call)
                    fn = c_dict.get("function")
                    if isinstance(fn, dict) and "arguments" in fn:
                        repaired_args = cls.sanitize_arguments_json(fn["arguments"])
                        if repaired_args != fn["arguments"]:
                            fn["arguments"] = repaired_args
                            repairs_applied.append(
                                f"Repaired tool arguments JSON for call '{c_dict.get('id')}'"
                            )
                        c_dict["function"] = fn
                    cleaned_calls.append(c_dict)

                repaired_msg["tool_calls"] = cleaned_calls
                repaired.append(repaired_msg)

                call_ids = [c.get("id") for c in cleaned_calls if c.get("id")]

                # Inspect subsequent tool messages following this assistant message
                j = i + 1
                received_tool_ids: set[str] = set()
                while j < n and messages[j].get("role") == "tool":
                    cand_id = messages[j].get("tool_call_id")
                    if cand_id in call_ids:
                        received_tool_ids.add(cand_id)
                        repaired.append(dict(messages[j]))
                    elif cand_id in all_call_ids:
                        # Belongs to another call block; preserve it
                        repaired.append(dict(messages[j]))
                    else:
                        # Orphan tool message
                        dropped_count += 1
                        repairs_applied.append(
                            f"Dropped unmatched tool message with id '{cand_id}'"
                        )
                    j += 1

                # Synthesize placeholders for any missing tool calls in this block
                for cid in call_ids:
                    if cid not in received_tool_ids:
                        synthesized_count += 1
                        synth_msg = {
                            "role": "tool",
                            "tool_call_id": cid,
                            "content": "[Notice: Tool execution was interrupted or missing in transcript]",
                        }
                        repaired.append(synth_msg)
                        repairs_applied.append(
                            f"Synthesized placeholder response for unresponded tool_call '{cid}'"
                        )

                i = j
                continue

            # Standard message (user, system, or assistant without tool_calls)
            repaired.append(dict(msg))
            i += 1

        is_modified = (
            dropped_count > 0 or synthesized_count > 0 or len(repairs_applied) > 0
        )

        return HistoryRepairResult(
            repaired_messages=tuple(repaired),
            dropped_count=dropped_count,
            synthesized_count=synthesized_count,
            repairs_applied=tuple(repairs_applied),
            is_modified=is_modified,
        )


__all__ = [
    "ToolHistoryRepairEngine",
]
