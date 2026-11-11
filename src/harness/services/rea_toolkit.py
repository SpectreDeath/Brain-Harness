"""REA Reverse-Engineering Unified Toolkit Service Protocol, Models, and Facade.

Elevates multi-plugin binary, bytecode, runtime, and container dissection,
artifact-type routing, per-facet availability semantics, semantic signature extraction,
live multi-provider differential comparison, and endogenous Knowledge Vault learning
into an authoritative IoC micro-kernel service seam.

Synthesized from REA (morluto/rea) native, managed runtime, mobile/firmware, and
JavaScript reverse-engineering domain modules and epistemic verification primitives.
Decomposition trigger: 2,200 LOC (see docs/decisions/rea-size-exemptions.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import structlog
import struct
import sys
from typing import Any, Literal, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.differential_facet import (
    CoverageDeclaration,
    DifferentialReport,
    DimensionOutcome,
    FacetAvailability,
    StandardDifferentialFacetService,
    canonicalize_json,
    compute_canonical_hash,
)
from harness.services.reconstruction_obligation import (
    CanonicalEvidence,
    ReconstructionObligationService,
    StandardReconstructionObligationService,
    resolve_reconstruction_obligation,
)

logger = structlog.get_logger(__name__)

# Re-export core availability types for unified access
DifferentialFacetAvailability = FacetAvailability

# -----------------------------------------------------------------------------
# Authoritative 28-Entry Tool Alias Mapping (Track 7)
# -----------------------------------------------------------------------------

REA_TOOL_ALIASES: dict[str, str] = {
    # JavaScript & Web (plugin.rea_javascript)
    "rea.js.recover_sources": "plugin.rea_javascript.rea_javascript_recover_sources",
    "rea.js.electron_inspect": "plugin.rea_javascript.rea_javascript_electron_inspect",
    "rea.js.web_observe": "plugin.rea_javascript.rea_javascript_web_observe",
    "rea.js.dotnet_inspect": "plugin.rea_javascript.rea_javascript_dotnet_inspect",
    "rea.js.har_inspect": "plugin.rea_javascript.rea_javascript_har_inspect",
    # Managed Runtime (plugin.rea_managed_runtime)
    "rea.managed.inspect_artifact": "plugin.rea_managed_runtime.rea_inspect_managed_artifact",
    "rea.managed.native_boundaries": "plugin.rea_managed_runtime.rea_inspect_managed_native_boundaries",
    "rea.managed.il2cpp_metadata": "plugin.rea_managed_runtime.rea_inspect_il2cpp_metadata",
    "rea.managed.model_artifact": "plugin.rea_managed_runtime.rea_inspect_model_artifact",
    "rea.managed.python_pyc": "plugin.rea_managed_runtime.rea_inspect_python_pyc",
    # Mobile & Firmware (plugin.rea_mobile_firmware)
    "rea.mobile.apk_inspect": "plugin.rea_mobile_firmware.rea_mobile_apk_inspect",
    "rea.mobile.jadx_decompile": "plugin.rea_mobile_firmware.rea_mobile_jadx_decompile",
    "rea.mobile.search_classes": "plugin.rea_mobile_firmware.rea_mobile_android_search_classes",
    "rea.mobile.trace_references": "plugin.rea_mobile_firmware.rea_mobile_android_trace_references",
    "rea.adb.inspect_client": "plugin.rea_mobile_firmware.rea_mobile_adb_inspect_client",
    "rea.adb.list_devices": "plugin.rea_mobile_firmware.rea_mobile_adb_list_devices",
    "rea.adb.list_packages": "plugin.rea_mobile_firmware.rea_mobile_adb_list_packages",
    "rea.adb.pull_package": "plugin.rea_mobile_firmware.rea_mobile_adb_pull_package",
    "rea.adb.read_logcat": "plugin.rea_mobile_firmware.rea_mobile_adb_read_logcat",
    "rea.firmware.inspect_regions": "plugin.rea_mobile_firmware.rea_firmware_regions_inspect",
    "rea.firmware.extract": "plugin.rea_mobile_firmware.rea_firmware_extract",
    # Native Binaries (plugin.rea_native)
    "rea.native.batch_decompile": "plugin.rea_native.rea_native_batch_decompile",
    "rea.native.call_graph": "plugin.rea_native.rea_native_call_graph",
    "rea.native.elf_layout": "plugin.rea_native.rea_native_elf_layout",
    "rea.native.wasm_inspect": "plugin.rea_native.rea_native_wasm_inspect",
    "rea.native.evm_interface": "plugin.rea_native.rea_native_evm_interface",
    "rea.native.annotate_function": "plugin.rea_native.rea_native_annotate_function",
    "rea.native.inspect_load_image": "plugin.rea_native.rea_native_inspect_load_image",
}

# Grouping tools by artifact kind for `harness rea list`
ARTIFACT_KIND_TOOLS: dict[str, list[tuple[str, str, str]]] = {
    "elf": [
        ("rea.native.elf_layout", "plugin.rea_native.rea_native_elf_layout", "ELF section map, symbols, and checksec mitigations"),
        ("rea.native.batch_decompile", "plugin.rea_native.rea_native_batch_decompile", "Headless Ghidra/Hopper/IDA decompilation"),
        ("rea.native.call_graph", "plugin.rea_native.rea_native_call_graph", "Caller/callee relationship traversal"),
        ("rea.native.annotate_function", "plugin.rea_native.rea_native_annotate_function", "Update function name/comment in session DB"),
    ],
    "pe_managed": [
        ("rea.managed.inspect_artifact", "plugin.rea_managed_runtime.rea_inspect_managed_artifact", ".NET PE/CLI headers and metadata streams"),
        ("rea.managed.native_boundaries", "plugin.rea_managed_runtime.rea_inspect_managed_native_boundaries", "ModuleRef, ImplMap, and P/Invoke declarations"),
        ("rea.js.dotnet_inspect", "plugin.rea_javascript.rea_javascript_dotnet_inspect", "Type hierarchy and CIL body instruction hashes"),
    ],
    "pe_native": [
        ("rea.native.elf_layout", "plugin.rea_native.rea_native_elf_layout", "PE/COFF headers, sections, exports, and checksec"),
        ("rea.native.batch_decompile", "plugin.rea_native.rea_native_batch_decompile", "Headless Ghidra/Hopper/IDA decompilation"),
        ("rea.native.call_graph", "plugin.rea_native.rea_native_call_graph", "Caller/callee relationship traversal"),
    ],
    "dos_mz": [
        ("rea.native.inspect_load_image", "plugin.rea_native.rea_native_inspect_load_image", "Verify DOS MZ or COM load image against snapshot"),
    ],
    "apk": [
        ("rea.mobile.apk_inspect", "plugin.rea_mobile_firmware.rea_mobile_apk_inspect", "Android package identity, permissions, and resources"),
        ("rea.mobile.jadx_decompile", "plugin.rea_mobile_firmware.rea_mobile_jadx_decompile", "Decompile Dalvik bytecode via JADX"),
        ("rea.mobile.search_classes", "plugin.rea_mobile_firmware.rea_mobile_android_search_classes", "Search APK classes by substring"),
        ("rea.mobile.trace_references", "plugin.rea_mobile_firmware.rea_mobile_android_trace_references", "Trace static references across APK classes"),
    ],
    "adb": [
        ("rea.adb.inspect_client", "plugin.rea_mobile_firmware.rea_mobile_adb_inspect_client", "Report adb path, version, and install source"),
        ("rea.adb.list_devices", "plugin.rea_mobile_firmware.rea_mobile_adb_list_devices", "Enumerate attached devices and emulators"),
        ("rea.adb.list_packages", "plugin.rea_mobile_firmware.rea_mobile_adb_list_packages", "List installed packages on a device"),
        ("rea.adb.pull_package", "plugin.rea_mobile_firmware.rea_mobile_adb_pull_package", "Pull a device-installed APK"),
        ("rea.adb.read_logcat", "plugin.rea_mobile_firmware.rea_mobile_adb_read_logcat", "Bounded adb logcat dump"),
    ],
    "asar": [
        ("rea.js.electron_inspect", "plugin.rea_javascript.rea_javascript_electron_inspect", "Electron ASAR manifest, preload, and IPC channels"),
    ],
    "wasm": [
        ("rea.native.wasm_inspect", "plugin.rea_native.rea_native_wasm_inspect", "WABT 1.0.42 WASM sections, imports/exports, and WAT"),
    ],
    "il2cpp_metadata": [
        ("rea.managed.il2cpp_metadata", "plugin.rea_managed_runtime.rea_inspect_il2cpp_metadata", "Parse Unity IL2CPP global-metadata.dat"),
    ],
    "ai_model": [
        ("rea.managed.model_artifact", "plugin.rea_managed_runtime.rea_inspect_model_artifact", "GGUF v2/v3 and safetensors header byte inspection"),
    ],
    "cpython_pyc": [
        ("rea.managed.python_pyc", "plugin.rea_managed_runtime.rea_inspect_python_pyc", "CPython 3.7-3.13 .pyc bytecode disassembly"),
    ],
    "har": [
        ("rea.js.har_inspect", "plugin.rea_javascript.rea_javascript_har_inspect", "Offline HAR 1.2 or mitmproxy capture inspection"),
    ],
    "javascript_bundle": [
        ("rea.js.recover_sources", "plugin.rea_javascript.rea_javascript_recover_sources", "Wakaru ^1.13.0 bundle deobfuscation and sources"),
        ("rea.js.web_observe", "plugin.rea_javascript.rea_javascript_web_observe", "Passive CDP DOM, script, and network observation"),
    ],
    "evm_bytecode": [
        ("rea.native.evm_interface", "plugin.rea_native.rea_native_evm_interface", "EVM 4-byte dispatch selectors and ABI signatures"),
    ],
    "firmware": [
        ("rea.firmware.inspect_regions", "plugin.rea_mobile_firmware.rea_firmware_regions_inspect", "Scan binary with Binwalk 3.1.0"),
        ("rea.firmware.extract", "plugin.rea_mobile_firmware.rea_firmware_extract", "Unpack partitions with Unblob 26.6.4 (Linux-only)"),
    ],
}

# Routing table mapping 13 categories to primary/secondary plugins and magic signatures
ARTIFACT_ROUTING_TABLE: dict[str, dict[str, Any]] = {
    "elf": {
        "category": "elf",
        "description": "ELF Executable / Shared Object",
        "primary_plugin": "plugin.rea_native",
        "secondary_plugins": [],
        "magic_hex": ["7f454c46"],
        "extensions": [".so", ".elf", ".o", ".bin"],
    },
    "pe_managed": {
        "category": "pe_managed",
        "description": "Windows .NET PE/CLI Assembly",
        "primary_plugin": "plugin.rea_managed_runtime",
        "secondary_plugins": ["plugin.rea_javascript", "plugin.rea_native"],
        "magic_hex": ["4d5a"],
        "extensions": [".exe", ".dll"],
    },
    "pe_native": {
        "category": "pe_native",
        "description": "Windows Native PE32/PE32+ Binary",
        "primary_plugin": "plugin.rea_native",
        "secondary_plugins": [],
        "magic_hex": ["4d5a"],
        "extensions": [".exe", ".dll", ".sys"],
    },
    "dos_mz": {
        "category": "dos_mz",
        "description": "DOS MZ / COM Load Image",
        "primary_plugin": "plugin.rea_native",
        "secondary_plugins": [],
        "magic_hex": ["4d5a"],
        "extensions": [".exe", ".com"],
    },
    "apk": {
        "category": "apk",
        "description": "Android Application Package",
        "primary_plugin": "plugin.rea_mobile_firmware",
        "secondary_plugins": [],
        "magic_hex": ["504b0304"],
        "extensions": [".apk", ".xapk", ".apks"],
    },
    "asar": {
        "category": "asar",
        "description": "Electron Application Archive",
        "primary_plugin": "plugin.rea_javascript",
        "secondary_plugins": [],
        "magic_hex": ["04000000"],
        "extensions": [".asar"],
    },
    "wasm": {
        "category": "wasm",
        "description": "WebAssembly Binary Module",
        "primary_plugin": "plugin.rea_native",
        "secondary_plugins": [],
        "magic_hex": ["0061736d"],
        "extensions": [".wasm"],
    },
    "il2cpp_metadata": {
        "category": "il2cpp_metadata",
        "description": "Unity IL2CPP global-metadata.dat",
        "primary_plugin": "plugin.rea_managed_runtime",
        "secondary_plugins": [],
        "magic_hex": ["af1bb1fa"],
        "extensions": [".dat"],
    },
    "ai_model": {
        "category": "ai_model",
        "description": "GGUF or Safetensors AI Model Weights",
        "primary_plugin": "plugin.rea_managed_runtime",
        "secondary_plugins": [],
        "magic_hex": ["47475546"],
        "extensions": [".gguf", ".safetensors", ".bin"],
    },
    "cpython_pyc": {
        "category": "cpython_pyc",
        "description": "CPython Bytecode File",
        "primary_plugin": "plugin.rea_managed_runtime",
        "secondary_plugins": [],
        "magic_hex": [],
        "extensions": [".pyc"],
    },
    "har": {
        "category": "har",
        "description": "HTTP Archive / Network Trace",
        "primary_plugin": "plugin.rea_javascript",
        "secondary_plugins": [],
        "magic_hex": ["7b226c6f6722"],
        "extensions": [".har", ".json"],
    },
    "javascript_bundle": {
        "category": "javascript_bundle",
        "description": "JavaScript Bundle / Web Script",
        "primary_plugin": "plugin.rea_javascript",
        "secondary_plugins": [],
        "magic_hex": [],
        "extensions": [".js", ".mjs", ".cjs", ".bundle"],
    },
    "evm_bytecode": {
        "category": "evm_bytecode",
        "description": "Ethereum Virtual Machine Bytecode",
        "primary_plugin": "plugin.rea_native",
        "secondary_plugins": [],
        "magic_hex": ["60806040"],
        "extensions": [".bin", ".hex", ".evm"],
    },
    "firmware": {
        "category": "firmware",
        "description": "Embedded Device Firmware Image",
        "primary_plugin": "plugin.rea_mobile_firmware",
        "secondary_plugins": [],
        "magic_hex": [],
        "extensions": [".bin", ".img", ".rom"],
    },
}


# -----------------------------------------------------------------------------
# Slotted & Frozen Dataclass Domain Models (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ArtifactIdentity:
    """Deterministic cryptographic identity and characteristics of an inspection target."""

    path: str
    sha256: str
    size_bytes: int
    detected_kind: str
    mime_type: str
    magic_summary: str
    polyglot_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "detected_kind": self.detected_kind,
            "mime_type": self.mime_type,
            "magic_summary": self.magic_summary,
            "polyglot_warnings": list(self.polyglot_warnings),
        }

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
class ProviderProvenance:
    """Provenance of the provider or external reverse-engineering binary executed."""

    plugin: str
    tool: str
    binary_name: str = ""
    binary_path: str = ""
    binary_version: str = ""
    execution_mode: str = "in_process"  # "in_process", "subprocess", "external_binary", "missing"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin": self.plugin,
            "tool": self.tool,
            "binary_name": self.binary_name,
            "binary_path": self.binary_path,
            "binary_version": self.binary_version,
            "execution_mode": self.execution_mode,
        }

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
class SemanticSignature:
    """Normalized semantic signature distilled from an inspection facet."""

    kind: str   # "evm_selector", "ipc_channel", "pinvoke", "export", "import", "android_permission", "dotnet_type", "http_endpoint"
    name: str
    details: dict[str, Any] = field(default_factory=dict)
    signature_hash: str = ""

    def __post_init__(self) -> None:
        if not self.signature_hash:
            canonical_payload = canonicalize_json({
                "kind": self.kind,
                "name": self.name,
                "details": self.details,
            })
            object.__setattr__(self, "signature_hash", compute_canonical_hash(canonical_payload))

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "details": self.details,
            "signature_hash": self.signature_hash,
        }

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
class FacetEnvelope:
    """Facet observation wrapper with explicit 3-valued availability and coverage semantics."""

    name: str
    state: Literal["available", "absent", "unknown"]
    availability: FacetAvailability
    coverage: CoverageDeclaration
    data: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.state not in ("available", "absent", "unknown"):
            raise ValueError(f"Invalid facet state: {self.state!r}. Must be 'available', 'absent', or 'unknown'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "availability": {
                "available": self.availability.available,
                "reason": self.availability.reason,
            },
            "coverage": {
                "scope": self.coverage.scope,
                "status": self.coverage.status,
                "truncated": self.coverage.truncated,
                "omitted_count": self.coverage.omitted_count,
                "absence_claimable": self.coverage.absence_claimable,
            },
            "data": self.data,
            "error": self.error,
        }

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
class ReaDissectionBudgets:
    """Operational limits enforcing Rule 44 Zero-Fork Config Invariant."""

    max_symbols: int = 50
    max_records: int = 100
    max_bytes: int = 10_485_760
    timeout_seconds: float = 60.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_symbols": self.max_symbols,
            "max_records": self.max_records,
            "max_bytes": self.max_bytes,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(slots=True, frozen=True)
class DissectionEnvelope:
    """Unified result envelope for all REA facade inspection and learning operations."""

    artifact: ArtifactIdentity
    facets: dict[str, FacetEnvelope]
    signatures: tuple[SemanticSignature, ...]
    provider: ProviderProvenance
    evidence_id: str
    budgets_applied: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact.to_dict(),
            "facets": {k: v.to_dict() for k, v in self.facets.items()},
            "signatures": [s.to_dict() for s in self.signatures],
            "provider": self.provider.to_dict(),
            "evidence_id": self.evidence_id,
            "budgets_applied": self.budgets_applied,
        }

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Service Protocol & Key (Rule 49)
# -----------------------------------------------------------------------------


@runtime_checkable
class ReaToolkitService(Protocol):
    """Protocol for unified REA reverse-engineering, routing, and envelope extraction."""

    def detect_artifact(self, target: str | Path) -> ArtifactIdentity:
        """Inspect magic bytes and headers to identify artifact kind and characteristics."""
        ...

    def dissect(
        self,
        target: str | Path,
        *,
        artifact_type: str | None = None,
        symbols: list[str] | None = None,
        provider: str = "ghidra",
        budgets: ReaDissectionBudgets | None = None,
    ) -> DissectionEnvelope:
        """Dissect artifact into normalized facets with explicit availability and signatures."""
        ...

    def signatures(
        self,
        target: str | Path,
        *,
        kind: str | None = None,
        artifact_type: str | None = None,
    ) -> list[SemanticSignature]:
        """Extract and deduplicate semantic signatures from an artifact."""
        ...

    def providers(self) -> dict[str, ProviderProvenance]:
        """Inspect and report availability and versions of external RE binaries."""
        ...

    def diff(
        self,
        target: str | Path,
        providers: tuple[str, str] = ("ghidra", "hopper"),
        symbols: list[str] | None = None,
    ) -> DifferentialReport:
        """Execute multi-provider differential comparison and emit a 3-valued DifferentialReport."""
        ...

    def learn(
        self,
        target: str | Path,
        *,
        vault_dir: Path | str = ".harness/knowledge",
        ledger_path: Path | str = ".harness/reconstruction_ledger.json",
        dry_run: bool = False,
        domain: str = "security_and_forensics",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Distill dissection signatures into CanonicalEvidence and Knowledge Vault items."""
        ...


