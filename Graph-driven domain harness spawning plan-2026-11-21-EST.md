# Graph-driven domain harness spawning plan — 2026-11-21 EST

Use Brain Harness's live skill knowledge graph (`19` clusters, `55` cross-cluster bridges) and Knowledge Vault (`382` KIs) to design, document, and spawn a prioritized set of lean, high-value domain harnesses — each backed by an explicit documentation contract and ICM workspace layout so no spawned harness is a nebulous collection of files.

## Verified starting state (BH `f337079`, 2026-11-21)

What exists and is verified live:

- **Spawning & plugin seam:** `HarnessSpawnerEngine` + `HarnessSpawnerPlugin` (`plugins/agent_orchestration/harness_spawner/`) + `harness spawn` CLI (`run`, `review`, `list`, `retire`, `propose`, `adopt`, `reject`, `check-drift`), all routed through `get_spawner_service` (`5718fa6`). All six spawn defaults (`Q2–Q7`) are confirmed (`f337079`, `"keep all six as-is"`).
- **Skill knowledge graph & vault discovery:**
  - `harness skills clusters` discovers `19` functional skill clusters with central hubs, cohesion percentages, and emergent capabilities (ranging from tight `2–5` skill clusters at `17–50%` cohesion up to `8–23` skill mixed hubs at `10–12%` cohesion).
  - `harness skills bridges --json` discovers `55` cross-cluster macro edges.
  - `harness skills joint-query <TOPIC> --json` queries both the Skill Graph and `.harness/knowledge/` (`382` KIs), returning `knowledge_items` (with `isnad_status`), `skills`, `linked_pairs`, `unbridged_kis`, and `ungrounded_skills`.
- **ICM workspace architecture:** `icm-workspace-architect` skill and `harness icm` CLI (`scaffold`, `audit`, `links`, `quotes`, `index`) in `src/harness/commands/icm.py` and `src/harness/services/icm_architect/`.
- **Doc tooling:** `harness doc` (`audit`, `drift`, `scaffold`, `wiki-compile`, `wiki-lint`) and `dock.yaml` materialization (`src/harness/services/harness_spawner/materialize.py`).

Verified gaps to close as part of this plan:

1. **`IcmScaffolder.scaffold_form()` (`src/harness/services/icm_architect/scaffolder.py:56-116`) only scaffolds `pipeline` and `record_library`.** The other 3 canonical ICM forms (`knowledge_bundle`, `context_map`, `system_map`) do not yet generate their form-specific `CONTEXT.md` and directories.
2. **Materialized harnesses currently lack a documentation bundle.** `materialize_spawn_as_dock()` (`materialize.py:76`) writes only the `BRAIN_SURFACE` tree (`AGENTS.md`, `.agents/skills/*/SKILL.md`, scripts), `dock.yaml`, and `.harness/spawn_tree_digest.json`. There is no required `README.md`, `CONTEXT.md`, `docs/USE_CASES.md`, `docs/PROVENANCE.md`, `docs/RUNBOOK.md`, or companion `CARD.md` verification.
3. **No graph-to-blueprint ranking seam.** Selecting which clusters/bridges make the highest-value harnesses and assembling their skill + KI + ICM-form blueprints is currently manual.
4. **No worktree/branch materialization mode.** Today `--materialize <dir>` writes a standalone dock-linked directory; optional `git worktree` branch mode (`harness/<name>`) is not wired yet.

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick the independent-check box (`5.2`) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change the confirmed spawn defaults (`Q2–Q7` in `Harness spawning research-2026-11-13-EST.md`) or weaken the merge-back policy (zero silent auto-adoption; never raw-`git merge` a trimmed domain branch back into `main`).
- Do not delete or move `.agents/skills/` directories on `main` (`tests/test_plugin_integration_drift.py` asserts live skill and plugin counts on `main`).
- Do not touch any unticked box in any other plan (`Spawn provenance 3.3`, `Spawn capability completion 5.2`, `Spawn completion follow-up 3.1`, etc.) and do not re-open any ticked box.

---

## Mandatory Documentation Inclusion Specification (Every Spawned Harness)

