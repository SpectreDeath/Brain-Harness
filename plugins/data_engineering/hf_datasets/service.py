"""Hugging Face Datasets Service Adapter & Backward Compatibility Re-export."""

from __future__ import annotations

from harness.services.hf_datasets import (
    DefaultHfDatasetsService,
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetsService,
    HfDatasetVaultCommit,
    HfStorageStrategy,
    HfStreamConfig,
    HfTransformationSpec,
    HfTransformResult,
)

# Authoritative engine re-export for backward-compatibility with legacy imports
HfDatasetsServiceImpl = DefaultHfDatasetsService

__all__ = [
    "DefaultHfDatasetsService",
    "HfColumnSchema",
    "HfDatasetMetadata",
    "HfDatasetVaultCommit",
    "HfDatasetsService",
    "HfDatasetsServiceImpl",
    "HfStorageStrategy",
    "HfStreamConfig",
    "HfTransformResult",
    "HfTransformationSpec",
]
