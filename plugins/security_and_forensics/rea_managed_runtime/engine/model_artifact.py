"""Slotted pure-Python AI model artifact inspection engine.

Synthesized from REA (morluto/rea) src/domain/model/modelArtifact.ts.
Inspects GGUF v2/v3 and safetensors files using direct O(1) byte-offset seeks
without allocating RAM or GPU memory for weight buffers (Rule 48).
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from harness.services.rea_managed_runtime import (
    ModelArtifactReport,
    ModelTensorDescriptor,
)

GGUF_MAGIC = b"GGUF"  # 0x46554747 little-endian


class ModelArtifactEngine:
    """Slotted engine for zero-allocation GGUF and safetensors inspection."""

    __slots__ = ()

    def inspect_model(
        self,
        model_path: str,
        preview_tensors: int = 50,
    ) -> ModelArtifactReport:
        """Inspect model artifact header and return ModelArtifactReport."""
        path = Path(model_path)
        if not path.is_file():
            return ModelArtifactReport(
                status="error",
                model_path=str(path),
                error=f"File not found: {path}",
            )

        file_size = path.stat().st_size
        if file_size < 8:
            return ModelArtifactReport(
                status="error",
                model_path=str(path),
                error=f"File too small ({file_size} bytes)",
            )

        try:
            with open(path, "rb") as f:
                prefix = f.read(8)

                # Check GGUF
                if prefix[:4] == GGUF_MAGIC:
                    return self._parse_gguf(f, path, prefix, preview_tensors)

                # Check Safetensors: uint64 header size
                (header_len,) = struct.unpack("<Q", prefix)
                if 2 < header_len < min(file_size - 8, 100_000_000):
                    test_bytes = f.read(2)
                    f.seek(8)
                    if test_bytes.startswith(b"{"):
                        return self._parse_safetensors(
                            f, path, header_len, preview_tensors
                        )

                return ModelArtifactReport(
                    status="unsupported_format",
                    model_path=str(path),
                    format="unknown",
                    error="Unrecognized model format; not GGUF or Safetensors",
                )

        except Exception as exc:
            return ModelArtifactReport(
                status="error",
                model_path=str(path),
                error=f"Failed to inspect model artifact: {exc}",
            )

    def _parse_gguf(
        self,
        f: Any,
        path: Path,
        prefix: bytes,
        preview_tensors: int,
    ) -> ModelArtifactReport:
        """Parse GGUF v2/v3 header via bounded byte seeks."""
        version = struct.unpack("<I", prefix[4:8])[0]
        format_name = f"gguf_v{version}"

        # GGUF v2/v3: tensor_count (uint64), metadata_kv_count (uint64)
        header_counts = f.read(16)
        if len(header_counts) < 16:
            return ModelArtifactReport(
                status="truncated",
                model_path=str(path),
                format=format_name,
                version=version,
                error="Truncated GGUF header counts",
            )

        tensor_count, kv_count = struct.unpack("<QQ", header_counts)
        metadata_preview: dict[str, Any] = {}

        # Parse a subset of metadata KV pairs
        def read_gguf_string() -> str | None:
            len_bytes = f.read(8)
            if len(len_bytes) < 8:
                return None
            str_len = struct.unpack("<Q", len_bytes)[0]
            if str_len > 10_000_000:
                return None
            val_bytes = f.read(str_len)
            return val_bytes.decode("utf-8", errors="replace")

        def skip_gguf_value(val_type: int) -> Any:
            # Type mapping: 0=U8, 1=I8, 2=U16, 3=I16, 4=U32, 5=I32, 6=F32, 7=BOOL,
            # 8=STRING, 9=ARRAY, 10=U64, 11=I64, 12=F64
            type_sizes = {
                0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8
            }
            if val_type in type_sizes:
                raw = f.read(type_sizes[val_type])
                if val_type == 7 and raw:
                    return bool(raw[0])
                if val_type in (0, 2, 4, 10) and raw:
                    fmt = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}[len(raw)]
                    return struct.unpack(fmt, raw)[0]
                if val_type in (1, 3, 5, 11) and raw:
                    fmt = {1: "<b", 2: "<h", 4: "<i", 8: "<q"}[len(raw)]
                    return struct.unpack(fmt, raw)[0]
                if val_type == 6 and raw:
                    return round(struct.unpack("<f", raw)[0], 4)
                if val_type == 12 and raw:
                    return round(struct.unpack("<d", raw)[0], 4)
                return "<scalar>"
            elif val_type == 8:
                return read_gguf_string()
            elif val_type == 9:
                elem_type_and_len = f.read(12)
                if len(elem_type_and_len) == 12:
                    elem_type, arr_len = struct.unpack("<IQ", elem_type_and_len)
                    # Skip array data without materializing full arrays into RAM
                    if elem_type in type_sizes:
                        f.seek(f.tell() + (arr_len * type_sizes[elem_type]))
                    else:
                        for _ in range(min(arr_len, 5)):
                            read_gguf_string()
                    return f"<array of {arr_len} items>"
            return "<unknown>"

        for _ in range(min(kv_count, 30)):
            k = read_gguf_string()
            if not k:
                break
            type_bytes = f.read(4)
            if len(type_bytes) < 4:
                break
            v_type = struct.unpack("<I", type_bytes)[0]
            val = skip_gguf_value(v_type)
            metadata_preview[k] = val

        # Fast seek to tensor descriptors if possible
        tensors: list[ModelTensorDescriptor] = []
        return ModelArtifactReport(
            status="ok",
            model_path=str(path),
            format=format_name,
            version=version,
            tensor_count=tensor_count,
            metadata_kv_count=kv_count,
            metadata_preview=metadata_preview,
            tensors=tensors,
        )

    def _parse_safetensors(
        self,
        f: Any,
        path: Path,
        header_len: int,
        preview_tensors: int,
    ) -> ModelArtifactReport:
        """Parse Safetensors JSON header without reading weights."""
        header_bytes = f.read(header_len)
        header_str = header_bytes.decode("utf-8", errors="replace")
        header_json = json.loads(header_str)

        metadata_dict = header_json.get("__metadata__") or {}
        tensors: list[ModelTensorDescriptor] = []

        for key, val in header_json.items():
            if key == "__metadata__" or not isinstance(val, dict):
                continue
            shape = val.get("shape") or []
            dtype = val.get("dtype") or "unknown"
            offsets = val.get("data_offsets") or [0, 0]
            start_off = offsets[0] if len(offsets) > 0 else 0
            end_off = offsets[1] if len(offsets) > 1 else start_off
            byte_len = max(0, end_off - start_off)

            if len(tensors) < preview_tensors:
                tensors.append(
                    ModelTensorDescriptor(
                        name=key,
                        type_name=dtype,
                        shape=shape,
                        offset=start_off,
                        byte_length=byte_len,
                    )
                )

        return ModelArtifactReport(
            status="ok",
            model_path=str(path),
            format="safetensors",
            version=1,
            tensor_count=len(header_json) - (1 if "__metadata__" in header_json else 0),
            metadata_kv_count=len(metadata_dict),
            metadata_preview=metadata_dict,
            tensors=tensors,
        )
