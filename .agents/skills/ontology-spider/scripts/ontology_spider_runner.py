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
_SEARCH_ROOTS: list[Path] = [_REPO_ROOT / "src", _REPO_ROOT]
if not (_REPO_ROOT / "plugins").is_dir():
    try:
        import harness as _harness_pkg
    except ImportError:
        _harness_pkg = None  # type: ignore[assignment]
    if _harness_pkg is not None and getattr(_harness_pkg, "__file__", None):
        _prime_root = Path(_harness_pkg.__file__).resolve().parents[2]
        if (_prime_root / "plugins").is_dir():
            _SEARCH_ROOTS.extend([_prime_root / "src", _prime_root])
for _candidate in reversed(_SEARCH_ROOTS):
    if _candidate.is_dir():
        _candidate_str = str(_candidate)
        if _candidate_str not in sys.path:
            sys.path.insert(0, _candidate_str)

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
    parser = argparse.ArgumentParser(description="Headless Ontology-Spider Knowledge Vault & Repository runner")
    parser.add_argument("--vault", default=".harness/knowledge", help="Vault directory or JSON path")
    parser.add_argument("--repo", default=None, help="Optional target code/research repository directory")
    parser.add_argument(
        "--portfolio", action="store_true", help="Analyze --repo as a multi-repository portfolio folder"
    )
    parser.add_argument("--max-depth", type=int, default=4, help="Maximum scan depth per unit in --repo mode")
    parser.add_argument("--max-files-per-unit", type=int, default=120, help="File cap per unit in --repo mode")
    parser.add_argument("--as-of", default=None, help="Optional ISO timestamp for bi-temporal edge slicing")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum edge confidence threshold")
    parser.add_argument("--max-results", type=int, default=5000, help="Maximum query answer cap")
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
    competency_questions = _parse_competency_args(args.competency)

    if args.repo:
        repo_path = Path(args.repo)
        v_dir = vault if vault.exists() else None
        if args.portfolio:
            payload["portfolio"] = service.analyze_portfolio(
                repo_path,
                vault_dir=v_dir,
                max_depth=args.max_depth,
                max_files_per_unit=args.max_files_per_unit,
            ).to_dict()
        else:
            payload["repository"] = service.analyze_repository(
                repo_path,
                vault_dir=v_dir,
                max_depth=args.max_depth,
                max_files_per_unit=args.max_files_per_unit,
            ).to_dict()
            if args.query or args.validate or args.export or args.rank_entropy or competency_questions:
                model = service.load_repository_model(
                    repo_path,
                    vault_dir=v_dir,
                    max_depth=args.max_depth,
                    max_files_per_unit=args.max_files_per_unit,
                )
                if args.query:
                    payload["query"] = service.query_model(
                        model,
                        args.query,
                        rank_by_distance=args.rank_by_distance,
                        max_results=args.max_results,
                    )
                if args.validate:
                    from ontology_spider.api import validate_model

                    payload["violations"] = validate_model(model)
                if args.export:
                    from ontology_spider.api import export_model

                    payload["export"] = {"format": args.export, "content": export_model(model, format=args.export)}
                if competency_questions:
                    from ontology_spider.api import evaluate_competency_questions

                    payload["competency"] = evaluate_competency_questions(model, competency_questions)
                if args.rank_entropy:
                    from ontology_spider.api import rank_discriminating_attributes

                    project_ids = [eid for eid, ent in model.entities.items() if "raw_name" in ent.attributes]
                    payload["entropy_ranks"] = rank_discriminating_attributes(model, project_ids or None)
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.query:
        payload["query"] = service.query(
            vault,
            args.query,
            rank_by_distance=args.rank_by_distance,
            as_of=args.as_of,
            min_confidence=args.min_confidence,
            max_results=args.max_results,
        )
    if args.validate:
        payload["violations"] = service.validate(vault, as_of=args.as_of, min_confidence=args.min_confidence)
    if args.export:
        payload["export"] = {
            "format": args.export,
            "content": service.export(vault, format=args.export, as_of=args.as_of, min_confidence=args.min_confidence),
        }
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
