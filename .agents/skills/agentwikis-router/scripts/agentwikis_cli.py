# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""AgentWikis CLI Engine — Headless CLI Seam & Workflow Dispatcher.

Operationalizes https://agentwikis.com/for-agents and local AgentWikis corpus:
- Discovery catalog listing (list-wikis)
- Boundary inspection & trust semantics (scope)
- Intent classification & calibrated abstention (match-skill)
- Full-text search with calibrated confidence (search)
- Offline-first document section slice retrieval (read-doc)
- MCP client configuration emission (mcp-config)
- Open Data Contract standard validation (validate-contract)
- DAMA-DMBOK 6-dimension data quality profiling (quality-profile)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from agentwikis_engine import (
    AgentWikisEngine,
)

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def get_engine(
    corpus_dir: str | None = None, base_url: str = "https://agentwikis.com"
) -> AgentWikisEngine:
    """Instantiates AgentWikisEngine using relocatable resolution."""
    return AgentWikisEngine(corpus_dir=corpus_dir, base_url=base_url)


def cmd_list_wikis(args: argparse.Namespace) -> int:
    """Lists wikis filtered by category, tag, or query string."""
    engine = get_engine(args.corpus_dir, args.base_url)
    filtered = engine.list_wikis(category=args.category, tag=args.tag, query=args.query)
    results = [w.to_dict() for w in filtered]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(results), "wikis": results}, f, indent=2)

    print(f"Success! Listed {len(results)} wikis. Written to: {out_path}")
    return 0