Every durable domain harness spawned under this plan **must** include the following 7-part documentation and contract bundle so it is immediately intelligible to both humans and cold agents:

| # | Path | Audience | Purpose & Required Sections | Verification Gate |
|---|---|---|---|---|
| 1 | `README.md` | Human | **Identity & Quick Start:** Domain mission, concrete use cases, explicit **"Out of Scope / Do NOT Use For"** boundary, lineage header (`Prime` commit SHA, cluster/bridge ID, spawn ID, date), quick-start CLI commands, skill inventory table, and seeded KI table. | Non-empty, required headings present, zero broken relative links (`harness icm links .`). |
| 2 | `AGENTS.md` (+ `CLAUDE.md` / `GEMINI.md` pointers) | Agent (L0) | **Small Routing Entry (`< 60` lines / `<= 500` tokens):** 2-line identity, routing table to `README.md`, `CONTEXT.md`, `docs/`, `_shared/`, and `.agents/skills/*/SKILL.md`, domain invariants, and explicit merge-back rule (stage via `propose`, never auto-adopt). | `SurfaceSpec` `validate()` + `harness icm audit .` (`AGENTS.md < 60` lines). |
| 3 | `CONTEXT.md` + stage/shelf `CONTEXT.md` | Agent (L1/L2) | **Operational Contracts:** ICM form map (`pipeline` / `record_library` / `knowledge_bundle` / `context_map` / `system_map`), numbered stages or shelf schema, exact backticked `Inputs`, explicit `Do NOT load:` deflections, `Outputs`, and `Check` (`check.md` gate). | `harness icm audit .` (`< 8,000` tokens/step) + `harness icm links .`. |
| 4 | `docs/USE_CASES.md` | Human + Agent | **Worked Scenarios:** 2–3 concrete end-to-end walkthroughs (trigger/input -> stage or command sequence -> expected artifact -> pass/fail check criterion) demonstrating real usage. | Required sections present; relative links resolve. |
| 5 | `docs/PROVENANCE.md` | Auditor | **Graph & Knowledge Lineage:** Exact `skills clusters` / `skills bridges` / `skills joint-query` inputs used to choose this harness, skill-count and estimated token savings vs Prime (`114` skills -> `3–5` skills), and table of every seeded KI with its `isnad_status` (`VERIFIED` required for ground-truth claims; `UNVERIFIED` excluded or explicitly flagged). | Deterministic JSON/Markdown check; zero `UNVERIFIED` KIs promoted as verified. |
| 6 | `docs/RUNBOOK.md` | Operator | **Lifecycle & Merge-Back Guide:** Commands to inspect (`dock inspect`), validate (`dock run <name> validate`), check drift (`spawn check-drift`), re-materialize when Prime updates, propose learnings (`spawn propose`), and adopt/reject (`spawn adopt` / `reject`). Includes explicit warning against raw `git merge` into `main` if branch/worktree-backed. | Commands match live CLI (`docs/reference/cli.md` parity). |
| 7 | `.agents/skills/<skill>/SKILL.md` + `CARD.md` + `dock.yaml` | Agent + Runtime | **Executable Surface & Manifest:** Only the `3–5` selected skills (plus `icm-workspace-architect`), each retaining its companion `CARD.md` (Rule 37) and passing Rule 44 description bounds (`100–350` chars with negative boundary); `dock.yaml` declares permissions (`write: false`, `push: false` by default), boundaries, `tools`, `validate`, and `audit-docs` entrypoints. | `SurfaceSpec.validate()` + `SkillCardRule` + `dock run <name> validate` (`DOCK_HARNESS_OK`). |

---

## Prioritized Harness Portfolio (Derived from Live Graph Data)

Selection rubric for ranking candidates from `harness skills clusters` (`19` clusters) + `harness skills bridges` (`55` bridges) + `harness skills joint-query`:
1. **Repeatability & Frequency:** Solves a recurring engineering or research workflow run weekly.
2. **Token Savings:** Replaces `114` Prime workspace skills (`~10,226` est. tokens) with `3–5` domain skills (`~350–600` est. tokens — **~94–96% workspace skill reduction**).
3. **Graph Cohesion & Grounding:** Draws from a tight cluster (`>= 17%` cohesion) or high-value bridge, backed by `VERIFIED` KIs in `.harness/knowledge/`.
4. **Clear ICM Form Fit:** Maps cleanly to a deterministic ICM form with disk-verifiable `check.md` or `_index.md` outputs.

