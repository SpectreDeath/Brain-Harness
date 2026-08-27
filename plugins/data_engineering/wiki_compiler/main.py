"""Main entrypoint and typed tool registrations for Wiki Compiler plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceKey
from plugins.data_engineering.wiki_compiler.compiler_core import (
    WikiGraphQuery,
    build_graph,
    compile_pages,
    compile_pages_incremental,
    compile_virtual_wiki as core_compile_virtual_wiki,
    compile_wiki,
    extract_all,
    extract_entity,
    generate_corpus,
    lint,
    orphan_ids,
)

logger = structlog.get_logger()


def compile_wiki_directory(
    raw_dir: str,
    output_dir: str,
    run_linter: bool = True,
) -> dict[str, Any]:
    """Compile an entire raw notes directory into a cross-referenced Markdown wiki preserving notes.

    Args:
        raw_dir: Path to directory containing raw notes (.txt or .md).
        output_dir: Destination path for compiled wiki pages.
        run_linter: Whether to run post-compilation link and orphan linter.

    Returns:
        Structured compile summary with page counts, edge metrics, written paths, and lint results.
    """
    try:
        res = compile_wiki(raw_dir=raw_dir, output_dir=output_dir, run_lint=run_linter)
        return {
            "status": "ok",
            "raw_dir": str(Path(raw_dir).resolve()),
            "output_dir": str(Path(output_dir).resolve()),
            "entities_compiled": res["entities_count"],
            "cross_references_built": res["edges_count"],
            "written_pages_count": len(res["written_paths"]),
            "orphan_pages_count": res["orphan_count"],
            "lint_report": res["lint_report"],
        }
    except Exception as e:
        logger.error("wiki_compilation_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def compile_virtual_wiki(
    notes: dict[str, str],
    preserve_sections: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compile in-memory notes into a cross-referenced Markdown wiki without disk I/O.

    Args:
        notes: Dictionary of note name -> raw text content.
        preserve_sections: Optional existing page contents to preserve ## Notes sections.

    Returns:
        Structured virtual wiki pages dictionary and mention graph stats.
    """
    if not notes:
        return {
            "status": "ok",
            "entities_count": 0,
            "edges_count": 0,
            "orphan_count": 0,
            "pages": {},
        }
    try:
        res = core_compile_virtual_wiki(notes=notes, preserve_sections=preserve_sections)
        return {
            "status": "ok",
            **res,
        }
    except Exception as e:
        logger.error("virtual_wiki_compilation_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def query_wiki_graph(
    raw_dir: str | None = None,
    notes: dict[str, str] | None = None,
    query_type: str = "neighborhood",
    root_entity: str | None = None,
    target_entity: str | None = None,
    max_hops: int = 2,
) -> dict[str, Any]:
    """Perform topological graph queries over the wiki mention network.

    Args:
        raw_dir: Optional path to directory containing raw notes.
        notes: Optional in-memory notes dictionary.
        query_type: Query type: 'neighborhood', 'backlinks', 'path', 'clusters', or 'orphans'.
        root_entity: Target entity ID for neighborhood/backlinks/path source.
        target_entity: Target entity ID for path queries.
        max_hops: Maximum search distance for neighborhood queries.

    Returns:
        Structured graph query results.
    """
    try:
        if raw_dir:
            entities = extract_all(raw_dir)
        elif notes:
            from plugins.data_engineering.wiki_compiler.compiler_core import extract_entity_from_text
            entities = {extract_entity_from_text(text, name).entity_id: extract_entity_from_text(text, name) for name, text in notes.items()}
        else:
            return {"status": "error", "error": "Must provide either raw_dir or notes"}

        graph = build_graph(entities)
        query_engine = WikiGraphQuery(graph, entities)

        if query_type == "backlinks":
            if not root_entity:
                return {"status": "error", "error": "root_entity required for backlinks query"}
            return {"status": "ok", "query_type": query_type, "backlinks": query_engine.get_backlinks(root_entity)}

        elif query_type == "neighborhood":
            if not root_entity:
                return {"status": "error", "error": "root_entity required for neighborhood query"}
            return {"status": "ok", "query_type": query_type, "neighborhood": query_engine.get_neighborhood(root_entity, max_hops=max_hops)}

        elif query_type == "path":
            if not root_entity or not target_entity:
                return {"status": "error", "error": "Both root_entity (source) and target_entity are required"}
            path = query_engine.find_path(root_entity, target_entity)
            return {"status": "ok", "query_type": query_type, "source": root_entity, "target": target_entity, "path": path}

        elif query_type == "clusters":
            return {"status": "ok", "query_type": query_type, "clusters": query_engine.get_clusters()}

        elif query_type == "orphans":
            return {"status": "ok", "query_type": query_type, "orphans": orphan_ids(graph)}

        else:
            return {"status": "error", "error": f"Unknown query_type: {query_type}"}

    except Exception as e:
        logger.error("query_wiki_graph_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def compile_wiki_incremental(
    raw_dir: str,
    output_dir: str,
) -> dict[str, Any]:
    """Compile wiki pages only writing changed markdown files to disk (dirty-tracking diff writer)."""
    try:
        entities = extract_all(raw_dir)
        graph = build_graph(entities)
        res = compile_pages_incremental(entities, graph, output_dir)
        return {
            "status": "ok",
            "raw_dir": str(Path(raw_dir).resolve()),
            "output_dir": str(Path(output_dir).resolve()),
            **res,
        }
    except Exception as e:
        logger.error("incremental_compile_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def extract_entity_metadata(file_path: str) -> dict[str, Any]:
    """Extract metadata, name, and aliases from a single note file.

    Args:
        file_path: Path to note file.

    Returns:
        Structured entity dictionary.
    """
    try:
        entity = extract_entity(file_path)
        return {"status": "ok", "entity": entity.to_dict()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def build_reference_graph(raw_dir: str) -> dict[str, Any]:
    """Extract all entities and compute the full directional cross-reference graph.

    Args:
        raw_dir: Path to directory containing raw notes.

    Returns:
        Graph dictionary mapping entity IDs to outgoing and incoming reference sets.
    """
    try:
        entities = extract_all(raw_dir)
        graph = build_graph(entities)
        serializable_graph = {
            eid: {
                "outgoing": sorted(edges["outgoing"]),
                "incoming": sorted(edges["incoming"]),
            }
            for eid, edges in graph.items()
        }
        return {
            "status": "ok",
            "entities_count": len(entities),
            "graph": serializable_graph,
            "orphans": orphan_ids(graph),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def lint_wiki(compiled_dir: str) -> dict[str, Any]:
    """Lint compiled wiki directory for broken [[wikilinks]] and unreferenced orphan pages.

    Args:
        compiled_dir: Path to directory containing compiled .md pages.

    Returns:
        Structured lint report with broken links and orphan pages.
    """
    try:
        report = lint(compiled_dir)
        return {"status": "ok", "lint_report": report.to_dict()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def generate_synthetic_notes(
    output_dir: str,
    num_files: int = 20,
    seed: int = 42,
) -> dict[str, Any]:
    """Generate a synthetic corpus of raw notes with embedded cross-mentions for benchmarking.

    Args:
        output_dir: Target directory to write synthetic .txt note files.
        num_files: Number of note files to generate (default: 20).
        seed: Random seed for deterministic generation (default: 42).

    Returns:
        List of generated file paths.
    """
    try:
        paths = generate_corpus(output_dir, num_files=num_files, seed=seed)
        return {
            "status": "ok",
            "generated_count": len(paths),
            "output_dir": str(Path(output_dir).resolve()),
            "files": paths,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


class WikiCompilerService:
    """Service provider for Wiki Compilation and Knowledge Graph Navigation."""

    def compile(self, raw_dir: str, output_dir: str, run_linter: bool = True) -> dict[str, Any]:
        return compile_wiki_directory(raw_dir=raw_dir, output_dir=output_dir, run_linter=run_linter)

    def compile_virtual(self, notes: dict[str, str], preserve_sections: dict[str, str] | None = None) -> dict[str, Any]:
        return compile_virtual_wiki(notes=notes, preserve_sections=preserve_sections)

    def compile_incremental(self, raw_dir: str, output_dir: str) -> dict[str, Any]:
        return compile_wiki_incremental(raw_dir=raw_dir, output_dir=output_dir)

    def query_graph(
        self,
        raw_dir: str | None = None,
        notes: dict[str, str] | None = None,
        query_type: str = "neighborhood",
        root_entity: str | None = None,
        target_entity: str | None = None,
        max_hops: int = 2,
    ) -> dict[str, Any]:
        return query_wiki_graph(
            raw_dir=raw_dir,
            notes=notes,
            query_type=query_type,
            root_entity=root_entity,
            target_entity=target_entity,
            max_hops=max_hops,
        )

    def extract(self, file_path: str) -> dict[str, Any]:
        return extract_entity_metadata(file_path)

    def build_graph(self, raw_dir: str) -> dict[str, Any]:
        return build_reference_graph(raw_dir)

    def lint(self, compiled_dir: str) -> dict[str, Any]:
        return lint_wiki(compiled_dir)

    def generate_corpus(self, output_dir: str, num_files: int = 20, seed: int = 42) -> dict[str, Any]:
        return generate_synthetic_notes(output_dir=output_dir, num_files=num_files, seed=seed)


WIKI_COMPILER_SERVICE_KEY = ServiceKey[WikiCompilerService]("domain.wiki_compiler")
