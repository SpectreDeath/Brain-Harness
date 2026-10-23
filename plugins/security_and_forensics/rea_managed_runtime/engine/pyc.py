"""Slotted pure-Python CPython .pyc bytecode inspection and disassembly engine.

Synthesized from REA (morluto/rea) src/domain/python/ and src/contracts/python/.
Validates 16-byte headers across Python 3.7-3.13 and disassembles code objects.
"""

from __future__ import annotations

import dis
import marshal
import struct
from pathlib import Path
from typing import Any

from harness.services.rea_managed_runtime import PycInspectReport

# Magic number mapping for CPython versions
CPYTHON_MAGIC_MAP = {
    3390: "3.7", 3391: "3.7", 3392: "3.7", 3393: "3.7", 3394: "3.7",
    3410: "3.8", 3411: "3.8", 3412: "3.8", 3413: "3.8",
    3420: "3.9", 3421: "3.9", 3422: "3.9", 3423: "3.9", 3424: "3.9", 3425: "3.9",
    3430: "3.10", 3431: "3.10", 3432: "3.10", 3433: "3.10", 3439: "3.10",
    3490: "3.11", 3491: "3.11", 3492: "3.11", 3493: "3.11", 3494: "3.11", 3495: "3.11",
    3530: "3.12", 3531: "3.12",
    3570: "3.13", 3571: "3.13",
}


class PycEngine:
    """Slotted engine for inspecting and disassembling CPython .pyc files."""

    __slots__ = ()

    def inspect_pyc(
        self,
        pyc_path: str,
        disassemble: bool = True,
    ) -> PycInspectReport:
        """Inspect CPython .pyc file and optionally disassemble bytecode."""
        path = Path(pyc_path)
        if not path.is_file():
            return PycInspectReport(
                status="error",
                pyc_path=str(path),
                error=f"File not found: {path}",
            )

        file_size = path.stat().st_size
        if file_size < 16:
            return PycInspectReport(
                status="error",
                pyc_path=str(path),
                error=f"File too small for valid .pyc header ({file_size} bytes)",
            )

        try:
            with open(path, "rb") as f:
                header = f.read(16)
                magic_num, crlf = struct.unpack("<2s2s", header[:4])
                if crlf != b"\r\n":
                    return PycInspectReport(
                        status="invalid_magic",
                        pyc_path=str(path),
                        error="Invalid .pyc CRLF terminator",
                    )

                (magic_val,) = struct.unpack("<H", magic_num)
                cpython_ver = CPYTHON_MAGIC_MAP.get(magic_val, f"CPython (magic {magic_val})")

                flags, timestamp = struct.unpack("<II", header[4:12])

                # Read code object using marshal
                f.seek(16)
                code_obj = marshal.load(f)

                code_name = getattr(code_obj, "co_name", "<module>")
                sample_dis: list[str] = []
                instruction_count = 0

                if disassemble:
                    try:
                        for instr in dis.get_instructions(code_obj):
                            instruction_count += 1
                            if len(sample_dis) < 30:
                                argval_repr = f" ({instr.argrepr})" if instr.argrepr else ""
                                sample_dis.append(
                                    f"{instr.offset:4d} {instr.opname:<20} {instr.arg or ''}{argval_repr}"
                                )
                    except Exception as dis_err:
                        sample_dis.append(f"<disassembly error: {dis_err}>")

                return PycInspectReport(
                    status="ok",
                    pyc_path=str(path),
                    magic=magic_val,
                    cpython_version=cpython_ver,
                    timestamp=timestamp,
                    code_object_name=code_name,
                    instruction_count=instruction_count,
                    sample_disassembly=sample_dis,
                )

        except Exception as exc:
            return PycInspectReport(
                status="error",
                pyc_path=str(path),
                error=f"Failed to inspect .pyc bytecode: {exc}",
            )
