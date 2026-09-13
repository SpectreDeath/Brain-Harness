# Multi-Agent Memory Graph RAG with Temporal Decay

## Context
Pure vector RAG flattens structured relationships into loose semantic similarity, failing to preserve causal lineages or prioritize recent architectural changes over stale documentation.

## Distilled Learning
Integrate a Graph RAG pipeline with temporal memory decay:
- Represent workspace and architectural facts as knowledge graph triples: `(Subject, Predicate, Object)`.
- Apply an exponential temporal decay function: $w(t) = w_0 \cdot e^{-\lambda \Delta t}$, where $\Delta t$ is session elapsed time and $\lambda$ is the domain decay rate.
- Protect foundational architectural invariants from decay by assigning an infinite half-life (`decay_exempt = true`).
- Execute multi-hop graph traversals to gather relational context before querying vector embeddings.

## Triggers & Seam Choices
- **Trigger**: Long-term memory recall, knowledge item indexing, and cross-session learning.
- **Seam Choice**: Federate into `harness.services.neo4j_graph` and `harness.services.memory_decay_engine`.
