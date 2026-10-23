"""REA Managed Runtime & Bytecode Forensics Plugin for Brain Harness.

Deepened architecture decomposing .NET PE/CLI metadata inspection,
Unity IL2CPP binary parsing, zero-allocation AI model artifact inspection,
and CPython bytecode disassembly into focused domain sub-engines.
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.rea_managed_runtime import (
    REA_MANAGED_RUNTIME_KEY,
    Il2cppMetadataReport,
    ManagedArtifactReport,
    ManagedBoundariesReport,
    ModelArtifactReport,
    PycInspectReport,
    ReaManagedRuntimeService,
)
from plugins.security_and_forensics.rea_managed_runtime.engine import (
    ReaManagedRuntimeEngine,
)

logger = structlog.get_logger(__name__)

_GLOBAL_ENGINE = ReaManagedRuntimeEngine()


# -----------------------------------------------------------------------------
# Top-Level Entrypoint Tool Handlers Matching Manifest Signatures
# -----------------------------------------------------------------------------


def rea_inspect_managed_artifact(
    target_path: str,
    extract_members: bool = True,
) -> ManagedArtifactReport:
    """Inspect an explicit Windows PE/CLI or .NET DLL without loading it as a live assembly."""
    return _GLOBAL_ENGINE.inspect_managed_artifact(
        target_path=target_path, extract_members=extract_members
    )


def rea_inspect_managed_native_boundaries(
    target_path: str,
) -> ManagedBoundariesReport:
    """Inspect PE/CLI ModuleRef, ImplMap, and P/Invoke declarations."""
    return _GLOBAL_ENGINE.inspect_managed_native_boundaries(target_path=target_path)


def rea_inspect_il2cpp_metadata(
    metadata_path: str,
    max_records: int = 100,
) -> Il2cppMetadataReport:
    """Parse Unity IL2CPP global-metadata.dat (versions 24, 27, 29, 31, 39)."""
    return _GLOBAL_ENGINE.inspect_il2cpp_metadata(
        metadata_path=metadata_path, max_records=max_records
    )


def rea_inspect_model_artifact(
    model_path: str,
    preview_tensors: int = 50,
) -> ModelArtifactReport:
    """Inspect local GGUF v2/v3 or safetensors headers using direct byte seeks."""
    return _GLOBAL_ENGINE.inspect_model_artifact(
        model_path=model_path, preview_tensors=preview_tensors
    )


def rea_inspect_python_pyc(
    pyc_path: str,
    disassemble: bool = True,
) -> PycInspectReport:
    """Inspect local CPython 3.7-3.13 .pyc bytecode files and disassemble opcodes."""
    return _GLOBAL_ENGINE.inspect_python_pyc(
        pyc_path=pyc_path, disassemble=disassemble
    )


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle (Rule 45)
# -----------------------------------------------------------------------------


class ReaManagedRuntimePlugin(HarnessPlugin, ReaManagedRuntimeService):
    """Brain Harness Plugin providing managed runtime and bytecode reverse engineering capabilities."""

    name = "plugin.rea_managed_runtime"
    version = "1.0.0"
    description = (
        "REA managed runtime & bytecode forensics: .NET PE/CLI headers, Unity IL2CPP global-metadata.dat, "
        "zero-allocation GGUF/safetensors inspection, and CPython bytecode disassembly."
    )
    trusted = True

    def __init__(self, engine: ReaManagedRuntimeEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [REA_MANAGED_RUNTIME_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(REA_MANAGED_RUNTIME_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation Delegations
    # -------------------------------------------------------------------------

    def inspect_managed_artifact(
        self,
        target_path: str,
        extract_members: bool = True,
    ) -> ManagedArtifactReport:
        return self._engine.inspect_managed_artifact(
            target_path=target_path, extract_members=extract_members
        )

    def inspect_managed_native_boundaries(
        self,
        target_path: str,
    ) -> ManagedBoundariesReport:
        return self._engine.inspect_managed_native_boundaries(target_path=target_path)

    def inspect_il2cpp_metadata(
        self,
        metadata_path: str,
        max_records: int = 100,
    ) -> Il2cppMetadataReport:
        return self._engine.inspect_il2cpp_metadata(
            metadata_path=metadata_path, max_records=max_records
        )

    def inspect_model_artifact(
        self,
        model_path: str,
        preview_tensors: int = 50,
    ) -> ModelArtifactReport:
        return self._engine.inspect_model_artifact(
            model_path=model_path, preview_tensors=preview_tensors
        )

    def inspect_python_pyc(
        self,
        pyc_path: str,
        disassemble: bool = True,
    ) -> PycInspectReport:
        return self._engine.inspect_python_pyc(
            pyc_path=pyc_path, disassemble=disassemble
        )


# Exported module-level singleton (Rule 45)
plugin = ReaManagedRuntimePlugin()
