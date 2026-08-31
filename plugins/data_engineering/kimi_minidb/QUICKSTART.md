# Kimi MiniDb Plugin (`plugin.kimi_minidb`)

The `plugin.kimi_minidb` brings Kimi Code's zero-dependency, pure-language embedded document/KV store pattern with CRC32-checksummed write-ahead logging (WAL) and snapshot compaction into Brain Harness.

## Features

1. **Embedded In-Memory Speed (`kimi_minidb_put` / `kimi_minidb_get`)**:
   - Sub-microsecond document mutations and lookups across collections.
   - CRC32 checksum generation and bit-rot corruption detection on reads.
2. **Durable WAL Framing**:
   - Append-only audit log tracking mutations in strict sequence order.
3. **Generational Snapshot Compaction (`kimi_minidb_compact`)**:
   - Merges accumulated WAL frames into a clean baseline snapshot, advancing the generation counter.

## Usage Recipes

### 1. Store and Query Session Data
```python
from plugins.data_engineering.kimi_minidb.main import kimi_minidb_put, kimi_minidb_get

# Put document into "sessions" collection
res = await kimi_minidb_put(
    collection="sessions",
    key="sess_abc123",
    value={"user_id": "u42", "turns": 14, "tokens_used": 2840}
)
print("Saved record:", res["record"]["crc32_checksum"])

# Retrieve document with CRC32 verification
fetch = await kimi_minidb_get(collection="sessions", key="sess_abc123")
print("Fetched record:", fetch["record"]["value"])
```

### 2. Compact Snapshot
```python
from plugins.data_engineering.kimi_minidb.main import kimi_minidb_compact

compaction_report = await kimi_minidb_compact()
print(f"Compacted to generation {compaction_report['new_generation']}, reclaimed {compaction_report['wal_frames_reclaimed']} frames")
```
