# Memory & Epistemics Domain Architecture

The Memory & Epistemics domain governs declarative skill knowledge graph indexing, semantic vector retrieval, context distillation, prompt benchmarking, and unbroken claim provenance (Isnad).

---

## Domain Scope & Boundaries

This domain manages persistent intelligence, long-term memory, and epistemic truth verification:
- In Scope: Directed skill knowledge graphs, topological routing, OKF Git-native episodic memory, biographical memory federation, vector retrieval, and Isnad chain-of-custody audits.
- Out of Scope: Ephemeral step scratchpads (Agent Orchestration), raw tabular statistics (Data Engineering), or low-level SQLite C extensions (Kernel).

---

## Ubiquitous Language & Core Terminology

- *Skill Graph*: A directed knowledge graph indexing skills, triggers, stages, and anti-patterns for autonomous routing and chaining. (*Avoid*: Tool index, skill list, capability table)
- *Isnad*: An unbroken, verifiable chain of custody linking a factual claim back to a primary code URI, tool event, or document. (*Avoid*: Provenance, source link, citation)
- *Vector Index*: A local semantic retrieval structure combining dense embedding cosine similarity with sparse lexical matching. (*Avoid*: Embeddings database, search index)
- *Context Distiller*: A compression engine that transforms dense multi-token data tables or documents into compact heuristic invariants. (*Avoid*: Summarizer, trimmer, minifier)
- *Prompt Benchmark*: A structured matrix comparing prompt efficacy, token consumption, and model latency across test workloads. (*Avoid*: Prompt score, evaluation test)
- *Brain Introspector*: A reflection engine that analyzes attached brain transcripts and conversation trees to distill reusable procedural patterns. (*Avoid*: Memory searcher, history parser, log crawler)
- *Repository Introspector*: An analytical tool that extracts architectural patterns, commit trajectories, and engineering heuristics from Git repositories. (*Avoid*: Code scanner, repo scraper, git summarizer)
- *Endogenous Reflector*: An autobiographical reflection engine that harvests ephemeral reports, transcripts, and logs to distill verified, Isnad-grounded Knowledge Items. (*Avoid*: Log summarizer, chat scraper, history exporter)

---

## Architectural Invariants & Patterns

- Multi-Store Memory Federation (Rule 22): Agents connect to active session stores via read-only SQLite URI modes (`file:...?mode=ro`) to prevent database lock contention.
- Strict Reachability & Zero-Synthetic Routing (Rule 55): Topological graph routing (`get_chain()`) returns explicit `no_path` and empty chain collections when no directed path exists, avoiding synthesized fake edges.
- Dual-Lens Cognitive Distillation (Rule 41): Distillation engines bifurcate analysis into an epistemic introspection seam (committing truth models to the Knowledge Vault) and a procedural skill synthesis seam (scaffolding `SKILL.md` + `CARD.md`).
- Canonical Knowledge Vault Dual-File Format (Rule 40): Persisted knowledge items written to disk under `.harness/knowledge/<ki_id>/` use the canonical dual-file directory format (`metadata.json` + `summary.md`).

---

## Co-Located Plugins & Micro-Kernel Services

- Skill Knowledge Graph: [`src/harness/services/skill_graph.py`](../../../src/harness/services/skill_graph.py) providing `SkillKnowledgeGraphService` (`SKILL_GRAPH_SERVICE_KEY`).
- Skill Card Parser: [`src/harness/services/skill_parser.py`](../../../src/harness/services/skill_parser.py) providing `SkillCardParserService`.
- OKF Memory Service: [`src/harness/services/okf_memory.py`](../../../src/harness/services/okf_memory.py) providing `OKF_MEMORY_SERVICE_KEY`.
- Vector Index Service: [`src/harness/services/vector_index.py`](../../../src/harness/services/vector_index.py) providing `VECTOR_INDEX_SERVICE_KEY`.
- Skill Knowledge Graph Plugin: [`plugins/memory_and_epistemics/skill_knowledge_graph/`](../../../plugins/memory_and_epistemics/skill_knowledge_graph/README.md).

---

## Associated Agent Skills

- [`epistemic-isnad-audit`](../../../.agents/skills/epistemic-isnad-audit/SKILL.md): Verifies unbroken chain-of-custody lineage for facts and architectural decisions.
- [`epistemic-memory-lifecycle`](../../../.agents/skills/epistemic-memory-lifecycle/SKILL.md): Executes 8-state knowledge item promotion pipelines.
- [`okf-memory-governor`](../../../.agents/skills/okf-memory-governor/SKILL.md): Governs Git-native agent memory using OKF v0.2 protocols.
- [`harness-reflector`](../../../.agents/skills/harness-reflector/SKILL.md): Introspects and distills learnings from execution logs and transcripts.
