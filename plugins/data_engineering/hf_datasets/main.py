"""Hugging Face Datasets Plugin entrypoint for Brain Harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.hf_datasets import (
    HF_DATASETS_SERVICE_KEY,
    DefaultHfDatasetsService,
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetsService,
    HfDatasetVaultCommit,
    HfStorageStrategy,
    HfTransformationSpec,
    HfTransformResult,
)

logger = structlog.get_logger(__name__)


class HfDatasetsPlugin(HarnessPlugin, HfDatasetsService):
    """Brain Harness Plugin providing PyArrow zero-copy dataset streaming and profiling."""

    name = "domain.hf_datasets"
    version = "1.0.0"
    description = "Hugging Face Datasets engine: PyArrow zero-copy tables, lazy streaming iterables, lakehouse conversion, and schema profiling"
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._impl: HfDatasetsService = DefaultHfDatasetsService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [HF_DATASETS_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(HF_DATASETS_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # HfDatasetsService Protocol Implementation Delegating to Core Engine
    # -------------------------------------------------------------------------

    def inspect_dataset(
        self, path_or_name: str, split: str | None = None
    ) -> HfDatasetMetadata:
        return self._impl.inspect_dataset(path_or_name, split)

    def evaluate_storage_strategy(
        self,
        path_or_name: str,
        split: str | None = None,
        auto_stream_threshold_mb: int = 500,
    ) -> HfStorageStrategy:
        return self._impl.evaluate_storage_strategy(
            path_or_name, split, auto_stream_threshold_mb
        )

    def stream_sample(
        self, path_or_name: str, split: str = "train", max_samples: int = 10
    ) -> list[dict[str, Any]]:
        return self._impl.stream_sample(path_or_name, split, max_samples)

    def profile_schema(self, path_or_name: str) -> list[HfColumnSchema]:
        return self._impl.profile_schema(path_or_name)

    def transform_dataset(
        self, input_path: str, output_path: str, spec: HfTransformationSpec
    ) -> HfTransformResult:
        return self._impl.transform_dataset(input_path, output_path, spec)

    def convert_format(
        self, input_path: str, output_path: str, target_format: str = "parquet"
    ) -> HfTransformResult:
        return self._impl.convert_format(input_path, output_path, target_format)

    def commit_to_vault(
        self,
        dataset_name: str,
        metadata: HfDatasetMetadata,
        schemas: list[HfColumnSchema],
        vault_root: str | None = None,
    ) -> HfDatasetVaultCommit:
        return self._impl.commit_to_vault(dataset_name, metadata, schemas, vault_root)


# Module-level singleton per Rule 45
plugin = HfDatasetsPlugin()


# Top-level entrypoint functions declared in plugin.json for AST inspection & tool resolution
def hf_inspect_dataset(
    path_or_name: str, split: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Inspect dataset splits, features, row counts, and metadata without full data pull."""
    meta = plugin.inspect_dataset(path_or_name, split)
    return {
        "status": "ok",
        "name": meta.name,
        "split": meta.split,
        "num_rows": meta.num_rows,
        "features": meta.features,
        "format": meta.format,
        "byte_size": meta.byte_size,
        "is_streaming": meta.is_streaming,
    }


def hf_evaluate_storage_strategy(
    path_or_name: str,
    split: str | None = None,
    auto_stream_threshold_mb: int = 500,
    **kwargs: Any,
) -> dict[str, Any]:
    """Evaluate dataset footprint and select between memory-mapped Arrow and streaming iterators."""
    strat = plugin.evaluate_storage_strategy(
        path_or_name, split, auto_stream_threshold_mb
    )
    return {
        "status": "ok",
        "strategy": strat.strategy,
        "reason": strat.reason,
        "estimated_bytes": strat.estimated_bytes,
        "recommended_batch_size": strat.recommended_batch_size,
        "recommended_workers": strat.recommended_workers,
        "requires_streaming": strat.requires_streaming,
    }


def hf_stream_sample(
    path_or_name: str, split: str = "train", max_samples: int = 10, **kwargs: Any
) -> dict[str, Any]:
    """Lazily sample N records from a streaming dataset iterator."""
    records = plugin.stream_sample(path_or_name, split, max_samples)
    return {
        "status": "ok",
        "source": path_or_name,
        "split": split,
        "sample_count": len(records),
        "records": records,
    }


def hf_profile_schema(path_or_name: str, **kwargs: Any) -> dict[str, Any]:
    """Extract detailed column schemas, Arrow types, nullability, and sample values."""
    schemas = plugin.profile_schema(path_or_name)
    return {
        "status": "ok",
        "source": path_or_name,
        "column_count": len(schemas),
        "columns": [
            {
                "name": s.name,
                "arrow_type": s.arrow_type,
                "is_nullable": s.is_nullable,
                "feature_type": s.feature_type,
                "sample_values": list(s.sample_values),
            }
            for s in schemas
        ],
    }


def hf_transform_dataset(
    input_path: str,
    output_path: str,
    filter_field: str | None = None,
    filter_op: str | None = None,
    filter_value: Any = None,
    select_columns: list[str] | tuple[str, ...] | None = None,
    batch_size: int = 100,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute lazy filtering, column projection, and batch transformation."""
    spec = HfTransformationSpec(
        filter_field=filter_field,
        filter_op=filter_op,
        filter_value=filter_value,
        select_columns=tuple(select_columns) if select_columns else (),
        batch_size=batch_size,
    )
    res = plugin.transform_dataset(input_path, output_path, spec)
    return {
        "status": res.status,
        "rows_processed": res.rows_processed,
        "execution_time_ms": res.execution_time_ms,
        "cache_fingerprint": res.cache_fingerprint,
        "output_path": res.output_path,
    }


def hf_convert_format(
    input_path: str, output_path: str, target_format: str = "parquet", **kwargs: Any
) -> dict[str, Any]:
    """Convert dataset file between CSV, JSON, Arrow, and Parquet lakehouse formats."""
    res = plugin.convert_format(input_path, output_path, target_format)
    return {
        "status": res.status,
        "rows_processed": res.rows_processed,
        "execution_time_ms": res.execution_time_ms,
        "cache_fingerprint": res.cache_fingerprint,
        "output_path": res.output_path,
    }


def hf_commit_to_vault(
    dataset_name: str,
    input_path: str,
    split: str = "train",
    vault_root: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40)."""
    meta = plugin.inspect_dataset(input_path, split)
    schemas = plugin.profile_schema(input_path)
    commit = plugin.commit_to_vault(dataset_name, meta, schemas, vault_root)
    return {
        "status": "ok",
        "ki_id": commit.ki_id,
        "title": commit.title,
        "metadata_path": commit.metadata_path,
        "summary_path": commit.summary_path,
        "cache_fingerprint": commit.cache_fingerprint,
        "features_count": commit.features_count,
        "total_rows": commit.total_rows,
    }
