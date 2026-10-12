"""Layer 1 deterministic sanity checks Click command."""

from __future__ import annotations

import json as _json

import click

from harness.commands.self_eval.resolver import get_self_eval_service


@click.command("layer1")
@click.argument("text")
@click.option("--schema", default=None, help="Expected schema format (json, xml)")
@click.option("--min-len", type=int, default=10, help="Minimum character length")
@click.option("--max-len", type=int, default=5000, help="Maximum character length")
@click.option(
    "--whitelist", default=None, help="Comma-separated authorized URL domains"
)
@click.option("--syntax", default=None, help="Language syntax validator (e.g. python)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def layer1_cmd(
    text: str,
    schema: str | None,
    min_len: int,
    max_len: int,
    whitelist: str | None,
    syntax: str | None,
    json_output: bool,
) -> None:
    """Execute sub-millisecond Layer 1 deterministic sanity checks on raw text."""
    svc = get_self_eval_service()
    allowed_domains = [d.strip() for d in whitelist.split(",")] if whitelist else None

    rep = svc.evaluate_layer1(
        output_text=text,
        expected_schema=schema,
        min_len=min_len,
        max_len=max_len,
        allowed_domains=allowed_domains,
        syntax_lang=syntax,
    )

    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    status_icon = "PASS" if rep.passed else "FAIL"
    click.echo(f"Layer 1 Status: {status_icon} (Latency: {rep.total_latency_ms:.2f}ms)")
    if rep.refusal_detected:
        click.echo("  [WARNING] Unprompted canned refusal detected!")
    if rep.hallucinated_urls:
        click.echo(
            f"  [WARNING] Unauthorized/Hallucinated URLs: {rep.hallucinated_urls}"
        )
    for c in rep.checks:
        c_status = "OK" if c["passed"] else "FAIL"
        click.echo(f"  [{c_status}] {c['name']}: {c['message']}")
