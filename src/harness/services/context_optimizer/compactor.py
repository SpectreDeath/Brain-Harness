"""Observation compactor strategies with progressive middle-out truncation."""

from __future__ import annotations

import json
import sys
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class MiddleOutObservationCompactor:
    """Default observation compactor with progressive middle-out string and JSON truncation."""

    @property
    def name(self) -> str:
        return "middle_out_compactor"

    def compact(
        self,
        action_name: str,
        observation: Any,
        *,
        max_chars: int,
        compact_json: bool = True,
    ) -> str:
        if observation is None:
            return "Observation: None"

        if isinstance(observation, str):
            text = observation.strip()
            if len(text) > max_chars:
                head = text[: max_chars // 2]
                tail = text[-max_chars // 2 :]
                omitted = len(text) - len(head) - len(tail)
                return f"{head}\n... [TRUNCATED {omitted} CHARS] ...\n{tail}"
            return text

        if isinstance(observation, (dict, list)):
            try:
                if compact_json:
                    text = json.dumps(observation, separators=(",", ":"), default=str)
                else:
                    text = json.dumps(observation, indent=2, default=str)
            except Exception:
                text = str(observation)

            if len(text) > max_chars:
                head = text[: max_chars // 2]
                tail = text[-max_chars // 2 :]
                omitted = len(text) - len(head) - len(tail)
                return f"{head}\n... [TRUNCATED JSON {omitted} CHARS] ...\n{tail}"
            return text

        return str(observation)


__all__ = [
    "MiddleOutObservationCompactor",
]
