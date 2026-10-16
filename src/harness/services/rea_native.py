"""REA Native Inspection Service Protocol, models, and ServiceKey.

Elevates native binary, assembly, disassembly, bytecode inspection,
and reverse engineering workflows into an IoC micro-kernel service seam.
Synthesized from REA (morluto/rea) native modules (Ghidra, Hopper, IDA, WABT, pwntools, EVM).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey


# -----------------------------------------------------------------------------
# Typed Domain Models & Response Envelopes
# -----------------------------------------------------------------------------


class ReaReportBase(BaseModel):
    """Base model with dictionary-style backward compatibility."""

    def __getitem__(self, key: str) -> Any:
        try:
            val = getattr(self, key)
            return val
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class DecompileProcedure(ReaReportBase):
    """Decompiled procedure information."""

    symbol: str
    address: str = ""
    pseudocode: str = ""
    status: str = "ok"
    error: str | None = None


class BatchDecompileReport(ReaReportBase):
    """Result envelope for batch decompilation."""

    status: str = "ok"
    provider: str = "ghidra"
    target_path: str
    procedures: list[DecompileProcedure] = Field(default_factory=list)
    error: str | None = None


class CallGraphEdge(ReaReportBase):
    """Directed edge in a call graph."""

    caller: str
    callee: str
    call_type: str = "direct"


class CallGraphReport(ReaReportBase):
    """Result envelope for call graph traversal."""

    status: str = "ok"
    entry_symbol: str
    depth: int = 3
    direction: str = "callee"
    nodes: list[str] = Field(default_factory=list)
    edges: list[CallGraphEdge] = Field(default_factory=list)
    error: str | None = None


class BinaryMitigations(ReaReportBase):
    """Exploit mitigation flags."""

    nx: bool = True
    canary: bool = True
    pie: bool = True
    relro: str = "full"
    fortify: bool = False


class ElfLayoutReport(ReaReportBase):
    """Result envelope for ELF/PE binary layout and checksec analysis."""

    status: str = "ok"
    target_path: str
    arch: str = "x86_64"
    format: str = "ELF"
    sections: list[dict[str, Any]] = Field(default_factory=list)
    imported_symbols: list[str] = Field(default_factory=list)
    exported_symbols: list[str] = Field(default_factory=list)
    mitigations: BinaryMitigations | None = None
    error: str | None = None


class WasmInspectReport(ReaReportBase):
    """Result envelope for WABT WebAssembly inspection."""

    status: str = "ok"
    wasm_path: str
    wabt_version: str = "1.0.42"
    sections: list[dict[str, Any]] = Field(default_factory=list)
    imports: list[dict[str, str]] = Field(default_factory=list)
    exports: list[dict[str, str]] = Field(default_factory=list)
    wat_disassembly: str | None = None
    error: str | None = None


class EvmInterfaceReport(ReaReportBase):
    """Result envelope for EVM bytecode parsing and interface extraction."""

    status: str = "ok"
    selectors: list[dict[str, Any]] = Field(default_factory=list)
    opcodes_count: int = 0
    resolved_signatures: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


class FunctionAnnotationReport(ReaReportBase):
    """Result envelope for native function annotation."""

    status: str = "ok"
    target_path: str
    address: str
    name: str | None = None
    comment: str | None = None
    error: str | None = None


class LoadImageReport(ReaReportBase):
    """Result envelope for DOS MZ/COM load image inspection."""

    status: str = "ok"
    target_path: str
    format: str = "MZ"
    header_digest: str = ""
    memory_digest: str = ""
    relocations_count: int = 0
    matches_snapshot: bool = True
    error: str | None = None


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Service Protocol & Key
# -----------------------------------------------------------------------------


@runtime_checkable
class ReaNativeService(Protocol):
    """Protocol for native reverse engineering, decompilation, and binary analysis."""

    def batch_decompile(
        self,
        target_path: str,
        symbols: list[str],
        provider: str = "ghidra",
    ) -> BatchDecompileReport | dict[str, Any]:
        """Decompile one or more procedure symbols concurrently via headless Ghidra, Hopper, or IDA."""
        ...

    def call_graph(
        self,
        target_path: str,
        entry_symbol: str,
        depth: int = 3,
        direction: str = "callee",
    ) -> CallGraphReport | dict[str, Any]:
        """Traverse caller or callee relationships from a procedure entrypoint."""
        ...

    def elf_layout(
        self,
        target_path: str,
        checksec: bool = True,
    ) -> ElfLayoutReport | dict[str, Any]:
        """Offline static binary inspection: section map, symbols, and exploit mitigations."""
        ...

    def wasm_inspect(
        self,
        wasm_path: str,
        emit_wat: bool = True,
    ) -> WasmInspectReport | dict[str, Any]:
        """Validate and inspect WebAssembly binaries via WABT 1.0.42."""
        ...

    def evm_interface(
        self,
        bytecode_hex: str,
        resolve_signatures: bool = True,
    ) -> EvmInterfaceReport | dict[str, Any]:
        """Parse flat EVM bytecode, extract 4-byte selectors, and resolve ABI signatures."""
        ...

    def annotate_native_function(
        self,
        target_path: str,
        address: str,
        name: str | None = None,
        comment: str | None = None,
    ) -> FunctionAnnotationReport | dict[str, Any]:
        """Update a function name and/or entry comment in the session database."""
        ...

    def inspect_native_load_image(
        self,
        target_path: str,
    ) -> LoadImageReport | dict[str, Any]:
        """Verify a loaded DOS MZ or COM image against its target snapshot."""
        ...


REA_NATIVE_KEY: ServiceKey[ReaNativeService] = ServiceKey("service.rea_native")


def resolve_rea_native(ctx: ServiceContext) -> ReaNativeService | None:
    """Resolve ReaNativeService from context if registered."""
    return ctx.optional(REA_NATIVE_KEY)
