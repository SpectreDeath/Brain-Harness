---
name: discovery-index-scout
description: Discover, catalog, and query public record archives, legislative transcripts, corporate filings, campaign finance data, and research corpora from curated open discovery indexes. Do not use for raw web scraping, credentialed system breaches, or ad-hoc RDBMS administration.
provides: "service.discovery_index_scout"
requires:
  - "service.skill_knowledge_graph"
---

# Discovery Index Scout: Open Intelligence & Primary Record Discovery

`discovery-index-scout` is the production-grade intelligence skill for discovering, evaluating, querying, and cataloging primary public records, legislative proceedings, corporate disclosures, campaign finances, and academic research corpora across 46+ curated discovery repositories. It operationalizes foundational discovery indexes into a disciplined 5-phase engineering workflow that eliminates **Prompt Sprawl**, **General Knowledge Restatement**, and **Static Fork Nightmares**.

See [CARD.md](CARD.md) for the companion summary card, 5-phase progression table, and vocabulary cheat sheet.
Consult `/hf-datasets-engineer` for large-scale Hugging Face corpus ingestion, `/structured-data-scout` for Kaggle/UCI tabular datasets, and `/epistemic-isnad-audit` for unbroken provenance verification.

---

## The 5-Phase Discovery SDLC Loop

```
[1. Trigger Engineering & Scoping] ──► [2. Config Decoupling] ──► [3. Programmatic Search & Salvage]
                                                                                │
                                                                                ▼
[5. Security Audit & Graph Index] ◄── [4. Two-Phase Verification & Gates]
```

---

## Phase 1: Trigger Engineering & Discovery Scoping

Design high-precision activation boundaries and classify candidate inquiries:

1. **Apply Front-Loaded Trigger Phrases**:
   - `discover public records`: Scout federal open data catalogs, court dockets, or agency filings.
   - `scout transcript corpora`: Search C-SPAN, Internet Archive TV News, Hansard, or presidential debates.
   - `query campaign finance`: Trace political contributions, PAC spending, and lobbying disclosures.
   - `map open discovery indexes`: Survey PolData, Awesome Public Datasets, or Rev speech corpora.
   - `catalog research datasets`: Locate DOI-backed academic replication packages in Zenodo or Harvard Dataverse.
2. **Enforce Negative Boundaries**:
   - Do not use for raw, unauthenticated web scraping of arbitrary websites (use dedicated browser or crawler plugins).
   - Do not use for credentialed network penetration attacks or private system breaches.
   - Do not use for ad-hoc SQL relational database management or transactional production writes.
3. **Classify by Provenance Tier**:
   - Prioritize Primary Official sources (Congress.gov, GovInfo, SEC EDGAR, FEC) for legal and regulatory claims.
   - Use Academic Repositories (Zenodo, Dataverse, ICPSR) for statistical empirical research.

> Completion Gate: `Trigger matrix validated` (positive recall $\ge 90\%$, near-miss false-positive rate $0\%$, negative boundary defined).

---

## Phase 2: Configuration & Zero-Fork Customization

Decouple discovery defaults from repository-specific customization without forking core skill packages:

1. **Scaffold Default Configuration**:
   - `config.default.yaml` defines base operational parameters: line budget limit (500), token budget (6000), default output format (`json`), query limit (20), request timeout (30s), and four enabled categories (`transcripts`, `public_records`, `research_corpora`, `github_indexes`).
2. **Support Additive Extension Lists**:
   - Extend candidate discovery endpoints without modifying skill files by specifying `extra_sources` in `.agents/skills.config.yaml`:
     ```yaml
     discovery-index-scout:
       extra_sources:
         - name: "State Legislative Archive"
           category: "transcripts"
           url: "https://example.gov/legislature"
           access_method: "REST API"
           provenance_tier: "State Official"
     ```
3. **Verify 3-Tier Precedence**:
   - Precedence: Project Override (`.agents/skills.config.yaml`) $\rightarrow$ Skill Default (`config.default.yaml`) $\rightarrow$ Hardcoded Fallback.
   - Execute configuration resolution to confirm clean merges:
     ```bash
     python .agents/skills/agent-skill-sdlc/scripts/resolve_config.py discovery-index-scout --print-sources
     ```

> Completion Gate: `Config resolution clean` (`resolve_config.py` resolves cleanly across all tiers with zero unmerged conflicts).

---

## Phase 3: Programmatic Index Querying & Salvage Tooling

Execute deterministic searches across curated sources and repair model output in-flight:

