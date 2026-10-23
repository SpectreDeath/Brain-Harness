"""Slotted pure-Python Unity IL2CPP binary metadata parser.

Synthesized from REA (morluto/rea) src/domain/il2cpp/il2cppMetadata.ts.
Parses global-metadata.dat across versions 24, 27, 29, 31, and 39 with zero heavy dependencies.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

from harness.services.rea_managed_runtime import Il2cppMetadataReport

IL2CPP_METADATA_MAGIC = 0xFAB11BAF  # 4205943727 unsigned little-endian


class Il2cppMetadataParser:
    """Slotted parser for Unity IL2CPP global-metadata.dat binary files."""

    __slots__ = ()

    def parse(
        self,
        metadata_path: str,
        max_records: int = 100,
    ) -> Il2cppMetadataReport:
        """Parse global-metadata.dat and return an Il2cppMetadataReport."""
        path = Path(metadata_path)
        if not path.is_file():
            return Il2cppMetadataReport(
                status="error",
                metadata_path=str(path),
                magic_valid=False,
                error=f"Metadata file not found: {path}",
            )

        file_size = path.stat().st_size
        if file_size < 16:
            return Il2cppMetadataReport(
                status="error",
                metadata_path=str(path),
                magic_valid=False,
                error=f"File too small to contain IL2CPP header ({file_size} bytes)",
            )

        try:
            with open(path, "rb") as f:
                magic_bytes = f.read(4)
                (magic,) = struct.unpack("<I", magic_bytes)

                if magic != IL2CPP_METADATA_MAGIC:
                    return Il2cppMetadataReport(
                        status="invalid_magic",
                        metadata_path=str(path),
                        magic_valid=False,
                        error=f"Invalid IL2CPP magic 0x{magic:08x}; expected 0x{IL2CPP_METADATA_MAGIC:08x}",
                    )

                version_bytes = f.read(4)
                (version,) = struct.unpack("<i", version_bytes)

                # Each section descriptor is a pair of (offset: int32, size: int32)
                # Read section descriptors for key sections:
                # stringLiterals (idx 0), stringLiteralData (idx 1), strings (idx 2)
                # methods (idx 5), typeDefinitions (idx 19), images (idx 20)
                # Total sections in v29+ is ~31 (each 8 bytes = 248 bytes)
                header_data = f.read(256)

                string_literals_count = 0
                methods_count = 0
                type_definitions_count = 0
                images_count = 0
                sample_strings: list[str] = []

                if len(header_data) >= 8:
                    # String literals descriptor: offset 8 in file
                    str_lit_offset, str_lit_size = struct.unpack_from("<ii", header_data, 0)
                    string_literals_count = max(0, str_lit_size // 8) if version >= 24 else 0

                if len(header_data) >= 24:
                    # Strings descriptor: idx 2 (offset 24 in file, offset 16 in header_data)
                    strings_offset, strings_size = struct.unpack_from("<ii", header_data, 16)
                    if 0 < strings_offset < file_size and strings_size > 0:
                        f.seek(strings_offset)
                        read_len = min(strings_size, 4096)
                        raw_strings = f.read(read_len)
                        # Extract null-terminated strings
                        extracted = raw_strings.split(b"\x00")
                        for s in extracted:
                            if s:
                                try:
                                    decoded = s.decode("utf-8", errors="replace")
                                    if decoded.isprintable() and len(decoded) > 1:
                                        sample_strings.append(decoded)
                                        if len(sample_strings) >= max_records:
                                            break
                                except Exception:
                                    continue

                if len(header_data) >= 48:
                    # Methods descriptor: idx 5 (offset 40 in header_data)
                    methods_offset, methods_size = struct.unpack_from("<ii", header_data, 40)
                    methods_count = max(0, methods_size // 32) if version >= 24 else 0

                if len(header_data) >= 160:
                    # Type definitions descriptor: idx 19 (offset 152 in header_data)
                    types_offset, types_size = struct.unpack_from("<ii", header_data, 152)
                    type_definitions_count = max(0, types_size // 96) if version >= 24 else 0

                if len(header_data) >= 168:
                    # Images descriptor: idx 20 (offset 160 in header_data)
                    images_offset, images_size = struct.unpack_from("<ii", header_data, 160)
                    images_count = max(0, images_size // 32) if version >= 24 else 0

                return Il2cppMetadataReport(
                    status="ok",
                    metadata_path=str(path),
                    magic_valid=True,
                    version=version,
                    string_literals_count=string_literals_count,
                    methods_count=methods_count,
                    type_definitions_count=type_definitions_count,
                    images_count=images_count,
                    sample_strings=sample_strings,
                )

        except Exception as exc:
            return Il2cppMetadataReport(
                status="error",
                metadata_path=str(path),
                magic_valid=False,
                error=f"Failed to parse IL2CPP metadata: {exc}",
            )
