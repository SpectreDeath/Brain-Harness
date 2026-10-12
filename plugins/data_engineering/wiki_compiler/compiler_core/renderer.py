"""Markdown wiki page renderer with human notes preservation."""

from __future__ import annotations

import os

from plugins.data_engineering.wiki_compiler.compiler_core.models import SECTION_RE, Entity


def _parse_existing_sections(text: str) -> dict[str, str]:
    """Parse existing markdown page into a dictionary of section heading -> content."""
    sections = {}
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[heading] = text[start:end].strip("\n")
    return sections


def render_page(
    entity: Entity,
    graph_edges: dict[str, set[str]],
    entities: dict[str, Entity],
    existing_content: str | None = None,
    existing_path: str | None = None,
) -> str:
    """Render a compiled Markdown wiki page preserving human-authored notes."""
    preserved_notes = ""
    if existing_content:
        old_sections = _parse_existing_sections(existing_content)
        preserved_notes = old_sections.get("Notes", "").strip()
    elif existing_path and os.path.exists(existing_path):
        try:
            with open(existing_path, "r", encoding="utf-8") as f:
                old_text = f.read()
            old_sections = _parse_existing_sections(old_text)
            preserved_notes = old_sections.get("Notes", "").strip()
        except Exception:
            preserved_notes = ""

    lines = [f"# {entity.name}", ""]

    # 1. Compiler-owned: Metadata
    lines.append("## Metadata")
    lines.append(f"- created: {entity.created or 'unknown'}")
    lines.append(f"- aliases: {', '.join(entity.aliases) if entity.aliases else 'none'}")
    lines.append(f"- source: {entity.source_path}")
    lines.append("")

    # 2. Compiler-owned: Related
    lines.append("## Related")
    outgoing = sorted(graph_edges.get("outgoing", set()))
    if outgoing:
        for target_id in outgoing:
            target_name = entities[target_id].name if target_id in entities else target_id
            lines.append(f"- [[{target_name}]]")
    else:
        lines.append("- (no outgoing references found)")
    lines.append("")

    # 3. Compiler-owned: Referenced By
    lines.append("## Referenced By")
    incoming = sorted(graph_edges.get("incoming", set()))
    if incoming:
        for source_id in incoming:
            source_name = entities[source_id].name if source_id in entities else source_id
            lines.append(f"- [[{source_name}]]")
    else:
        lines.append("- (orphan: no other page links here)")
    lines.append("")

    # 4. Compiler-owned: Body
    lines.append("## Body")
    lines.append(entity.body)
    lines.append("")

    # 5. Human-owned: Notes (preserved)
    lines.append("## Notes")
    lines.append(preserved_notes if preserved_notes else "_(add your own notes here -- preserved on recompile)_")
    lines.append("")

    return "\n".join(lines)
