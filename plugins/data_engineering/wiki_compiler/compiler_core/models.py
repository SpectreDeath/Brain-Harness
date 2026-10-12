"""Slotted models, regex patterns, and string slug normalization for wiki compiler."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
import re
from typing import Any

HEADER_HASH_RE = re.compile(r"^#\s*(.+)$")
CREATED_RE = re.compile(r"^created:\s*(.+)$", re.IGNORECASE)
ALIASES_RE = re.compile(r"^aliases:\s*(.+)$", re.IGNORECASE)
_WORD_RE = re.compile(r"[A-Za-z0-9']+")
LINK_RE = re.compile(r"\[\[(.+?)\]\]")
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def _slugify(name: str) -> str:
    """Normalize string to lowercase underscore-separated slug."""
    return name.lower().replace(" ", "_").replace("-", "_")


def _derive_name_from_filename(path: str) -> str:
    """Derive capitalized title from file basename."""
    base = os.path.splitext(os.path.basename(path))[0]
    return base.replace("_", " ").title()


@dataclass(slots=True)
class Entity:
    """Structured wiki entity note with aliases, creation date, and body."""

    entity_id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    created: str = ""
    body: str = ""
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize entity structure to dictionary."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "aliases": list(self.aliases),
            "created": self.created,
            "body": self.body,
            "source_path": self.source_path,
        }


@dataclass(slots=True)
class LintReport:
    """Diagnostic report capturing broken links and orphaned pages in compiled wiki."""

    total_pages: int = 0
    broken_links: list[tuple[str, str]] = field(default_factory=list)
    orphan_pages: list[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        """Check if compiled wiki is free of broken links and orphans."""
        return not self.broken_links and not self.orphan_pages

    def to_dict(self) -> dict[str, Any]:
        """Serialize lint diagnostics to dictionary."""
        return {
            "total_pages": self.total_pages,
            "broken_links": [{"source": src, "target": tgt} for src, tgt in self.broken_links],
            "orphan_pages": list(self.orphan_pages),
            "is_clean": self.is_clean(),
        }
