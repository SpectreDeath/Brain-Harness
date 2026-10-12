"""Constants and token estimation heuristics for context compilation."""

from __future__ import annotations

import builtins

_BUILTIN_NAMES = set(dir(builtins))
KNOWN_EVENT_DECORATORS = {"receiver", "signal", "event", "on", "hook", "register", "route"}
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count with 4 chars/token heuristic."""
    return max(1, len(text) // CHARS_PER_TOKEN)
