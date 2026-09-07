# Direct File API vs. Chunked RAG Architectural Guide

This reference guide establishes the architectural decision boundaries between Direct File API Upload and Chunked Retrieval-Augmented Generation (RAG) for document-grounded AI analysis workflows.

---

## Comparative Decision Matrix

| Dimension | Direct File API Upload (Eva Patel / Modern SDK) | Chunked RAG (Vector Database Pipeline) |
|---|---|---|
| **Context Window Consumption** | Direct ingestion of full document into multimodal context | Top-$K$ similarity retrieval chunks injected into context |
| **Document Size Target** | Small to Medium (Single files $\le 50$ MB, $\le 100$k tokens) | Large to Massive (Repositories, enterprise corpora $> 500$ pages) |
| **Pipeline Latency** | **Ultra-Low**: 1 network call (upload once, query multiple times) | **Medium-High**: Embedding generation, vector search, ranker latency |
| **System Complexity** | Zero infrastructure (no embeddings, chunking, or vector DB) | High (parsers, chunk splitters, vector store, distance metrics) |
| **Cross-Document Synthesis** | Constrained to active file handles attached to session | Native cross-document federation across millions of chunks |
| **Information Loss** | **Zero**: Model sees entire unbroken document topology | Non-zero: Risk of boundary slicing, context loss across chunk splits |
| **Operational Cost** | Per-query token cost across entire file context | Lower per-query token cost, but recurring vector storage overhead |

---

## Triage Decision Tree

Use this heuristic to select the appropriate context architecture:

```
                  [Incoming File Analysis Task]
                                │
               Is total document size > 50 MB
               or exceeds model token window?
                     ├── YES ──► Route to Chunked RAG Pipeline
                     │           (Embed, Index in Chroma/Qdrant, Top-K Retrieval)
                     └── NO
                          │
             Is multi-document cross-synthesis across
             hundreds of unlinked files required?
                     ├── YES ──► Route to Chunked RAG Pipeline
                     └── NO  ──► Route to Direct File API Upload
                                 (Upload file via client.files.create,
                                  bind file_id to responses/chat endpoint)
```

---

## Best Practices for Direct File Upload

1. **Upload Once, Query Many**: Store the returned `file_id` across the session lifetime. Never re-upload the same document on subsequent user turns.
2. **Pre-flight Whitelisting**: Restrict incoming file extensions before network egress (`.pdf`, `.docx`, `.csv`, `.txt`).
3. **Purpose Parameterization**: Set `purpose="user_data"` to isolate user-supplied documents from fine-tuning or evaluation pipelines.
4. **Graceful Deletion**: On session teardown, invoke `client.files.delete(file_id)` to prevent storage accumulation.
