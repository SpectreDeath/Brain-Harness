"""REA Native Binary Inspection & Reverse Engineering Plugin for Brain Harness.

Deepened architecture decomposing native binary layout (pure-Python ELF/PE),
WebAssembly inspection (WABT/pure-Python), EVM bytecode disassembly,
and decompiler orchestration into focused domain sub-engines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.rea_native import (
    REA_NATIVE_KEY,
    BatchDecompileReport,
    CallGraphReport,
    ElfLayoutReport,
    EvmInterfaceReport,
    FunctionAnnotationReport,
    LoadImageReport,
    ReaNativeService,
    WasmInspectReport,
)
from plugins.security_and_forensics.rea_native.engine import (
    BinaryLayoutEngine,
    DecompilerEngine,
    EvmEngine,
    NativeAnalysisSessionCache,
    WasmEngine,
)

logger = structlog.get_logger(__name__)


# -----------------------------------------------------------------------------
# Deepened Domain Engine Coordinating Specialized Sub-Engines
# -----------------------------------------------------------------------------


class ReaNativeEngine:
    """Coordinating domain facade delegating to specialized binary layout, wasm, evm, and decompiler engines."""

    def __init__(
        self,
        ghidra_headless_path: str | None = None,
        wabt_wasm2wat_path: str | None = None,
        session_cache: NativeAnalysisSessionCache | None = None,
    ) -> None:
        self.session_cache = session_cache or NativeAnalysisSessionCache()
        self.layout_engine = BinaryLayoutEngine(session_cache=self.session_cache)
        self.wasm_engine = WasmEngine(wabt_wasm2wat_path=wabt_wasm2wat_path)
        self.evm_engine = EvmEngine()
        self.decompiler_engine = DecompilerEngine(
            ghidra_headless_path=ghidra_headless_path,
            session_cache=self.session_cache,
        )

    @property
    def ghidra_headless_path(self) -> str | None:
        return self.decompiler_engine.ghidra_headless_path

    @property
    def wabt_wasm2wat_path(self) -> str | None:
        return self.wasm_engine.wabt_wasm2wat_path

    # --- Decompiler Operations ---

    def batch_decompile(
        self,
        target_path: str,
        symbols: list[str],
        provider: str = "ghidra",
    ) -> dict[str, Any]:
        """Decompile procedure symbols concurrently via headless decompiler provider."""
        return self.decompiler_engine.batch_decompile(
            target_path=target_path, symbols=symbols, provider=provider
        )

    def call_graph(
        self,
        target_path: str,
        entry_symbol: str,
        depth: int = 3,
        direction: str = "callee",
    ) -> dict[str, Any]:
        """Traverse caller or callee relationships from a procedure entrypoint."""
        return self.decompiler_engine.call_graph(
            target_path=target_path,
            entry_symbol=entry_symbol,
            depth=depth,
            direction=direction,
        )

    def annotate_native_function(
        self,
        target_path: str,
        address: str,
        name: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Atomically update a function name and/or entry comment in the session database."""
        return self.decompiler_engine.annotate_function(
            target_path=target_path, address=address, name=name, comment=comment
        )

    # --- Binary Layout & Mitigations ---

    def elf_layout(
        self,
        target_path: str,
        checksec: bool = True,
    ) -> dict[str, Any]:
        """Inspect binary layout, sections, exports, and exploit mitigations."""
        return self.layout_engine.elf_layout(target_path=target_path, checksec=checksec)

    def inspect_native_load_image(
        self,
        target_path: str,
    ) -> dict[str, Any]:
        """Verify a loaded DOS MZ or COM image against its target snapshot."""
        return self.layout_engine.inspect_load_image(target_path=target_path)

    # --- WebAssembly Inspection ---

    def wasm_inspect(
        self,
        wasm_path: str,
        emit_wat: bool = True,
    ) -> dict[str, Any]:
        """Validate and inspect WebAssembly binaries via WABT 1.0.42."""
        return self.wasm_engine.wasm_inspect(wasm_path=wasm_path, emit_wat=emit_wat)

    # --- EVM Bytecode Disassembly ---

    def evm_interface(
        self,
        bytecode_hex: str,
        resolve_signatures: bool = True,
    ) -> dict[str, Any]:
        """Parse flat EVM bytecode, extract 4-byte dispatch selectors, and resolve ABI signatures."""
        return self.evm_engine.evm_interface(
            bytecode_hex=bytecode_hex, resolve_signatures=resolve_signatures
        )


_GLOBAL_ENGINE = ReaNativeEngine()


