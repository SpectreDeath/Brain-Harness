"""Data Management Click CLI command group and subcommand bindings."""

from __future__ import annotations

import json
import click

from harness.commands._utils import _run_async
from harness.commands.data.contracts import validate_contract_cmd
from harness.commands.data.golden_records import resolve_golden_records_cmd
from harness.commands.data.maturity import assess_maturity_cmd
from harness.commands.data.pipeline import run_medallion_pipeline_cmd
from harness.commands.data.quality import profile_quality_cmd
from harness.commands.data.topk_cli import register_topk_commands
from harness.services.data_management import MaturityReport, QualityScorecard


@click.group("data")
def data_group() -> None:
    """Enterprise data management, contracts, quality profiling, and Medallion pipelines."""
    pass


@data_group.command("validate")
@click.option("--contract", required=True, help="Path to contract JSON/YAML file")
@click.option("--data", "--dataset", "data", required=True, help="Path to dataset JSON/YAML file")
@click.option("--max-quarantine", default=0.05, type=float, help="Max quarantine ratio before failure")
@click.option("--output", help="Optional output JSON path")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result to stdout")
def validate_cli(contract: str, data: str, max_quarantine: float, output: str | None, json_out: bool) -> None:
    """Validate dataset against an Open Data Contract."""
    result = _run_async(validate_contract_cmd(
        contract_path=contract, data_path=data, max_quarantine_ratio=max_quarantine, out_path=output,
    ))
    if json_out:
        click.echo(json.dumps({k: v for k, v in result.items() if k != "report"}, indent=2))
        return
    status_str = click.style("Compliant", fg="green") if result["is_compliant"] else click.style("Non-Compliant", fg="red")
    click.echo(f"\n[Open Data Contract Validation: {result['contract_name']} v{result['version']}] -> {status_str}")
    click.echo(f"  Valid: {result['valid_records']}/{result['total_records']} | Quarantined: {result['quarantined_records']}")
    if result["violations"]:
        click.echo(f"  Violations ({len(result['violations'])} total):")
        for v in result["violations"][:5]:
            click.echo(f"    - [Row {v.get('record_index')}] {v.get('field')}: {v.get('message')}")


@data_group.command("profile")
@click.option("--data", "--dataset", "data", required=True, help="Path to dataset JSON/YAML file")
@click.option("--rules", "--config", "rules", help="Path to quality rules YAML/JSON file")
@click.option("--key", default="id", help="Primary key field")
@click.option("--threshold", default=70.0, type=float, help="Pass score threshold (0-100)")
@click.option("--markdown", "markdown_out", is_flag=True, help="Output Markdown report to stdout")
@click.option("--out-markdown", help="Optional output Markdown report file path")
@click.option("--output", help="Optional output JSON report path")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result to stdout")
def profile_cli(
    data: str, rules: str | None, key: str, threshold: float,
    markdown_out: bool, out_markdown: str | None, output: str | None, json_out: bool,
) -> None:
    """Profile dataset across 6 DAMA quality dimensions."""
    result = _run_async(profile_quality_cmd(
        data_path=data, rules_path=rules, key_field=key, pass_threshold=threshold,
        out_markdown=out_markdown, out_json=output,
    ))
    if json_out:
        click.echo(json.dumps({k: v for k, v in result.items() if k != "scorecard"}, indent=2))
        return
    if markdown_out:
        scorecard: QualityScorecard = result["scorecard"]
        click.echo(scorecard.generate_markdown())
        return

    status_str = click.style("PASSED", fg="green") if result["passed"] else click.style("FAILED", fg="red")
    click.echo(f"\n[Data Quality Profile Report] Quality Score: {result['overall_score']:.1f}/100 -> {status_str}")
    for dim_name, dim in sorted(result["dimensions"].items()):
        dim_status = click.style("PASS", fg="green") if dim["passed"] else click.style("FAIL", fg="red")
        click.echo(f"  - {dim_name.capitalize()}: {dim['score']:.1f}% [{dim_status}] ({dim['failed_checks']} defects)")


