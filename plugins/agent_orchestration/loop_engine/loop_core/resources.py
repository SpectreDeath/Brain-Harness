"""Resource and decision stores for tri-state polling and deadlock resolution (Rule 12)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True)
class ResourceStore:
    """Slotted store for external resources with eventually-available polling semantics (Rule 12)."""

    available: dict[str, Any] = field(default_factory=dict)
    eventually_available: dict[str, int] = field(default_factory=dict)
    _poll_counts: dict[str, int] = field(default_factory=dict)

    def retrieve(self, key: str) -> tuple[str, Any]:
        """Poll for a resource key returning ('resolved' | 'pending' | 'missing', value)."""
        if key in self.available:
            return "resolved", self.available[key]
        if key in self.eventually_available:
            self._poll_counts[key] = self._poll_counts.get(key, 0) + 1
            if self._poll_counts[key] >= self.eventually_available[key]:
                value = f"resolved:{key}"
                self.available[key] = value
                return "resolved", value
            return "pending", None
        return "missing", None

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": dict(self.available),
            "eventually_available": dict(self.eventually_available),
            "poll_counts": dict(self._poll_counts),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ResourceStore:
        return cls(
            available=dict(d.get("available", {})),
            eventually_available=dict(d.get("eventually_available", {})),
            _poll_counts=dict(d.get("poll_counts", {})),
        )


@dataclass(slots=True)
class DecisionFixture:
    """Slotted store for decision lookups and user response fixtures (Rule 12)."""

    answers: dict[str, Any] = field(default_factory=dict)

    def ask(self, key: str) -> tuple[str, Any]:
        """Poll for a decision response returning ('resolved' | 'missing', value)."""
        if key in self.answers:
            return "resolved", self.answers[key]
        return "missing", None

    def to_dict(self) -> dict[str, Any]:
        return {"answers": dict(self.answers)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DecisionFixture:
        return cls(answers=dict(d.get("answers", {})))


__all__ = [
    "DecisionFixture",
    "ResourceStore",
]
