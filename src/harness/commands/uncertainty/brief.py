"""CLI command for generating HTML visual brief."""

from __future__ import annotations

import click

from .resolver import get_uncertainty_service


@click.command("brief")
@click.option("--query", "-q", default="Configure internal VPN", help="Query")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Custom output HTML path",
)
def brief_cmd(query: str, output: str | None) -> None:
    """Generate interactive HTML visual brief in %TEMP%."""
    svc = get_uncertainty_service()
    res = svc.intercept_request(
        query=query,
        retrieved_chunks=["VPN client configuration for remote staff..."],
        token_logprobs=[-0.1, -0.05, -0.2],
        draft_response="Follow the corporate VPN guide.",
    )
    path = svc.generate_visual_brief(res, output_path=output)
    click.echo(f"Visual Brief generated: {path}")
