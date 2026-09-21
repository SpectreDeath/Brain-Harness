"""Standalone CLI dispatch wrapper delegating to UncertaintyGuardEngine.

Enforces Rule 49: bifurcates CLI dispatch into a thin wrapper delegating to the underlying slotted domain engine.
"""

from __future__ import annotations

import json
import sys

# Ensure UTF-8 stream codec entrypoint invariant (Rule 23)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import click
from uncertainty_guard_engine import (
    UncertaintyGuardEngine,
)


@click.group()
def cli() -> None:
    """Uncertainty-Aware AI Architect CLI — 3-Layer Deterministic Interception Engine."""


@cli.command("gate")
@click.option("--query", "-q", required=True, help="User input query string")
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.45,
    help="Cosine similarity boundary threshold",
)
@click.option(
    "--domain",
    "-d",
    multiple=True,
    help="Operational domain centroids (default: corporate IT)",
)
def gate_cmd(query: str, threshold: float, domain: tuple[str, ...]) -> None:
    """Evaluate Layer 1 input domain boundary gating."""
    domains = list(domain) if domain else None
    engine = UncertaintyGuardEngine()
    res = engine.verify_boundary(query, target_domains=domains, threshold=threshold)
    click.echo(
        json.dumps(
            {
                "is_valid": res.is_valid,
                "score": res.score,
                "matched_domain": res.matched_domain,
                "latency_ms": res.latency_ms,
                "reason": res.reason,
            },
            indent=2,
        )
    )


@cli.command("retrieval")
@click.option("--query", "-q", required=True, help="User input query")
@click.option(
    "--chunk",
    "-c",
    multiple=True,
    required=True,
    help="Retrieved context chunks to score",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.60,
    help="Minimum context sufficiency threshold",
)
def retrieval_cmd(query: str, chunk: tuple[str, ...], threshold: float) -> None:
    """Evaluate Layer 2 retrieval quality and semantic distance scoring."""
    engine = UncertaintyGuardEngine()
    res = engine.score_retrieval(query, list(chunk), minimum_relevance=threshold)
    click.echo(
        json.dumps(
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


@cli.command("logprobs")
@click.option(
    "--logprob",
    "-l",
    multiple=True,
    type=float,
    required=True,
    help="Sequence of token log probabilities",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=-0.35,
    help="Minimum sequence mean logprob threshold",
)
def logprobs_cmd(logprob: tuple[float, ...], threshold: float) -> None:
    """Evaluate Layer 3 token generation log probabilities and perplexity."""
    engine = UncertaintyGuardEngine()
    res = engine.validate_logprobs(list(logprob), logprob_threshold=threshold)
    click.echo(
        json.dumps(
            {
                "is_confident": res.is_confident,
                "avg_logprob": res.avg_logprob,
                "perplexity": res.perplexity,
                "threshold": res.threshold,
                "token_count": res.token_count,
                "action": res.action,
            },
            indent=2,
        )
    )


@cli.command("pipeline")
@click.option("--query", "-q", required=True, help="User input query")
@click.option("--chunk", "-c", multiple=True, help="Retrieved context chunks")
@click.option(
    "--logprob",
    "-l",
    multiple=True,
    type=float,
    help="Sequence of token logprobs",
)
@click.option("--response", "-r", default="Draft answer", help="Draft LLM generation")
def pipeline_cmd(
    query: str,
    chunk: tuple[str, ...],
    logprob: tuple[float, ...],
    response: str,
) -> None:
    """Execute end-to-end 3-layer request interception lifecycle."""
    engine = UncertaintyGuardEngine()
    res = engine.intercept_request(
        query=query,
        retrieved_chunks=list(chunk) if chunk else None,
        token_logprobs=list(logprob) if logprob else None,
        draft_response=response,
    )
    click.echo(
        json.dumps(
            {
                "state": res.state,
                "gate_passed": res.gate_passed,
                "latency_ms": res.total_latency_ms,
                "boundary_valid": res.boundary_result.is_valid,
                "boundary_score": res.boundary_result.score,
                "retrieval_sufficient": (
                    res.retrieval_result.has_sufficient_context
                    if res.retrieval_result
                    else False
                ),
                "logprob_confident": (
                    res.logprob_result.is_confident if res.logprob_result else False
                ),
                "ticket_id": (
                    res.escalation_ticket.ticket_id if res.escalation_ticket else None
                ),
                "response": res.response_text,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    cli()