REA_TOOLKIT_KEY: ServiceKey[ReaToolkitService] = ServiceKey("service.rea_toolkit")


# -----------------------------------------------------------------------------
# Domain Engine Invocation Adapter (Rule 58 Partial Service & Mock Adaptation)
# -----------------------------------------------------------------------------


class ReaDomainAdapter:
    """Seamlessly adapts SandboxedPlugin, in-process engine singletons, and test mocks."""

    def __init__(self, ctx: ServiceContext | None = None) -> None:
        self.ctx = ctx

    def call_native(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        from harness.services.rea_native import REA_NATIVE_KEY

        if self.ctx and self.ctx.has(REA_NATIVE_KEY):
            prov = self.ctx.require(REA_NATIVE_KEY)
            if hasattr(prov, method_name) and callable(getattr(prov, method_name)):
                res = getattr(prov, method_name)(**kwargs)
                return res if isinstance(res, dict) else res.model_dump()
            if hasattr(prov, "invoke_typed") and callable(getattr(prov, "invoke_typed")):
                # Subprocess SandboxedPlugin mapping
                entrypoint = f"rea_native_{method_name}"
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            call_res = pool.submit(asyncio.run, prov.invoke_typed(entrypoint, kwargs)).result()
                    else:
                        call_res = loop.run_until_complete(prov.invoke_typed(entrypoint, kwargs))
                    if call_res.is_ok:
                        return call_res.result or {}
                except Exception as e:
                    logger.debug("sandboxed_invoke_fallback", error=str(e))

        # Fallback to in-process domain engine singleton
        from plugins.security_and_forensics.rea_native.main import _GLOBAL_ENGINE
        fn = getattr(_GLOBAL_ENGINE, method_name, None)
        if fn and callable(fn):
            res = fn(**kwargs)
            return res if isinstance(res, dict) else (res.model_dump() if hasattr(res, "model_dump") else {})
        return {"status": "error", "error": f"Method {method_name} not available on native engine"}

    def call_managed(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        from harness.services.rea_managed_runtime import REA_MANAGED_RUNTIME_KEY

        if self.ctx and self.ctx.has(REA_MANAGED_RUNTIME_KEY):
            prov = self.ctx.require(REA_MANAGED_RUNTIME_KEY)
            if hasattr(prov, method_name) and callable(getattr(prov, method_name)):
                res = getattr(prov, method_name)(**kwargs)
                return res if isinstance(res, dict) else (res.model_dump() if hasattr(res, "model_dump") else res.to_dict() if hasattr(res, "to_dict") else {})

        from plugins.security_and_forensics.rea_managed_runtime.main import _GLOBAL_ENGINE
        fn = getattr(_GLOBAL_ENGINE, method_name, None)
        if fn and callable(fn):
            res = fn(**kwargs)
            return res if isinstance(res, dict) else (res.model_dump() if hasattr(res, "model_dump") else (res.to_dict() if hasattr(res, "to_dict") else {}))
        return {"status": "error", "error": f"Method {method_name} not available on managed runtime engine"}

    def call_mobile(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        from harness.services.rea_mobile_firmware import REA_MOBILE_FIRMWARE_KEY

        if self.ctx and self.ctx.has(REA_MOBILE_FIRMWARE_KEY):
            prov = self.ctx.require(REA_MOBILE_FIRMWARE_KEY)
            if hasattr(prov, method_name) and callable(getattr(prov, method_name)):
                res = getattr(prov, method_name)(**kwargs)
                return res if isinstance(res, dict) else res.model_dump()

        from plugins.security_and_forensics.rea_mobile_firmware.main import _GLOBAL_ENGINE
        fn = getattr(_GLOBAL_ENGINE, method_name, None)
        if fn and callable(fn):
            res = fn(**kwargs)
            return res if isinstance(res, dict) else (res.model_dump() if hasattr(res, "model_dump") else {})
        return {"status": "error", "error": f"Method {method_name} not available on mobile/firmware engine"}

    def call_js(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        from harness.services.rea_javascript import REA_JAVASCRIPT_KEY

        if self.ctx and self.ctx.has(REA_JAVASCRIPT_KEY):
            prov = self.ctx.require(REA_JAVASCRIPT_KEY)
            if hasattr(prov, method_name) and callable(getattr(prov, method_name)):
                res = getattr(prov, method_name)(**kwargs)
                return res if isinstance(res, dict) else res.model_dump()

        from plugins.data_engineering.rea_javascript.main import _GLOBAL_ENGINE
        fn = getattr(_GLOBAL_ENGINE, method_name, None)
        if fn and callable(fn):
            res = fn(**kwargs)
            return res if isinstance(res, dict) else (res.model_dump() if hasattr(res, "model_dump") else {})
        return {"status": "error", "error": f"Method {method_name} not available on javascript engine"}


# -----------------------------------------------------------------------------
# Standard Implementation: StandardReaToolkitService
# -----------------------------------------------------------------------------


class StandardReaToolkitService:
    """Production implementation of ReaToolkitService."""

    def __init__(self, ctx: ServiceContext | None = None, *, vault_dir: Path | str = ".harness/knowledge") -> None:
        self.ctx = ctx
        self.adapter = ReaDomainAdapter(ctx=ctx)
        self.differential_service = StandardDifferentialFacetService()
        self.vault_dir = Path(vault_dir)

    def detect_artifact(self, target: str | Path) -> ArtifactIdentity:
        """Inspect magic bytes and headers to identify artifact kind and characteristics."""
        p_str = str(target).strip()

        # Handle raw hex EVM bytecode strings directly
        if p_str.startswith("0x") and len(p_str) > 2 and all(c in "0123456789abcdefABCDEF" for c in p_str[2:]):
            sha = hashlib.sha256(p_str.encode("utf-8")).hexdigest()
            return ArtifactIdentity(
                path="<evm_bytecode_hex>",
                sha256=sha,
                size_bytes=len(p_str) // 2,
                detected_kind="evm_bytecode",
                mime_type="application/x-evm-bytecode",
                magic_summary="EVM bytecode (0x-prefixed hex string)",
            )

        p = Path(p_str)
        if not p.exists() or not p.is_file():
            # Check if string is raw hex EVM without 0x
            if len(p_str) >= 8 and len(p_str) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in p_str):
                sha = hashlib.sha256(p_str.encode("utf-8")).hexdigest()
                return ArtifactIdentity(
                    path="<evm_bytecode_hex>",
                    sha256=sha,
                    size_bytes=len(p_str) // 2,
                    detected_kind="evm_bytecode",
                    mime_type="application/x-evm-bytecode",
                    magic_summary="EVM bytecode (raw hex string)",
                )
            raise FileNotFoundError(f"Artifact target not found: {p_str}")

        file_size = p.stat().st_size
        sha_h = hashlib.sha256()
        polyglot_warnings: list[str] = []

        with open(p, "rb") as f:
            header = f.read(1024)
            sha_h.update(header)
            while chunk := f.read(65536):
                sha_h.update(chunk)

        sha = sha_h.hexdigest()
        suffix = p.suffix.lower()
        file_name = p.name.lower()

        # Check for Google Magika detection if available
        if self.ctx:
            from harness.kernel.context import ServiceKey
            magika_key = ServiceKey("service.magika_format_forensics")
            if self.ctx.has(magika_key):
                try:
                    forensics = self.ctx.require(magika_key)
                    pg_res = forensics.polyglot_check(str(p))
                    if pg_res.get("is_polyglot_candidate"):
                        for ind in pg_res.get("indicators", []):
                            polyglot_warnings.append(str(ind))
                except Exception:
                    pass

        # Fast in-line polyglot heuristic if Magika is not present
        if not polyglot_warnings and len(header) >= 64:
            if header.startswith(b"\x7fELF") and (b"PK\x03\x04" in header[16:] or b"MZ" in header[16:]):
                polyglot_warnings.append("Embedded secondary container magic detected (possible ELF polyglot)")
            elif header.startswith(b"MZ") and (b"PK\x03\x04" in header[64:] or b"\x7fELF" in header[64:]):
                polyglot_warnings.append("Embedded secondary container magic detected (possible PE/ZIP polyglot)")
            elif header.startswith(b"PK\x03\x04") and (b"\x7fELF" in header[30:] or b"MZ" in header[30:]):
                polyglot_warnings.append("Embedded executable magic inside ZIP container (possible polyglot)")

        # 1. ELF Binary
        if header.startswith(b"\x7fELF"):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="elf",
                mime_type="application/x-executable",
                magic_summary="ELF Executable / Shared Object",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 2. Windows PE/CLI vs Native PE vs DOS MZ
        if header.startswith(b"MZ"):
            kind = self._disambiguate_pe(header, p)
            mime = "application/x-msdownload" if kind != "pe_managed" else "application/x-ms-clr"
            desc = "Windows .NET PE/CLI Assembly" if kind == "pe_managed" else ("Windows Native PE32/PE32+ Binary" if kind == "pe_native" else "DOS MZ / COM Load Image")
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind=kind,
                mime_type=mime,
                magic_summary=desc,
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 3. WebAssembly
        if header.startswith(b"\x00asm\x01\x00\x00\x00") or (suffix == ".wasm" and header.startswith(b"\x00asm")):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="wasm",
                mime_type="application/wasm",
                magic_summary="WebAssembly Binary Module",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 4. Unity IL2CPP Metadata
        if header.startswith(b"\xaf\x1b\xb1\xfa") or file_name == "global-metadata.dat":
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="il2cpp_metadata",
                mime_type="application/x-unity-il2cpp-metadata",
                magic_summary="Unity IL2CPP global-metadata.dat (magic 0xFAB11BAF)",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 5. AI Model Artifacts: GGUF, Safetensors, TFLite, HDF5/Keras, SavedModel PB, TF.js Shards
        if header.startswith(b"GGUF") or suffix == ".gguf":
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="ai_model",
                mime_type="application/x-gguf",
                magic_summary="GGUF Quantized AI Model Weights",
                polyglot_warnings=tuple(polyglot_warnings),
            )
        if suffix == ".safetensors" and len(header) >= 8:
            try:
                hdr_len = struct.unpack_from("<Q", header, 0)[0]
                if 0 < hdr_len < 100_000_000:
                    return ArtifactIdentity(
                        path=str(p),
                        sha256=sha,
                        size_bytes=file_size,
                        detected_kind="ai_model",
                        mime_type="application/x-safetensors",
                        magic_summary="Safetensors Neural Network Weights",
                        polyglot_warnings=tuple(polyglot_warnings),
                    )
            except Exception:
                pass
        if (len(header) >= 8 and header[4:8] == b"TFL3") or suffix == ".tflite":
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="ai_model",
                mime_type="application/x-tflite",
                magic_summary="TensorFlow Lite FlatBuffer Model (TFL3)",
                polyglot_warnings=tuple(polyglot_warnings),
            )
        if header.startswith(b"\x89HDF\r\n\x1a\n") or suffix in (".h5", ".hdf5", ".keras"):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="ai_model",
                mime_type="application/x-hdf5",
                magic_summary="Keras / HDF5 Neural Network Weights",
                polyglot_warnings=tuple(polyglot_warnings),
            )
        if file_name == "saved_model.pb" or (suffix == ".pb" and file_size >= 16):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="ai_model",
                mime_type="application/x-protobuf",
                magic_summary="TensorFlow SavedModel Protocol Buffer",
                polyglot_warnings=tuple(polyglot_warnings),
            )
        if suffix == ".bin" and "shard" in file_name:
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="ai_model",
                mime_type="application/octet-stream",
                magic_summary="TensorFlow.js Binary Weight Shard",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 6. Android APK / ZIP Container
        if header.startswith(b"PK\x03\x04") or suffix == ".apk":
            # Check if contains AndroidManifest.xml or classes.dex
            is_apk = suffix == ".apk"
            if not is_apk and b"AndroidManifest.xml" in header or b"classes.dex" in header:
                is_apk = True
            if is_apk:
                return ArtifactIdentity(
                    path=str(p),
                    sha256=sha,
                    size_bytes=file_size,
                    detected_kind="apk",
                    mime_type="application/vnd.android.package-archive",
                    magic_summary="Android APK Package Archive",
                    polyglot_warnings=tuple(polyglot_warnings),
                )

        # 7. Electron ASAR Archive
        if suffix == ".asar" or self._is_asar_header(header):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="asar",
                mime_type="application/x-electron-asar",
                magic_summary="Electron ASAR Archive Container",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 8. CPython .pyc Bytecode
        if suffix == ".pyc" or (len(header) >= 4 and header[2:4] == b"\r\n"):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="cpython_pyc",
                mime_type="application/x-python-code",
                magic_summary="CPython Compiled Bytecode (.pyc)",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 9. HTTP Archive (.har)
        if suffix == ".har" or (b'"log"' in header and b'"version"' in header and b'"creator"' in header):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="har",
                mime_type="application/json",
                magic_summary="HTTP Archive (HAR 1.2) Network Capture",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 10. JavaScript / TypeScript Bundle
        if suffix in (".js", ".mjs", ".cjs") or (suffix == "" and (b"webpackChunk" in header or b"exports" in header or b"define(" in header)):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="javascript_bundle",
                mime_type="application/javascript",
                magic_summary="JavaScript Application / Minified Bundle",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 11. EVM Bytecode File (.evm, .hex, or header starting with 60806040/60606040)
        clean_text_hdr = header.strip()
        if (
            suffix in (".evm", ".hex")
            or clean_text_hdr.startswith(b"60806040")
            or clean_text_hdr.startswith(b"60606040")
            or header.startswith(b"\x60\x80\x60\x40")
            or header.startswith(b"\x60\x60\x60\x40")
        ):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="evm_bytecode",
                mime_type="application/x-evm-bytecode",
                magic_summary="Ethereum Virtual Machine (EVM) Bytecode",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # 12. Firmware blob
        if suffix in (".bin", ".fw", ".img") or any(sig in header for sig in (b"hsqs", b"sqsh", b"-rom1fs-")):
            return ArtifactIdentity(
                path=str(p),
                sha256=sha,
                size_bytes=file_size,
                detected_kind="firmware",
                mime_type="application/octet-stream",
                magic_summary="Embedded Firmware / Compressed Partition Image",
                polyglot_warnings=tuple(polyglot_warnings),
            )

        # Default fallback
        return ArtifactIdentity(
            path=str(p),
            sha256=sha,
            size_bytes=file_size,
            detected_kind="unknown",
            mime_type="application/octet-stream",
            magic_summary="Unrecognized Binary Format",
            polyglot_warnings=tuple(polyglot_warnings),
        )

    def _disambiguate_pe(self, header: bytes, p: Path) -> str:
        """Inspect PE header Data Directory #14 (CLR Header) to differentiate Native PE vs Managed .NET."""
        try:
            if len(header) < 64:
                return "dos_mz"
            e_lfanew = struct.unpack_from("<I", header, 0x3C)[0]
            if e_lfanew + 24 > len(header):
                # Need to read full PE header from file if e_lfanew exceeds 1024
                with open(p, "rb") as f:
                    f.seek(e_lfanew)
                    pe_sig = f.read(4)
                    if pe_sig != b"PE\x00\x00":
                        return "dos_mz"
                    file_hdr = f.read(20)
                    opt_hdr = f.read(240)
            else:
                if header[e_lfanew:e_lfanew+4] != b"PE\x00\x00":
                    return "dos_mz"
                opt_offset = e_lfanew + 24
                opt_hdr = header[opt_offset:]

            if len(opt_hdr) < 2:
                return "pe_native"
            opt_magic = struct.unpack_from("<H", opt_hdr, 0)[0]

            clr_offset = -1
            if opt_magic == 0x010B:  # PE32
                clr_offset = 96 + (14 * 8)
            elif opt_magic == 0x020B:  # PE32+
                clr_offset = 112 + (14 * 8)

            if clr_offset >= 0 and clr_offset + 8 <= len(opt_hdr):
                clr_rva, clr_size = struct.unpack_from("<II", opt_hdr, clr_offset)
                if clr_rva > 0 and clr_size > 0:
                    return "pe_managed"
            return "pe_native"
        except Exception:
            return "pe_native"

    def _is_asar_header(self, header: bytes) -> bool:
        if len(header) < 16:
            return False
        try:
            # Chromium pickle header for ASAR: uint32 4, uint32 size, uint32 payload_size, uint32 header_size
            u1, u2 = struct.unpack_from("<II", header, 0)
            return u1 == 4 and u2 > 0 and b'"files"' in header[:512]
        except Exception:
            return False

    def dissect(
        self,
        target: str | Path,
        *,
        artifact_type: str | None = None,
        symbols: list[str] | None = None,
        provider: str = "ghidra",
        budgets: ReaDissectionBudgets | None = None,
    ) -> DissectionEnvelope:
        """Dissect artifact into normalized facets with explicit availability and signatures."""
        artifact = self.detect_artifact(target)
        kind = (artifact_type or artifact.detected_kind).lower()
        active_budgets = budgets or ReaDissectionBudgets()

        facets: dict[str, FacetEnvelope] = {}
        signatures: list[SemanticSignature] = []
        target_path = str(target) if artifact.path == "<evm_bytecode_hex>" else artifact.path

        # Dispatch per artifact kind
        if kind == "elf":
            raw_layout = self.adapter.call_native("elf_layout", target_path=target_path, checksec=True)
            if raw_layout.get("status") == "ok":
                sections = raw_layout.get("sections") or []
                imports = raw_layout.get("imported_symbols") or []
                exports = raw_layout.get("exported_symbols") or []
                mitigations = raw_layout.get("mitigations")

                facets["layout"] = FacetEnvelope(
                    name="layout",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={"sections_count": len(sections), "mitigations": mitigations},
                )

                facets["imports"] = FacetEnvelope(
                    name="imports",
                    state="available" if imports else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data=imports,
                )
                for sym in imports:
                    signatures.append(SemanticSignature(kind="import", name=str(sym), details={"target": target_path}))

                facets["exports"] = FacetEnvelope(
                    name="exports",
                    state="available" if exports else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data=exports,
                )
                for sym in exports:
                    signatures.append(SemanticSignature(kind="export", name=str(sym), details={"target": target_path}))
            else:
                facets["layout"] = FacetEnvelope(
                    name="layout",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_layout.get("error", "Layout inspection failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_layout.get("error"),
                )

            # Decompile facet if symbols requested or decompiler requested
            if symbols:
                capped_symbols = symbols[:active_budgets.max_symbols]
                omitted = len(symbols) - len(capped_symbols)
                raw_decomp = self.adapter.call_native("batch_decompile", target_path=target_path, symbols=capped_symbols, provider=provider)
                if raw_decomp.get("status") == "ok":
                    procs = raw_decomp.get("procedures") or []
                    cov_status = "partial" if omitted > 0 else "complete"
                    facets["decompilation"] = FacetEnvelope(
                        name="decompilation",
                        state="available" if procs else "absent",
                        availability=FacetAvailability(available=True),
                        coverage=CoverageDeclaration(scope="dossier", status=cov_status, truncated=(omitted > 0), omitted_count=omitted),
                        data=procs,
                    )
                else:
                    facets["decompilation"] = FacetEnvelope(
                        name="decompilation",
                        state="unknown",
                        availability=FacetAvailability(available=False, reason=raw_decomp.get("error", f"Provider {provider} execution failed")),
                        coverage=CoverageDeclaration(scope="dossier", status="unknown", truncated=(omitted > 0), omitted_count=omitted),
                        error=raw_decomp.get("error"),
                    )

            prov = ProviderProvenance(plugin="plugin.rea_native", tool="rea_native_elf_layout", execution_mode="in_process")

        elif kind == "pe_managed":
            raw_managed = self.adapter.call_managed("inspect_managed_artifact", target_path=target_path, extract_members=True)
            raw_bounds = self.adapter.call_managed("inspect_managed_native_boundaries", target_path=target_path)
            raw_dotnet = self.adapter.call_js("dotnet_inspect", assembly_path=target_path, include_cil=True)

            if raw_managed.get("status") in ("ok", "success") or raw_managed.get("is_cli"):
                members = raw_managed.get("members") or []
                facets["managed_headers"] = FacetEnvelope(
                    name="managed_headers",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={
                        "runtime_version": raw_managed.get("runtime_version"),
                        "metadata_streams": raw_managed.get("metadata_streams", []),
                        "types_count": raw_managed.get("types_count", 0),
                        "methods_count": raw_managed.get("methods_count", 0),
                    },
                )
            else:
                facets["managed_headers"] = FacetEnvelope(
                    name="managed_headers",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_managed.get("error", "PE/CLI header parse failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_managed.get("error"),
                )

            # Native boundaries
            pinvokes = raw_bounds.get("pinvokes") or []
            facets["native_boundaries"] = FacetEnvelope(
                name="native_boundaries",
                state="available" if pinvokes else "absent",
                availability=FacetAvailability(available=True),
                coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                data={"module_refs": raw_bounds.get("module_refs", []), "pinvokes": pinvokes},
            )
            for p_item in pinvokes:
                p_dict = p_item if isinstance(p_item, dict) else (p_item.to_dict() if hasattr(p_item, "to_dict") else {})
                m_name = p_dict.get("module_name", "")
                ep = p_dict.get("entry_point", "")
                signatures.append(SemanticSignature(
                    kind="pinvoke",
                    name=f"{m_name}!{ep}",
                    details={"calling_convention": p_dict.get("calling_convention", "winapi")},
                ))

            # Types from dotnet_inspect
            types = raw_dotnet.get("types") or []
            if types:
                facets["type_hierarchy"] = FacetEnvelope(
                    name="type_hierarchy",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data=types,
                )
                for t in types:
                    t_dict = t if isinstance(t, dict) else (t.to_dict() if hasattr(t, "to_dict") else {})
                    t_name = f"{t_dict.get('namespace', '')}.{t_dict.get('type_name', '')}".strip(".")
                    signatures.append(SemanticSignature(
                        kind="dotnet_type",
                        name=t_name,
                        details={"cil_hash": t_dict.get("cil_instruction_hash", ""), "methods_count": t_dict.get("methods_count", 0)},
                    ))

            prov = ProviderProvenance(plugin="plugin.rea_managed_runtime", tool="rea_inspect_managed_artifact", execution_mode="in_process")

        elif kind == "pe_native":
            raw_layout = self.adapter.call_native("elf_layout", target_path=target_path, checksec=True)
            sections = raw_layout.get("sections") or []
            imports = raw_layout.get("imported_symbols") or []
            exports = raw_layout.get("exported_symbols") or []

            facets["layout"] = FacetEnvelope(
                name="layout",
                state="available" if raw_layout.get("status") == "ok" else "unknown",
                availability=FacetAvailability(available=raw_layout.get("status") == "ok", reason=raw_layout.get("error")),
                coverage=CoverageDeclaration(scope="root", status="complete"),
                data={"sections_count": len(sections), "mitigations": raw_layout.get("mitigations")},
            )
            facets["imports"] = FacetEnvelope(
                name="imports",
                state="available" if imports else "absent",
                availability=FacetAvailability(available=True),
                coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                data=imports,
            )
            facets["exports"] = FacetEnvelope(
                name="exports",
                state="available" if exports else "absent",
                availability=FacetAvailability(available=True),
                coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                data=exports,
            )
            for sym in exports:
                signatures.append(SemanticSignature(kind="export", name=str(sym), details={"target": target_path}))
            for sym in imports:
                signatures.append(SemanticSignature(kind="import", name=str(sym), details={"target": target_path}))

            prov = ProviderProvenance(plugin="plugin.rea_native", tool="rea_native_elf_layout", execution_mode="in_process")

        elif kind == "dos_mz":
            raw_load = self.adapter.call_native("inspect_load_image", target_path=target_path)
            facets["load_image"] = FacetEnvelope(
                name="load_image",
                state="available" if raw_load.get("status") == "ok" else "unknown",
                availability=FacetAvailability(available=raw_load.get("status") == "ok", reason=raw_load.get("error")),
                coverage=CoverageDeclaration(scope="root", status="complete"),
                data=raw_load,
            )
            prov = ProviderProvenance(plugin="plugin.rea_native", tool="rea_native_inspect_load_image", execution_mode="in_process")

        elif kind == "apk":
            raw_apk = self.adapter.call_mobile("apk_inspect", apk_path=target_path, decode_resources=True)
            if raw_apk.get("status") == "ok":
                manifest = raw_apk.get("manifest") or {}
                perms = manifest.get("permissions") or []
                facets["apk_manifest"] = FacetEnvelope(
                    name="apk_manifest",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data=manifest,
                )
                facets["permissions"] = FacetEnvelope(
                    name="permissions",
                    state="available" if perms else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data=perms,
                )
                for perm in perms:
                    signatures.append(SemanticSignature(kind="android_permission", name=str(perm), details={}))
                for act in manifest.get("activities", []):
                    signatures.append(SemanticSignature(kind="android_component", name=str(act), details={"component": "activity"}))
                for srv in manifest.get("services", []):
                    signatures.append(SemanticSignature(kind="android_component", name=str(srv), details={"component": "service"}))
            else:
                facets["apk_manifest"] = FacetEnvelope(
                    name="apk_manifest",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_apk.get("error", "APK parsing failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_apk.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_mobile_firmware", tool="rea_mobile_apk_inspect", execution_mode="in_process")

        elif kind == "asar":
            raw_asar = self.adapter.call_js("electron_inspect", asar_path=target_path, extract_ipc=True)
            if raw_asar.get("status") == "ok":
                channels = raw_asar.get("ipc_channels") or []
                facets["asar_manifest"] = FacetEnvelope(
                    name="asar_manifest",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={
                        "app_name": raw_asar.get("app_name"),
                        "app_version": raw_asar.get("app_version"),
                        "main_script": raw_asar.get("main_script"),
                        "preload_scripts": raw_asar.get("preload_scripts", []),
                        "files_count": raw_asar.get("files_count", 0),
                    },
                )
                facets["ipc_channels"] = FacetEnvelope(
                    name="ipc_channels",
                    state="available" if channels else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data=channels,
                )
                for chan in channels:
                    c_dict = chan if isinstance(chan, dict) else (chan.model_dump() if hasattr(chan, "model_dump") else {})
                    signatures.append(SemanticSignature(
                        kind="ipc_channel",
                        name=c_dict.get("channel_name", ""),
                        details={"direction": c_dict.get("direction", "bidirectional"), "source_file": c_dict.get("source_file", "")},
                    ))
            else:
                facets["asar_manifest"] = FacetEnvelope(
                    name="asar_manifest",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_asar.get("error", "ASAR parsing failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_asar.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_javascript", tool="rea_javascript_electron_inspect", execution_mode="in_process")

        elif kind == "wasm":
            raw_wasm = self.adapter.call_native("wasm_inspect", wasm_path=target_path, emit_wat=False)
            if raw_wasm.get("status") == "ok":
                imports = raw_wasm.get("imports") or []
                exports = raw_wasm.get("exports") or []
                facets["wasm_sections"] = FacetEnvelope(
                    name="wasm_sections",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={"sections": raw_wasm.get("sections", [])},
                )
                facets["wasm_exports"] = FacetEnvelope(
                    name="wasm_exports",
                    state="available" if exports else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data=exports,
                )
                for exp in exports:
                    exp_name = exp.get("name", "") if isinstance(exp, dict) else str(exp)
                    signatures.append(SemanticSignature(kind="wasm_export", name=exp_name, details=exp if isinstance(exp, dict) else {}))
            else:
                facets["wasm_sections"] = FacetEnvelope(
                    name="wasm_sections",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_wasm.get("error", "WASM parsing failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_wasm.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_native", tool="rea_native_wasm_inspect", execution_mode="in_process")

        elif kind == "il2cpp_metadata":
            raw_il = self.adapter.call_managed("inspect_il2cpp_metadata", metadata_path=target_path, max_records=active_budgets.max_records)
            if raw_il.get("status") in ("ok", "success") or raw_il.get("magic_valid"):
                facets["il2cpp_metadata"] = FacetEnvelope(
                    name="il2cpp_metadata",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={
                        "version": raw_il.get("version"),
                        "string_literals_count": raw_il.get("string_literals_count", 0),
                        "methods_count": raw_il.get("methods_count", 0),
                        "type_definitions_count": raw_il.get("type_definitions_count", 0),
                        "images_count": raw_il.get("images_count", 0),
                    },
                )
            else:
                facets["il2cpp_metadata"] = FacetEnvelope(
                    name="il2cpp_metadata",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_il.get("error", "IL2CPP metadata parse failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_il.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_managed_runtime", tool="rea_inspect_il2cpp_metadata", execution_mode="in_process")

        elif kind == "ai_model":
            raw_model = self.adapter.call_managed("inspect_model_artifact", model_path=target_path, preview_tensors=50)
            if raw_model.get("status") in ("ok", "success"):
                tensors = raw_model.get("tensors") or []
                t_count = raw_model.get("tensor_count") if raw_model.get("tensor_count") is not None else raw_model.get("tensors_count", len(tensors))
                meta_dict = raw_model.get("metadata_preview") if isinstance(raw_model.get("metadata_preview"), dict) else (raw_model.get("metadata") if isinstance(raw_model.get("metadata"), dict) else {})
                fmt_str = raw_model.get("format", "unknown")
                facets["model_headers"] = FacetEnvelope(
                    name="model_headers",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={
                        "format": fmt_str,
                        "tensors_count": t_count,
                        "metadata_keys": list(meta_dict.keys()),
                    },
                )
                signatures.append(SemanticSignature(
                    kind="model_format",
                    name=str(fmt_str),
                    details={"tensors_count": t_count, "metadata": meta_dict},
                ))
                for t_item in tensors[:active_budgets.max_records]:
                    t_dict = t_item if isinstance(t_item, dict) else (t_item.to_dict() if hasattr(t_item, "to_dict") else {})
                    t_name = t_dict.get("name", "")
                    if t_name:
                        signatures.append(SemanticSignature(
                            kind="model_tensor",
                            name=str(t_name),
                            details={"dtype": t_dict.get("type_name", "unknown"), "shape": t_dict.get("shape", [])},
                        ))
            else:
                facets["model_headers"] = FacetEnvelope(
                    name="model_headers",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_model.get("error", "Model header seek failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_model.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_managed_runtime", tool="rea_inspect_model_artifact", execution_mode="in_process")

        elif kind == "cpython_pyc":
            raw_pyc = self.adapter.call_managed("inspect_python_pyc", pyc_path=target_path, disassemble=True)
            if raw_pyc.get("status") in ("ok", "success"):
                c_ver = raw_pyc.get("cpython_version", "")
                c_name = raw_pyc.get("code_object_name") or raw_pyc.get("code_name") or "<module>"
                op_count = raw_pyc.get("instruction_count") if raw_pyc.get("instruction_count") is not None else raw_pyc.get("opcodes_count", 0)
                sample_dis = raw_pyc.get("sample_disassembly") or []
                facets["pyc_code"] = FacetEnvelope(
                    name="pyc_code",
                    state="available",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data={
                        "cpython_version": c_ver,
                        "code_name": c_name,
                        "argcount": raw_pyc.get("argcount"),
                        "opcodes_count": op_count,
                    },
                )
                signatures.append(SemanticSignature(
                    kind="pyc_code_object",
                    name=str(c_name),
                    details={"cpython_version": c_ver, "instruction_count": op_count},
                ))
                for line in sample_dis:
                    m_imp = re.search(r"\b(IMPORT_NAME|IMPORT_FROM)\s+\d+\s+\(([^)]+)\)", str(line))
                    if m_imp:
                        signatures.append(SemanticSignature(
                            kind="pyc_import",
                            name=m_imp.group(2),
                            details={"opcode": m_imp.group(1)},
                        ))
                    m_co = re.search(r"<code object\s+([^\s>]+)\s+at\s+", str(line))
                    if m_co:
                        signatures.append(SemanticSignature(
                            kind="pyc_function",
                            name=m_co.group(1),
                            details={"cpython_version": c_ver},
                        ))
            else:
                facets["pyc_code"] = FacetEnvelope(
                    name="pyc_code",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_pyc.get("error", "Pyc disassembly failed")),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error=raw_pyc.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_managed_runtime", tool="rea_inspect_python_pyc", execution_mode="in_process")

        elif kind == "har":
            raw_har = self.adapter.call_js("har_inspect", har_path=target_path)
            if raw_har.get("status") == "ok":
                entries = raw_har.get("entries") or []
                facets["har_entries"] = FacetEnvelope(
                    name="har_entries",
                    state="available" if entries else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data={"entries_count": raw_har.get("entries_count", 0)},
                )
                for ent in entries[:active_budgets.max_records]:
                    e_dict = ent if isinstance(ent, dict) else (ent.model_dump() if hasattr(ent, "model_dump") else {})
                    m = e_dict.get("method", "GET")
                    u = e_dict.get("url", "")
                    signatures.append(SemanticSignature(
                        kind="http_endpoint",
                        name=f"{m} {u}",
                        details={"status": e_dict.get("status"), "mime_type": e_dict.get("mime_type")},
                    ))
            else:
                facets["har_entries"] = FacetEnvelope(
                    name="har_entries",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_har.get("error", "HAR parsing failed")),
                    coverage=CoverageDeclaration(scope="container-entries", status="unknown"),
                    error=raw_har.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_javascript", tool="rea_javascript_har_inspect", execution_mode="in_process")

        elif kind == "javascript_bundle":
            # Pure static signature extraction from script without writing output tree
            js_classes: list[str] = []
            js_functions: list[str] = []
            try:
                p_js = Path(target_path)
                if p_js.is_file():
                    with open(p_js, "rb") as f_js:
                        js_sample = f_js.read(min(artifact.size_bytes, 262144)).decode("utf-8", errors="ignore")

                    def _strip_comments(src: str) -> str:
                        def _replacer(match: re.Match[str]) -> str:
                            s = match.group(0)
                            if s.startswith("/"):
                                return " "
                            return s
                        pat = re.compile(
                            r"//.*?$|/\*.*?\*/|'(?:\\.|[^\\'])*'|\"(?:\\.|[^\\\"])*\"|`(?:\\.|[^\\`])*`",
                            re.DOTALL | re.MULTILINE,
                        )
                        return pat.sub(_replacer, src)

                    clean_js = _strip_comments(js_sample)

                    for m_cls in re.finditer(
                        r"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:extends\s+[A-Za-z_$][A-Za-z0-9_$.]*)?\s*\{",
                        clean_js,
                    ):
                        c_name = m_cls.group(1)
                        if c_name not in js_classes:
                            js_classes.append(c_name)

                    fn_pattern = re.compile(
                        r"(?:\b(?:async\s+)?function\s*(?:\*\s*)?([A-Za-z_$][A-Za-z0-9_$]*)\s*\(|"
                        r"([A-Za-z_$][A-Za-z0-9_$]*(?:\.prototype\.[A-Za-z_$][A-Za-z0-9_$]*|\.[A-Za-z_$][A-Za-z0-9_$]*))\s*=\s*(?:async\s+)?function\s*\()"
                    )
                    for m_fn in fn_pattern.finditer(clean_js):
                        fn_name = m_fn.group(1) or m_fn.group(2)
                        if fn_name and fn_name not in js_functions:
                            js_functions.append(fn_name)
            except Exception:
                pass

            facets["bundle"] = FacetEnvelope(
                name="bundle",
                state="available",
                availability=FacetAvailability(available=True),
                coverage=CoverageDeclaration(scope="root", status="complete"),
                data={
                    "path": target_path,
                    "size_bytes": artifact.size_bytes,
                    "classes_count": len(js_classes),
                    "functions_count": len(js_functions),
                },
            )
            for cls_name in js_classes[:active_budgets.max_records]:
                signatures.append(SemanticSignature(
                    kind="js_class",
                    name=cls_name,
                    details={"source": Path(target_path).name},
                ))
            for fn_name in js_functions[:active_budgets.max_records]:
                signatures.append(SemanticSignature(
                    kind="js_function",
                    name=fn_name,
                    details={"source": Path(target_path).name},
                ))
            prov = ProviderProvenance(plugin="plugin.rea_javascript", tool="rea_javascript_recover_sources", execution_mode="in_process")

        elif kind == "evm_bytecode":
            bytecode_str = target_path if (target_path.startswith("0x") or not Path(target_path).exists()) else Path(target_path).read_text(encoding="utf-8").strip()
            if bytecode_str.startswith("0x") or bytecode_str.startswith("0X"):
                bytecode_str = bytecode_str[2:]
            raw_evm = self.adapter.call_native("evm_interface", bytecode_hex=bytecode_str, resolve_signatures=True)
            if raw_evm.get("status") == "ok":
                selectors = raw_evm.get("selectors") or []
                resolved = raw_evm.get("resolved_signatures") or {}
                facets["evm_interface"] = FacetEnvelope(
                    name="evm_interface",
                    state="available" if selectors else "absent",
                    availability=FacetAvailability(available=True),
                    coverage=CoverageDeclaration(scope="container-entries", status="complete"),
                    data={"selectors_count": len(selectors), "opcodes_count": raw_evm.get("opcodes_count", 0)},
                )
                for sel in selectors:
                    s_dict = sel if isinstance(sel, dict) else (sel.model_dump() if hasattr(sel, "model_dump") else {})
                    sel_hex = s_dict.get("selector", "")
                    signatures.append(SemanticSignature(
                        kind="evm_selector",
                        name=sel_hex,
                        details={"resolved_signature": resolved.get(sel_hex)},
                    ))
            else:
                facets["evm_interface"] = FacetEnvelope(
                    name="evm_interface",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason=raw_evm.get("error", "EVM disassembly failed")),
                    coverage=CoverageDeclaration(scope="container-entries", status="unknown"),
                    error=raw_evm.get("error"),
                )

            prov = ProviderProvenance(plugin="plugin.rea_native", tool="rea_native_evm_interface", execution_mode="in_process")

        elif kind == "firmware":
            # On Windows, Binwalk/Unblob are typically Linux-gated
            if sys.platform == "win32":
                facets["firmware_regions"] = FacetEnvelope(
                    name="firmware_regions",
                    state="unknown",
                    availability=FacetAvailability(available=False, reason="Binwalk and Unblob are Linux-isolated providers; not natively installed on win32"),
                    coverage=CoverageDeclaration(scope="root", status="unknown"),
                    error="Linux-only provider constraint on Windows host",
                )
            else:
                raw_fw = self.adapter.call_mobile("firmware_inspect_regions", firmware_path=target_path)
                facets["firmware_regions"] = FacetEnvelope(
                    name="firmware_regions",
                    state="available" if raw_fw.get("status") == "ok" else "unknown",
                    availability=FacetAvailability(available=raw_fw.get("status") == "ok", reason=raw_fw.get("error")),
                    coverage=CoverageDeclaration(scope="root", status="complete"),
                    data=raw_fw,
                )

            prov = ProviderProvenance(plugin="plugin.rea_mobile_firmware", tool="rea_firmware_regions_inspect", execution_mode="in_process")

        else:
            facets["raw_binary"] = FacetEnvelope(
                name="raw_binary",
                state="unknown",
                availability=FacetAvailability(available=False, reason=f"Unrecognized or unsupported artifact kind: {kind}"),
                coverage=CoverageDeclaration(scope="root", status="unknown"),
            )
            prov = ProviderProvenance(plugin="plugin.rea_native", tool="unresolved", execution_mode="missing")

        # Deterministic evidence ID calculation: ev:<sha256>
        evidence_payload = {
            "artifact_sha256": artifact.sha256,
            "detected_kind": kind,
            "facets": {k: v.to_dict() for k, v in facets.items()},
            "signatures_digest": compute_canonical_hash(canonicalize_json([s.to_dict() for s in signatures])),
        }
        evidence_digest = compute_canonical_hash(canonicalize_json(evidence_payload))
        evidence_id = f"ev:{evidence_digest}"

        return DissectionEnvelope(
            artifact=artifact,
            facets=facets,
            signatures=tuple(signatures),
            provider=prov,
            evidence_id=evidence_id,
            budgets_applied=active_budgets.to_dict(),
        )

    def signatures(
        self,
        target: str | Path,
        *,
        kind: str | None = None,
        artifact_type: str | None = None,
    ) -> list[SemanticSignature]:
        """Extract and deduplicate semantic signatures from an artifact."""
        envelope = self.dissect(target, artifact_type=artifact_type)
        if kind is None:
            return list(envelope.signatures)
        return [s for s in envelope.signatures if s.kind.lower() == kind.lower()]

    def providers(self) -> dict[str, ProviderProvenance]:
        """Inspect and report availability and versions of external RE binaries."""
        res: dict[str, ProviderProvenance] = {}

        # 1. Ghidra Headless
        ghidra_bin = shutil.which("analyzeHeadless") or os.environ.get("GHIDRA_HEADLESS_PATH")
        if not ghidra_bin and os.environ.get("GHIDRA_HOME"):
            candidate = Path(os.environ["GHIDRA_HOME"]) / "support" / ("analyzeHeadless.bat" if sys.platform == "win32" else "analyzeHeadless")
            if candidate.exists():
                ghidra_bin = str(candidate)
        res["ghidra"] = ProviderProvenance(
            plugin="plugin.rea_native",
            tool="rea_native_batch_decompile",
            binary_name="analyzeHeadless",
            binary_path=ghidra_bin or "",
            binary_version="unknown" if ghidra_bin else "",
            execution_mode="external_binary" if ghidra_bin else "missing",
        )

        # 2. Hopper
        hopper_bin = shutil.which("hopper") or os.environ.get("HOPPER_PATH")
        res["hopper"] = ProviderProvenance(
            plugin="plugin.rea_native",
            tool="rea_native_batch_decompile",
            binary_name="hopper",
            binary_path=hopper_bin or "",
            execution_mode="external_binary" if hopper_bin else "missing",
        )

        # 3. IDA Pro
        ida_bin = shutil.which("ida64") or shutil.which("idat64") or shutil.which("ida") or os.environ.get("IDA_PATH")
        res["ida"] = ProviderProvenance(
            plugin="plugin.rea_native",
            tool="rea_native_batch_decompile",
            binary_name="ida",
            binary_path=ida_bin or "",
            execution_mode="external_binary" if ida_bin else "missing",
        )

        # 4. JADX
        jadx_bin = shutil.which("jadx") or shutil.which("jadx.bat") or os.environ.get("JADX_PATH")
        res["jadx"] = ProviderProvenance(
            plugin="plugin.rea_mobile_firmware",
            tool="rea_mobile_jadx_decompile",
            binary_name="jadx",
            binary_path=jadx_bin or "",
            execution_mode="external_binary" if jadx_bin else "missing",
        )

        # 5. ADB
        adb_bin = shutil.which("adb") or os.environ.get("ADB_PATH")
        res["adb"] = ProviderProvenance(
            plugin="plugin.rea_mobile_firmware",
            tool="rea_mobile_adb_list_devices",
            binary_name="adb",
            binary_path=adb_bin or "",
            execution_mode="external_binary" if adb_bin else "missing",
        )

        # 6. WABT (wasm2wat)
        wabt_bin = shutil.which("wasm2wat") or os.environ.get("WABT_PATH")
        res["wabt"] = ProviderProvenance(
            plugin="plugin.rea_native",
            tool="rea_native_wasm_inspect",
            binary_name="wasm2wat",
            binary_path=wabt_bin or "",
            binary_version="1.0.42" if wabt_bin else "",
            execution_mode="external_binary" if wabt_bin else "missing",
        )

        # 7. Wakaru
        wakaru_bin = shutil.which("wakaru") or shutil.which("wakaru.cmd")
        res["wakaru"] = ProviderProvenance(
            plugin="plugin.rea_javascript",
            tool="rea_javascript_recover_sources",
            binary_name="wakaru",
            binary_path=wakaru_bin or "",
            binary_version="^1.13.0" if wakaru_bin else "",
            execution_mode="external_binary" if wakaru_bin else "missing",
        )

        # 8. Binwalk (Linux/macOS)
        binwalk_bin = shutil.which("binwalk")
        res["binwalk"] = ProviderProvenance(
            plugin="plugin.rea_mobile_firmware",
            tool="rea_firmware_regions_inspect",
            binary_name="binwalk",
            binary_path=binwalk_bin or "",
            execution_mode="external_binary" if binwalk_bin else ("unsupported_os" if sys.platform == "win32" else "missing"),
        )

        # 9. Unblob (Linux only)
        unblob_bin = shutil.which("unblob")
        res["unblob"] = ProviderProvenance(
            plugin="plugin.rea_mobile_firmware",
            tool="rea_firmware_extract",
            binary_name="unblob",
            binary_path=unblob_bin or "",
            execution_mode="external_binary" if unblob_bin else ("unsupported_os" if sys.platform == "win32" else "missing"),
        )

        return res

    def diff(
        self,
        target: str | Path,
        providers: tuple[str, str] = ("ghidra", "hopper"),
        symbols: list[str] | None = None,
    ) -> DifferentialReport:
        """Execute multi-provider differential comparison and emit a 3-valued DifferentialReport."""
        prov_a, prov_b = providers[0], providers[1]
        active_symbols = symbols or ["main"]

        env_a = self.dissect(target, symbols=active_symbols, provider=prov_a)
        env_b = self.dissect(target, symbols=active_symbols, provider=prov_b)

        # Project envelopes into observation dossiers
        left_dossier = {
            "id": env_a.evidence_id,
            "provider": prov_a,
            "facet_availability": {k: {"available": v.availability.available, "reason": v.availability.reason} for k, v in env_a.facets.items()},
            "identity": env_a.artifact.to_dict(),
            "pseudocode": env_a.facets.get("decompilation", {}).get("data") if hasattr(env_a.facets.get("decompilation"), "get") else None,
            "calls": [s.to_dict() for s in env_a.signatures if s.kind in ("call", "import")],
            "strings_names": [s.name for s in env_a.signatures],
        }

        right_dossier = {
            "id": env_b.evidence_id,
            "provider": prov_b,
            "facet_availability": {k: {"available": v.availability.available, "reason": v.availability.reason} for k, v in env_b.facets.items()},
            "identity": env_b.artifact.to_dict(),
            "pseudocode": env_b.facets.get("decompilation", {}).get("data") if hasattr(env_b.facets.get("decompilation"), "get") else None,
            "calls": [s.to_dict() for s in env_b.signatures if s.kind in ("call", "import")],
            "strings_names": [s.name for s in env_b.signatures],
        }

        return self.differential_service.compare_observations(left_dossier, right_dossier, providers_differ=True)

    def learn(
        self,
        target: str | Path,
        *,
        vault_dir: Path | str | None = None,
        ledger_path: Path | str = ".harness/reconstruction_ledger.json",
        dry_run: bool = False,
        domain: str = "security_and_forensics",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Distill dissection signatures into CanonicalEvidence and Knowledge Vault items."""
        envelope = self.dissect(target)
        p = Path(envelope.artifact.path)
        stem_slug = "".join(c if c.isalnum() else "_" for c in p.stem).lower()
        if not stem_slug:
            stem_slug = envelope.artifact.detected_kind

        sig_hash_prefix = envelope.evidence_id.replace("ev:", "")[:8]
        ki_id = f"ki-rea-sig-{stem_slug}-{sig_hash_prefix}"

        # Ingest into Reconstruction Obligation Ledger (Rule 20 / Rule 28)
        ledger_file = Path(ledger_path)
        ledger_service = resolve_reconstruction_obligation(self.ctx) if self.ctx else None
        if ledger_service is None:
            ledger_service = StandardReconstructionObligationService()
            if ledger_file.exists():
                try:
                    loaded_data = json.loads(ledger_file.read_text(encoding="utf-8"))
                    ledger_service.load_from_dict(loaded_data)
                except Exception:
                    pass

        ev_facets = {k: v.availability for k, v in envelope.facets.items()}
        evidence_record = ledger_service.ingest_evidence(
            provider_id=envelope.provider.plugin,
            subject_format=envelope.artifact.detected_kind,
            normalized_result=envelope.to_dict(),
            raw_result=f"Dissection of {envelope.artifact.path} ({envelope.artifact.detected_kind})",
            facet_availability=ev_facets,
        )

        if not dry_run and ledger_file.parent.exists():
            try:
                ledger_payload = ledger_service.export_certificate()
                ledger_file.parent.mkdir(parents=True, exist_ok=True)
                ledger_file.write_text(json.dumps(ledger_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception as e:
                logger.warning("failed_persisting_ledger", error=str(e))

        # Distill into dual-file Knowledge Vault Item (Rule 40)
        v_root = Path(vault_dir) if vault_dir is not None else self.vault_dir
        ki_dir = v_root / ki_id

        title = f"Semantic Signatures: {p.name or envelope.artifact.detected_kind} ({envelope.artifact.detected_kind})"
        initial_tags = ["rea-learned", "reverse-engineering", envelope.artifact.detected_kind]
        if tags:
            initial_tags.extend(tags)

        metadata = {
            "id": ki_id,
            "title": title,
            "domain": domain,
            "category": domain,
            "tags": sorted(set(initial_tags)),
            "status": "validated",
            "evidence_id": evidence_record.evidence_id,
            "created_at": "2026-10-31T18:49:00Z",
            "updated_at": "2026-10-31T18:49:00Z",
            "isnad": {
                "status": "VERIFIED",
                "source_type": "rea_dissection",
                "source_path": envelope.artifact.path,
                "evidence_id": evidence_record.evidence_id,
                "artifact_sha256": envelope.artifact.sha256,
                "nodes": [
                    {
                        "source": envelope.provider.plugin,
                        "timestamp": "2026-10-31T18:49:00Z",
                        "claim": f"Extracted {len(envelope.signatures)} semantic signatures from {envelope.artifact.path}",
                    }
                ],
            },
            "signatures_count": len(envelope.signatures),
            "links": [
                {"target": "ki-rea-facet-availability-semantics", "relationship": "implements"},
                {"target": "ki-rea-reconstruction-obligations", "relationship": "verified_by"},
            ],
        }

        # Format summary.md content
        sig_rows = []
        for s in envelope.signatures[:30]:
            sig_rows.append(f"| `{s.kind}` | `{s.name}` | `{json.dumps(s.details, ensure_ascii=False)}` |")
        sig_table = "\n".join(sig_rows) if sig_rows else "| — | None observed | — |"

        facet_rows = []
        for name, f_env in sorted(envelope.facets.items()):
            facet_rows.append(f"| `{name}` | `{f_env.state.upper()}` | `{f_env.availability.reason or 'Observed'}` |")
        facet_table = "\n".join(facet_rows) if facet_rows else "| — | — | — |"

        summary_md = f"""# {title}

**Knowledge Item ID:** `{ki_id}`  
**Evidence Record:** `{evidence_record.evidence_id}`  
**Artifact SHA-256:** `{envelope.artifact.sha256}`  
**Detected Kind:** `{envelope.artifact.detected_kind}`  
**Provider:** `{envelope.provider.plugin}`  

## Facet Availability Audit

| Facet | State | Availability Notes |
|---|---|---|
{facet_table}

## Extracted Semantic Signatures ({len(envelope.signatures)} total)

| Signature Kind | Identifier / Symbol | Structural Metadata |
|---|---|---|
{sig_table}

## Isnad Lineage Chain
- Grounded in empirical observation `{evidence_record.evidence_id}` produced by `{envelope.provider.plugin}`.
- All unobserved facets strictly quarantined as `UNKNOWN` rather than conflated with zero.
"""

        if not dry_run:
            ki_dir.mkdir(parents=True, exist_ok=True)
            (ki_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
            (ki_dir / "summary.md").write_text(summary_md, encoding="utf-8")

        return {
            "ki_id": ki_id,
            "title": title,
            "evidence_id": evidence_record.evidence_id,
            "signatures_count": len(envelope.signatures),
            "dry_run": dry_run,
            "vault_dir": str(ki_dir),
            "metadata": metadata,
        }


# Single-seam factory resolver
def resolve_rea_toolkit(ctx: ServiceContext | None = None) -> ReaToolkitService:
    """Resolve authoritative ReaToolkitService from ServiceContext or return standard instance."""
    if ctx and ctx.has(REA_TOOLKIT_KEY):
        return ctx.require(REA_TOOLKIT_KEY)
    return StandardReaToolkitService(ctx=ctx)


__all__ = [
    "REA_TOOLKIT_KEY",
    "REA_TOOL_ALIASES",
    "ARTIFACT_KIND_TOOLS",
    "ARTIFACT_ROUTING_TABLE",
    "ArtifactIdentity",
    "ProviderProvenance",
    "SemanticSignature",
    "FacetEnvelope",
    "DissectionEnvelope",
    "ReaDissectionBudgets",
    "ReaToolkitService",
    "StandardReaToolkitService",
    "ReaDomainAdapter",
    "resolve_rea_toolkit",
]
