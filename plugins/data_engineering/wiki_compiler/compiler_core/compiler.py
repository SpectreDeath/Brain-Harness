"""Wiki compilation pipeline, dirty-diff writer, linter, and synthetic corpus generator."""

from __future__ import annotations

import os
from pathlib import Path
import random
from typing import Any

from plugins.data_engineering.wiki_compiler.compiler_core.extractor import (
    extract_all,
    extract_entity_from_text,
)
from plugins.data_engineering.wiki_compiler.compiler_core.graph import build_graph, orphan_ids
from plugins.data_engineering.wiki_compiler.compiler_core.models import (
    LINK_RE,
    SECTION_RE,
    Entity,
    LintReport,
    _slugify,
)
from plugins.data_engineering.wiki_compiler.compiler_core.renderer import render_page


def compile_virtual_wiki(
    notes: dict[str, str],
    preserve_sections: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compile in-memory notes into a cross-referenced Markdown wiki without disk I/O."""
    preserve = preserve_sections or {}
    entities: dict[str, Entity] = {}
    for name, content in notes.items():
        ent = extract_entity_from_text(content, identifier=name)
        entities[ent.entity_id] = ent

    graph = build_graph(entities)
    pages: dict[str, str] = {}
    for eid, ent in entities.items():
        prev_content = preserve.get(f"{eid}.md") or preserve.get(eid)
        pages[f"{eid}.md"] = render_page(ent, graph[eid], entities, existing_content=prev_content)

    return {
        "entities_count": len(entities),
        "edges_count": sum(len(v["outgoing"]) for v in graph.values()),
        "orphan_count": len(orphan_ids(graph)),
        "orphans": orphan_ids(graph),
        "pages": pages,
    }


def compile_pages(
    entities: dict[str, Entity],
    graph: dict[str, dict[str, set[str]]],
    output_dir: str,
) -> list[str]:
    """Compile entities into disk Markdown files."""
    os.makedirs(output_dir, exist_ok=True)
    written = []
    for eid, entity in entities.items():
        out_path = os.path.join(output_dir, f"{eid}.md")
        content = render_page(entity, graph[eid], entities, existing_path=out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(str(Path(out_path).resolve()))
    return written


def compile_pages_incremental(
    entities: dict[str, Entity],
    graph: dict[str, dict[str, set[str]]],
    output_dir: str,
) -> dict[str, Any]:
    """Compile wiki pages only writing changed content (dirty-tracking diff writer)."""
    os.makedirs(output_dir, exist_ok=True)
    written = []
    skipped = []

    for eid, entity in entities.items():
        out_path = os.path.join(output_dir, f"{eid}.md")
        content = render_page(entity, graph[eid], entities, existing_path=out_path)

        # Check existing
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                existing = f.read()
            if existing == content:
                skipped.append(str(Path(out_path).resolve()))
                continue

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(str(Path(out_path).resolve()))

    return {
        "written_count": len(written),
        "skipped_count": len(skipped),
        "written_paths": written,
        "skipped_paths": skipped,
    }


def _extract_section(text: str, heading: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        if m.group(1).strip() == heading:
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end]
    return ""


def lint(output_dir: str) -> LintReport:
    """Audit compiled wiki directory for broken cross-references and orphaned pages."""
    report = LintReport()
    if not os.path.exists(output_dir):
        return report

    files = sorted(f for f in os.listdir(output_dir) if f.endswith(".md"))
    report.total_pages = len(files)
    known_slugs = {os.path.splitext(f)[0] for f in files}
    incoming_count = {slug: 0 for slug in known_slugs}

    for fname in files:
        path = os.path.join(output_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        for match in LINK_RE.finditer(text):
            target_name = match.group(1)
            target_slug = _slugify(target_name)
            if target_slug not in known_slugs:
                report.broken_links.append((fname, target_name))

        related_text = _extract_section(text, "Related")
        for match in LINK_RE.finditer(related_text):
            target_slug = _slugify(match.group(1))
            if target_slug in incoming_count:
                incoming_count[target_slug] += 1

    for slug, count in incoming_count.items():
        if count == 0:
            report.orphan_pages.append(f"{slug}.md")

    report.orphan_pages.sort()
    return report


def generate_corpus(output_dir: str, num_files: int = 50, seed: int = 42) -> list[str]:
    """Generate synthetic note dataset for benchmark evaluations."""
    os.makedirs(output_dir, exist_ok=True)
    rng = random.Random(seed)

    entity_names = [
        f"Entity Alpha {i}" if i % 2 == 0 else f"Concept Beta {i}"
        for i in range(num_files)
    ]

    written_paths = []
    for i, name in enumerate(entity_names):
        slug = _slugify(name)
        file_path = os.path.join(output_dir, f"{slug}.txt")

        targets = rng.sample(entity_names, min(3, len(entity_names)))
        mentions = " ".join([f"This topic strongly relates to {t} in practice." for t in targets if t != name])

        content = f"""# {name}
created: 2026-08-{10 + (i % 15):02d}
aliases: {name.lower()}, {name.replace(' ', '-')}

{name} is an important architectural component.
{mentions}
Further research is ongoing for {name}.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        written_paths.append(str(Path(file_path).resolve()))

    return written_paths


def compile_wiki(raw_dir: str, output_dir: str, run_lint: bool = True) -> dict[str, Any]:
    """Compile raw notes into structured wiki and return execution summary."""
    entities = extract_all(raw_dir)
    graph = build_graph(entities)
    written = compile_pages(entities, graph, output_dir)
    report = lint(output_dir) if run_lint else None

    return {
        "entities_count": len(entities),
        "edges_count": sum(len(v["outgoing"]) for v in graph.values()),
        "written_paths": written,
        "lint_report": report.to_dict() if report else None,
        "orphan_count": len(orphan_ids(graph)),
    }
