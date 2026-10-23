"""REA Managed Runtime Inspection Service Protocol, models, and ServiceKey.

Elevates .NET PE/CLI, Unity IL2CPP, Python pyc, and AI model artifact (GGUF/safetensors)
inspection workflows into an IoC micro-kernel service seam.
Synthesized from REA (morluto/rea) managed and model artifact domain engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey


# -----------------------------------------------------------------------------
# Slotted & Frozen Domain Models with Dictionary Compatibility (Rule 12)
# -----------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ReaManagedReportBase:
    """Base slotted, frozen dataclass with dictionary-style read compatibility."""

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


@dataclass(slots=True, frozen=True)
class ManagedMember(ReaManagedReportBase):
    """Declared member (type, method, or field) in a managed PE/CLI artifact."""

    name: str
    member_type: str  # "type", "method", "field"
    parent: str | None = None
    flags: int = 0
    token: int = 0


@dataclass(slots=True, frozen=True)
class ManagedArtifactReport(ReaManagedReportBase):
    """Result envelope for .NET PE/CLI binary inspection."""

    status: str
    target_path: str
    is_cli: bool = False
    runtime_version: str = ""
    metadata_streams: list[str] = field(default_factory=list)
    types_count: int = 0
    methods_count: int = 0
    members: list[ManagedMember] = field(default_factory=list)
    has_strong_name: bool = False
    error: str | None = None


@dataclass(slots=True, frozen=True)
class PInvokeDeclaration(ReaManagedReportBase):
    """Declared P/Invoke or native boundary import."""

    module_name: str
    entry_point: str
    calling_convention: str = "winapi"
    exact_spelling: bool = False


@dataclass(slots=True, frozen=True)
class ManagedBoundariesReport(ReaManagedReportBase):
    """Result envelope for PE/CLI native interop boundaries and P/Invoke declarations."""

    status: str
    target_path: str
    module_refs: list[str] = field(default_factory=list)
    pinvokes: list[PInvokeDeclaration] = field(default_factory=list)
    unmanaged_exports_count: int = 0
    error: str | None = None


@dataclass(slots=True, frozen=True)
class Il2cppMetadataReport(ReaManagedReportBase):
    """Result envelope for Unity IL2CPP global-metadata.dat parsing."""

    status: str
    metadata_path: str
    magic_valid: bool = False
    version: int = 0
    string_literals_count: int = 0
    methods_count: int = 0
    type_definitions_count: int = 0
    images_count: int = 0
    sample_strings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True, frozen=True)
class ModelTensorDescriptor(ReaManagedReportBase):
    """Tensor descriptor in an AI model artifact (GGUF or safetensors)."""

    name: str
    type_name: str
    shape: list[int] = field(default_factory=list)
    offset: int = 0
    byte_length: int = 0


@dataclass(slots=True, frozen=True)
class ModelArtifactReport(ReaManagedReportBase):
    """Result envelope for zero-allocation AI model artifact inspection."""

    status: str
    model_path: str
    format: str = "unknown"  # "gguf_v2", "gguf_v3", "safetensors"
    version: int = 0
    tensor_count: int = 0
    metadata_kv_count: int = 0
    metadata_preview: dict[str, Any] = field(default_factory=dict)
    tensors: list[ModelTensorDescriptor] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True, frozen=True)
class PycInspectReport(ReaManagedReportBase):
    """Result envelope for CPython .pyc bytecode disassembly."""

    status: str
    pyc_path: str
    magic: int = 0
    cpython_version: str = ""
    timestamp: int = 0
    code_object_name: str = "<module>"
    instruction_count: int = 0
    sample_disassembly: list[str] = field(default_factory=list)
    error: str | None = None


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Service Protocol & Key
# -----------------------------------------------------------------------------


@runtime_checkable
class ReaManagedRuntimeService(Protocol):
    """Protocol for managed runtime, bytecode, and AI model artifact inspection."""

    def inspect_managed_artifact(
        self,
        target_path: str,
        extract_members: bool = True,
    ) -> ManagedArtifactReport | dict[str, Any]:
        """Inspect a PE/CLI or .NET DLL without loading it as a live assembly."""
        ...

    def inspect_managed_native_boundaries(
        self,
        target_path: str,
    ) -> ManagedBoundariesReport | dict[str, Any]:
        """Inspect PE/CLI ModuleRef, ImplMap, and P/Invoke declarations."""
        ...

    def inspect_il2cpp_metadata(
        self,
        metadata_path: str,
        max_records: int = 100,
    ) -> Il2cppMetadataReport | dict[str, Any]:
        """Parse Unity IL2CPP global-metadata.dat (versions 24, 27, 29, 31, 39)."""
        ...

    def inspect_model_artifact(
        self,
        model_path: str,
        preview_tensors: int = 50,
    ) -> ModelArtifactReport | dict[str, Any]:
        """Inspect GGUF v2/v3 or safetensors headers using direct O(1) byte seeks."""
        ...

    def inspect_python_pyc(
        self,
        pyc_path: str,
        disassemble: bool = True,
    ) -> PycInspectReport | dict[str, Any]:
        """Inspect local CPython 3.7-3.13 .pyc bytecode files and disassemble opcodes."""
        ...


REA_MANAGED_RUNTIME_KEY: ServiceKey[ReaManagedRuntimeService] = ServiceKey(
    "service.rea_managed_runtime"
)


def resolve_rea_managed_runtime(ctx: ServiceContext) -> ReaManagedRuntimeService | None:
    """Resolve ReaManagedRuntimeService from context if registered."""
    return ctx.optional(REA_MANAGED_RUNTIME_KEY)
