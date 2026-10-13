"""CLI command for Layer 1 input boundary gating."""

from __future__ import annotations

import json as _json
import click

from .resolver import get_uncertainty_service


@click.command("gate")
@click.option("--query", "-q", required=True, help="User input query")
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.45,
    help="Cosine boundary threshold (default: 0.45)",
)
@click.option(
    "--domain", "-d", multiple=True, help="Custom operational domain centroid"
)
def gate_cmd(query: str, threshold: float, domain: tuple[str, ...]) -> None:
    """Evaluate Layer 1 input domain boundary gating."""
    svc = get_uncertainty_service()
    domains = list(domain) if domain else None
    res = svc.verify_boundary(query, target_domains=domains, threshold=threshold)
    click.echo(
        _json.dumps(
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
