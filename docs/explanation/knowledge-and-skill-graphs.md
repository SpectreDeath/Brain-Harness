# Knowledge and Skill Graphs: Dual-Graph Architecture

## Overview

The Harness cognitive model partitions knowledge and runtime capabilities into two complementary, strongly-typed directed acyclic graphs (DAGs):

1. **Epistemic Knowledge Graph (Knowledge Vault)**: Represents verified truths, architectural invariants, empirical observations, and lineage claims (`isnad`). This answers *what the harness knows*.
2. **Procedural Skill Graph (Agent Skills)**: Represents actionable workflows, toolchains, heuristic playbooks, and diagnostic contracts (`SKILL.md` + `CARD.md`). This answers *how the harness acts*.

Before the dual-graph integration, these systems operated independently. The joint query architecture bridges them, discovering lineage pairs, unbridged knowledge items (facts without operational skills), and ungrounded skills (capabilities without verified epistemic grounding).

---

## Architectural Taxonomy

```
                   ┌──────────────────────────────────────┐
                   │          User Intent / Query         │
                   └──────────────────┬───────────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│        Knowledge Vault        │               │       Skill Graph Router      │
│     (.harness/knowledge)      │               │       (.agents/skills)        │
├───────────────────────────────┤               ├───────────────────────────────┤
│ • Canonical dual-file format  │               │ • Slotted SkillCard models    │
│ • Isnad verification lineage  │               │ • Louvain community clusters  │
│ • References & code anchors   │               │ • Intent embedding & routing  │
└───────────────┬───────────────┘               └───────────────┬───────────────┘
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │      Joint Query Engine       │
                        │ (query_knowledge_and_skills)  │
                        ├───────────────────────────────┤
                        │ • Epistemic-to-Procedural Map │
                        │ • Domain Lineage Linking      │
                        │ • Unbridged Gap Identification│
                        └───────────────────────────────┘
```

---

## The Knowledge Vault (Epistemic Graph)

The Knowledge Vault stores items as dual-file directories under `.harness/knowledge/<ki_id>/`:
- `metadata.json`: Contains structured identifiers, `isnad` provenance chains, source references, tags, and directed edges (`references_code`, `became_skill`, `supersedes`).
- `summary.md`: Unstructured natural-language distilled truth and empirical guidance.

### Edge Types in Knowledge Graph
- `references_code`: Connects a Knowledge Item to concrete source file implementations in `src/` or `plugins/`.
- `became_skill`: Connects a conceptual breakthrough or research paper to an executable agent skill in `.agents/skills/`.
- `supersedes`: Explicitly retires an older mental model or superseded invariant with a newer replacement.
- `same_domain`: Inferred clustering based on shared taxonomy and tag overlaps.

---

## The Skill Knowledge Graph (Procedural Graph)

Agent skills reside under `.agents/skills/<skill-name>/` with accompanying metadata cards `CARD.md`:
- `SKILL.md`: Deep-module execution guide containing workflow phases, scripts, and anti-patterns.
- `CARD.md`: Slotted summary card parsed by `SkillCardParser` defining metadata, parameter schemas, and mandatory checkpoints.

### Graph Community Topology
The skill graph organizes skills into topological clusters (e.g., `developer_experience`, `security_and_forensics`, `agent_orchestration`) and calculates cross-cluster bridges where high-centrality skills route requests across domain boundaries.

---

## Joint Query and Cross-Graph Lineage

The joint query seam (`harness knowledge joint-query` and `harness skills joint-query`) unifies retrieval across both graphs:

1. **Dual Search**: Simultaneously searches semantic text and metadata in the Knowledge Vault while executing intent routing against skill cards.
2. **Lineage Alignment**: Discovers `domain_lineage` connections when a skill's name or tags align with a Knowledge Item's title, domain, or declared anchors.
3. **Gap Detection**:
   - `unbridged_kis`: Knowledge items that describe critical concepts or invariants but lack corresponding agent skills to enforce or automate them.
   - `ungrounded_skills`: Agent skills that provide workflows but lack verifiable epistemic lineage or provenance records in the vault.

---

## CLI Seams

```bash
# Query both graphs simultaneously
harness knowledge joint-query "security review" --json
harness skills joint-query "reverse engineering" --json

# Inspect cross-cluster bridges in the skill topology
harness skills bridges --json

# Rebuild the skill catalog index
harness skills index --json
```

See the [CLI Reference](../reference/cli.md) and [Use God's Eye View](../how-to/use-gods-eye-view.md) for details on toolkit commands.

