"""Thin CLI wrapper delegating to the micro-kernel GraphitiZepMemoryEngine."""

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

from harness.services.graphiti_zep_memory import GraphitiZepMemoryEngine  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graphiti-zep-memory-engine")
    sub = parser.add_subparsers(dest="command", required=True)

    p_temp = sub.add_parser("normalize-temporal")
    p_temp.add_argument("--fact", required=True)
    p_temp.add_argument("--reference-time", required=True)
    p_temp.add_argument("--valid-at", default=None)
    p_temp.add_argument("--invalid-at", default=None)
    p_temp.add_argument("--existing-edges-json", default="[]")
    p_temp.add_argument("--contradicted-ids-json", default="[]")

    p_dedup = sub.add_parser("dedup-entities")
    p_dedup.add_argument("--extracted-json", required=True)
    p_dedup.add_argument("--existing-json", default="[]")
    p_dedup.add_argument("--edge-endpoints-json", default="[]")
    p_dedup.add_argument("--kept-edge-endpoints-json", default=None)

    p_rerank = sub.add_parser("rerank-hybrid")
    p_rerank.add_argument("--method", required=True, choices=["rrf", "mmr", "node_distance"])
    p_rerank.add_argument("--ranked-lists-json", default="[]")
    p_rerank.add_argument("--query-vector-json", default="[]")
    p_rerank.add_argument("--candidate-vectors-json", default="{}")
    p_rerank.add_argument("--center-node-uuid", default=None)
    p_rerank.add_argument("--hop-distances-json", default="{}")
    p_rerank.add_argument("--rank-const", type=int, default=1)
    p_rerank.add_argument("--mmr-lambda", type=float, default=0.5)
    p_rerank.add_argument("--min-score", type=float, default=0.0)

    p_comm = sub.add_parser("cluster-and-ontology")
    p_comm.add_argument("--projection-json", required=True)
    p_comm.add_argument("--episodes-json", default="[]")
    p_comm.add_argument("--entities-json", default="[]")
    p_comm.add_argument("--edges-json", default="[]")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    engine = GraphitiZepMemoryEngine()

    if args.command == "normalize-temporal":
        report = engine.normalize_bitemporal_edges(
            fact=args.fact,
            reference_time=args.reference_time,
            valid_at=args.valid_at,
            invalid_at=args.invalid_at,
            existing_edges=json.loads(args.existing_edges_json),
            contradicted_ids=json.loads(args.contradicted_ids_json),
        )
    elif args.command == "dedup-entities":
        kept_raw = args.kept_edge_endpoints_json
        report = engine.resolve_entities_and_endpoints(
            extracted_entities=json.loads(args.extracted_json),
            existing_entities=json.loads(args.existing_json),
            edge_endpoints=json.loads(args.edge_endpoints_json),
            kept_edge_endpoints=json.loads(kept_raw) if kept_raw is not None else None,
        )
    elif args.command == "rerank-hybrid":
        report = engine.rerank_hybrid_results(
            method=args.method,
            ranked_lists=json.loads(args.ranked_lists_json),
            query_vector=json.loads(args.query_vector_json),
            candidate_vectors=json.loads(args.candidate_vectors_json),
            center_node_uuid=args.center_node_uuid,
            hop_distances=json.loads(args.hop_distances_json),
            rank_const=args.rank_const,
            mmr_lambda=args.mmr_lambda,
            min_score=args.min_score,
        )
    else:
        report = engine.cluster_communities_and_compile_ontology(
            neighbor_projection=json.loads(args.projection_json),
            episode_batches=json.loads(args.episodes_json),
            entity_schemas=json.loads(args.entities_json),
            edge_schemas=json.loads(args.edges_json),
        )

    print(json.dumps(asdict(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
