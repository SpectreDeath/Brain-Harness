"""Active prefix rule repository and catastrophic danger pattern matcher."""

from __future__ import annotations

import re
import sys
from typing import Any

from plugins.security_and_forensics.codex_execpolicy.engine.models import (
    _DEFAULT_ALLOW_PREFIXES,
    _DEFAULT_DENY_PATTERNS,
    PrefixRule,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_ACTIVE_RULES: list[PrefixRule] = list(_DEFAULT_ALLOW_PREFIXES)


def get_active_rules() -> list[PrefixRule]:
    """Return a copy of the active prefix rules."""
    return list(_ACTIVE_RULES)


def reset_active_rules() -> None:
    """Reset active prefix rules to default configuration."""
    global _ACTIVE_RULES
    _ACTIVE_RULES = list(_DEFAULT_ALLOW_PREFIXES)


def _check_danger_patterns(command_str: str) -> tuple[str, str, str] | None:
    """Check raw text and tokens for catastrophic security patterns."""
    for pattern, desc, action in _DEFAULT_DENY_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            return (pattern, desc, action)
    return None


def amend_prefix_rule(
    prefix_pattern: str,
    action: str,
    comment: str = "",
) -> dict[str, Any]:
    """Dynamically add or update an allowed/prompt/deny prefix rule in the active execution policy."""
    global _ACTIVE_RULES

    clean_pat = prefix_pattern.strip()
    clean_action = action.strip().lower()

    if clean_action not in ("allow", "prompt", "deny"):
        return {
            "status": "error",
            "error": f"Invalid action '{action}'. Must be 'allow', 'prompt', or 'deny'.",
        }

    tokens = clean_pat.split()
    if not tokens:
        return {"status": "error", "error": "Prefix pattern cannot be empty."}

    updated = False
    for r in _ACTIVE_RULES:
        if r.pattern == tokens:
            r.action = clean_action
            if comment:
                r.comment = comment
            updated = True
            break

    if not updated:
        _ACTIVE_RULES.insert(0, PrefixRule(tokens, clean_action, comment or "User amended rule"))

    return {
        "status": "ok",
        "amended_pattern": clean_pat,
        "action": clean_action,
        "comment": comment,
        "is_update": updated,
        "total_active_rules": len(_ACTIVE_RULES),
    }


__all__ = [
    "_check_danger_patterns",
    "amend_prefix_rule",
    "get_active_rules",
    "reset_active_rules",
]
