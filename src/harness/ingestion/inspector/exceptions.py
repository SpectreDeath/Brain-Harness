"""Exceptions for repository inspection subsystem."""

from __future__ import annotations


class InspectionError(Exception):
    """Raised when repository inspection fails."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Inspection failed for {path}: {reason}")
