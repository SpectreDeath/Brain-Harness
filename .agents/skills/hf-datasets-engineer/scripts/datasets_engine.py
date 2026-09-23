"""Standalone domain execution script for hf-datasets-engineer skill (PEP 723)."""

# /// script
# dependencies = ["pydantic", "structlog"]
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# UTF-8 stream codec entrypoint invariant (Rule 23 / Rule 50)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Prepend workspace root and src/ to sys.path (Rule 50)
_workspace_root = Path(__file__).resolve().parents[4]
_src_dir = _workspace_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from harness.services.hf_datasets import (
    DefaultHfDatasetsService,
    HfTransformationSpec,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hugging Face Datasets Domain Engine")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect dataset metadata and splits")
    p_inspect.add_argument("path_or_name", help="Dataset path or identifier")
    p_inspect.add_argument("--split", default="train", help="Dataset split")

    # profile
    p_profile = subparsers.add_parser("profile", help="Profile column schemas and Arrow types")
    p_profile.add_argument("path_or_name", help="Dataset path or identifier")

    # strategy
    p_strategy = subparsers.add_parser("strategy", help="Evaluate storage strategy (mmap vs stream)")
    p_strategy.add_argument("path_or_name", help="Dataset path or identifier")
    p_strategy.add_argument("--split", default="train", help="Dataset split")
    p_strategy.add_argument("--threshold-mb", type=int, default=500, help="Threshold in MB")

    # sample
    p_sample = subparsers.add_parser("sample", help="Sample records from dataset without RAM blowout")
    p_sample.add_argument("path_or_name", help="Dataset path or identifier")
    p_sample.add_argument("--split", default="train", help="Dataset split")
    p_sample.add_argument("--n", type=int, default=5, help="Number of records to sample")

    # transform
    p_transform = subparsers.add_parser("transform", help="Filter, select columns, and transform")
    p_transform.add_argument("input_path", help="Source file path")
    p_transform.add_argument("output_path", help="Target file path")
    p_transform.add_argument("--filter-field", default=None, help="Field to filter on")
    p_transform.add_argument("--filter-op", default=None, help="Filter operator (eq, neq, gt, gte, lt, lte, contains, in)")
    p_transform.add_argument("--filter-val", default=None, help="Value to match")
    p_transform.add_argument("--select-cols", default=None, help="Comma-separated column names")
    p_transform.add_argument("--batch-size", type=int, default=100, help="Batch chunk size")

    # convert
    p_convert = subparsers.add_parser("convert", help="Convert dataset between formats")
    p_convert.add_argument("input_path", help="Source file path")
    p_convert.add_argument("output_path", help="Target file path")
    p_convert.add_argument("--format", default="parquet", help="Target format (parquet/arrow/json/csv)")

    # commit-vault
    p_vault = subparsers.add_parser("commit-vault", help="Commit dataset catalog to Knowledge Vault")
    p_vault.add_argument("dataset_name", help="Dataset name")
    p_vault.add_argument("input_path", help="Source dataset path")
    p_vault.add_argument("--split", default="train", help="Dataset split")
    p_vault.add_argument("--vault-root", default=None, help="Knowledge Vault root")

    args = parser.parse_args()
    engine = DefaultHfDatasetsService()

    if args.subcommand == "inspect":
        meta = engine.inspect_dataset(args.path_or_name, args.split)
        print(json.dumps({
            "name": meta.name,
            "split": meta.split,
            "num_rows": meta.num_rows,
            "features": meta.features,
            "format": meta.format,
            "byte_size": meta.byte_size,
            "is_streaming": meta.is_streaming,
        }, indent=2))

    elif args.subcommand == "profile":
        schemas = engine.profile_schema(args.path_or_name)
        print(json.dumps([
            {
                "name": s.name,
                "arrow_type": s.arrow_type,
                "is_nullable": s.is_nullable,
                "feature_type": s.feature_type,
                "sample_values": list(s.sample_values),
            }
            for s in schemas
        ], indent=2))

    elif args.subcommand == "strategy":
        strat = engine.evaluate_storage_strategy(args.path_or_name, args.split, args.threshold_mb)
        print(json.dumps({
            "strategy": strat.strategy,
            "reason": strat.reason,
            "estimated_bytes": strat.estimated_bytes,
            "recommended_batch_size": strat.recommended_batch_size,
            "recommended_workers": strat.recommended_workers,
            "requires_streaming": strat.requires_streaming,
        }, indent=2))

    elif args.subcommand == "sample":
        samples = engine.stream_sample(args.path_or_name, args.split, args.n)
        print(json.dumps(samples, indent=2))

    elif args.subcommand == "transform":
        cols = tuple(c.strip() for c in args.select_cols.split(",")) if args.select_cols else ()
        spec = HfTransformationSpec(
            filter_field=args.filter_field,
            filter_op=args.filter_op,
            filter_value=args.filter_val,
            select_columns=cols,
            batch_size=args.batch_size,
        )
        res = engine.transform_dataset(args.input_path, args.output_path, spec)
        print(json.dumps({
            "status": res.status,
            "rows_processed": res.rows_processed,
            "execution_time_ms": res.execution_time_ms,
            "cache_fingerprint": res.cache_fingerprint,
            "output_path": res.output_path,
        }, indent=2))

    elif args.subcommand == "convert":
        res = engine.convert_format(args.input_path, args.output_path, args.format)
        print(json.dumps({
            "status": res.status,
            "rows_processed": res.rows_processed,
            "execution_time_ms": res.execution_time_ms,
            "cache_fingerprint": res.cache_fingerprint,
            "output_path": res.output_path,
        }, indent=2))

    elif args.subcommand == "commit-vault":
        meta = engine.inspect_dataset(args.input_path, args.split)
        schemas = engine.profile_schema(args.input_path)
        commit = engine.commit_to_vault(args.dataset_name, meta, schemas, args.vault_root)
        print(json.dumps({
            "status": "ok",
            "ki_id": commit.ki_id,
            "title": commit.title,
            "metadata_path": commit.metadata_path,
            "summary_path": commit.summary_path,
            "cache_fingerprint": commit.cache_fingerprint,
            "features_count": commit.features_count,
            "total_rows": commit.total_rows,
        }, indent=2))


if __name__ == "__main__":
    main()
