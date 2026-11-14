"""Headless CLI runner for the ontology-spider skill (Rule 50 & Rule 57)."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPT_PATH = Path(__file__).resolve()
_REPO_ROOT = _SCRIPT_PATH.parents[4]
_SRC_ROOT = _REPO_ROOT / "src"
for _candidate in (str(_SRC_ROOT), str(_REPO_ROOT)):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from harness.services.ontology_spider import OntologySpiderKernelService  # noqa: E402


def _parse_competency_args(raw_items: list[str] | None) -> list[str]:
    questions: list[str] = []
    for entry in raw_items or []:
        for part in entry.split(","):
            cleaned = part.strip()
            if cleaned:
                questions.append(cleaned)
    return questions


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI parser for standalone ontology-spider skill execution."""
    parser = argparse.ArgumentParser(description="Headless Ontology-Spider Knowledge Vault runner")
    parser.add_argument("--vault", default=".harness/knowledge", help="Vault directory or JSON path")
    parser.add_argument("--as-of", default=None, help="Optional ISO timestamp for bi-temporal edge slicing")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum edge confidence threshold")
    parser.add_argument("--query", default=None, help="Controlled .dialog query string")
    parser.add_argument("--rank-by-distance", action="store_true", help="Attach hop distance scores and sort")
    parser.add_argument("--validate", action="store_true", help="Run structural integrity checks")
    parser.add_argument("--export", choices=["json", "dialog", "dot", "html"], default=None, help="Export format")
    parser.add_argument("--competency", action="append", help="Competency question(s) (repeatable or comma-separated)")
    parser.add_argument("--rank-entropy", action="store_true", help="Rank attributes by Shannon/Laya information gain")
    parser.add_argument("--audit-epistemics", action="store_true", help="Run federated structural and isnad audit")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute requested ontology-spider operation and print JSON payload."""
    args = build_parser().parse_args(argv)
    service = OntologySpiderKernelService()
    vault = Path(args.vault)
    payload: dict[str, Any] = {}

    if args.query:
        payload["query"] = service.query(
            vault,
            args.query,
            rank_by_distance=args.rank_by_distance,
            as_of=args.as_of,
            min_confidence=args.min_confidence,
        )
    if args.validate:
        payload["violations"] = service.validate(vault, as_of=args.as_of, min_confidence=args.min_confidence)
    if args.export:
        payload["export"] = {
            "format": args.export,
            "content": service.export(vault, format=args.export, as_of=args.as_of, min_confidence=args.min_confidence),
        }
    competency_questions = _parse_competency_args(args.competency)
    if competency_questions:
        payload["competency"] = asdict(service.evaluate_competency(vault, competency_questions, as_of=args.as_of))
    if args.rank_entropy:
        payload["entropy_ranks"] = [asdict(item) for item in service.rank_attributes(vault, as_of=args.as_of)]
    if args.audit_epistemics or not payload:
        payload["audit"] = asdict(
            service.audit_vault_epistemics(vault, as_of=args.as_of, min_confidence=args.min_confidence)
        )

    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