1. **Query Curated Discovery Repositories**:
   - Query the discovery catalog by category, keyword, or tag without polluting LLM system prompts:
     ```bash
     python .agents/skills/discovery-index-scout/scripts/search_index.py --category public_records --keyword "lobbying" --format json
     ```
   - When determining which discovery endpoint to route a query to, consult [source-taxonomy.md](references/source-taxonomy.md) for the full 36-endpoint classification with access methods and provenance levels.
   - When initializing a new intelligence stack for a research project from scratch, follow the 7-step prioritized sequence in [starting-sequence-playbook.md](references/starting-sequence-playbook.md).
2. **Maintain Local Provenance Registry**:
   - Track discovered endpoints and verified data assets in the local ledger (`registry.json`):
     ```bash
     python .agents/skills/discovery-index-scout/scripts/catalog_registry.py list --format markdown
     python .agents/skills/discovery-index-scout/scripts/catalog_registry.py stats
     ```
3. **Execute Local Zero-Token Salvage**:
   - Prior to paying LLM tokens on JSON parse failures, run local string salvage:
     ```bash
     python .agents/skills/discovery-index-scout/scripts/salvage.py -i raw_output.txt --validate
     ```
   - Applies 5-pass local repair: code fences $\rightarrow$ outermost braces $\rightarrow$ trailing commas $\rightarrow$ Python literals/unquoted keys $\rightarrow$ AST fallback.

> Completion Gate: `Scripts verified non-interactive and salvage operational` (zero `input()` calls, relocatable relative paths, local string salvage operational).

---

## Phase 4: Two-Phase Verification & Quality Gates

Enforce strict syntactic and semantic compliance across the skill package:

1. **Two-Phase Validation Checks**:
   - **Phase 1 (Syntactic)**: YAML frontmatter valid, name is strict kebab-case, description length in [100, 350] chars, line budget $\le 500$, sequential heading levels.
   - **Phase 2 (Semantic)**: `CARD.md` single-pipe borders (`│`), exact `SKILL:` tag identifier, binary completion gates for all 5 phases, `## Anti-Patterns` formatting, reference trigger coverage for all files in `references/`.
2. **Run Validation Suite**:
   - Execute the diagnostic validator against the skill directory:
     ```bash
     python .agents/skills/agent-skill-sdlc/scripts/validate_skill.py .agents/skills/discovery-index-scout --json
     ```
3. **Path-Targeted Repair Protocol**:
   - On semantic validation warnings, repair only the affected file block. Enforce a hard circuit-breaker at 3 repair cycles.

> Completion Gate: `Two-phase validation passes` (`validate_skill.py` exits 0 with zero failed diagnostic checks).

---

## Phase 5: Security Auditing & Graph Indexing

Audit execution risks, verify supply-chain invariants, and graduate the skill to v5:

1. **Execute SkillSpector 70-Pattern Security Audit**:
   - Scan all bundled scripts in `scripts/` across 4 weighted dimensions: Dangerous System Calls (30%), Network Exfiltration (30%), Filesystem Mutation (20%), and Credential Access (20%).
   - Assert that aggregate Security Risk Score $\le 20$ (**SAFE** band).
2. **Run Harness Platform Validation**:
   - Verify skill package structure against Harness platform standards:
     ```bash
     harness skills validate .agents/skills/discovery-index-scout
     ```
3. **Index into Skill Knowledge Graph & Context Map**:
   - Commit the skill node into the active knowledge graph and register in `CONTEXT-MAP.md` under `research_and_intel`.

> Completion Gate: `Pre-flight score <= 20` (SkillSpector score $\le 20$, `harness skills validate` passes, skill indexed in graph).

---

## Anti-Patterns

- **Prompt Sprawl** — Inlining 46+ discovery repository URLs directly into model context instead of querying `scripts/search_index.py` on demand.
- **Static Fork Nightmare** — Forking entire skill repositories just to customize or add project-specific endpoints rather than using additive `extra_sources` in `.agents/skills.config.yaml`.
- **Vague Description Syndrome** — Authoring ambiguous trigger descriptions that cause router confusion between specialized discovery indexes and generic search.
- **General Knowledge Restatement** — Wasting token budget explaining what C-SPAN or the SEC is instead of focusing on deterministic query flags and access methods.
- **Prose-Only Procedure** — Describing discovery search steps purely in natural language without deterministic verification scripts.
- **Naive Full-Reprompt Retry** — Resending full agent prompts on structured output parse errors instead of using local string salvage (`salvage.py`).
- **Interactive Script Hang** — Bundling scripts that invoke blocking input prompts, causing agent proactor transports to freeze indefinitely.
- **Absolute Path Brittleness** — Hardcoding user-specific machine absolute paths in skill scripts rather than resolving anchors via `Path(__file__).resolve().parent`.
- **Missing Cross-Skill Delegation** — Attempting to re-implement Hugging Face dataset loading or Kaggle scraping in-skill rather than delegating to `/hf-datasets-engineer` and `/structured-data-scout`.
