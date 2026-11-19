"""Offset-indexed binary artifact bundle supporting O(1) seek/read lookups (Rule 48)."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .models import ArtifactOffsetRecord


class OffsetManifestIndex:
    """Contiguous binary artifact bundle with JSON sidecar offsets for direct byte-range seeks."""

    def __init__(self, bundle_path: Path, records: dict[str, ArtifactOffsetRecord]) -> None:
        self._bundle_path = Path(bundle_path)
        self._records = dict(records)

    @property
    def bundle_path(self) -> Path:
        return self._bundle_path

    @property
    def records(self) -> Mapping[str, ArtifactOffsetRecord]:
        return MappingProxyType(self._records)

    @classmethod
    def default_index_path(cls, bundle_path: Path) -> Path:
        return Path(f"{bundle_path}.index.json")

    @classmethod
    def build(
        cls,
        bundle_path: Path,
        artifacts: Mapping[str, Any],
        *,
        index_path: Path | None = None,
    ) -> OffsetManifestIndex:
        """Pack artifacts into ``bundle_path`` and persist offset metadata."""
        bundle = Path(bundle_path)
        idx_file = Path(index_path) if index_path is not None else cls.default_index_path(bundle)
        bundle.parent.mkdir(parents=True, exist_ok=True)
        records: dict[str, ArtifactOffsetRecord] = {}
        with open(bundle, "wb") as bf:
            for artifact_id, raw in artifacts.items():
                if isinstance(raw, (bytes, bytearray)):
                    data = bytes(raw)
                elif isinstance(raw, str):
                    data = raw.encode("utf-8")
                else:
                    data = json.dumps(raw, sort_keys=True).encode("utf-8")
                offset = bf.tell()
                bf.write(data)
                records[artifact_id] = ArtifactOffsetRecord(
                    artifact_id=artifact_id,
                    offset=offset,
                    size_bytes=len(data),
                )
        idx_payload = [
            {"artifact_id": r.artifact_id, "offset": r.offset, "size_bytes": r.size_bytes}
            for r in records.values()
        ]
        idx_file.write_text(json.dumps(idx_payload, indent=2), encoding="utf-8")
        return cls(bundle, records)

    @classmethod
    def load(cls, bundle_path: Path, *, index_path: Path | None = None) -> OffsetManifestIndex:
        """Load offset records from the sidecar JSON index."""
        bundle = Path(bundle_path)
        idx_file = Path(index_path) if index_path is not None else cls.default_index_path(bundle)
        raw_items = json.loads(idx_file.read_text(encoding="utf-8"))
        records = {
            item["artifact_id"]: ArtifactOffsetRecord(
                artifact_id=item["artifact_id"],
                offset=int(item["offset"]),
                size_bytes=int(item["size_bytes"]),
            )
            for item in raw_items
        }
        return cls(bundle, records)

    def read_bytes(self, artifact_id: str) -> bytes:
        """Read an artifact slice directly via ``seek(offset)`` + ``read(size_bytes)``."""
        rec = self._records[artifact_id]
        with open(self._bundle_path, "rb") as bf:
            bf.seek(rec.offset)
            data = bf.read(rec.size_bytes)
        if len(data) != rec.size_bytes:
            raise OSError(f"Short read for {artifact_id!r}: expected {rec.size_bytes}, got {len(data)}")
        return data

    def read_json(self, artifact_id: str) -> Any:
        """Decode a UTF-8 JSON payload from its packed binary slice."""
        return json.loads(self.read_bytes(artifact_id).decode("utf-8"))
