# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
catalog_registry.py — Local Source Registry & Provenance Manager CLI.

Thin CLI adapter delegating to the authoritative DiscoveryCatalogEngine.
Maintains local source provenance, update cadences, and export capabilities.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 standard streams entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Local import of discovery_engine
try:
    from discovery_engine import CURATED_SOURCES_DATA, DiscoveryCatalogEngine, DiscoverySource
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from discovery_engine import CURATED_SOURCES_DATA, DiscoveryCatalogEngine, DiscoverySource

# Backward-compatibility alias
RegistryEntry = DiscoverySource
RegistryStore = DiscoveryCatalogEngine


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local Source Registry & Provenance Manager for Discovery Indexes."
    )
    parser.add_argument("--registry-path", type=Path, default=None, help="Custom path to registry.json file.")
    subparsers = parser.add_subparsers(dest="command")

    # Command: list
    list_p = subparsers.add_parser("list", help="List registered discovery sources.")
    list_p.add_argument("--category", "-c", help="Filter by category.")
    list_p.add_argument("--format", choices=["json", "table", "markdown"], default="table")

    # Command: add
    add_p = subparsers.add_parser("add", help="Register a new discovery source.")
    add_p.add_argument("--name", required=True, help="Full source name.")
    add_p.add_argument("--category", required=True, choices=["transcripts", "public_records", "research_corpora", "github_indexes", "custom"])
    add_p.add_argument("--url", required=True, help="Primary endpoint or landing URL.")
    add_p.add_argument("--access-method", default="Web Search / API", help="Access paradigm (API, Bulk, Web).")
    add_p.add_argument("--provenance", default="Primary Official", help="Provenance tier.")
    add_p.add_argument("--cadence", default="Daily", help="Update cadence.")
    add_p.add_argument("--formats", nargs="*", default=["JSON"], help="Supported export formats.")
    add_p.add_argument("--notes", default="", help="Methodology or credential notes.")

    # Command: stats
    subparsers.add_parser("stats", help="Show registry distribution statistics.")

    # Command: init-default
    subparsers.add_parser("init-default", help="Initialize registry with default discovery indexes.")

    args = parser.parse_args()

    engine = DiscoveryCatalogEngine(registry_path=args.registry_path)

    if args.command == "add":
        src = engine.register_source(
            {
                "name": args.name,
                "category": args.category,
                "url": args.url,
                "access_method": args.access_method,
                "provenance_tier": args.provenance,
                "update_cadence": args.cadence,
                "export_formats": args.formats,
                "notes": args.notes,
            },
            persist=True,
        )
        print(f"Successfully registered source: {src.name} [{src.id}]")

    elif args.command == "init-default":
        count = 0
        for item in CURATED_SOURCES_DATA:
            engine.register_source(item, persist=False)
            count += 1
        engine.save_registry()
        print(f"Initialized registry with {count} discovery sources at: {engine.registry_path}")

    elif args.command == "stats":
        print(json.dumps(engine.get_stats(), indent=2))

    elif args.command == "list" or args.command is None:
        category = getattr(args, "category", None)
        fmt = getattr(args, "format", "table")
        results = engine.search(category=category, limit=100)

        if fmt == "json":
            print(engine.format_json(results))
        elif fmt == "markdown":
            print(engine.format_markdown(results))
        else:
            print(engine.format_table(results))

    return 0


if __name__ == "__main__":
    sys.exit(main())
