"""Note extraction and entity parsing from text and raw markdown files."""

from __future__ import annotations

import os
from pathlib import Path

from plugins.data_engineering.wiki_compiler.compiler_core.models import (
    ALIASES_RE,
    CREATED_RE,
    HEADER_HASH_RE,
    Entity,
    _slugify,
)


def extract_entity_from_text(text: str, identifier: str = "virtual_note") -> Entity:
    """Extract entity structure from raw string text."""
    lines = text.splitlines()
    name = None
    aliases = []
    created = ""
    body_lines = []

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            body_lines.append(raw_line)
            continue

        if name is None:
            m = HEADER_HASH_RE.match(line)
            if m:
                name = m.group(1).strip()
                continue
            if line.isupper() and idx == 0:
                name = line.title()
                continue

        m = CREATED_RE.match(line)
        if m:
            created = m.group(1).strip()
            continue

        m = ALIASES_RE.match(line)
        if m:
            aliases = [a.strip() for a in m.group(1).split(",") if a.strip()]
            continue

        body_lines.append(raw_line)

    if name is None:
        name = identifier.replace("_", " ").title()

    entity_id = _slugify(name)
    body = "\n".join(body_lines).strip()

    return Entity(
        entity_id=entity_id,
        name=name,
        aliases=aliases,
        created=created,
        body=body,
        source_path=identifier,
    )


def extract_entity(path: str) -> Entity:
    """Extract entity from a single file on disk."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    ent = extract_entity_from_text(text, identifier=os.path.splitext(os.path.basename(path))[0])
    ent.source_path = str(Path(path).resolve())
    return ent


def extract_all(raw_dir: str) -> dict[str, Entity]:
    """Scan directory and parse all notes (.txt, .md) into entities."""
    entities = {}
    if not os.path.exists(raw_dir):
        return entities
    for fname in sorted(os.listdir(raw_dir)):
        if not (fname.endswith(".txt") or fname.endswith(".md")):
            continue
        path = os.path.join(raw_dir, fname)
        entity = extract_entity(path)
        entities[entity.entity_id] = entity
    return entities
