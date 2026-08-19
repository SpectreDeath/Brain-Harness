# Memory & Epistemics Context

The Memory & Epistemics context governs declarative skill indexing, semantic vector retrieval, context distillation, prompt benchmarking, and claim lineage.

## Language

**Skill Graph**:
A directed knowledge graph indexing skills, triggers, stages, and anti-patterns for autonomous routing and chaining.
_Avoid_: Tool index, skill list, capability table

**Isnad**:
An unbroken, verifiable chain of custody linking a factual claim back to a primary code URI, tool event, or document.
_Avoid_: Provenance, source link, citation

**Vector Index**:
A local semantic retrieval structure combining dense embedding cosine similarity with sparse lexical matching.
_Avoid_: Embeddings database, search index

**Context Distiller**:
A compression engine that transforms dense multi-token data tables or documents into compact heuristic invariants.
_Avoid_: Summarizer, trimmer, minifier

**Prompt Benchmark**:
A structured matrix comparing prompt efficacy, token consumption, and model latency across test workloads.
_Avoid_: Prompt score, evaluation test