@data_group.command("resolve")
@click.option("--data", "--dataset", "data", required=True, help="Path to input entity records JSON/YAML")
@click.option("--key", "--keys", "keys", multiple=True, help="Match key fields")
@click.option("--source", "--sources", "sources", multiple=True, help="Source system priority order")
@click.option("--output", help="Optional output JSON path for golden records")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result to stdout")
def resolve_cli(
    data: str, keys: tuple[str, ...], sources: tuple[str, ...], output: str | None, json_out: bool,
) -> None:
    """Resolve multi-source records into canonical Golden Records."""
    result = _run_async(resolve_golden_records_cmd(
        data_path=data, match_keys=list(keys) if keys else None,
        sources=list(sources) if sources else None, out_path=output,
    ))
    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    click.echo("\n[Golden Records Resolution]")
    click.echo(f"  Input records: {result['input_records']}")
    click.echo(f"  Golden entities generated: {result['golden_records_count']}")
    for g in result["golden_records"]:
        click.echo(f"  [{g['master_id']}] Sources: {g['contributing_sources']} ({g['source_records_count']} records)")


@data_group.command("maturity")
@click.option("--scores", "--survey", "scores", help="JSON/YAML string or path with capability level scores (0 to 5)")
@click.option("--target", default=4, type=int, help="Target maturity level (default: 4)")
@click.option("--org", default="Enterprise Organization", help="Organization name")
@click.option("--summary", is_flag=True, help="Print markdown summary to stdout")
@click.option("--output", help="Optional output JSON report path")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result to stdout")
def maturity_cli(
    scores: str | None, target: int, org: str, summary: bool, output: str | None, json_out: bool,
) -> None:
    """Evaluate Level 0–5 Data Management Maturity."""
    result = _run_async(assess_maturity_cmd(
        scores_path=scores, target_level=target, org_name=org, out_path=output,
    ))
    if json_out:
        click.echo(json.dumps({k: v for k, v in result.items() if k != "report"}, indent=2))
        return
    if summary:
        report: MaturityReport = result["report"]
        click.echo(report.generate_summary_markdown())
        return

    click.echo(f"\n[Data Management Maturity Assessment: {result['organization']}]")
    click.echo(f"  Overall: Level {result['overall_level']:.1f}/5.0 ({result['stage']}) -> Target: Level {result['target_level']}.0")
    for dim_name, d in result["capabilities"].items():
        gap_val = d["gap"]
        gap_str = click.style("ON TARGET", fg="green") if gap_val <= 0 else click.style(f"GAP -{gap_val}", fg="yellow")
        click.echo(f"  - {d['dimension_name']}: Level {d['current_level']} [{gap_str}]")


@data_group.command("pipeline")
@click.option("--raw", "--data", "--dataset", "raw", required=True, help="Path to raw dataset JSON/YAML")
@click.option("--contract", required=True, help="Path to contract JSON/YAML")
@click.option("--quality", "--rules", "quality", help="Path to quality rules JSON/YAML")
@click.option("--source", "source", help="Source system name")
@click.option("--key", "--keys", "keys", multiple=True, help="Match/primary key fields")
@click.option("--out-gold", help="Path to output Gold curated marts JSON")
@click.option("--out-quarantine", help="Path to output quarantined records JSON")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result to stdout")
def pipeline_cli(
    raw: str, contract: str, quality: str | None, source: str | None,
    keys: tuple[str, ...], out_gold: str | None, out_quarantine: str | None, json_out: bool,
) -> None:
    """Execute end-to-end Medallion lakehouse pipeline (Bronze -> Silver -> Gold)."""
    result = _run_async(run_medallion_pipeline_cmd(
        raw_path=raw, contract_path=contract, quality_path=quality,
        source_system=source, primary_keys=list(keys) if keys else None,
        out_gold=out_gold, out_quarantine=out_quarantine,
    ))
    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    status_str = click.style("SUCCESS", fg="green") if result["success"] else click.style("BREACHED", fg="red")
    click.echo(f"\n[Medallion Pipeline Execution: {result['batch_id']}] -> {status_str}")
    click.echo(f"  Bronze Ingested: {result['bronze_count']}")
    click.echo(f"  Silver Cleansed: {result['silver_count']} (Quarantined: {result['quarantine_count']})")
    click.echo(f"  Gold records: {result['gold_count']}")


# Register DeepSelect TopK subcommands onto data_group
register_topk_commands(data_group)
