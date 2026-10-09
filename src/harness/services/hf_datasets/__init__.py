"""Hugging Face Datasets Service subpackage — streaming, lakehouse formats, and schema profiling."""

from .models import (
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetVaultCommit,
    HfStorageStrategy,
    HfStreamConfig,
    HfTransformationSpec,
    HfTransformResult,
)
from .protocol import (
    HF_DATASETS_SERVICE_KEY,
    HfDatasetsService,
)
from .resolvers import resolve_hf_datasets_service
from .service import DefaultHfDatasetsService

__all__ = [
    "DefaultHfDatasetsService",
    "HF_DATASETS_SERVICE_KEY",
    "HfColumnSchema",
    "HfDatasetMetadata",
    "HfDatasetVaultCommit",
    "HfDatasetsService",
    "HfStorageStrategy",
    "HfStreamConfig",
    "HfTransformationSpec",
    "HfTransformResult",
    "resolve_hf_datasets_service",
]
