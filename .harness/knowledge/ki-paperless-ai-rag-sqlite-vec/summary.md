# In-Database Vector RAG with SQLite-Vec, LlamaIndex, and Hybrid Tantivy BM25 Dispatch

## Epistemic Introspection & Overview

In version 3.0 and 3.1, Paperless-NGX introduced native Retrieval-Augmented Generation (`paperless_ai`). Rather than requiring heavy external vector database deployments (e.g. Qdrant, Milvus, Chroma), Paperless-NGX integrates the `sqlite-vec` extension directly within SQLite (`llmindex.db`), keeping operational overhead minimal while providing local and remote embedding support.

---

## Vector Store Architecture (`paperless_ai/vector_store.py`)

- **Storage Engine**: `PaperlessSqliteVecVectorStore` subclasses `BasePydanticVectorStore` from LlamaIndex.
- **Database File**: Persisted to `llmindex.db` in the data directory.
- **Virtual Table Design**: Employs SQLite virtual tables (`vec0`) for KNN cosine distance calculations:
  - `document_chunks`: Stores serialized node text, embeddings, and document foreign keys.
  - `document_meta`: Stores document modification timestamps, page counts, and title tags.
  - `index_meta`: Tracks schema versions (`SCHEMA_VERSION = 2`) and compaction thresholds.
- **Compaction Routine**: Rebuilds virtual tables periodically when row deletion fragmentation exceeds live row counts, reclaiming unindexed disk space.

---

## Indexing & Chunking Pipeline (`paperless_ai/indexing.py`)

- **Chunking Parameters**:
  - `RAG_NUM_OUTPUT = 512` tokens per chunk.
  - `RAG_CHUNK_OVERLAP = 200` tokens overlap across chunk boundaries.
- **Memory Bounding**: Streams documents using `QuerySetStream` with `_INDEX_STREAM_CHUNK_SIZE = 1000` rows per batch to prevent RAM exhaustion during bulk initial migrations.
- **Embedding Flexibility**: Supports HuggingFace local models (`sentence-transformers`), Ollama local models, and OpenAI-compatible API providers via `paperless.config.AIConfig`.

---

## Hybrid Search & Streaming RAG Chat Seam (`paperless_ai/chat.py`)

- **Hybrid Dispatch**:
  - Lexical full-text queries route to the Tantivy engine (`whoosh-compat[tantivy]`), providing sub-millisecond keyword matching, boolean queries, and fuzzy matching.
  - Semantic questions route through LlamaIndex vector retrieval (`CHAT_RETRIEVER_TOP_K = 5`), retrieving top matching chunks.
- **Citation Protocol**:
  - Streaming responses from `/api/documents/chat/` emit textual answers followed by a delimiter:
    `__PAPERLESS_CHAT_METADATA__`
  - The metadata payload contains a structured JSON array of referenced documents (`id`, `title`, `page`) allowing client agents to inspect and verify primary sources.
