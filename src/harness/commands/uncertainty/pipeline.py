"""CLI command for 3-layer request interception pipeline."""

from __future__ import annotations

import json as _json
import click

from .resolver import get_uncertainty_service


@click.command("pipeline")
@click.option("--query", "-q", required=True, help="User input query")
@click.option("--chunk", "-c", multiple=True, help="Retrieved context chunks")
@click.option(
    "--logprob",
    "-l",
    multiple=True,
    type=float,
    help="Token log probabilities",
)
@click.option(
    "--response", "-r", default="Verified response", help="Draft LLM generation"
)
def pipeline_cmd(
    query: str,
    chunk: tuple[str, ...],
    logprob: tuple[float, ...],
    response: str,
) -> None:
    """Execute end-to-end 3-layer request interception lifecycle."""
    svc = get_uncertainty_service()
    res = svc.intercept_request(
        query=query,
        retrieved_chunks=list(chunk) if chunk else None,
        token_logprobs=list(logprob) if logprob else None,
        draft_response=response,
    )
    click.echo(
        _json.dumps(
            {
                "state": res.state,
                "gate_passed": res.gate_passed,
                "latency_ms": res.total_latency_ms,
                "boundary_score": res.boundary_result.score,
                "boundary_valid": res.boundary_result.is_valid,
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
