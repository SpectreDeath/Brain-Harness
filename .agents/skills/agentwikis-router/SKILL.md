---
name: agentwikis-router
description: "Route developer tasks against AgentWikis knowledge bases, evaluate declared scope boundaries, extract offline docs, and dispatch skills. Do not use for generic web scraping or non-technical chat."
---

# AgentWikis Router & Knowledge Distiller

`agentwikis-router` operationalizes [https://agentwikis.com/for-agents](https://agentwikis.com/for-agents) and the local `AgentWikis` corpus (10.2 MB across 62 curated wikis and 25 specialized skills) as an authoritative, structured knowledge and skill-routing substrate.

Guided by the **Data-to-Value Lifecycle Continuum** and **Hybrid Data Topology** (Graph of Trees with Hash-Indexed Extraction Queue), this skill provides zero-latency documentation slices, trust-calibrated abstention, and contract-first governance.

See [CARD.md](CARD.md) for the companion quick-reference card, 5-stage reference matrix, and quality checklist.
See [config.default.yaml](config.default.yaml) for zero-fork operational budgets, quality thresholds, and timeout parameters.
See [contracts/agentwikis_contract.yaml](contracts/agentwikis_contract.yaml) for the machine-readable Open Data Contract (ODCS).

---

## The 5-Stage Operational Progression

```
[1. Scope & Trust Triage] ──► [2. Contracted Medallion Pipeline] ──► [3. Visual Brief & Topology Review]
                                                                                │
                                                                                ▼
[5. Slice Retrieval & Dispatch] ◄── [4. 6-Dimension Quality Gating] ◄──────────┘
```

---

## Stage 1: Scope & Trust Triage (Intent Mapping)

Before fetching or reading documentation, evaluate whether the user query aligns with declared wiki boundaries:

1. **Evaluate Intent & Boundary Fit**:
   - Execute `match-skill` to match the user task against the 62 wikis and 25 curated skills:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py match-skill "<task_prompt>" --limit 3 --output match.json
     ```
2. **Inspect Trust Semantics & Calibrated Abstention**:
   - Inspect `match.json` for `in_scope` and `calibrated_confident`:
     - If `in_scope: true` and `calibrated_confident: true`: Proceed to Stage 2.
     - If `in_scope: false` or `calibrated_confident: false`: **Abstain immediately** (~94% correct abstention rate) and fall back to live web search (`search_web`), adhering to the AgentWikis trust contract.
3. **Verify Version Freshness**:
   - Inspect `scope.currentAs` to confirm the documented software version matches the user's environment:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py scope <wiki_slug> --output scope.json
     ```

> **Completion gate**: `Scope verified and confidence calibrated` (`in_scope: true`, calibrated confidence confirmed, negative boundary check passed).

---

## Stage 2: Contract-First Ingestion & Medallion Lakehouse

Transform raw documentation feeds into typed, governed analytical assets through contract-first lakehouse engineering:

1. **Assert Open Data Contract Compliance (ODCS)**:
   - Validate incoming corpus metadata against `contracts/agentwikis_contract.yaml`:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py validate-contract --output contract_report.json
     ```
   - Enforce schema conformity across wikis, scope objects, and skill records.
2. **Traverse Medallion Lakehouse Tiers**:
   - **Bronze Layer (Raw Ingestion)**: Immutable full-text dump (`llms-full.txt`) and raw Markdown endpoints with source isnad metadata (`_ingested_at`, `_source_url`).
   - **Silver Layer (Cleansed & Slotted)**: Normalized, strongly-typed slotted entities (`WikiEntity`, `WikiScope`, `SkillEntity`) enforcing `Rule 12` (`slots=True, frozen=True`).
   - **Gold Layer (Curated Agent Marts)**: Topic-sliced Markdown chunks, inverted search indices, and graph-ready routing bridges.

> **Completion gate**: `Open Data Contract validated` (`validate-contract` returns compliant status with zero schema violations).

---

## Stage 3: Visual Brief & Topology Review

Generate an interactive, self-contained HTML brief in `%TEMP%` to visually inspect routing topologies before execution:

1. **Target Location**:
   - Write to `%TEMP%\agentwikis_routing_brief.html` (or project artifact directory).
2. **Render Visual Topology**:
   - Render the **Hybrid Data Topology DAG** via Mermaid.js:
     - 62 wikis interconnected across 7 categorical domains (Agents, DevTools, Inference, ImageGen, Blockchain, Trading, Marketing).
     - Individual wikis decomposed into hierarchical document trees (`wiki/index.md` &rarr; `concepts/`, `summaries/`, `entities/`).
     - $O(1)$ Hash Map direct lookup and priority triage extraction queues.
   - Embed an **Interactive Blast Radius Matrix** listing affected document slices and token estimates.
3. **Delivery**: Surface clickable `file:///` link to the user.

> **Completion gate**: `Visual Brief rendered` (self-contained HTML brief generated in `%TEMP%` and delivered to user).

---

## Stage 4: 6-Dimension Quality Gating & Checkpoint

Eliminate silent documentation drift and hallucinations through comprehensive DAMA-DMBOK data quality profiling:

1. **Execute 6-Dimension Quality Audit**:
   - Profile the corpus across all 6 canonical DAMA data quality dimensions:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py quality-profile --min-score 85.0 --output quality_scorecard.md
     ```
   - **Accuracy**: Validate slug syntax and URI structures.
   - **Completeness**: Assert presence of descriptions, categories, and `scope.covers`.
   - **Consistency**: Verify cross-referenced wikis exist in the registry.
   - **Timeliness / Freshness**: Flag wikis stale by $>24$ months.
   - **Validity**: Validate ISO-8601 timestamps and Markdown delimiter syntax.
   - **Uniqueness**: Assert zero duplicate slugs in the registry.
2. **Mandatory Checkpoint Gate**:
   - Confirm aggregate quality score $\ge 85.0\%$. If failing, pause batch retrieval and quarantine defective records.

> **Completion gate**: `Quality score >= 85.0%` (automated 6-dimension quality scorecard passes with zero critical failures).

---

## Stage 5: Zero-Latency Slice Retrieval & Skill Dispatch

Extract targeted documentation sections locally and dispatch execution to specialized agent skills:

1. **Extract Zero-Latency Local Markdown Slices**:
   - Extract the target document section via O(1) byte-offset seek from `llms-full.txt` (9.77 MB) without network latency:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py read-doc "<wiki_slug>/<doc_path>" [--section "<heading>"] --output doc_slice.md
     ```
   - Or compile a bounded context pack in a single call:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py context-pack "<task_prompt>" --max-tokens 2000 --output context_pack.md
     ```
   - In Harness agent loops, resolve in-memory via micro-kernel IoC: `context.require(AGENTWIKIS_SERVICE_KEY)`.
2. **Dispatch to Specialized Skills**:
   - If the task matches a local workspace skill (e.g. `pocock-skills`, `crafting-skills`, `deepen-architecture`), activate the skill to execute the workflow.
3. **Emit MCP Server Configuration (Optional)**:
   - Generate client setup configurations for Antigravity, Claude Code, or standard JSON:
     ```powershell
     python .agents/skills/agentwikis-router/scripts/agentwikis_cli.py mcp-config --client antigravity --output mcp_config.json
     ```
4. **Cite Provenance**:
   - Ground model responses with verifiable citations to source wiki paths in the reference footer.

> **Completion gate**: `Documentation slice retrieved and dispatched` (targeted markdown written to disk, provenance footer cited).

---

## Trust Semantics & Operational Invariants

- **Scope Boundary**: Every wiki defines explicit `covers` and `notCovered` sets. If out of scope, never guess; escalate to web search.
- **Calibrated Abstention**: When searching, `calibrated_confident: false` indicates the wiki corpus lacks the answer (~94% correct abstention).
- **File Output Invariant**: All CLI commands output results to files, preventing terminal context flooding.
- **Relocatable Path Resolution**: Corpus paths resolve dynamically via `--corpus-dir`, `AGENTWIKIS_CORPUS_DIR`, or `config.default.yaml`.
- **Remote Rate Limiting**: Remote HTTP queries enforce a 1 req/sec delay with exponential backoff on HTTP 429/5xx.

---

## Anti-Patterns

- **Context Flooding Monolith** — Dumping multi-megabyte raw corpus files directly into model context instead of extracting targeted sections to disk.
- **Passive Data Swamp** — Storing and querying documentation files without data contracts, governance rules, or quality metrics.
- **Uncontracted Producer Drift** — Unilaterally altering Markdown headers or index schemas without machine-readable contract validation.
- **Hallucinatory Extrapolation** — Guessing answers when a wiki declares the topic under `notCovered` instead of falling back to web search.
- **Silent Scope Bypassing** — Executing technical commands without verifying the `currentAs` version date against the user's software environment.
- **Redundant Network Calls** — Querying remote endpoints over HTTP when the full text is already available locally.
- **Hardcoded Absolute Paths** — Hardcoding user-specific machine absolute paths in skill scripts, causing failures in sandboxes and CI runners.
- **Unregistered Orphan Skill** — Operating a skill without registering it in `CONTEXT-MAP.md`, the Knowledge Vault, or graph indexer.
