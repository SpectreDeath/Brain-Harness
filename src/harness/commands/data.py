"""Data Management CLI command implementations and pure async entrypoints.

Provides headless execution seams for:
- Open Data Contract validation
- 6-Dimension data quality profiling
- Master Data Golden Record entity resolution
- Level 0–5 Data Management Maturity assessment
- End-to-end Medallion lakehouse pipeline runs
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import click
import structlog
import yaml

from harness.commands._utils import _run_async
from harness.services.data_management import (
    ContractValidationReport,
    DataManagementEngine,
    EntityRecord,
    GoldenRecord,
    MaturityReport,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    QualityScorecard,
)

logger = structlog.get_logger()


# --- Pure Async Command Functions ---

async def validate_contract_cmd(
    contract_path: str,
    data_path: str | None = None,
    dataset_path: str | None = None,
    max_quarantine_ratio: float = 0.05,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Validate data records against an Open Data Contract definition."""
    c_p = Path(contract_path)
    d_path = data_path or dataset_path
    if not d_path:
        raise ValueError("data_path or dataset_path must be provided")
    d_p = Path(d_path)

    contract_def = yaml.safe_load(c_p.read_text(encoding="utf-8")) or {}
    raw_data = yaml.safe_load(d_p.read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    engine = DataManagementEngine()
    report = engine.validate_contract(raw_data, contract_def, max_quarantine_ratio=max_quarantine_ratio)

    ret = {
        "valid": report.is_compliant,
        "is_compliant": report.is_compliant,
        "total_records": report.total_records,
        "valid_records": report.valid_records,
        "quarantined_records": report.quarantined_records,
        "violations_count": len(report.violations),
        "contract_name": report.contract_name,
        "version": report.version,
        "violations": [v.to_dict() for v in report.violations],
        "report": report,
    }
    if out_path:
        Path(out_path).write_text(json.dumps({k: v for k, v in ret.items() if k != "report"}, indent=2), encoding="utf-8")

    return ret


async def profile_quality_cmd(
    data_path: str | None = None,
    dataset_path: str | None = None,
    rules_path: str | None = None,
    key_field: str = "id",
    pass_threshold: float = 70.0,
    out_markdown: str | None = None,
    out_json: str | None = None,
) -> dict[str, Any]:
    """Profile data records across the 6 DAMA quality dimensions."""
    d_path = data_path or dataset_path
    if not d_path:
        raise ValueError("data_path or dataset_path must be provided")
    d_p = Path(d_path)

    raw_data = yaml.safe_load(d_p.read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    req_fields = None
    keys = [key_field] if key_field != "id" else None
    if rules_path:
        r_p = Path(rules_path)
        if r_p.exists():
            cfg = yaml.safe_load(r_p.read_text(encoding="utf-8")) or {}
            rules_block = cfg.get("rules", cfg)
            req_fields = rules_block.get("completeness", {}).get("required_fields")
            acc_dict = rules_block.get("accuracy", {}).get("numeric_ranges")
            if acc_dict:
                acc_ranges = {k: (float(v[0]), float(v[1])) for k, v in acc_dict.items()}
            thresh = cfg.get("thresholds", {}).get("overall_min_score")
            if thresh is not None:
                pass_threshold = float(thresh)
            uniq_keys = rules_block.get("uniqueness", {}).get("primary_keys")
            if uniq_keys and not keys:
                keys = list(uniq_keys)
    if not keys:
        keys = [key_field]

    engine = DataManagementEngine()
    scorecard = engine.profile_quality(
        raw_data,
        dataset_name=d_p.stem,
        key_fields=keys,
        required_fields=req_fields,
        accuracy_ranges=acc_ranges,
        pass_threshold=pass_threshold,
    )

    ret = {
        "passed": scorecard.passed,
        "overall_score": scorecard.overall_score,
        "total_records": scorecard.total_records,
        "dimensions": {k: v.to_dict() for k, v in scorecard.dimensions.items()},
        "defects_summary": scorecard.defects_summary,
        "scorecard": scorecard,
    }
    if out_json:
        Path(out_json).write_text(json.dumps({k: v for k, v in ret.items() if k != "scorecard"}, indent=2), encoding="utf-8")
    if out_markdown:
        Path(out_markdown).write_text(scorecard.generate_markdown(), encoding="utf-8")

    return ret


async def resolve_golden_records_cmd(
    data_path: str | None = None,
    dataset_path: str | None = None,
    match_keys: str | list[str] | None = None,
    source_priority: str | list[str] | None = None,
    sources: str | list[str] | None = None,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Cluster multi-source feeds and resolve canonical Golden Records."""
    d_path = data_path or dataset_path
    if not d_path:
        raise ValueError("data_path or dataset_path must be provided")
    d_p = Path(d_path)

    raw_data = yaml.safe_load(d_p.read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    if isinstance(match_keys, str):
        match_keys = [k.strip() for k in match_keys.split(",") if k.strip()]
    prios = source_priority or sources
    if isinstance(prios, str):
        prios = [s.strip() for s in prios.split(",") if s.strip()]

    records = [
        EntityRecord(
            record_id=r.get("record_id") or r.get("student_id") or f"rec_{i}",
            source_system=r.get("source_system", "unknown"),
            updated_at=r.get("updated_at", "2026-01-01T00:00:00Z"),
            attributes=r.get("attributes", r),
        )
        for i, r in enumerate(raw_data)
    ]

    engine = DataManagementEngine()
    golden_records = engine.resolve_golden_records(
        records,
        match_keys=match_keys or ["student_id", "national_id", "id"],
        source_priority=prios or ["registrar_system", "mobility_portal", "crm"],
    )

    ret = {
        "golden_records": [g.to_dict() for g in golden_records],
        "input_records": len(raw_data),
        "golden_records_count": len(golden_records),
    }
    if out_path:
        Path(out_path).write_text(json.dumps(ret, indent=2), encoding="utf-8")

    return ret


async def assess_maturity_cmd(
    scores_path: str | None = None,
    survey_path: str | None = None,
    target_level: int = 4,
    org_name: str = "Enterprise Organization",
    out_path: str | None = None,
) -> dict[str, Any]:
    """Evaluate Level 0–5 Data Management Maturity."""
    s_path = survey_path or scores_path
    scores: dict[str, int] = {}
    organization = org_name
    if s_path:
        p = Path(s_path)
        if p.exists():
            loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        else:
            loaded = yaml.safe_load(s_path)
        if isinstance(loaded, dict):
            if "organization" in loaded:
                organization = loaded["organization"]
            if "capabilities" in loaded:
                for k, v in loaded["capabilities"].items():
                    if isinstance(v, dict) and "level" in v:
                        scores[k] = int(v["level"])
                    elif isinstance(v, (int, float)):
                        scores[k] = int(v)
            else:
                scores = loaded
    else:
        scores = {
            "data_governance": 2,
            "data_architecture": 3,
            "data_modeling": 3,
            "data_quality": 2,
            "data_security_privacy": 3,
            "data_engineering_ops": 2,
        }

    engine = DataManagementEngine()
    report = engine.assess_maturity(scores, target_level=target_level, organization_name=organization)

    ret = {
        "organization": report.organization_name,
        "overall_level": report.overall_maturity_level,
        "target_level": report.target_maturity_level,
        "stage": report.maturity_stage,
        "capabilities": {k: v.to_dict() for k, v in report.dimension_scores.items()},
        "roadmap": list(report.prioritized_roadmap),
        "report": report,
    }
    if out_path:
        Path(out_path).write_text(json.dumps({k: v for k, v in ret.items() if k != "report"}, indent=2), encoding="utf-8")

    return ret


async def run_medallion_pipeline_cmd(
    dataset_path: str | None = None,
    raw_path: str | None = None,
    contract_path: str | None = None,
    quality_path: str | None = None,
    source_system: str | None = None,
    primary_keys: str | list[str] | tuple[str, ...] | None = None,
    key_fields: list[str] | None = None,
    sources: list[str] | None = None,
    out_gold: str | None = None,
    out_quarantine: str | None = None,
) -> dict[str, Any]:
    """Execute end-to-end Medallion pipeline (Bronze -> Silver MDM -> Gold Mart)."""
    d_path = dataset_path or raw_path
    if not d_path:
        raise ValueError("dataset_path or raw_path must be provided")
    raw_data = yaml.safe_load(Path(d_path).read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    contract_def = {}
    if contract_path:
        c_p = Path(contract_path)
        if c_p.exists():
            contract_def = yaml.safe_load(c_p.read_text(encoding="utf-8")) or {}

    quality_rules = {}
    if quality_path:
        q_p = Path(quality_path)
        if q_p.exists():
            quality_rules = yaml.safe_load(q_p.read_text(encoding="utf-8")) or {}

    keys = primary_keys or key_fields or ["student_id", "national_id", "id"]
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(",") if k.strip()]

    source_prio = sources or ["registrar_system", "mobility_portal", "admissions_crm"]
    if source_system and source_system not in source_prio:
        source_prio = [source_system] + list(source_prio)

    match_k = None
    if primary_keys and "student_id" in primary_keys:
        match_k = ["student_id"]
    if quality_rules:
        uniq_keys = quality_rules.get("rules", {}).get("uniqueness", {}).get("primary_keys")
        if uniq_keys:
            keys = uniq_keys

    config = MedallionPipelineConfig(
        contract_def=contract_def,
        quality_rules=quality_rules,
        key_fields=tuple(keys),
        match_keys=tuple(match_k) if match_k else None,
        source_priority=tuple(source_prio),
    )

    engine = DataManagementEngine()
    result = engine.execute_medallion_pipeline(raw_data, config)

    if out_gold:
        Path(out_gold).write_text(json.dumps(result.gold_marts, indent=2), encoding="utf-8")
    if out_quarantine:
        Path(out_quarantine).write_text(json.dumps(result.quarantined_records, indent=2), encoding="utf-8")

    return result.to_dict()


# --- Click CLI Group ---

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
    result = _run_async(validate_contract_cmd(contract_path=contract, data_path=data, max_quarantine_ratio=max_quarantine, out_path=output))
    if json_out:
        clean_dict = {k: v for k, v in result.items() if k != "report"}
        click.echo(json.dumps(clean_dict, indent=2))
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
    data: str,
    rules: str | None,
    key: str,
    threshold: float,
    markdown_out: bool,
    out_markdown: str | None,
    output: str | None,
    json_out: bool,
) -> None:
    """Profile dataset across 6 DAMA quality dimensions."""
    result = _run_async(profile_quality_cmd(
        data_path=data,
        rules_path=rules,
        key_field=key,
        pass_threshold=threshold,
        out_markdown=out_markdown,
        out_json=output,
    ))
    if json_out:
        clean_dict = {k: v for k, v in result.items() if k != "scorecard"}
        click.echo(json.dumps(clean_dict, indent=2))
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
    data: str,
    keys: tuple[str, ...],
    sources: tuple[str, ...],
    output: str | None,
    json_out: bool,
) -> None:
    """Resolve multi-source records into canonical Golden Records."""
    match_keys = list(keys) if keys else None
    source_prio = list(sources) if sources else None
    result = _run_async(resolve_golden_records_cmd(
        data_path=data,
        match_keys=match_keys,
        sources=source_prio,
        out_path=output,
    ))
    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    click.echo(f"\n[Golden Records Resolution]")
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
    scores: str | None,
    target: int,
    org: str,
    summary: bool,
    output: str | None,
    json_out: bool,
) -> None:
    """Evaluate Level 0–5 Data Management Maturity."""
    result = _run_async(assess_maturity_cmd(
        scores_path=scores,
        target_level=target,
        org_name=org,
        out_path=output,
    ))
    if json_out:
        clean_dict = {k: v for k, v in result.items() if k != "report"}
        click.echo(json.dumps(clean_dict, indent=2))
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
    raw: str,
    contract: str,
    quality: str | None,
    source: str | None,
    keys: tuple[str, ...],
    out_gold: str | None,
    out_quarantine: str | None,
    json_out: bool,
) -> None:
    """Execute end-to-end Medallion lakehouse pipeline (Bronze -> Silver -> Gold)."""
    match_keys = list(keys) if keys else None
    result = _run_async(run_medallion_pipeline_cmd(
        raw_path=raw,
        contract_path=contract,
        quality_path=quality,
        source_system=source,
        primary_keys=match_keys,
        out_gold=out_gold,
        out_quarantine=out_quarantine,
    ))
    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    status_str = click.style("SUCCESS", fg="green") if result["success"] else click.style("BREACHED", fg="red")
    click.echo(f"\n[Medallion Pipeline Execution: {result['batch_id']}] -> {status_str}")
    click.echo(f"  Bronze Ingested: {result['bronze_count']}")
    click.echo(f"  Silver Cleansed: {result['silver_count']} (Quarantined: {result['quarantine_count']})")
    click.echo(f"  Gold records: {result['gold_count']}")
