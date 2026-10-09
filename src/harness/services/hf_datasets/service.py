"""DefaultHfDatasetsService coordinator implementation conforming to HfDatasetsService."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .lakehouse import convert_format, write_records
from .models import (
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetVaultCommit,
    HfStorageStrategy,
    HfTransformationSpec,
    HfTransformResult,
)
from .profiler import (
    evaluate_storage_strategy,
    inspect_dataset,
    profile_schema,
    stream_sample,
)
from .protocol import HfDatasetsService
from .streamer import iter_records, probe_file_streaming
from .transforms import transform_dataset
from .vault import commit_to_vault


class DefaultHfDatasetsService(HfDatasetsService):
    """Production-grade Hugging Face Datasets engine with bounded streaming and lakehouse support."""

    def inspect_dataset(
        self, path_or_name: str, split: str | None = None
    ) -> HfDatasetMetadata:
        """Inspect schema, splits, and features without downloading or loading entire dataset."""
        return inspect_dataset(path_or_name, split)

    def evaluate_storage_strategy(
        self,
        path_or_name: str,
        split: str | None = None,
        auto_stream_threshold_mb: int = 500,
    ) -> HfStorageStrategy:
        """Evaluate physical footprint and select between memory-mapped Arrow and streaming."""
        return evaluate_storage_strategy(
            path_or_name, split, auto_stream_threshold_mb
        )

    def stream_sample(
        self, path_or_name: str, split: str = "train", max_samples: int = 10
    ) -> list[dict[str, Any]]:
        """Lazily sample N records without loading entire dataset into RAM."""
        return stream_sample(path_or_name, split, max_samples)

    def profile_schema(self, path_or_name: str) -> list[HfColumnSchema]:
        """Profile and return comprehensive column schemas and Arrow data types."""
        return profile_schema(path_or_name)

    def transform_dataset(
        self, input_path: str, output_path: str, spec: HfTransformationSpec
    ) -> HfTransformResult:
        """Execute lazy filtering, column projection, and batched transformations."""
        return transform_dataset(input_path, output_path, spec)

    def convert_format(
        self, input_path: str, output_path: str, target_format: str = "parquet"
    ) -> HfTransformResult:
        """Convert datasets between JSON, CSV, Arrow, and Parquet columnar lakehouse formats."""
        return convert_format(input_path, output_path, target_format)

    def commit_to_vault(
        self,
        dataset_name: str,
        metadata: HfDatasetMetadata,
        schemas: list[HfColumnSchema],
        vault_root: str | None = None,
    ) -> HfDatasetVaultCommit:
        """Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40)."""
        return commit_to_vault(dataset_name, metadata, schemas, vault_root)

    # Protected backward compatibility helper methods
    def _iter_records(
        self, path_or_name: str, max_records: int | None = None
    ) -> Iterator[dict[str, Any]]:
        return iter_records(path_or_name, max_records)

    def _probe_file_streaming(self, p: Path) -> tuple[dict[str, str], int]:
        return probe_file_streaming(p)

    def _write_records(
        self, out_p: Path, records: list[dict[str, Any]], fmt: str
    ) -> None:
        write_records(out_p, records, fmt)
