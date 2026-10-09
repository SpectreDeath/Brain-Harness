"""Authoritative service protocol and ServiceKey for Hugging Face Datasets operations (Rule 49)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

from .models import (
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetVaultCommit,
    HfStorageStrategy,
    HfTransformationSpec,
    HfTransformResult,
)


@runtime_checkable
class HfDatasetsService(Protocol):
    """Authoritative service protocol for Hugging Face Datasets operations."""

    def inspect_dataset(
        self, path_or_name: str, split: str | None = None
    ) -> HfDatasetMetadata:
        """Inspect schema, splits, and features without downloading or loading entire dataset."""
        ...

    def evaluate_storage_strategy(
        self,
        path_or_name: str,
        split: str | None = None,
        auto_stream_threshold_mb: int = 500,
    ) -> HfStorageStrategy:
        """Evaluate physical footprint and select between memory-mapped Arrow and streaming."""
        ...

    def stream_sample(
        self, path_or_name: str, split: str = "train", max_samples: int = 10
    ) -> list[dict[str, Any]]:
        """Lazily sample N records from a streaming dataset iterator without eager memory blowout."""
        ...

    def profile_schema(self, path_or_name: str) -> list[HfColumnSchema]:
        """Profile and return comprehensive column schemas and Arrow data types."""
        ...

    def transform_dataset(
        self, input_path: str, output_path: str, spec: HfTransformationSpec
    ) -> HfTransformResult:
        """Execute lazy filtering, column projection, and batched transformations."""
        ...

    def convert_format(
        self, input_path: str, output_path: str, target_format: str = "parquet"
    ) -> HfTransformResult:
        """Convert datasets between JSON, CSV, Arrow, and Parquet columnar lakehouse formats."""
        ...

    def commit_to_vault(
        self,
        dataset_name: str,
        metadata: HfDatasetMetadata,
        schemas: list[HfColumnSchema],
        vault_root: str | None = None,
    ) -> HfDatasetVaultCommit:
        """Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40)."""
        ...


HF_DATASETS_SERVICE_KEY: ServiceKey[HfDatasetsService] = ServiceKey(
    "service.hf_datasets"
)
