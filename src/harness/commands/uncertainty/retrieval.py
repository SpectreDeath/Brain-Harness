"""CLI command for Layer 2 retrieval relevance scoring."""

from __future__ import annotations

import json as _json
import click

from .resolver import get_uncertainty_service


@click.command("retrieval")
@click.option("--query", "-q", required=True, help="User input query")
@click.option(
    "--chunk",
    "-c",
    multiple=True,
    required=True,
    help="Retrieved document chunks to score",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.60,
    help="Minimum context relevance threshold (default: 0.60)",
)
def retrieval_cmd(query: str, chunk: tuple[str, ...], threshold: float) -> None:
    """Evaluate Layer 2 retrieval relevance and context sufficiency."""
    svc = get_uncertainty_service()
    res = svc.score_retrieval(query, list(chunk), minimum_relevance=threshold)
    click.echo(
        _json.dumps(
            {
                "has_sufficient_context": res.has_sufficient_context,
                "top_score": res.top_score,
                "min_threshold": res.min_threshold,
                "action": res.action,
                "scored_chunks": [
                    {"id": c.chunk_id, "score": c.score, "content": c.content}
                    for c in res.scored_chunks
                ],
            },
            indent=2,
        )
    )