def cmd_scope(args: argparse.Namespace) -> int:
    """Returns declared scope boundaries and version freshness for a wiki."""
    engine = get_engine(args.corpus_dir, args.base_url)
    wikis, _ = engine.load_entities()
    slug = args.wiki.strip().lower()

    matched = wikis.get(slug)
    if not matched:
        print(f"Error: Wiki '{slug}' not found in registry.", file=sys.stderr)
        return 1

    result = {
        "slug": matched.slug,
        "title": matched.title,
        "category": matched.category,
        "last_updated": matched.last_updated,
        "document_count": matched.document_count,
        "scope": matched.scope.to_dict(),
        "raw_base": matched.raw_base,
        "xl_documents": matched.xl_document_count,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Success! Scope for '{slug}' written to: {out_path}")
    return 0


def cmd_match_skill(args: argparse.Namespace) -> int:
    """Evaluates task intent against wiki scopes and skills with calibrated abstention."""
    engine = get_engine(args.corpus_dir, args.base_url)
    result = engine.match_intent(args.query, limit=args.limit)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    status_str = "IN_SCOPE" if result.in_scope else "OUT_OF_SCOPE"
    conf_str = "CONFIDENT" if result.calibrated_confident else "ABSTAIN"
    print(f"Success! Match status: [{status_str} | {conf_str}]. Written to: {out_path}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Searches corpus across titles and scope descriptions with calibrated confidence."""
    engine = get_engine(args.corpus_dir, args.base_url)
    hits = engine.search(query=args.query, wiki=args.wiki, limit=args.limit)
    selected = [h.to_dict() for h in hits]
    has_confident = any(h.get("calibrated_confident", False) for h in selected)

    payload = {
        "query": args.query.strip().lower(),
        "calibrated_confident": has_confident,
        "confident": has_confident,
        "total_hits": len(hits),
        "total_matches": len(hits),
        "results": selected,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(
        f"Success! Search returned {len(selected)} results (Confident: {has_confident}). Written to: {out_path}"
    )
    return 0


def cmd_context_pack(args: argparse.Namespace) -> int:
    """Compiles one-shot token-bounded context pack for an agent task."""
    engine = get_engine(args.corpus_dir, args.base_url)
    pack_md = engine.prepare_context_pack(query=args.query, max_tokens=args.max_tokens)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(pack_md)

    print(
        f"Success! Prepared context pack ({len(pack_md)} chars). Written to: {out_path}"
    )
    return 0


def cmd_read_doc(args: argparse.Namespace) -> int:
    """Extracts exact Markdown document section offline or with remote fallback."""
    engine = get_engine(args.corpus_dir, args.base_url)
    try:
        doc_slice = engine.extract_document(
            doc_path=args.doc_path,
            section_heading=args.section,
            force_remote=args.remote,
        )
    except Exception as e:
        print(f"Error extracting document: {e}", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc_slice.content)

    print(
        f"Success! Read '{doc_slice.title}' ({len(doc_slice.content)} chars, Source: {doc_slice.source_isnad}). Written to: {out_path}"
    )
    return 0


def cmd_validate_contract(args: argparse.Namespace) -> int:
    """Validates the active corpus against Open Data Contract (ODCS)."""
    engine = get_engine(args.corpus_dir, args.base_url)
    contract_path = (
        Path(args.contract)
        if args.contract
        else Path(__file__).resolve().parent.parent
        / "contracts"
        / "agentwikis_contract.yaml"
    )

    try:
        report = engine.validate_contract(contract_path)
    except Exception as e:
        print(f"Error during contract validation: {e}", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    status_str = "COMPLIANT" if report.is_compliant else "VIOLATIONS DETECTED"
    print(
        f"Success! Contract status: [{status_str} | {len(report.violations)} violations]. Written to: {out_path}"
    )
    return 0 if report.is_compliant else 1


def cmd_quality_profile(args: argparse.Namespace) -> int:
    """Runs DAMA-DMBOK 6-dimension data quality profiling across the corpus."""
    engine = get_engine(args.corpus_dir, args.base_url)
    scorecard = engine.profile_data_quality(min_passing_score=args.min_score)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.suffix.lower() == ".md":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(scorecard.generate_markdown())
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(scorecard.to_dict(), f, indent=2)

    status_str = "PASS" if scorecard.passed else "FAIL"
    print(
        f"Success! Quality Scorecard: [{status_str} | Overall: {scorecard.overall_score:.1f}%]. Written to: {out_path}"
    )
    return 0 if scorecard.passed else 1


def cmd_mcp_config(args: argparse.Namespace) -> int:
    """Emits ready-to-use MCP server configuration."""
    client = args.client.lower()
    api_key = args.api_key or os.environ.get("AGENTWIKIS_API_KEY", "")
    cli_cmd = "claude mcp add agentwikis -- npx -y agentwikis-mcp"
    if api_key:
        cli_cmd += f" -e AGENTWIKIS_API_KEY={api_key}"

    config: dict[str, Any] = {
        "mcpServers": {
            "agentwikis": {
                "command": "npx",
                "args": ["-y", "agentwikis-mcp"],
                "env": {"AGENTWIKIS_API_KEY": api_key} if api_key else {},
            }
        },
        "cli_command": cli_cmd,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Success! MCP config for client '{client}' written to: {out_path}")
    return 0


def cmd_visual_brief(args: argparse.Namespace) -> int:
    """Generates an interactive HTML visual brief of the hybrid data topology (Stage 3)."""
    engine = get_engine(args.corpus_dir, args.base_url)
    brief_path = engine.generate_visual_brief(
        output_path=args.output,
        query=args.query,
        wiki_slug=args.wiki,
    )
    print(f"Success! Visual Brief generated: file:///{brief_path.as_posix()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Builds multi-command CLI parser."""
    parser = argparse.ArgumentParser(
        prog="agentwikis_cli",
        description="AgentWikis CLI Engine — Discovery, Boundary Evaluation & Knowledge Retrieval.",
    )
    parser.add_argument(
        "--corpus-dir", help="Path to AgentWikis corpus directory", default=None
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for remote AgentWikis API",
        default="https://agentwikis.com",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # list-wikis
    p_list = subparsers.add_parser(
        "list-wikis", help="List wikis filtered by category or tags"
    )
    p_list.add_argument("--category", help="Filter by category")
    p_list.add_argument("--tag", help="Filter by tag")
    p_list.add_argument(
        "--query", help="Filter by text query in slug, title, description"
    )
    p_list.add_argument("--output", required=True, help="Output JSON filepath")
    p_list.set_defaults(func=cmd_list_wikis)

    # scope
    p_scope = subparsers.add_parser("scope", help="Inspect declared scope for a wiki")
    p_scope.add_argument("wiki", help="Wiki slug (e.g. vllm, hermes)")
    p_scope.add_argument("--output", required=True, help="Output JSON filepath")
    p_scope.set_defaults(func=cmd_scope)

    # match-skill
    p_match = subparsers.add_parser(
        "match-skill", help="Match user task to in-scope wikis and skills"
    )
    p_match.add_argument("query", help="Task description or prompt")
    p_match.add_argument(
        "--limit", type=int, default=3, help="Max candidates to return"
    )
    p_match.add_argument("--output", required=True, help="Output JSON filepath")
    p_match.set_defaults(func=cmd_match_skill)

    # search
    p_search = subparsers.add_parser(
        "search", help="Search corpus with calibrated confidence"
    )
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--wiki", help="Optional wiki slug filter")
    p_search.add_argument("--limit", type=int, default=5, help="Max results")
    p_search.add_argument("--output", required=True, help="Output JSON filepath")
    p_search.set_defaults(func=cmd_search)

    # read-doc
    p_read = subparsers.add_parser("read-doc", help="Read Markdown document section")
    p_read.add_argument(
        "doc_path", help="Relative document path (e.g. vllm/wiki/index.md)"
    )
    p_read.add_argument("--section", help="Optional heading to slice")
    p_read.add_argument("--remote", action="store_true", help="Force remote HTTP fetch")
    p_read.add_argument("--output", required=True, help="Output Markdown filepath")
    p_read.set_defaults(func=cmd_read_doc)

    # validate-contract
    p_contract = subparsers.add_parser(
        "validate-contract", help="Validate corpus against Open Data Contract"
    )
    p_contract.add_argument(
        "--contract", help="Optional custom contract YAML path", default=None
    )
    p_contract.add_argument("--output", required=True, help="Output JSON filepath")
    p_contract.set_defaults(func=cmd_validate_contract)

    # quality-profile
    p_quality = subparsers.add_parser(
        "quality-profile", help="Run DAMA 6-dimension data quality profile"
    )
    p_quality.add_argument(
        "--min-score", type=float, default=85.0, help="Minimum passing score"
    )
    p_quality.add_argument(
        "--output", required=True, help="Output filepath (.json or .md)"
    )
    p_quality.set_defaults(func=cmd_quality_profile)

    # mcp-config
    p_mcp = subparsers.add_parser(
        "mcp-config", help="Generate MCP client setup configuration"
    )
    p_mcp.add_argument(
        "--client",
        default="antigravity",
        choices=["antigravity", "claude", "claude-code", "json"],
    )
    p_mcp.add_argument("--api-key", help="Optional Pro XL API key")
    p_mcp.add_argument("--output", required=True, help="Output configuration filepath")
    p_mcp.set_defaults(func=cmd_mcp_config)

    # context-pack
    p_pack = subparsers.add_parser(
        "context-pack", help="Compile one-shot token-bounded context pack"
    )
    p_pack.add_argument("query", help="Task description or prompt")
    p_pack.add_argument(
        "--max-tokens", type=int, default=4000, help="Token budget bound"
    )
    p_pack.add_argument("--output", required=True, help="Output Markdown filepath")
    p_pack.set_defaults(func=cmd_context_pack)

    # visual-brief (Stage 3)
    p_brief = subparsers.add_parser(
        "visual-brief", help="Generate interactive HTML visual brief and topology DAG"
    )
    p_brief.add_argument(
        "--output",
        help="Output HTML filepath (defaults to %%TEMP%%/agentwikis_routing_brief.html)",
        default=None,
    )
    p_brief.add_argument(
        "--query", help="Optional task query to highlight routing context", default=None
    )
    p_brief.add_argument(
        "--wiki", help="Optional wiki slug to focus blast radius", default=None
    )
    p_brief.set_defaults(func=cmd_visual_brief)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
