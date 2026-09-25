# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
search_index.py — CLI Search & Query Frontend for Discovery Indexes.

Thin CLI adapter delegating to the authoritative DiscoveryCatalogEngine.
Supports faceted filtering, weighted relevance ranking, and multi-format serialization.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Rule 23: UTF-8 standard streams entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Local import of discovery_engine
try:
    from discovery_engine import DiscoveryCatalogEngine, DiscoverySource, SearchResult
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from discovery_engine import DiscoveryCatalogEngine, DiscoverySource, SearchResult

# Backward-compatibility alias
_DEFAULT_ENGINE = DiscoveryCatalogEngine()
CURATED_SOURCES = _DEFAULT_ENGINE.list_all_sources()


def query_index(
    category: str | None = None,
    keyword: str | None = None,
    tag: str | None = None,
    provenance_tier: str | None = None,
    export_format: str | None = None,
    limit: int = 20,
) -> list[DiscoverySource]:
    """Backward-compatible query function delegating to DiscoveryCatalogEngine."""
    results = _DEFAULT_ENGINE.search(
        query=keyword,
        category=category,
        tag=tag,
        provenance_tier=provenance_tier,
        export_format=export_format,
        limit=limit,
    )
    return [r.source for r in results]


def format_table(results: list[DiscoverySource] | list[SearchResult]) -> str:
    return DiscoveryCatalogEngine.format_table(results)


def format_markdown(results: list[DiscoverySource] | list[SearchResult]) -> str:
    return DiscoveryCatalogEngine.format_markdown(results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search and filter curated discovery indexes, transcript corpora, and public records."
    )
    parser.add_argument(
        "--category",
        choices=["transcripts", "public_records", "research_corpora", "github_indexes"],
        help="Filter by specific functional category.",
    )
    parser.add_argument("--keyword", "-k", help="Free-text keyword match with weighted multi-field scoring.")
    parser.add_argument("--tag", "-t", help="Match a specific tag (e.g. 'congress', 'sec', 'nlp').")
    parser.add_argument("--provenance", help="Filter by provenance tier (e.g. 'Primary Official', 'Academic Archival').")
    parser.add_argument("--export-format", help="Filter by export capability (e.g. 'JSON', 'Parquet', 'XML').")
    parser.add_argument("--limit", "-n", type=int, default=20, help="Maximum number of results to return.")
    parser.add_argument(
        "--format",
        choices=["json", "table", "markdown"],
        default="json",
        help="Output serialization format (default: json).",
    )

    args = parser.parse_args()

    engine = DiscoveryCatalogEngine()
    results = engine.search(
        query=args.keyword,
        category=args.category,
        tag=args.tag,
        provenance_tier=args.provenance,
        export_format=args.export_format,
        limit=args.limit,
    )

    if args.format == "json":
        print(engine.format_json(results))
    elif args.format == "table":
        print(engine.format_table(results))
    elif args.format == "markdown":
        print(engine.format_markdown(results))

    return 0


if __name__ == "__main__":
    sys.exit(main())
