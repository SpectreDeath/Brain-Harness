"""CLI command for mining documentation debt clusters."""

from __future__ import annotations

import json as _json
import click

from .resolver import get_uncertainty_service


@click.command("calibrate")
@click.option(
    "--query",
    "-q",
    multiple=True,
    required=True,
    help="Under-retrieved or failing queries to cluster",
)
def calibrate_cmd(query: tuple[str, ...]) -> None:
    """Cluster under-retrieved queries to uncover missing documentation debt."""
    svc = get_uncertainty_service()
    clusters = svc.mine_documentation_debt(failed_queries=list(query))
    click.echo(
        _json.dumps(
            [
                {
                    "cluster_id": c.cluster_id,
                    "representative_topic": c.representative_topic,
                    "query_count": c.query_count,
                    "severity": c.severity,
                    "sample_queries": c.sample_queries,
                }
                for c in clusters
            ],
            indent=2,
        )
    )
