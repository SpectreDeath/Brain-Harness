"""Thin CLI wrapper delegating to the micro-kernel TrustGraphGovernorEngine."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_ROOT = _REPO_ROOT / "src"
for _candidate in (str(_SRC_ROOT), str(_REPO_ROOT)):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from harness.services.trustgraph_governor import TrustGraphGovernorEngine  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trustgraph-governor-engine")
    sub = parser.add_subparsers(dest="command", required=True)

    p_filter = sub.add_parser("filter-policy")
    p_filter.add_argument("--triples-json", required=True)
    p_filter.add_argument("--policies-json", default="[]")
    p_filter.add_argument("--attributes-json", default="{}")

    p_onto = sub.add_parser("validate-ontology")
    p_onto.add_argument("--ontology-json", required=True)
    p_onto.add_argument("--triples-json", required=True)
    p_onto.add_argument("--bypass-below", type=int, default=5)

    p_prov = sub.add_parser("build-provenance")
    p_prov.add_argument("--question-id", required=True)
    p_prov.add_argument("--query-text", required=True)
    p_prov.add_argument("--document-id", default=None)
    p_prov.add_argument("--prompt-tokens", type=int, default=0)
    p_prov.add_argument("--completion-tokens", type=int, default=0)

    p_laya = sub.add_parser("score-decision")
    p_laya.add_argument("--question-type", required=True)
    p_laya.add_argument("--options-json", required=True)
    p_laya.add_argument("--logits-json", required=True)
    p_laya.add_argument("--temperature", type=float, default=1.0)
    p_laya.add_argument("--option-tokens-each", type=int, default=12)
    p_laya.add_argument("--probs-normalized", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    engine = TrustGraphGovernorEngine()

    if args.command == "filter-policy":
        report = engine.evaluate_shacl_policy_filter(
            triples=json.loads(args.triples_json),
            policies=json.loads(args.policies_json),
            subject_attributes=json.loads(args.attributes_json),
        )
    elif args.command == "validate-ontology":
        report = engine.validate_ontology_extractions(
            ontology=json.loads(args.ontology_json),
            triples=json.loads(args.triples_json),
            bypass_selector_below=args.bypass_below,
        )
    elif args.command == "build-provenance":
        report = engine.build_provenance_trace(
            question_id=args.question_id,
            query_text=args.query_text,
            document_id=args.document_id,
            prompt_tokens=args.prompt_tokens,
            completion_tokens=args.completion_tokens,
        )
    else:
        report = engine.score_laya_decision(
            question_type=args.question_type,
            options=json.loads(args.options_json),
            logits_or_probs=json.loads(args.logits_json),
            temperature=args.temperature,
            option_tokens_each=args.option_tokens_each,
            probs_already_normalized=bool(args.probs_normalized),
        )

    print(json.dumps(asdict(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
