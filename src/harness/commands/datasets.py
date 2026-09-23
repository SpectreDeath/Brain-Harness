"""Headless Click CLI commands for Hugging Face Datasets introspection (Rule 10)."""

from __future__ import annotations

import json

import click

from harness.services.hf_datasets import (
    DefaultHfDatasetsService,
    HfTransformationSpec,
)


@click.group("datasets")
def datasets_group() -> None:
    """Hugging Face Datasets inspection, streaming, transformation, and lakehouse conversion commands."""


@datasets_group.command("inspect")
@click.argument("path_or_name")
@click.option("--split", default="train", help="Dataset split to inspect")
def inspect_dataset_cmd(path_or_name: str, split: str) -> None:
    """Inspect dataset metadata, splits, row count, and schema."""
    engine = DefaultHfDatasetsService()
    meta = engine.inspect_dataset(path_or_name, split)
    click.echo(
        json.dumps(
            {
                "name": meta.name,
                "split": meta.split,
                "num_rows": meta.num_rows,
                "features": meta.features,
                "format": meta.format,
                "byte_size": meta.byte_size,
                "is_streaming": meta.is_streaming,
            },
            indent=2,
        )
    )


@datasets_group.command("profile")
@click.argument("path_or_name")
def profile_schema_cmd(path_or_name: str) -> None:
    """Extract column schemas, Arrow data types, nullability, and sample values."""
    engine = DefaultHfDatasetsService()
    schemas = engine.profile_schema(path_or_name)
    click.echo(
        json.dumps(
            [
                {
                    "name": s.name,
                    "arrow_type": s.arrow_type,
                    "is_nullable": s.is_nullable,
                    "feature_type": s.feature_type,
                    "sample_values": list(s.sample_values),
                }
                for s in schemas
            ],
            indent=2,
        )
    )


@datasets_group.command("strategy")
@click.argument("path_or_name")
@click.option("--split", default="train", help="Dataset split")
@click.option(
    "--threshold-mb",
    default=500,
    type=int,
    help="Threshold in MB to trigger streaming strategy",
)
def evaluate_strategy_cmd(path_or_name: str, split: str, threshold_mb: int) -> None:
    """Evaluate dataset footprint and select between memory-mapped Arrow and streaming."""
    engine = DefaultHfDatasetsService()
    strat = engine.evaluate_storage_strategy(path_or_name, split, threshold_mb)
    click.echo(
        json.dumps(
            {
                "strategy": strat.strategy,
                "reason": strat.reason,
                "estimated_bytes": strat.estimated_bytes,
                "recommended_batch_size": strat.recommended_batch_size,
                "recommended_workers": strat.recommended_workers,
                "requires_streaming": strat.requires_streaming,
            },
            indent=2,
        )
    )


@datasets_group.command("sample")
@click.argument("path_or_name")
@click.option("--split", default="train", help="Dataset split")
@click.option("--n", default=5, type=int, help="Number of records to sample")
def sample_dataset_cmd(path_or_name: str, split: str, n: int) -> None:
    """Sample records from a local or streaming dataset without RAM blowout."""
    engine = DefaultHfDatasetsService()
    samples = engine.stream_sample(path_or_name, split, n)
    click.echo(json.dumps(samples, indent=2))


@datasets_group.command("transform")
@click.argument("input_path")
@click.argument("output_path")
@click.option("--filter-field", default=None, help="Field to filter on")
@click.option(
    "--filter-op",
    default=None,
    help="Filter operator: eq, neq, gt, gte, lt, lte, contains, in",
)
@click.option("--filter-val", default=None, help="Filter value to match")
@click.option(
    "--select-cols",
    default=None,
    help="Comma-separated column names to select",
)
@click.option("--batch-size", default=100, type=int, help="Chunk batch size")
def transform_dataset_cmd(
    input_path: str,
    output_path: str,
    filter_field: str | None,
    filter_op: str | None,
    filter_val: str | None,
    select_cols: str | None,
    batch_size: int,
) -> None:
    """Execute lazy filtering, column projection, and batch transformation."""
    engine = DefaultHfDatasetsService()
    cols = tuple(c.strip() for c in select_cols.split(",")) if select_cols else ()
    spec = HfTransformationSpec(
        filter_field=filter_field,
        filter_op=filter_op,
        filter_value=filter_val,
        select_columns=cols,
        batch_size=batch_size,
    )
    res = engine.transform_dataset(input_path, output_path, spec)
    click.echo(
        json.dumps(
            {
                "status": res.status,
                "rows_processed": res.rows_processed,
                "execution_time_ms": res.execution_time_ms,
                "cache_fingerprint": res.cache_fingerprint,
                "output_path": res.output_path,
            },
            indent=2,
        )
    )


@datasets_group.command("convert")
@click.argument("input_path")
@click.argument("output_path")
@click.option(
    "--format",
    default="parquet",
    help="Target format: parquet, arrow, json, jsonl, csv",
)
def convert_dataset_cmd(input_path: str, output_path: str, format: str) -> None:
    """Convert dataset file between CSV, JSON, Arrow, and Parquet lakehouse formats."""
    engine = DefaultHfDatasetsService()
    res = engine.convert_format(input_path, output_path, format)
    click.echo(
        json.dumps(
            {
                "status": res.status,
                "rows_processed": res.rows_processed,
                "execution_time_ms": res.execution_time_ms,
                "cache_fingerprint": res.cache_fingerprint,
                "output_path": res.output_path,
            },
            indent=2,
        )
    )


@datasets_group.command("commit-vault")
@click.argument("dataset_name")
@click.argument("input_path")
@click.option("--split", default="train", help="Dataset split")
@click.option(
    "--vault-root", default=None, help="Custom Knowledge Vault directory root"
)
def commit_vault_cmd(
    dataset_name: str, input_path: str, split: str, vault_root: str | None
) -> None:
    """Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40)."""
    engine = DefaultHfDatasetsService()
    meta = engine.inspect_dataset(input_path, split)
    schemas = engine.profile_schema(input_path)
    commit = engine.commit_to_vault(dataset_name, meta, schemas, vault_root)
    click.echo(
        json.dumps(
            {
                "status": "ok",
                "ki_id": commit.ki_id,
                "title": commit.title,
                "metadata_path": commit.metadata_path,
                "summary_path": commit.summary_path,
                "cache_fingerprint": commit.cache_fingerprint,
                "features_count": commit.features_count,
                "total_rows": commit.total_rows,
            },
            indent=2,
        )
    )
