# Hybrid In-Memory KV with Durable WAL Snapshot Persistence

## Architectural Summary
`@moonshot-ai/minidb` provides a pure-managed embedded key-value and document database pairing in-memory query speed with SQLite-style durable WAL and snapshot compaction.

## Operational Guidelines
1. **Append-Only WAL:** Write all document insertions, updates, and deletions to an append-only WAL with CRC32 frame checksums.
2. **Generational Snapshots:** Asynchronously compact the WAL into generational snapshot files when WAL size exceeds a threshold.
3. **Clustered Readers:** Support multiple concurrent reader processes that poll and tail the WAL to stay synchronized without write contention.
