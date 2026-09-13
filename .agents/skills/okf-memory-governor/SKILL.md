---
name: okf-memory-governor
description: Govern Git-native agent memory using OKF v0.2 protocols. Perform pre-edit governance scoping, sub-millisecond BM25 lexical search, atomic concept mutations, and trust-ordered schema validation. Do not use for unstructured web search, general file grep, or ad-hoc markdown editing.
category: memory_and_epistemics
version: 1.0.0
---

# OKF Memory Governor — Agent Skill

This skill enforces the Open Knowledge Framework (OKF v0.2) protocol across repository memory bundles, providing pre-edit governance scoping, BM25 lexical ranking, atomic mutations, and normative validation.

## Architectural Pillars

1. **The Visual Brief** — Generate dark-mode HTML briefs in `%TEMP%` for multi-concept topology and governance reviews.
2. **The Mandatory Checkpoint** — Require explicit user review (`RequestFeedback: true`) prior to any destructive concept deletion.
3. **Explicit Anti-Patterns** — Rigid behavioral boundaries eliminating unverified self-attestation and blanket directory scans.

See [CARD.md](CARD.md) for companion card and stage checklist.

---

## 1. Pre-Edit Governance Scope Check

Before proposing or executing any code modification in the workspace, query the knowledge bundle for concepts that explicitly govern the target path.

```bash
python .agents/skills/okf-memory-governor/scripts/okf_engine.py scope --target "src/api/auth.py"
```

Evaluate any attached `governance` constraints. If a governing concept establishes negative boundaries or architectural invariants, incorporate them into the step plan before proceeding.

> **Completion criterion**: Target code paths checked against bundle `code_refs` and all active governance constraints extracted.

---

## 2. Search-First Lexical Retrieval

When querying repository knowledge, use sub-millisecond BM25 lexical search with progressive disclosure (default `limit=3`).

```bash
python .agents/skills/okf-memory-governor/scripts/okf_engine.py search "jwt token expiration revocation" --limit 3
```

Never perform blanket directory scans (`list_dir`) or full-text greps on the `knowledge/` directory. Evaluate the 1-2 sentence descriptions of the top 3 candidates before loading full bodies.

> **Completion criterion**: Relevant concepts identified by BM25 scoring without scanning the entire knowledge directory.

---

## 3. Atomic Mutation & Frontmatter Sanitization

When creating or modifying concepts, sanitize scalar fields (no unescaped newlines), preserve provenance, and automatically sync parent indexes and audit logs.

```bash
python .agents/skills/okf-memory-governor/scripts/okf_engine.py create \
  --id "auth-jwt-revocation" \
  --title "JWT Token Revocation Strategy" \
  --type "architecture" \
  --description "Implements Redis-backed token denylist for instant session invalidation." \
  --governance "Never store raw JWT in denylist; use jti claim hash" \
  --code-refs "src/api/auth.py,src/core/security.py"
```

Agents must never self-attest as human actors in `verified.by`. All automated additions must record `generated.by: "agent:brain-harness"`.

> **Completion criterion**: Concept file written within root boundary, scalar frontmatter sanitized, `index.md` table updated, and `log.md` entry appended.

---

## 4. Relation Graph Linking

Maintain explicit semantic relationships between concepts in YAML frontmatter rather than relying on unstructured prose links.

```bash
python .agents/skills/okf-memory-governor/scripts/okf_engine.py relate \
  --source "auth-jwt-revocation" \
  --target "redis-connection-pool" \
  --description "Denylist checks execute against shared Redis pool"
```

All relationship targets must resolve to existing concept identifiers within the bundle.

> **Completion criterion**: Bidirectional relations updated in both concepts with zero dangling targets.

---

## 5. Normative Validation & Ledger Audit

Execute bundle validation before concluding any cognitive distillation or memory mutation session.

```bash
python .agents/skills/okf-memory-governor/scripts/okf_engine.py validate --strict
```

Verify that all concepts possess mandatory fields (`id`, `title`, `type`, `description`), valid concept types, unbroken relation links, and satisfy actor trust ordering invariants.

> **Completion criterion**: Bundle validation passes with 0 critical errors and 0 unhandled hygiene warnings.

---

## Anti-Patterns

- **Blanket Directory Scans** — Running `list_dir` or `grep` across the entire `knowledge/` folder, wasting context tokens and degrading search accuracy.
- **Actor Trust Escalation** — Marking automated agent-generated concepts as verified by human authorities without human review.
- **Dangling Relation References** — Linking to non-existent concept IDs in frontmatter `relations`, fracturing the knowledge graph.
- **Unsanitized Frontmatter Newlines** — Injecting multiline strings into scalar YAML fields (`title`, `id`, `type`), corrupting the bundle parser.
- **Manual Bookkeeping Edits** — Directly editing `index.md` or `log.md` instead of allowing the mutation engine to maintain atomic synchronization.