### Tier 1 — Highest Value (Spawn First, Wave 1)

| Priority | Harness Name | Graph Source (Live) | Included Skills (`4–5`) | ICM Form | Core Use Cases |
|---:|---|---|---|---|---|
| **1** | `harness-repo-distiller` | Bridge `cluster_12_brain_artifact_miner` (`50%` cohesion) -> `cluster_06_mind_reader` + `cluster_04_external_repo_bridge_forge` | `icm-workspace-architect`, `repo-triad-forge`, `epistemic-isnad-audit`, `brain-artifact-miner`, `conversation-trajectory-miner` | `knowledge_bundle` + `pipeline` | 1) Ingest an external GitHub repo in isolation and stage dual-file KIs with verbatim quote checks (`harness icm quotes`). 2) Mine session transcripts/artifacts into reusable skills without bloating Prime. |
| **2** | `harness-security-forensics` | `mantis-security-review` cluster (`5` skills, `20%` cohesion) + bridge to `plugin-seam-and-mirror-auditor` + `ki_20260908_mantis_01` | `icm-workspace-architect`, `mantis-security-review`, `rea-reverse-engineering`, `differential-facet-verifier`, `ethical-hacker-networking` | `record_library` + `pipeline` | 1) Commit-history security triage and finding deduplication tracked as frontmatter records (`findings/_index.md`). 2) Binary/bundle reverse-engineering and multi-provider claim verification with auditable evidence dossiers. |
| **3** | `harness-arch-modernizer` | `architecture-deepening-workflow` cluster (`3` skills, `17%` cohesion) + bridges to `data-topology-mapper` & `codebase-context-governor` | `icm-workspace-architect`, `architecture-deepening-workflow`, `monolith-decomposition-engine`, `data-topology-mapper`, `legacy-modernization-pipeline` | `system_map` + `pipeline` | 1) Map DAG seams and blast radius before touching legacy modules. 2) Decompose monolithic files to `<= 200` lines behind characterization test safety nets with `< 8,000` token stage contracts. |
| **4** | `harness-context-economizer` | `headroom-context-optimizer` cluster (`2` skills, `50%` cohesion) + bridges to `agent-harness-architect` & `codebase-context-governor` | `icm-workspace-architect`, `headroom-context-optimizer`, `token-economizer`, `codebase-context-governor`, `repo-doc-synchronizer` | `context_map` + `pipeline` | 1) Audit `AGENTS.md`, skills, and docs for Rule 11/44/47 bloat and link drift. 2) Profile and trim prompt/catalog token waste across repos before spawning or shipping changes. |

### Tier 2 — Specialized On-Demand Harnesses (Wave 2, Spawn When Needed)

| Priority | Harness Name | Graph Source (Live) | Included Skills (`3–5`) | ICM Form | Core Use Cases |
|---:|---|---|---|---|---|
| **5** | `harness-knowledge-graph` | `knowledge-graph-pipeline` cluster (`3` skills, `50%` cohesion) + bridge to `ebbinghaus-memory-governor` | `icm-workspace-architect`, `knowledge-graph-pipeline`, `neo4j-knowledge-graph-architect`, `sql-recursive-graph-traversal`, `ontological-engineering-coach` | `knowledge_bundle` + `pipeline` | Ingest tabular/domain corpora into Neo4j or recursive SQL CTE hierarchies with ontological/Gruber audits. |
| **6** | `harness-skill-factory` | `deep-skill-forge` subset + `skill-eval-assurance-runner` | `icm-workspace-architect`, `crafting-skills`, `agent-skill-sdlc`, `skill-eval-assurance-runner` | `pipeline` + `record_library` | Design, scaffold (`SKILL.md` + `CARD.md`), and statistically evaluate (`pass^k` / Wilson CI) new skills before admission to Prime (`runs/_index.md`). |
| **7** | `harness-data-lakehouse` | `bigquery-augmented-analytics` cluster (`4` skills, `25%` cohesion) | `icm-workspace-architect`, `bigquery-augmented-analytics`, `data-management-architect`, `garf-reporting-architect`, `paperless-document-pipeline` | `pipeline` + `record_library` | Govern ODCS/Medallion data contracts, SQL reporting DAGs, and hybrid document-pipeline queries. |
| **8** | `harness-cloud-k8s` | `cloud-infrastructure-architect` cluster (`2` skills, `10%` cohesion) | `icm-workspace-architect`, `cloud-infrastructure-architect`, `kubernetes-drift-guardian` | `record_library` + `pipeline` | Audit K8s manifest/RBAC drift, container sandboxing policies, and Prometheus exposition. |

