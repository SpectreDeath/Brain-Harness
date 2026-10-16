"""Pure-Python Dalvik Executable (DEX) Header & Class Descriptor Reader.

Provides zero-dependency offline extraction of class names, type descriptors,
and string tables directly from raw .dex files or APK archives.
Adheres to Rule 12 (dataclasses with slots) and Rule 32 (defensive visibility).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import struct
from typing import Any
import zipfile
import structlog

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class DexHeader:
    """Parsed Dalvik Executable file header."""

    file_size: int
    header_size: int
    endian_tag: int
    string_ids_size: int
    string_ids_off: int
    type_ids_size: int
    type_ids_off: int
    class_defs_size: int
    class_defs_off: int


class DexReader:
    """Pure-Python parser for Android Dalvik Executable (DEX) binaries."""

    DEX_MAGIC_PREFIX = b"dex\n"

    @classmethod
    def is_dex(cls, data: bytes) -> bool:
        """Verify whether byte stream starts with valid DEX magic bytes."""
        return len(data) >= 8 and data[:4] == cls.DEX_MAGIC_PREFIX

    @classmethod
    def parse_header(cls, data: bytes) -> DexHeader | None:
        """Parse DEX file header fields."""
        if not cls.is_dex(data) or len(data) < 112:
            return None

        try:
            # Header layout (offsets 32 to 104):
            # 32: file_size (4)
            # 36: header_size (4)
            # 40: endian_tag (4)
            # 44: link_size (4)
            # 48: link_off (4)
            # 52: map_off (4)
            # 56: string_ids_size (4)
            # 60: string_ids_off (4)
            # 64: type_ids_size (4)
            # 68: type_ids_off (4)
            # 72: proto_ids_size (4)
            # 76: proto_ids_off (4)
            # 80: field_ids_size (4)
            # 84: field_ids_off (4)
            # 88: method_ids_size (4)
            # 92: method_ids_off (4)
            # 96: class_defs_size (4)
            # 100: class_defs_off (4)
            endian = "<"
            endian_tag = struct.unpack_from("<I", data, 40)[0]
            if endian_tag == 0x78563412:
                endian = ">"  # Reverse endian

            (
                file_size,
                header_size,
                _,
                _,
                _,
                _,
                string_ids_size,
                string_ids_off,
                type_ids_size,
                type_ids_off,
                _,
                _,
                _,
                _,
                _,
                _,
                class_defs_size,
                class_defs_off,
            ) = struct.unpack_from(f"{endian}18I", data, 32)

            return DexHeader(
                file_size=file_size,
                header_size=header_size,
                endian_tag=endian_tag,
                string_ids_size=string_ids_size,
                string_ids_off=string_ids_off,
                type_ids_size=type_ids_size,
                type_ids_off=type_ids_off,
                class_defs_size=class_defs_size,
                class_defs_off=class_defs_off,
            )
        except Exception as err:
            logger.debug("dex_header_parse_failed", error=str(err))
            return None

    @classmethod
    def _read_uleb128(cls, data: bytes, offset: int) -> tuple[int, int]:
        """Decode an unsigned LEB128 integer returning (value, new_offset)."""
        result = 0
        shift = 0
        pos = offset
        while pos < len(data):
            byte = data[pos]
            pos += 1
            result |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
        return result, pos

    @classmethod
    def read_string(cls, data: bytes, string_data_off: int) -> str:
        """Read a null-terminated MUTF-8 string from DEX data section."""
        if string_data_off >= len(data):
            return ""
        try:
            _, str_start = cls._read_uleb128(data, string_data_off)
            null_pos = data.find(b"\x00", str_start)
            if null_pos == -1:
                null_pos = min(str_start + 256, len(data))
            return data[str_start:null_pos].decode("utf-8", errors="replace")
        except Exception:
            return ""

    @classmethod
    def extract_classes(cls, data: bytes, max_classes: int = 1000) -> list[str]:
        """Extract fully-qualified class names from a DEX binary."""
        header = cls.parse_header(data)
        if not header:
            return []

        classes: list[str] = []
        try:
            # Step 1: Read string offsets table
            str_offsets: list[int] = []
            str_count = min(header.string_ids_size, 5000)
            for i in range(str_count):
                off = header.string_ids_off + (i * 4)
                if off + 4 <= len(data):
                    str_offsets.append(struct.unpack_from("<I", data, off)[0])

            # Step 2: Read type IDs table (maps type_idx -> string_idx)
            type_to_str_idx: list[int] = []
            type_count = min(header.type_ids_size, 5000)
            for i in range(type_count):
                off = header.type_ids_off + (i * 4)
                if off + 4 <= len(data):
                    type_to_str_idx.append(struct.unpack_from("<I", data, off)[0])

            # Helper to resolve type_idx to class name
            def resolve_type(type_idx: int) -> str | None:
                if 0 <= type_idx < len(type_to_str_idx):
                    s_idx = type_to_str_idx[type_idx]
                    if 0 <= s_idx < len(str_offsets):
                        raw = cls.read_string(data, str_offsets[s_idx])
                        if raw.startswith("L") and raw.endswith(";"):
                            # Convert descriptor Lcom/example/App; -> com.example.App
                            return raw[1:-1].replace("/", ".")
                return None

            # Step 3: Read defined classes if class_defs table exists
            if header.class_defs_size > 0 and header.class_defs_off < len(data):
                class_count = min(header.class_defs_size, max_classes)
                for i in range(class_count):
                    off = header.class_defs_off + (i * 32)
                    if off + 4 <= len(data):
                        class_idx = struct.unpack_from("<I", data, off)[0]
                        cname = resolve_type(class_idx)
                        if cname and cname not in classes:
                            classes.append(cname)

            # Step 4: If no defined classes found, collect class-like types from type table
            if not classes:
                for t_idx in range(len(type_to_str_idx)):
                    cname = resolve_type(t_idx)
                    if cname and not cname.startswith("android.") and not cname.startswith("java."):
                        if cname not in classes:
                            classes.append(cname)
                    if len(classes) >= max_classes:
                        break

        except Exception as err:
            logger.debug("dex_classes_extraction_failed", error=str(err))

        return classes

    @classmethod
    def extract_dex_from_apk(cls, apk_path: str | Path) -> list[tuple[str, bytes]]:
        """Extract all DEX file entries (.dex) from an APK archive."""
        p = Path(apk_path)
        if not p.exists() or not zipfile.is_zipfile(p):
            return []

        dex_entries: list[tuple[str, bytes]] = []
        try:
            with zipfile.ZipFile(p, "r") as zf:
                for name in zf.namelist():
                    if name.endswith(".dex") and not name.startswith("__MACOSX"):
                        dex_entries.append((name, zf.read(name)))
        except Exception as err:
            logger.warning("apk_dex_extraction_failed", apk=str(p), error=str(err))

        return dex_entries
