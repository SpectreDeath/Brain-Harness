"""Coordinating facade engine for REA Managed Runtime & Bytecode Forensics."""

from __future__ import annotations

from typing import Any

from harness.services.rea_managed_runtime import (
    Il2cppMetadataReport,
    ManagedArtifactReport,
    ManagedBoundariesReport,
    ModelArtifactReport,
    PycInspectReport,
)
from plugins.security_and_forensics.rea_managed_runtime.engine.il2cpp import (
    Il2cppMetadataParser,
)
from plugins.security_and_forensics.rea_managed_runtime.engine.managed_pe import (
    ManagedPeEngine,
)
from plugins.security_and_forensics.rea_managed_runtime.engine.model_artifact import (
    ModelArtifactEngine,
)
from plugins.security_and_forensics.rea_managed_runtime.engine.pyc import PycEngine


class ReaManagedRuntimeEngine:
    """Coordinating facade delegating to specialized managed PE, IL2CPP, model, and pyc engines."""

    __slots__ = (
        "_managed_pe",
        "_il2cpp",
        "_model",
        "_pyc",
    )

    def __init__(self) -> None:
        self._managed_pe = ManagedPeEngine()
        self._il2cpp = Il2cppMetadataParser()
        self._model = ModelArtifactEngine()
        self._pyc = PycEngine()

    def inspect_managed_artifact(
        self,
        target_path: str,
        extract_members: bool = True,
    ) -> ManagedArtifactReport:
        """Inspect a PE/CLI binary or .NET DLL."""
        return self._managed_pe.inspect_artifact(target_path, extract_members=extract_members)

    def inspect_managed_native_boundaries(
        self,
        target_path: str,
    ) -> ManagedBoundariesReport:
        """Inspect PE/CLI ModuleRef and P/Invoke declarations."""
        return self._managed_pe.inspect_native_boundaries(target_path)

    def inspect_il2cpp_metadata(
        self,
        metadata_path: str,
        max_records: int = 100,
    ) -> Il2cppMetadataReport:
        """Parse Unity IL2CPP global-metadata.dat."""
        return self._il2cpp.parse(metadata_path, max_records=max_records)

    def inspect_model_artifact(
        self,
        model_path: str,
        preview_tensors: int = 50,
    ) -> ModelArtifactReport:
        """Inspect GGUF v2/v3 or safetensors headers using direct byte seeks."""
        return self._model.inspect_model(model_path, preview_tensors=preview_tensors)

    def inspect_python_pyc(
        self,
        pyc_path: str,
        disassemble: bool = True,
    ) -> PycInspectReport:
        """Inspect CPython .pyc bytecode file and disassemble instructions."""
        return self._pyc.inspect_pyc(pyc_path, disassemble=disassemble)


__all__ = [
    "Il2cppMetadataParser",
    "ManagedPeEngine",
    "ModelArtifactEngine",
    "PycEngine",
    "ReaManagedRuntimeEngine",
]