---

## Track 0 — User Decision Gate (Confirm Before Building)

- [ ] **0.1 Confirm storage layout for durable spawned harnesses.** Choose one:
  - **(a) Standalone dock-linked directories** under a dedicated root (e.g. `D:\GitHub\harnesses\<name>\` via `--materialize`, zero git branch management on `Brain Harness`), or
  - **(b) Git worktree branches** off `Brain Harness` (`harness/<name>` in e.g. `D:\GitHub\harnesses\<name>\` via `git worktree add`, sharing `src/` and `.venv` with trimmed `.agents/skills/` and scoped merge-back only).
  Record the user's exact choice and date verbatim.
- [ ] **0.2 Confirm Wave 1 scope.** Confirm which Tier 1 harnesses to spawn first (all 4 in Tier 1, a subset of 1–2 as a tracer bullet first, or swaps from Tier 2). Record the user's exact choice and date verbatim.
- [ ] **0.3 Confirm documentation strictness.** Confirm the 7-part Documentation Inclusion Specification above (specifically whether `docs/USE_CASES.md`, `docs/PROVENANCE.md`, and `docs/RUNBOOK.md` should be included in the canonical drift digest alongside `AGENTS.md` + skills, so editing docs without re-approving flags drift in `harness spawn check-drift`).

## Track 1 — Close ICM Scaffolder & Graph-Selection Gaps

- [ ] **1.1 Complete the 3 missing ICM scaffold forms.** Extend `IcmScaffolder.scaffold_form()` (`src/harness/services/icm_architect/scaffolder.py`) so `knowledge_bundle` (`sources/raw/`, `_meta/keep-out.txt`, `claims/`, `CONTEXT.md`), `context_map` (`CONTEXT.md` with `consumes:` / `produces:`, `domains/`, `_shared/`), and `system_map` (`CONTEXT.md`, `nouns/`, `verbs/`, `impact/_index.md`) generate valid, `harness icm audit`-passing skeletons. Add `@pytest.mark.unit` tests covering all 5 forms.
- [ ] **1.2 Build a deterministic graph-to-blueprint recommender.** Add a read-only service/helper (under `src/harness/services/harness_spawner/` + exposed through `HarnessSpawnerPlugin` and a CLI subcommand, e.g. `harness spawn blueprints` or `suggest`, documented in `docs/reference/cli.md` in the same commit) that reads `skills clusters`, `skills bridges`, and `skills joint-query`, scores candidates by cohesion, skill-budget savings, and verified KI grounding, and emits structured `HarnessBlueprint` specs (`name`, `domain`, `skills`, `icm_form`, `seeded_kis`, `use_cases`, `out_of_scope`).
- [ ] **1.3 Unit tests for blueprint scoring & KI grounding filter.** Verify deterministic ranking, exclusion/flagging of `UNVERIFIED` KIs, and strict skill-count capping (`<= 6` skills per blueprint by default). Marked `@pytest.mark.unit`.

## Track 2 — Documentation Bundle & Materialization Contract

- [ ] **2.1 Implement the 7-part Documentation Bundle generator & validator.** Add `build_harness_docs(blueprint, ...)` and `validate_harness_docs(repo_dir)` (under `src/harness/services/harness_spawner/`) generating `README.md`, `<60`-line `AGENTS.md` + pointers, ICM `CONTEXT.md` contracts, `docs/USE_CASES.md`, `docs/PROVENANCE.md`, `docs/RUNBOOK.md`, and copying companion `CARD.md` files for every included skill.
- [ ] **2.2 Wire documentation generation & `audit-docs` entrypoint into `materialize_spawn_as_dock` (and worktree mode if chosen in 0.1).**
  - Extend `materialize_spawn_as_dock()` (`src/harness/services/harness_spawner/materialize.py`) and `HarnessSpawnerPlugin.materialize()` so every materialized harness emits the full 7-part documentation bundle, adds an `audit-docs` entrypoint to `dock.yaml` (verifying required docs exist + relative links resolve), and records doc hashes in `.harness/spawn_tree_digest.json` (per decision `0.3`).
  - If option (b) worktree mode was chosen in `0.1`, add `--worktree <dir>` / branch creation (`harness/<name>`) with an explicit merge-back guard refusing raw full-branch merges into `main`.
- [ ] **2.3 Contract & portability tests.** `@pytest.mark.unit` tests verifying: (a) a materialized harness fails `validate_harness_docs()` if any of the 7 required doc artifacts or required sections is missing; (b) `dock run <name> validate` and `dock run <name> audit-docs` both pass with bare `python` stripped from `PATH`; (c) `harness icm audit` and `harness icm links` pass with zero errors; (d) tampering with `README.md` or `docs/RUNBOOK.md` is caught by `check-drift` (if enabled in `0.3`).

## Track 3 — Spawn Wave 1 Harnesses (End-to-End Real Runs)

- [ ] **3.1 Run graph blueprint discovery and save dated selection report.** Run the Track 1.2 recommender live against current `Brain Harness` (`19` clusters, `55` bridges, `382` KIs) and record the exact cluster metrics, seeded `VERIFIED` KIs, and token-budget delta for every Wave 1 harness selected in `0.2`.
- [ ] **3.2 Review and spawn each selected Wave 1 harness.** For each Wave 1 harness:
  1. Run `harness spawn review` to inspect the diff and canonical SHA-256 digest.
  2. Materialize via `harness spawn run --materialize ... --approve-dock` (or `--worktree` per `0.1`) with the 7-part Documentation Bundle and ICM layout.
  3. Verify `dock inspect`, `dock run <name> validate` (`DOCK_HARNESS_OK`), `dock run <name> audit-docs`, `harness icm audit`, `harness icm links`, and `harness spawn check-drift` (`drifted: false`).
  4. Record the exact token footprint (skills count + est. catalog tokens vs Prime's `114` skills) and dated log per spawned harness.

## Track 4 — Cold-Agent Walk Test & Use-Case Proof

- [ ] **4.1 Run the 8-Point ICM Cold Walk Test on every spawned Wave 1 harness.** Verify a cold agent with zero prior context can answer "where am I / what are my inputs / how do I verify" from `README.md` + `AGENTS.md` + `CONTEXT.md` in `<= 2` reads, with every step under `8,000` tokens and zero broken relative links.
- [ ] **4.2 Execute one real use case per spawned Wave 1 harness and exercise reviewed merge-back.** Run at least one worked scenario from each harness's `docs/USE_CASES.md`, stage one real finding/learning via `harness spawn propose`, and exercise `adopt` / `reject` (in an isolated sandbox or live vault only on explicit user approval) — proving the harness is operationally useful, not just a static scaffold.

## Track 5 — Verification

- [ ] **5.1 Re-run all gates with dated outputs.**
  - All spawn + ICM + documentation test suites (`pytest`)
  - Drift gates (`tests/test_plugin_integration_drift.py`, `tests/test_cli_content_drift.py`)
  - Full unit gate (`pytest -m "unit" -q --timeout=60`)
  - `ruff check .`, CI-scoped `ruff format --check`, and touched-file `ruff format --check`
  - `mypy src/harness/kernel --ignore-missing-imports` and `mypy` on modified modules (without `--ignore-missing-imports`)
  - `harness context lint`, `harness knowledge sync --strict`, and `uv lock --check`
  Record exact numbers reproducible on a fresh checkout and note machine-specific timings.
- [ ] **5.2 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
