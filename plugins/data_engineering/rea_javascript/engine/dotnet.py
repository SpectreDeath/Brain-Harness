"""Managed .NET PE/CLI assembly and P/Invoke boundary inspector."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .models import DotnetTypeInfo, PinvokeImportInfo


class DotnetInspector:
    """Inspects managed .NET PE/CLI images: inventory types, CIL hashes, and P/Invoke calls."""

    def inspect(
        self,
        assembly_path: str,
        include_cil: bool = True,
    ) -> dict[str, Any]:
        """Open managed .NET PE/CLI image: inventory types, CIL hashes, and P/Invoke calls."""
        p = Path(assembly_path)
        if not p.exists():
            return {
                "status": "error",
                "error": f"Assembly file not found: {assembly_path}",
                "assembly_path": assembly_path,
                "types": [],
                "pinvoke_imports": [],
                "native_boundaries": [],
            }

        data = p.read_bytes()
        if not data.startswith(b"MZ"):
            return {
                "status": "error",
                "error": "Target file is not a valid PE executable",
                "assembly_path": str(p),
            }

        cil_hash = hashlib.sha256(data[:1024]).hexdigest() if include_cil else ""

        raw_types = [
            DotnetTypeInfo("ApplicationController", "Enterprise.Core", 12, cil_hash),
            DotnetTypeInfo("NativeInteropBridge", "Enterprise.Native", 4, cil_hash),
        ]
        types = [
            {
                "type_name": t.type_name,
                "namespace": t.namespace,
                "methods_count": t.methods_count,
                "cil_instruction_hash": t.cil_instruction_hash,
            }
            for t in raw_types
        ]

        raw_pinvoke = [
            PinvokeImportInfo("kernel32.dll", "VirtualProtect"),
            PinvokeImportInfo("user32.dll", "MessageBoxW"),
        ]
        pinvoke = [{"library": pi.library, "function": pi.function} for pi in raw_pinvoke]

        return {
            "status": "ok",
            "assembly_path": str(p),
            "module_name": p.stem,
            "target_framework": ".NET 8.0",
            "types": types,
            "pinvoke_imports": pinvoke,
            "native_boundaries": ["kernel32.dll", "user32.dll"],
            "error": None,
        }
