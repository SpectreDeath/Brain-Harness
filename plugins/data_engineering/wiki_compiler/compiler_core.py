"""Core Wiki Compiler: Extraction, Phrase Index Mention Detection, Virtual Compilation, and Graph Analytics."""

from __future__ import annotations

import collections
import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HEADER_HASH_RE = re.compile(r"^#\s*(.+)$")
CREATED_RE = re.compile(r"^created:\s*(.+)$", re.IGNORECASE)
ALIASES_RE = re.compile(r"^aliases:\s*(.+)$", re.IGNORECASE)
_WORD_RE = re.compile(r"[A-Za-z0-9']+")
LINK_RE = re.compile(r"\[\[(.+?)\]\]")
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


@dataclass
class Entity:
    entity_id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    created: str = ""
    body: str = ""
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "aliases": list(self.aliases),
            "created": self.created,
            "body": self.body,
            "source_path": self.source_path,
        }


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def _derive_name_from_filename(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    return base.replace("_", " ").title()


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
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    ent = extract_entity_from_text(text, identifier=os.path.splitext(os.path.basename(path))[0])
    ent.source_path = str(Path(path).resolve())
    return ent


def extract_all(raw_dir: str) -> dict[str, Entity]:
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


def _build_phrase_index(entities: dict[str, Entity]) -> dict[str, list[tuple[tuple[str, ...], str]]]:
    index: dict[str, list[tuple[tuple[str, ...], str]]] = {}
    for eid, ent in entities.items():
        words = tuple(w.lower() for w in _WORD_RE.findall(ent.name))
        if words:
            index.setdefault(words[0], []).append((words, eid))
        for alias in ent.aliases:
            awords = tuple(w.lower() for w in _WORD_RE.findall(alias))
            if awords:
                index.setdefault(awords[0], []).append((awords, eid))

    for first_word in index:
        index[first_word].sort(key=lambda pair: -len(pair[0]))

    return index


def build_graph(entities: dict[str, Entity]) -> dict[str, dict[str, set[str]]]:
    graph: dict[str, dict[str, set[str]]] = {eid: {"outgoing": set(), "incoming": set()} for eid in entities}
    if not entities:
        return graph

    phrase_index = _build_phrase_index(entities)

    for eid, ent in entities.items():
        tokens = [w.lower() for w in _WORD_RE.findall(ent.body)]
        seen_targets = set()
        n = len(tokens)
        i = 0
        while i < n:
            candidates = phrase_index.get(tokens[i])
            if candidates:
                for words, target_id in candidates:
                    end = i + len(words)
                    if end <= n and tuple(tokens[i:end]) == words:
                        if target_id != eid:
                            seen_targets.add(target_id)
                        break
            i += 1

        for target_id in seen_targets:
            if target_id in graph:
                graph[eid]["outgoing"].add(target_id)
                graph[target_id]["incoming"].add(eid)

    return graph


def orphan_ids(graph: dict[str, dict[str, set[str]]]) -> list[str]:
    return sorted(eid for eid, edges in graph.items() if not edges["incoming"])


class WikiGraphQuery:
    """Graph analytics engine for topological querying over the wiki mention graph."""

    def __init__(self, graph: dict[str, dict[str, set[str]]], entities: dict[str, Entity]):
        self.graph = graph
        self.entities = entities

    def get_backlinks(self, entity_id: str) -> list[dict[str, str]]:
        if entity_id not in self.graph:
            return []
        return [
            {"entity_id": inc_id, "name": self.entities[inc_id].name if inc_id in self.entities else inc_id}
            for inc_id in sorted(self.graph[entity_id]["incoming"])
        ]

    def get_neighborhood(self, entity_id: str, max_hops: int = 2) -> dict[str, Any]:
        if entity_id not in self.graph:
            return {"root": entity_id, "nodes": [], "edges": []}

        visited = {entity_id: 0}
        queue = collections.deque([(entity_id, 0)])
        edges_out = []

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_hops:
                continue

            # explore outgoing and incoming
            neighbors = sorted(self.graph[curr]["outgoing"] | self.graph[curr]["incoming"])
            for nbr in neighbors:
                if nbr not in visited:
                    visited[nbr] = depth + 1
                    queue.append((nbr, depth + 1))
                if (curr, nbr) not in edges_out:
                    edges_out.append((curr, nbr))

        nodes_out = [
            {"entity_id": node_id, "name": self.entities[node_id].name if node_id in self.entities else node_id, "hop": hop}
            for node_id, hop in sorted(visited.items(), key=lambda kv: kv[1])
        ]

        return {
            "root": entity_id,
            "max_hops": max_hops,
            "node_count": len(nodes_out),
            "nodes": nodes_out,
            "edges": [{"source": src, "target": tgt} for src, tgt in edges_out],
        }

    def find_path(self, source_id: str, target_id: str) -> list[str] | None:
        """Find the shortest directed reference path from source to target entity."""
        if source_id not in self.graph or target_id not in self.graph:
            return None
        if source_id == target_id:
            return [source_id]

        queue = collections.deque([[source_id]])
        visited = {source_id}

        while queue:
            path = queue.popleft()
            curr = path[-1]
            for nbr in sorted(self.graph[curr]["outgoing"]):
                if nbr == target_id:
                    return [*path, nbr]
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append([*path, nbr])

        return None

    def get_clusters(self) -> list[list[str]]:
        """Compute weakly connected components of the wiki graph."""
        visited = set()
        clusters = []

        for eid in self.graph:
            if eid in visited:
                continue
            component = []
            queue = collections.deque([eid])
            visited.add(eid)

            while queue:
                curr = queue.popleft()
                component.append(curr)
                all_neighbors = self.graph[curr]["outgoing"] | self.graph[curr]["incoming"]
                for nbr in all_neighbors:
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)

            clusters.append(sorted(component))

        clusters.sort(key=lambda c: -len(c))
        return clusters


def _parse_existing_sections(text: str) -> dict[str, str]:
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


def compile_virtual_wiki(notes: dict[str, str], preserve_sections: dict[str, str] | None = None) -> dict[str, Any]:
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


def compile_pages(entities: dict[str, Entity], graph: dict[str, dict[str, set[str]]], output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    written = []
    for eid, entity in entities.items():
        out_path = os.path.join(output_dir, f"{eid}.md")
        content = render_page(entity, graph[eid], entities, existing_path=out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(str(Path(out_path).resolve()))
    return written


def compile_pages_incremental(entities: dict[str, Entity], graph: dict[str, dict[str, set[str]]], output_dir: str) -> dict[str, Any]:
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


@dataclass
class LintReport:
    total_pages: int = 0
    broken_links: list[tuple[str, str]] = field(default_factory=list)
    orphan_pages: list[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        return not self.broken_links and not self.orphan_pages

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_pages": self.total_pages,
            "broken_links": [{"source": src, "target": tgt} for src, tgt in self.broken_links],
            "orphan_pages": list(self.orphan_pages),
            "is_clean": self.is_clean(),
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
