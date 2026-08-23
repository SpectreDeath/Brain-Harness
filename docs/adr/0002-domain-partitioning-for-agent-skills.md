# ADR 0002: Domain Partitioning for Agent Skills

- **Status**: ACCEPTED
- **Date**: 2026-08-23
- **Deciders**: Brain Harness Core Architecture Team

---

## Context & Problem Statement

Following the successful partitioning of ecosystem plugins in ADR 0001, the workspace's growing library of agent skills (`.agents/skills/`) accumulated across diverse domains: statistical time-to-event modeling (`survival-analysis`), curated dataset ingestion (`structured-data-scout`), Aquinas-style reflection (`questio-reflection`), epistemic lineage verification (`epistemic-isnad-audit`), and codecraft (`crafting-skills`, `deepen-architecture`).

Without formal domain categorization:
1. Cognitive overlap arose between data ingestion, epistemic auditing, and agent orchestration.
2. Skill discoverability and intent routing lacked cohesion with the project's established [CONTEXT-MAP.md](../../CONTEXT-MAP.md).
3. Ubiquitous language definitions in domain `CONTEXT.md` files did not cover specialized skill terms.

## Decision

We have mapped all 11 agent skills into the seven bounded domains defined in `CONTEXT-MAP.md` and expanded the ubiquitous language glossaries in `docs/domains/*/CONTEXT.md`:

1. **Agent Orchestration**: `questio-reflection` (Aquinas-style adversarial reflection & objection-answering).
2. **Memory & Epistemics**: `epistemic-isnad-audit` (chain-of-custody lineage), `mind-reader` (brain trajectory reflection), `repo-reader` (codebase pattern introspection).
3. **Data Engineering**: `structured-data-scout` (curated registry ingestion), `survival-analysis` (time-to-event & Cox PH regression), `data-topology-mapper` (DAG and queue topology modeling).
4. **Software Engineering**: `crafting-skills` (deep-module skill blueprints), `deepen-architecture` (architecture deepening loop), `compute-model-assessor` (reasoning budget & model tiering).
5. **Integration & I/O**: `repo-to-plugin-forge` (automated plugin synthesis from attached repositories).
6. **Security & Forensics / Infra & Cloud**: Platform-level audit and container workflows; domain skills scaffolded on demand.

## Consequences

### Positive
- **Unified Domain Taxonomy**: Both plugins and agent skills now share the same 7 bounded contexts and ubiquitous language.
- **Sharpened Glossary**: Precise terms (`Time-to-Event Model`, `Data Topology Map`, `Deep Module`, `Skill Engine`, `Compute Budget`, `Brain Introspector`, `Repository Introspector`, `Questio Check`, `Plugin Forge`) established with opinionated `_Avoid_` boundaries.
- **Autonomous Intent Routing**: Multi-agent supervisors and skill knowledge graphs can reliably route user requests to domain-specialized skills.

### Negative / Trade-offs
- New skills authored in `.agents/skills` must declare their domain category in their companion card (`CARD.md`) and register within `CONTEXT-MAP.md`.