# -----------------------------------------------------------------------------
# Top-Level Entrypoint Tool Handlers Matching Manifest Signatures
# -----------------------------------------------------------------------------


def rea_native_batch_decompile(
    target_path: str,
    symbols: list[str],
    provider: str = "ghidra",
) -> dict[str, Any]:
    """Decompile one or more procedure symbols concurrently via headless Ghidra, Hopper, or IDA."""
    return _GLOBAL_ENGINE.batch_decompile(target_path=target_path, symbols=symbols, provider=provider)


def rea_native_call_graph(
    target_path: str,
    entry_symbol: str,
    depth: int = 3,
    direction: str = "callee",
) -> dict[str, Any]:
    """Traverse caller or callee relationships from a procedure entrypoint."""
    return _GLOBAL_ENGINE.call_graph(target_path=target_path, entry_symbol=entry_symbol, depth=depth, direction=direction)


def rea_native_elf_layout(
    target_path: str,
    checksec: bool = True,
) -> dict[str, Any]:
    """Offline static binary inspection via pwntools: section map, symbols, and exploit mitigations."""
    return _GLOBAL_ENGINE.elf_layout(target_path=target_path, checksec=checksec)


def rea_native_wasm_inspect(
    wasm_path: str,
    emit_wat: bool = True,
) -> dict[str, Any]:
    """Validate and inspect WebAssembly binaries via WABT 1.0.42."""
    return _GLOBAL_ENGINE.wasm_inspect(wasm_path=wasm_path, emit_wat=emit_wat)


def rea_native_evm_interface(
    bytecode_hex: str,
    resolve_signatures: bool = True,
) -> dict[str, Any]:
    """Parse flat EVM bytecode, extract 4-byte dispatch selectors, and resolve ABI signatures."""
    return _GLOBAL_ENGINE.evm_interface(bytecode_hex=bytecode_hex, resolve_signatures=resolve_signatures)


def rea_native_annotate_function(
    target_path: str,
    address: str,
    name: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Atomically update a function name and/or entry comment in the Ghidra session database."""
    return _GLOBAL_ENGINE.annotate_native_function(target_path=target_path, address=address, name=name, comment=comment)


def rea_native_inspect_load_image(
    target_path: str,
) -> dict[str, Any]:
    """Verify a loaded DOS MZ or COM image against its immutable target snapshot."""
    return _GLOBAL_ENGINE.inspect_native_load_image(target_path=target_path)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------


class ReaNativePlugin(HarnessPlugin, ReaNativeService):
    """Brain Harness Plugin providing native binary reverse engineering capabilities."""

    name = "plugin.rea_native"
    version = "1.0.0"
    description = (
        "REA native binary reverse engineering: Ghidra/Hopper/IDA decompilation, "
        "call graphs, pwntools ELF layout, WABT 1.0.42 WASM inspection, and EVM interface parsing."
    )
    trusted = True

    def __init__(self, engine: ReaNativeEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [REA_NATIVE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(REA_NATIVE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation Delegations
    # -------------------------------------------------------------------------

    def batch_decompile(
        self,
        target_path: str,
        symbols: list[str],
        provider: str = "ghidra",
    ) -> dict[str, Any]:
        return self._engine.batch_decompile(target_path=target_path, symbols=symbols, provider=provider)

    def call_graph(
        self,
        target_path: str,
        entry_symbol: str,
        depth: int = 3,
        direction: str = "callee",
    ) -> dict[str, Any]:
        return self._engine.call_graph(target_path=target_path, entry_symbol=entry_symbol, depth=depth, direction=direction)

    def elf_layout(
        self,
        target_path: str,
        checksec: bool = True,
    ) -> dict[str, Any]:
        return self._engine.elf_layout(target_path=target_path, checksec=checksec)

    def wasm_inspect(
        self,
        wasm_path: str,
        emit_wat: bool = True,
    ) -> dict[str, Any]:
        return self._engine.wasm_inspect(wasm_path=wasm_path, emit_wat=emit_wat)

    def evm_interface(
        self,
        bytecode_hex: str,
        resolve_signatures: bool = True,
    ) -> dict[str, Any]:
        return self._engine.evm_interface(bytecode_hex=bytecode_hex, resolve_signatures=resolve_signatures)

    def annotate_native_function(
        self,
        target_path: str,
        address: str,
        name: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        return self._engine.annotate_native_function(target_path=target_path, address=address, name=name, comment=comment)

    def inspect_native_load_image(
        self,
        target_path: str,
    ) -> dict[str, Any]:
        return self._engine.inspect_native_load_image(target_path=target_path)


plugin = ReaNativePlugin()
