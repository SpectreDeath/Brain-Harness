```
┌────────────────────────────────────────────────────────┐
│             SKILL: discovery-index-scout               │
├────────────────────────────────────────────────────────┤
│ SKILL:        discovery-index-scout                    │
│ Category:    research_and_intel                        │
│ Domain:      Intelligence / Open Data Discovery        │
│ Invocation:  /discovery-index-scout                    │
│ Triggers:    "discover public records",                │
│              "scout transcript corpora",               │
│              "query campaign finance",                 │
│              "map open discovery indexes",             │
│              "catalog research datasets"               │
│ Version:     5.0.0 (Multi-Engine Distributed)          │
│ Isolation:   in-process                                │
│ Provides:    "service.discovery_index_scout"           │
│ Requires:    "service.skill_knowledge_graph"          │
├────────────────────────────────────────────────────────┤
│ Target:      Autonomous open-data discovery engine     │
│              covering transcripts, public records,     │
│              research corpora, and index registries.   │
└────────────────────────────────────────────────────────┘
```

# Discovery Index Scout — Companion Summary Card

`discovery-index-scout` provides a standardized, deep-module intelligence framework for scouting, cataloging, querying, and verifying public record archives, legislative hearing transcripts, corporate filings, campaign finances, and academic research datasets across curated discovery repositories.

See [SKILL.md](SKILL.md) for the complete 5-phase operational procedure.
Related skills: `/hf-datasets-engineer` for large-scale Hugging Face dataset extraction, `/structured-data-scout` for Kaggle/UCI tabular sets, and `/epistemic-isnad-audit` for provenance verification.

---

## 5-Phase Progression Table

| Phase | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Phase 1: Trigger Engineering & Discovery Scoping** | Define strict activation boundaries, negative bounds, and query taxonomy | `SKILL.md` (frontmatter & bounds) | `Trigger matrix validated` |
| **Phase 2: Configuration & Zero-Fork Customization** | Implement 3-tier config precedence and additive source lists without forking | `config.default.yaml` + `resolve_config.py` | `Config resolution clean` |
| **Phase 3: Programmatic Index Querying & Salvage Tooling** | Equip agents with deterministic search CLI, registry store, and local salvage | `scripts/` + `salvage.py` | `Scripts verified non-interactive and salvage operational` |
| **Phase 4: Two-Phase Verification & Quality Gates** | Enforce syntactic AST validation and semantic reference coverage | `validate_skill.py` | `Two-phase validation passes` |
| **Phase 5: Security Auditing & Graph Indexing** | Execute SkillSpector security scan and commit to Skill Knowledge Graph | Security scorecard & Knowledge Graph commit | `Pre-flight score <= 20` |

---

## The Three Foundational Craft Pillars

1. **The Visual Brief Pillar**:
   - Every skill architecture must render an interactive, self-contained HTML visual brief written to `%TEMP%\<skill-name>-<timestamp>.html`.
   - Incorporates Mermaid DAG workflows, diagnostic scorecards, and anti-pattern defense matrices.

2. **The Mandatory Checkpoint Gate Pillar**:
   - Halts autonomous execution before modifying workspace code or committing artifacts.
   - Presents an explicit review plan with `RequestFeedback: true` to confirm boundaries and design decisions.

3. **The Anti-Pattern Defense Pillar**:
   - Hardens the agent against known anti-patterns (e.g. Prompt Sprawl, Static Forking, Interactive Script Hangs, General Knowledge Restatement).
   - Formatted strictly under `## Anti-Patterns` with `- **Name** — Description`.

---

## Vocabulary Cheat Sheet

- **Open Discovery Index**: A curated collection or meta-catalog that aggregates links, APIs, and access methods for primary public records and research corpora.
- **Provenance Tier**: The classification of source authoritativeness (`Primary Official`, `Academic Archival`, `Regulatory Primary`, `Public Interest Intelligence`).
- **Zero-Fork Customization**: Extending discovery capabilities with `extra_sources` in `.agents/skills.config.yaml` without modifying core skill packages.
- **Local String Salvage**: Deterministic 5-pass local repair of malformed model JSON outputs prior to consuming tokens on reprompts.
- **Multi-Pass Discovery Sequence**: A structured 7-step progression moving from political debate indexes down to financial tracing and temporal web audits.

---

## Invariants & Pre-Flight Verification Checklist

- [ ] `SKILL.md` contains valid YAML frontmatter with `name:`, `description:` (100-350 chars), `provides:`, and `requires:`.
- [ ] `SKILL.md` body is bounded strictly under 500 lines (`line_budget_limit`).
- [ ] `CARD.md` uses single-pipe `│` borders and contains exact `SKILL: discovery-index-scout` tag identifier.
- [ ] `## Anti-Patterns` section declared with items formatted as `- **Name** — Description`.
- [ ] Bundled scripts configure standard streams to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`).
- [ ] Zero interactive prompts (`input()`) in bundled Python scripts.
- [ ] Zero hardcoded machine absolute paths in bundled scripts.
- [ ] All reference documents in `references/` are linked with conditional trigger sentences in `SKILL.md`.
- [ ] `config.default.yaml` resolves cleanly across all 3 tiers via `resolve_config.py`.
- [ ] `validate_skill.py` passes with zero failures.
