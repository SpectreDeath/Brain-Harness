# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""Standalone OKF Memory Governor Engine and CLI Dispatcher.

Provides slotted and frozen high-performance data structures for BM25 ranking,
pre-edit governance scoping, and non-interactive bundle manipulation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Any

# Enforce UTF-8 standard streams on Windows environments (Rule 23)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ensure workspace root and plugins are in sys.path
_current = Path(__file__).resolve()
for parent in _current.parents:
    if (parent / "pyproject.toml").exists() or (parent / "plugins").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        if str(parent / "src") not in sys.path:
            sys.path.insert(0, str(parent / "src"))
        break

from plugins.memory_and_epistemics.okf_memory.main import OKFMemoryEngine


# -----------------------------------------------------------------------------
# Slotted and Frozen Dataclasses (Rule 12)
# -----------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class BM25Token:
    """Slotted and frozen lexical term container for high-volume indexing."""

    term: str
    field: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.term:
            raise ValueError("BM25Token term cannot be empty")
        if self.weight <= 0:
            raise ValueError("BM25Token weight must be positive")


@dataclass(slots=True, frozen=True)
class SearchCandidate:
    """Slotted and frozen search result candidate."""

    concept_id: str
    title: str
    score: float
    description: str = ""
    governance: tuple[str, ...] = field(default_factory=tuple)
    matched_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.concept_id:
            raise ValueError("SearchCandidate concept_id cannot be empty")


@dataclass(slots=True, frozen=True)
class OKFConceptNode:
    """Slotted and frozen immutable concept node representation."""

    concept_id: str
    title: str
    concept_type: str
    description: str
    body: str = ""
    governance: tuple[str, ...] = field(default_factory=tuple)
    code_refs: tuple[str, ...] = field(default_factory=tuple)
    generated_by: str = "agent:brain-harness"
    verified_by: str = ""

    def __post_init__(self) -> None:
        if not self.concept_id:
            raise ValueError("OKFConceptNode concept_id cannot be empty")
        if not self.title:
            raise ValueError("OKFConceptNode title cannot be empty")
        if not self.description:
            raise ValueError("OKFConceptNode description cannot be empty")


# -----------------------------------------------------------------------------
# CLI Entrypoint Dispatcher (Rule 42 — Non-interactive, zero input() calls)
# -----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OKF Memory Governor CLI Dispatcher")
    parser.add_argument("--bundle-dir", default="knowledge", help="Root directory of knowledge bundle")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scope
    scope_p = subparsers.add_parser("scope", help="Pre-edit governance scoping for target path")
    scope_p.add_argument("--target", required=True, help="Target file or directory path to check")

    # Search
    search_p = subparsers.add_parser("search", help="BM25 lexical search")
    search_p.add_argument("query", help="Search query string")
    search_p.add_argument("--limit", type=int, default=3, help="Maximum results (default: 3)")

    # Show
    show_p = subparsers.add_parser("show", help="Show full concept record")
    show_p.add_argument("concept_id", help="Concept identifier")

    # Create
    create_p = subparsers.add_parser("create", help="Create a new concept")
    create_p.add_argument("--id", required=True, help="Unique concept ID")
    create_p.add_argument("--title", required=True, help="Concept title")
    create_p.add_argument("--type", default="concept", help="Concept type")
    create_p.add_argument("--description", required=True, help="1-2 sentence description")
    create_p.add_argument("--body", default="", help="Markdown body")
    create_p.add_argument("--governance", default="", help="Comma-separated governance rules")
    create_p.add_argument("--code-refs", default="", help="Comma-separated code reference paths")

    # Update
    update_p = subparsers.add_parser("update", help="Update an existing concept")
    update_p.add_argument("--id", required=True, help="Concept ID")
    update_p.add_argument("--title", help="Updated title")
    update_p.add_argument("--description", help="Updated description")
    update_p.add_argument("--body", help="Updated body")
    update_p.add_argument("--governance", help="Comma-separated governance rules")
    update_p.add_argument("--code-refs", help="Comma-separated code references")

    # Relate
    relate_p = subparsers.add_parser("relate", help="Link two concepts bidirectionally")
    relate_p.add_argument("--source", required=True, help="Source concept ID")
    relate_p.add_argument("--target", required=True, help="Target concept ID")
    relate_p.add_argument("--description", default="", help="Relationship description")

    # Validate
    val_p = subparsers.add_parser("validate", help="Validate bundle schema and trust ordering")
    val_p.add_argument("--strict", action="store_true", help="Fail on warnings")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = OKFMemoryEngine(default_root=args.bundle_dir)

    if args.command == "scope":
        res = engine.search(for_path=args.target, bundle_dir=args.bundle_dir)
        print(json.dumps(res, indent=2))

    elif args.command == "search":
        res = engine.search(query=args.query, limit=args.limit, bundle_dir=args.bundle_dir)
        print(json.dumps(res, indent=2))

    elif args.command == "show":
        rec = engine.show(concept_id=args.concept_id, bundle_dir=args.bundle_dir)
        if rec is None:
            print(json.dumps({"status": "error", "error": f"Concept '{args.concept_id}' not found"}))
            sys.exit(1)
        print(json.dumps({"status": "ok", "concept": rec}, indent=2))

    elif args.command == "create":
        gov_list = [g.strip() for g in args.governance.split(",") if g.strip()] if args.governance else []
        refs_list = [c.strip() for c in args.code_refs.split(",") if c.strip()] if args.code_refs else []
        try:
            created = engine.create(
                concept_id=args.id,
                title=args.title,
                concept_type=args.type,
                description=args.description,
                body=args.body,
                governance=gov_list,
                code_refs=refs_list,
                bundle_dir=args.bundle_dir,
            )
            print(json.dumps({"status": "ok", "concept": created}, indent=2))
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}))
            sys.exit(1)

    elif args.command == "update":
        gov_list = [g.strip() for g in args.governance.split(",") if g.strip()] if args.governance else None
        refs_list = [c.strip() for c in args.code_refs.split(",") if c.strip()] if args.code_refs else None
        try:
            updated = engine.update(
                concept_id=args.id,
                title=args.title,
                description=args.description,
                body=args.body,
                governance=gov_list,
                code_refs=refs_list,
                bundle_dir=args.bundle_dir,
            )
            print(json.dumps({"status": "ok", "concept": updated}, indent=2))
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}))
            sys.exit(1)

    elif args.command == "relate":
        try:
            rel = engine.relate(
                source_id=args.source,
                target_id=args.target,
                description=args.description,
                bundle_dir=args.bundle_dir,
            )
            print(json.dumps(rel, indent=2))
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}))
            sys.exit(1)

    elif args.command == "validate":
        rep = engine.validate(strict=args.strict, bundle_dir=args.bundle_dir)
        print(json.dumps(rep, indent=2))
        if not rep["valid"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
