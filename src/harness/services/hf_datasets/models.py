"""Slotted and frozen domain models for Hugging Face Datasets operations (Rule 12)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class HfDatasetMetadata:
    """Immutable metadata describing a discovered or loaded dataset."""

    name: str
    split: str
    num_rows: int
    features: dict[str, str] = field(default_factory=dict)
    format: str = "arrow"
    byte_size: int = 0
    is_streaming: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("HfDatasetMetadata.name cannot be empty")
        if self.num_rows < 0:
            raise ValueError("HfDatasetMetadata.num_rows must be non-negative")


@dataclass(slots=True, frozen=True)
class HfStreamConfig:
    """Immutable operational configuration for lazy streaming iterator pipelines."""

    batch_size: int = 100
    buffer_size: int = 1000
    num_shards: int = 1
    max_samples: int = 100
    stream_url: str = ""

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("HfStreamConfig.batch_size must be positive")
        if self.max_samples <= 0:
            raise ValueError("HfStreamConfig.max_samples must be positive")


@dataclass(slots=True, frozen=True)
class HfColumnSchema:
    """Immutable schema description for an individual dataset column."""

    name: str
    arrow_type: str
    is_nullable: bool = True
    feature_type: str = "Value"
    sample_values: tuple[Any, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("HfColumnSchema.name cannot be empty")


@dataclass(slots=True, frozen=True)
class HfTransformResult:
    """Immutable outcome report of a dataset format conversion or mapping step."""

    status: str
    rows_processed: int
    execution_time_ms: float
    cache_fingerprint: str
    output_path: str = ""

    def __post_init__(self) -> None:
        if not self.status:
            raise ValueError("HfTransformResult.status cannot be empty")


@dataclass(slots=True, frozen=True)
class HfStorageStrategy:
    """Immutable recommendation evaluating Arrow memory-map vs. lazy generator streaming."""

    strategy: str  # 'mmap_arrow' or 'lazy_stream'
    reason: str
    estimated_bytes: int
    recommended_batch_size: int
    recommended_workers: int
    requires_streaming: bool

    def __post_init__(self) -> None:
        if not self.strategy:
            raise ValueError("HfStorageStrategy.strategy cannot be empty")
        if self.recommended_batch_size <= 0:
            raise ValueError(
                "HfStorageStrategy.recommended_batch_size must be positive"
            )


@dataclass(slots=True, frozen=True)
class HfTransformationSpec:
    """Declarative specification for lazy filtering, column projection, and mapping."""

    filter_field: str | None = None
    filter_op: str | None = (
        None  # 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'contains', 'in'
    )
    filter_value: Any = None
    select_columns: tuple[str, ...] = ()
    rename_columns: tuple[tuple[str, str], ...] = ()
    batch_size: int = 100

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("HfTransformationSpec.batch_size must be positive")


@dataclass(slots=True, frozen=True)
class HfDatasetVaultCommit:
    """Immutable audit record confirming dataset catalog commitment to Knowledge Vault."""

    ki_id: str
    title: str
    summary: str
    metadata_path: str
    summary_path: str
    cache_fingerprint: str
    features_count: int
    total_rows: int

    def __post_init__(self) -> None:
        if not self.ki_id:
            raise ValueError("HfDatasetVaultCommit.ki_id cannot be empty")
        if not self.title:
            raise ValueError("HfDatasetVaultCommit.title cannot be empty")
