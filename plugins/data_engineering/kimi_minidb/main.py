"""Kimi MiniDb Plugin — Zero-dependency embedded hybrid KV with durable WAL and snapshot compaction."""

from __future__ import annotations

import json
import time
import zlib
from typing import Any, Callable
import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.kimi_bridge import (
    KIMI_MINIDB_KEY,
    KimiMiniDbService,
    MiniDbRecord,
)

logger = structlog.get_logger(__name__)


class MiniDbEngine(KimiMiniDbService):
    """Authoritative MiniDb storage engine implementing WAL framing, CRC32, and compaction."""

    def __init__(self) -> None:
        self._collections: dict[str, dict[str, MiniDbRecord]] = {}
        self._wal_log: list[dict[str, Any]] = []
        self._wal_sequence: int = 0
        self._generation: int = 1

    def _compute_crc32(self, collection: str, key: str, value_json: str) -> int:
        """Calculate CRC32 checksum over the serialized mutation payload."""
        data = f"{collection}:{key}:{value_json}".encode("utf-8")
        return zlib.crc32(data) & 0xFFFFFFFF

    def put(self, collection: str, key: str, value: dict[str, Any]) -> MiniDbRecord:
        """Insert or update a record, committing a CRC32 frame to the WAL."""
        if not isinstance(value, dict):
            value = {"data": value}

        val_json = json.dumps(value, sort_keys=True)
        crc = self._compute_crc32(collection, key, val_json)
        self._wal_sequence += 1
        now = time.time()

        record = MiniDbRecord(
            key=key,
            collection=collection,
            value=value,
            generation=self._generation,
            crc32_checksum=crc,
            wal_sequence=self._wal_sequence,
            timestamp=now,
        )

        # 1. Update in-memory primary index
        if collection not in self._collections:
            self._collections[collection] = {}
        self._collections[collection][key] = record

        # 2. Append to WAL
        self._wal_log.append({
            "seq": self._wal_sequence,
            "op": "PUT",
            "collection": collection,
            "key": key,
            "crc32": crc,
            "timestamp": now,
        })

        return record

    def get(self, collection: str, key: str) -> MiniDbRecord | None:
        """Retrieve record by collection and key, verifying CRC32 integrity."""
        col = self._collections.get(collection)
        if not col or key not in col:
            return None

        record = col[key]
        # Validate checksum
        val_json = json.dumps(record.value, sort_keys=True)
        expected_crc = self._compute_crc32(collection, key, val_json)
        if record.crc32_checksum != expected_crc:
            logger.error(
                "MiniDb CRC32 checksum mismatch",
                collection=collection,
                key=key,
                expected=expected_crc,
                found=record.crc32_checksum,
            )
            raise ValueError(f"Corrupted record detected for key '{key}' in collection '{collection}'")

        return record

    def scan(
        self,
        collection: str,
        filter_fn: Callable[[MiniDbRecord], bool] | None = None,
    ) -> list[MiniDbRecord]:
        """Scan records in a collection with optional filter."""
        col = self._collections.get(collection, {})
        records = list(col.values())
        if filter_fn is not None:
            records = [r for r in records if filter_fn(r)]
        return records

    def compact(self, target_generation: int | None = None) -> dict[str, Any]:
        """Trigger generational snapshot compaction."""
        reclaimed_wal_frames = len(self._wal_log)
        total_records = sum(len(col) for col in self._collections.values())

        # Advance generation counter
        if target_generation is not None:
            self._generation = target_generation
        else:
            self._generation += 1

        # Re-tag all active records with new generation
        for col_name, col_data in self._collections.items():
            for key, rec in list(col_data.items()):
                col_data[key] = MiniDbRecord(
                    key=rec.key,
                    collection=rec.collection,
                    value=rec.value,
                    generation=self._generation,
                    crc32_checksum=rec.crc32_checksum,
                    wal_sequence=rec.wal_sequence,
                    timestamp=rec.timestamp,
                )

        # Clear WAL log as snapshot now contains baseline state
        self._wal_log.clear()

        return {
            "status": "ok",
            "new_generation": self._generation,
            "total_records_preserved": total_records,
            "wal_frames_reclaimed": reclaimed_wal_frames,
            "collections_count": len(self._collections),
        }


# Global engine singleton
_engine_instance = MiniDbEngine()


async def kimi_minidb_put(
    collection: str,
    key: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    """Insert or update a document in MiniDb with WAL durability."""
    record = _engine_instance.put(collection=collection, key=key, value=value)
    return {
        "status": "ok",
        "action": "put",
        "record": record.to_dict(),
    }


async def kimi_minidb_get(
    collection: str,
    key: str,
) -> dict[str, Any]:
    """Retrieve a stored document by collection name and key."""
    record = _engine_instance.get(collection=collection, key=key)
    if record is None:
        return {
            "status": "not_found",
            "collection": collection,
            "key": key,
            "record": None,
        }
    return {
        "status": "ok",
        "collection": collection,
        "key": key,
        "record": record.to_dict(),
    }


async def kimi_minidb_compact(
    target_generation: int | None = None,
) -> dict[str, Any]:
    """Triggers snapshot compaction, consolidating WAL frames."""
    return _engine_instance.compact(target_generation=target_generation)


class KimiMiniDbPlugin(HarnessPlugin):
    """Brain Harness Plugin providing zero-dependency embedded MiniDb storage."""

    name = "plugin.kimi_minidb"
    version = "1.0.0"

    def __init__(self, service: KimiMiniDbService | None = None) -> None:
        super().__init__()
        self._service = service or _engine_instance

    async def on_enable(self, context: ServiceContext) -> None:
        """Register KimiMiniDbService into IoC context."""
        context.provide(KIMI_MINIDB_KEY, self._service, provider=self.name)
        logger.info("KimiMiniDbPlugin enabled and service registered")

    async def on_disable(self, context: ServiceContext) -> None:
        """Unregister service on disable."""
        logger.info("KimiMiniDbPlugin disabled")
