"""CLI command for Layer 3 token logprob and perplexity validation."""

from __future__ import annotations

import json as _json
import click

from .resolver import get_uncertainty_service


@click.command("logprobs")
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
    help="Logprob safety threshold (default: -0.35)",
)
def logprobs_cmd(logprob: tuple[float, ...], threshold: float) -> None:
    """Evaluate Layer 3 token log probabilities and sequence perplexity."""
    svc = get_uncertainty_service()
    res = svc.validate_logprobs(list(logprob), logprob_threshold=threshold)
    click.echo(
        _json.dumps(
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
