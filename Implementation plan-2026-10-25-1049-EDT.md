# Brain Harness — Implementation Plan

**Created:** 2026-10-25 10:49 EDT
**Repo:** `SpectreDeath/brain-harness`
**Purpose:** One pick-away list for improving the project, synthesized from a full-repo analysis pass (kernel, agent/services, ingestion/bridges/MCP, CLI/UI/frontend, tests/CI/docs) plus direct reads of the October skill batch, the ICM push (`61476792`), and a 28-item sample of the `.harness/knowledge` vault (281 items total).

## How to use this plan

- Every item is a checkbox. Pick items off in any order, but the suggested sequence in §1 is the recommended one.
- **P0** = do first (security hole, or the core learning loop). **P1** = high leverage, do soon. **P2** = valuable, do when convenient. **Verify** = finding was blocked by GitHub rate limits during analysis and needs a re-read before acting.
- Evidence paths are given for every item so you can check the claim before starting.
- JSON, schemas, and structured data are inline as code blocks, per repo convention for handoff documents.

## 1. Suggested sequence

1. **Track 0 — Security ( §3 ).** One genuine vulnerability (Zip Slip in the fetcher) plus a few fail-open behaviors. These are small, independent, and should land before anything else that touches ingestion.
2. **Track 1 — The learning core ( §4, §5 ).** Self-reflection + knowledge graph. This is the most important part of the project: the epistemology (how the harness knows) and the ontology (how things relate). The single biggest gap in the whole repo is that the vault is currently write-only — reflection writes knowledge items, but nothing in the agent loop reads them back.
3. **Track 2 — Consolidation ( §6, §7 ).** The codebase has grown by deepening, and deepening has left seams: three DAG models, three plugin-handling layers, eleven bridge implementations, ~70 CLI names for ~45 groups. None of these are crises; all of them compound.
4. **Track 3 — Interfaces, tests, docs, skills ( §8, §9, §10 ).** CLI/UI drift, test-layout drift, doc drift, and skill-catalog hygiene.

## 2. Method and coverage caveats

- Analysis was done through the GitHub MCP connector. Midway through, the provider began returning HTTP 429 (rate limit) and the analysts stopped per the hard-stop rule rather than retrying. Consequences:
  - The kernel report is structural (directory maps verified; file contents mostly unverified).
  - The UI report could not open `commands/icm.py`, `session.py`, `plugins.py`, `skills/cli.py`, `ui/server/*`, or `frontend/package.json` / `App.tsx`.
  - The tests/CI report could not read workflow files, `docs/reference/`, `USER_MANUAL.md`, or `walkthrough.md`.
  - Items affected are marked **Verify** and collected in §11.
- Findings marked **verified** rest on files actually read. Findings marked **unverified** rest on structure, naming, or the repo's own rules and should be confirmed with a read before acting.
- The October skill batch (11 skills), the ICM commit, and the vault graph sample were read directly by the main agent and are not affected by the rate limit.

## 3. Track 0 — Security: the ingestion trust boundary

Ingestion is *designed* to consume untrusted foreign code, so its trust boundary is the project's most security-sensitive surface. These items are small and independent.

- [ ] **P0 — Fix Zip Slip in the fetcher.** `src/harness/ingestion/fetcher.py` calls `zf.extractall(target_dir)` with no member-path validation. GitHub-generated ZIPs are low-risk, but `_fetch_local_zip` and `_fetch_remote_zip` accept arbitrary archives, so a crafted archive with `../` entries writes outside the plugin directory — defeating the sandbox story before sandboxing starts. Fix: validate every member path against the target directory (reject absolute paths and `..` escapes) before extraction, and add a regression test with a malicious ZIP fixture.
- [ ] **P0 — Bound fetched content.** Responses are fully buffered in memory (`fetcher.py`, 120 s timeout, no max size) and the post-extract walk counts the whole tree. Add a max-bytes limit on downloads, a max-files / max-total-bytes limit on extraction, and stream instead of buffering. This closes the ZIP-bomb / giant-repo hazard.
- [ ] **P0 — Fix cache-key collisions.** GitHub fetches are correctly keyed `owner__repo`, but remote ZIPs are keyed by URL stem alone and local ZIPs by file stem. Two different sources named `tools.zip` collide, and a stale cached directory is returned silently whenever the target exists and `force` is unset. Fix: key caches by a hash of the full URL / file bytes plus stem, and invalidate on mismatch.
- [ ] **P1 — Make the PyPI converter fail loudly.** When the PyPI API is unreachable, `fetch_metadata` returns fabricated info (version `1.0.0`, empty `requires_dist`) in `src/harness/ingestion/pypi_converter.py`. A plugin can be synthesized from fake metadata instead of failing. Fix: raise on unreachable metadata; never synthesize from fabricated data.
- [ ] **P1 — State and enforce the isolation mode of dynamic plugins.** `src/harness/creator/dynamic/builder.py` (`from_code`) compiles raw code strings into in-memory plugins. If these run in-process, agent-supplied code execution in-process contradicts the subprocess-isolation-by-default rule for untrusted code. Fix: document the intended mode, enforce it in code, and add a test that dynamic plugins cannot escape it.
- [ ] **P1 — Pin or sandbox bridged peer code.** Bridges degrade gracefully when a substrate is *missing* (`src/harness/bridges/locator.py`), but bridged peer code (Em-Cubed, Memtext) is mounted in-process via path manipulation (`src/harness/bridges/em_cubed.py` imports `sys`). A compromised or version-skewed peer repo executes inside the harness process. Fix: version-pin peer substrates, or offer a sandboxed bridge mode; add a conformance test asserting the Memtext local fallback matches the real interface's guarantees.
- [ ] **P1 — Audit WASM and container executor defaults.** `src/harness/plugins/sandbox/wasm.py` and `container.py` are the least conventional executors. Verify WASI capability grants (filesystem/network) and container privilege defaults (rootless, read-only mounts). Sandbox breadth is only a strength if each executor's default posture is actually restrictive.
- [ ] **P2 — Remove the async/sync footgun in the validator.** `src/harness/creator/validator/` documents Rule 38 (`validate()` vs `validate_sync()`) rather than eliminating the confusion. Replace with a single entry point that detects sync context, so new callers cannot hit the unawaited-coroutine trap.

## 4. Track 1A — Epistemology: close the learning loop

This is the highest-leverage work in the repo. Reflection currently writes knowledge items that nothing reads.

- [ ] **P0 — Retrieve knowledge items into agent step context.** Verified: `list_knowledge_items` is called only from `services/storage/vault_operations.py` itself, `commands/reflection.py`, and tests — never from `agent/`. The vault is populated by `services/reflection_worker.py` (300 s interval, 0.80 minimum confidence) → `creator/reflection.py` → `.harness/knowledge/`, and synced into storage, but no step, prompt, or router reads it back. Fix: retrieve relevant KIs into step context — at minimum alongside the skill guidance already injected in `agent/react/prompting.py:build_react_initial_messages` (which currently injects up to 4 skills and nothing from the vault). Start with a bounded budget (e.g. top 3 KIs by tag/category overlap with the task) so token budgets stay bounded, and keep it behind the same deterministic pruning the RepoMap already uses.
- [ ] **P0 — Measure retrieval usage and let it prune/promote.** Once retrieval exists, log which KIs get retrieved and whether the steps that used them succeeded. Promote repeatedly useful items, demote or archive never-retrieved ones. Without this, the vault grows by age, not by evidence — and "it learns" stays a slogan instead of a mechanism.
- [ ] **P1 — Give claims a lifecycle, not just a boolean.** Isnad claims today carry `verified: true/false`, a source, and an evidence type. Add: a confidence score, status transitions (`unverified → verified → challenged → superseded`), and explicit supersession links, so the vault can represent "we used to believe X, now we believe Y, here's why" instead of accumulating contradictory items silently.
- [ ] **P1 — Detect contradictions.** With 281 items, some disagree. Add a periodic pass that flags KIs with incompatible assertions on the same topic (same tags/category, conflicting claim text). Surface conflicts as a review queue rather than resolving them automatically — the point is to notice, not to auto-rewrite history.
- [ ] **P1 — Consolidate the reflection write path.** The write path crosses three packages: `services/reflection_worker.py` (daemon), `creator/reflection.py` (engine), `commands/reflection.py` (CLI). Consolidate the write path into the storage service so that adding the read path (§4, first item) is one seam, not three.
- [ ] **P1 — Decide the vault's single source of truth.** `services/storage/vault_operations.py:sync_knowledge_vault` syncs disk → storage one-way. If anything writes storage directly, disk and storage diverge silently. Decide: disk is canonical (per the dual-file invariant) and storage is a rebuildable cache — then enforce it (rebuild storage from disk on startup or on demand; reject direct storage writes for KIs).
- [ ] **P1 — Fix the silent failure in the skill-guidance seam.** `agent/react/prompting.py` wraps `resolve_skill_intelligence` in a bare `except Exception: pass` — if the skill service breaks, the loop silently runs with zero skill guidance and no log line. Fix: log at warning level at minimum, and surface a degraded-mode flag on the trajectory so runs that lost guidance are visible.
- [ ] **P2 — Re-route skills as tasks evolve.** Skill guidance is injected once, in initial messages; `execute_step` re-injects RepoMap every step but never re-routes skills. Long tasks that drift into new subproblems keep their step-1 skills. Fix: re-route per wave or per N steps within the existing `max_skills=4` budget.
- [ ] **P2 — Record skill-creation provenance.** The October analysis showed skills are created by *different combinations* of skills (book-to-skill-forge vs repo-triad-forge vs the new ICM combination). Record, per skill, which combination produced it — ideally as lineage edges into the vault (see §5). This makes "it learns" measurable: which combinations produce skills that get used, and which produce shelfware.

## 5. Track 1B — Ontology: make the graph explicit and typed

The graph exercise in this session (28 sampled items, 37 nodes, 27 edges) showed the vault's relationships are currently *implicit* — reconstructed from shared file paths, shared category strings, and skill docs. A graph you have to reconstruct by string-matching is a graph you cannot query reliably.

- [ ] **P0 — Add typed edges to KI metadata.** Extend the metadata schema with an explicit `edges` list. Proposed schema (to be refined against the current `metadata.json` format):

```json
{
  "id": "ki_20261024_icm_architect",
  "edges": [
    { "type": "became_skill", "target": "icm-workspace-architect", "target_kind": "skill" },
    { "type": "distilled_from", "target": "arXiv:2603.16021", "target_kind": "source" },
    { "type": "references_code", "target": "src/harness/services/icm_architect/", "target_kind": "path" },
    { "type": "synthesizes", "target": "ki_20261019_pyrit_redteam_01", "target_kind": "ki" },
    { "type": "supersedes", "target": "ki_20260821_03", "target_kind": "ki" },
    { "type": "contradicts", "target": "ki_20260913_pr_lens_schema", "target_kind": "ki" }
  ]
}
```

Edge types to support at minimum: `distilled_from`, `became_skill`, `became_plugin`, `references_code`, `synthesizes`, `supersedes`, `contradicts`, `same_domain`. Rules for the schema: every edge is directional, every edge carries its type (no untyped "related to"), and `supersedes`/`contradicts` edges are the mechanism that implements the claim lifecycle in §4.
- [ ] **P0 — Backfill edges for existing items mechanically, then curate.** Shared code references (older schema `references[]` paths), shared categories, and skill docs that name their source KI are all mechanically derivable — the graph exercise proved it. Generate edges from those signals, mark them `derived: true`, and let curation upgrade them. Do not hand-write 281 items' edges.
- [ ] **P1 — Unify the two metadata eras.** Older items use `summary + references`; newer items use `tags + isnad + category`. They do not interoperate, which puts a seam through the middle of the graph's own history. Fix: migrate older items to the current schema (mechanical where possible: `references[]` paths → `references_code` edges, `summary` → summary field), or introduce a versioned schema (`schema_version` field) with adapters so old and new items query uniformly. Do not leave the seam.
- [ ] **P1 — Replace free-form categories with a controlled hierarchical taxonomy.** Current categories mix styles: `agent_orchestration` next to `reverse-engineering / differential-analysis / facet-semantics`. Define a taxonomy (domain → subdomain, e.g. `agent_orchestration`, `security_and_forensics/reverse_engineering`, `memory_and_epistemics`), validate it at KI creation, and provide a migration map for existing values. This is what lets the graph answer "all security knowledge" instead of guessing which strings count.
- [ ] **P1 — Suggest links at KI creation time.** Most sampled nodes were isolates. When a new KI is distilled, propose links to existing items by shared refs, overlapping tags, and nearby categories, and require the authoring agent to accept or reject each. The graph should densify deliberately, not by accident.
- [ ] **P1 — Build a KI graph query service.** The skill graph already exists (`services/skill_graph/`); the vault needs its equivalent. Minimal viable queries: lineage of a skill (which KIs fed it), dependents of a KI (which skills/plugins cite it), contradictions of a KI, and neighborhood of a topic. Build it on the typed edges from the first item, not on string matching.
- [ ] **P2 — Fix the tag problem.** Finding from the sample: tags are specific labels, not connective tissue — only one shared tag across 28 items. Either make tags do connective work (a small controlled vocabulary of cross-cutting tags, validated at creation) or stop treating them as graph edges and rely on the typed edges above. Do not do both half-heartedly.

## 6. Track 2A — Kernel and plugin seams

Structural findings (directory maps verified; most file contents unverified — see §11 for the re-read list).

- [ ] **P1 — Map and resolve the three plugin-handling layers.** Plugin lifecycle logic lives in at least three places: `kernel/lifecycle/manager/`, `kernel/runtime/` (`plugins.py` *and* `plugin_ops.py` — two near-synonymous names), and `plugins/` (`loader.py`, `catalog.py`). Map which module owns discovery, loading, enabling, disabling, and unloading; merge or re-document overlaps. This is exactly the seam duplication the repo's own Rule 20 ("in-place deepening over tool sprawl") forbids.
- [ ] **P1 — Resolve the reconciler duplication.** Both `kernel/reconciler.py` and `kernel/runtime/reconcile.py` exist. Verify whether the split is intentional (kernel-level state vs runtime-level plugin set) or drift, and document the contract between them.
- [ ] **P1 — Clean up naming collisions.** `plugins/sandboxed.py` sits next to a `plugins/sandbox/` package; `plugins/bridge_runner.py` sits next to `plugins/transport.py`. Check whether each pair is genuinely distinct (e.g. sandboxed-plugin base class vs executor package; wire protocol vs bridged-plugin execution) and fold or rename what is a wrapper.
- [ ] **P1 — Run a dispose/revoke test-and-review pass.** Rule 54 exists because the `_dispose_stack` inverse-accumulator mechanism (realm keys, provider metadata, `revoke()` / `revoke_all_from()` purging) has bitten before. Partial unload/revoke is where IoC containers leak or double-dispose. Add targeted tests: revoke one service, revoke all from one provider, unload a plugin mid-session, then assert no orphaned closures fire on container disposal.
- [ ] **P1 — Verify event-bus durability guarantees.** Append-only semantics (Rule 4) depend on the `events/bus/` implementation. Confirm: JSONL persistence, no delete/mutate API surface, and backpressure behavior for slow subscribers. Write the guarantees down in `events/README.md` if they are not already there.
- [ ] **P2 — Verify factory trust gating and rule compliance by grep.** Confirm in `plugins/sandbox/factory.py` that the default executor is subprocess (or venv/WASM) and in-process requires an explicit trust flag; grep `kernel/context/` for `ServiceKey` usage and any string-keyed resolution paths (Rule 2); check `plugins/base.py` and the drop-in convention for the module-level `plugin = MyPlugin()` singleton (Rule 45), since a missing singleton silently breaks loader discovery.

## 7. Track 2B — Services consolidation

`services/` holds 100+ modules. The loop/service separation is genuinely good; the problem is sprawl at the edges.

- [ ] **P1 — Unify or map the three DAG models.** `services/agent_graph.py` (execution thread DAG), `agent/session/` trees (`SessionTreeNode`), and `agent/swarm/` (`SwarmDAG`) model closely related structures with separate stores and renderers. The composite thread key (`{run_id}_{node_id}`) already hints at collision risk. Either build one DAG substrate with role-typed nodes, or document the mapping between the three and the key discipline. Do not leave three models undescribed.
- [ ] **P1 — Unify the skill subsystem.** Skill capability is spread across `skill_graph/`, `skill_parser/`, `skill_pipeline.py`, `skill_clustering/`, `skill_visualizer.py`, plus `skill_graph/adapter.py` whose documented job is papering over partial providers (Rule 58). The adapter's existence is a smell: the seams grew organically. Consider a single `skills/` package with parser/graph/pipeline as submodules.
- [ ] **P1 — Pick canonical import paths and deprecate facades.** `services/compute_assessor.py` (facade over `services/compute/`) and `agent/context_optimizer.py` (facade over `services/context_optimizer/`) are 100% re-export shims. Fine individually, but every elevated capability now has two import paths, doubling drift surface. Pick one canonical path per capability and deprecate the other.
- [ ] **P1 — Audit the overlap clusters (names suggest, contents must confirm).** Memory systems: `okf_memory.py`, `memgraphrag.py`, `memory_decay/`, `graphiti.py`, `semantic_cache.py`, `vector_index.py`, `embedding_cluster.py`. Harness-evaluation systems: `agent_harness.py`, `ai_native_harness.py`, `coding_harness_calibrator.py`, `harness_compass.py`, `self_evaluating_pipeline.py`, `prompt_benchmark.py`. Foreign-agent bridges: `chatbotx`, `claude_code`, `gemini_vercel`, `kimi_bridge`, `openhands_bridge`, `opencode_bridge`, `orca_bridge`, `openclaw_bridge`, `django_bridge`, `tau_bridge`, `brain_bridge`. For each cluster: read the modules, merge or document the boundary, and delete or fold what is dead.
- [ ] **P1 — Settle the bridge layering rule.** Several integrations exist twice: a service-layer file (`services/orca_bridge.py`, `django_bridge.py`, `opencode_bridge.py`, `openclaw_bridge.py`) *and* a plugin-layer counterpart, plus `bridges/` substrate adapters, `plugins/*_bridge` gateway plugins, `creator/archetypes/mcp_bridge.py`, and `mcp/client_plugin.py` — four meanings of "bridge" with different contracts. Either consolidate or document the rule (e.g. service = engine, plugin = wrapper) and enforce it in review.
- [ ] **P1 — Build a shared bridge scaffold.** Eleven foreign-agent bridges is a fragmentation risk even if each is small. A shared scaffold (auth, transport, tool mapping, error taxonomy) cuts the per-bridge cost and makes the next bridge a day's work instead of a week's.
- [ ] **P2 — Audit session export duplication.** `agent/session/` contains both top-level `exporter.py` and `manager/export.py`. Either they serve different layers or one is dead/duplicate — a small audit settles it.
- [ ] **P2 — Document or move thin protocol-only modules.** `services/test_runner.py` (~2.7 KB) is models + key with no implementation in the file. If implementations live in plugins, document the split; if the protocol is dead weight in the core tree, move it out.

## 8. Track 2C — Ingestion breadth and correctness

- [ ] **P1 — Add non-GitHub sources.** Every URL regex in `src/harness/ingestion/fetcher.py` is `github.com`-only (plus `git@github.com` SSH), despite the "universal" naming. Add GitLab, Codeberg, and generic-git support, or narrow the claim. This caps the "ingest any repository" promise.
- [ ] **P1 — Bring JS/TS inspection to parity.** AST extraction is Python-only (`ingestion/inspector/ast_extractor.py`: `extract_python_entrypoints`, `try_python_ast`). JS/TS repos get manifest-level treatment only (`try_package_json`), even though the creator scaffolds JS/TS and the validator has a `JavaScriptStaticAnalysisRule`. Deep inspection coverage is asymmetric across languages.
- [ ] **P1 — Verify monorepo partitioning actually happens.** `ingestion/converter.py` is 100 lines and mostly delegates to `SandboxedPlugin`; the ingestion README invokes Rule 18 (domain-partitioned synthesis for monorepos), but no partitioning logic is visible in the converter head. Find where monorepo splitting happens — a monorepo ingested as one plugin violates the repo's own rule.
- [ ] **P1 — Resolve the MCP protocol version mismatch.** `src/harness/mcp/protocol.py` sets `DEFAULT_PROTOCOL_VERSION = "2024-11-05"`, while `mcp/README.md` claims MCP 2026-07-28 and Rule 24 cites the same 2026 date. Either the codec lags the spec or the docs overclaim — both cannot be true. Fix the codec or the docs, and add a test pinning the version.
- [ ] **P2 — Add Streamable HTTP transport to the MCP server.** `mcp/server/server.py` wires `AsyncStdioServerTransport` only; there is no Streamable HTTP transport in `mcp/server/`, which limits hosting the harness for remote agent environments.
- [ ] **P2 — Pin the vendored external snapshot.** `plugins/external/Pocock-skills-main/` is a complete third-party repo snapshot (21 entries) with no visible version pin. It loads as a plugin, so it goes stale silently as upstream evolves. Pin it (commit hash + update procedure) or move it out of the load path.
- [ ] **P2 — Resolve the probable duplicate plugin.** `plugins/security_and_forensics/` contains both `pyrit_red_teaming` and `pyrit_redteaming` — near-identical names that strongly suggest a rename leftover or accidental duplicate. Confirm and delete one.
- [ ] **P2 — Fix the flywheel count inconsistency.** `bridges/README.md` says "800+ domain skills"; `bridges/flywheel.py` says "839+". Trivial in itself, but it shows the catalog number is asserted in two places with no live source. Generate the number or drop it.

## 9. Track 3A — CLI, commands, and UI

- [ ] **P1 — Fix alias sprawl.** `src/harness/cli.py` registers ~70 names for ~45 groups (verified): `doc-builder`/`hf-doc-builder`, `architect`/`harness-architect`, `gate`/`ai-native-harness`, `bigquery`/`bq`, `gemini-vercel`/`streaming-chatbot`/`gemini-chat`, `pre-commit-security`/`security-guard`/`shift-left`, `brain-miner`/`miner`/`artifact-miner`, `trajectory`/`trajectory-miner`/`conversation-miner`, `temp`/`temp-miner`/`ephemeral-miner`, `icm`/`icm-architect`, and more. `--help` becomes a wall of near-duplicates, and docs/tests must cover every alias. Fix: one canonical name per group plus a single declared alias table with a deprecation policy.
- [ ] **P1 — Generate the command catalog.** The `cli.py` module docstring lists ~13 commands; the file actually registers ~70 names. Docs drift is already happening at the front door. Generate the docstring (or a command catalog page) from the registered groups instead of hand-maintaining it.
- [ ] **P1 — Run a command inventory.** Overlapping domains in `commands/`: three miner groups (`brain_miner`, `trajectory_miner`, `temp_miner`), `doc` vs `doc_builder`, `compass` vs `architect`/`harness_architect`, `gis` vs `datasets` vs `data` vs `bigquery`. Produce group → subcommand count → backing service, then consolidate thin groups or document the boundaries.
- [ ] **P1 — Add a Rule 6 lint/test.** Rule 6 requires each CLI group to be declared exactly once in a single co-located block. `cli.py` itself holds (one import, one registration block — that half verified), but per-module declaration could not be checked (rate limit), and the `skills/` layout (four `cli_*.py` files) is precisely where a group could be re-declared or shadowed. Add a test that imports every group from its module and asserts exactly one definition site.
- [ ] **P1 — Nail down the UI serving story.** `ui/static/` contains only `index.html`, yet AGENTS.md's negative boundaries reference `src/harness/ui/static/vendor/` — a directory that does not appear in the listing. And `pyproject.toml` packages `src/` only, with no frontend build step. Answer, and document: when a user runs `harness ui` from a pip install, do they get the Vite app, the minimal `static/index.html`, or a broken page? Confirm `commands/runtime.py` (`ui_cli`) wires to `ui.server.app` rather than to `static/index.html` alone.
- [ ] **P2 — Check the frontend properly.** `frontend/package.json`, `services/`, `types/`, and `modals/` could not be read (rate limit). Check: framework versions, whether the API client is typed or endpoints are hardcoded, and whether `services/` covers all 8 views (Overview, Agent, Graph, Plugins, Sandboxes, Skills, Swarm, Timeline) or some views are stubs.
- [ ] **P2 — Verify CLI↔UI reuse and document it.** The dashboard's 8 views cover only a fraction of the ~45 CLI groups — fine if headless-first is an explicit decision, but nothing in the structure proves web routes reuse command implementations rather than duplicating logic. Inspect `ui/server/adapter.py`: if routes call the same service layer as the Click commands, say so in `ui/README.md`; if they shell out to the CLI or duplicate logic, fix that drift vector.

## 10. Track 3B — Tests, CI, docs, and skills hygiene

- [ ] **P1 — Resolve the test-layout contradiction.** AGENTS.md says tests "mirror `src/harness/` structure," but 350 test files sit flat at `tests/` root — no `tests/kernel/`, `tests/agent/`, `tests/services/`, only `plugins/`, `skills/`, `unit/`. Either the convention is stale or "mirroring" now means filename prefixes. Confirm the intended layout and either restructure or correct AGENTS.md. At 350+ files, flat layout makes ownership, targeted runs (`pytest tests/services/...`), and dead-test detection harder.
- [ ] **P1 — Audit decomposition-test proliferation.** 73 `*_decomposition.py` files suggest tests generated alongside each decomposition cycle. Risk: duplicated or overlapping contract tests, and tests that assert the decomposition itself rather than behavior — brittle under the next refactor. Audit for duplicate coverage and adopt a rule: decomposition tests must assert behavior, not file layout.
- [ ] **P1 — Verify the CI matrix and sharding.** The repeated cross-platform fixes (Windows UTF-8/proactor Rules 23, 26, 29, 30, 53, 56; Linux-vs-Windows path failures in `71704660`) point to platform divergence as the chronic CI failure mode, and a 350-file suite with a 60 s per-test timeout can run very long unsplit. Verify: does CI run Windows + Linux (+ macOS?), does it split by marker (unit vs integration vs slow), and are timeouts set at the job level? If the suite runs monolithically, marker-based sharding is the obvious fix.
- [ ] **P1 — Make doc-threshold gates deterministic.** `71704660` explicitly mentions "doc thresholds" among Linux CI failures. If CI gates on documentation coverage/length thresholds, review what the gate measures and whether it fails on content or on formatting (line endings, path separators) — formatting gates will keep flaking across platforms.
- [ ] **P1 — Run the docs-drift checklist.** (a) Does the CLI reference document the `harness icm` group added 2026-10-25, or does USER_MANUAL predate it? (b) Do `docs/plugins/` pages match the current `plugins/` directory? (c) Does `walkthrough.md` still match the current CLI surface? (d) Are `docs/reference/` pages generated from code or hand-maintained (hand-maintained = drift-prone)? Also fix the verified drift: `plugins/README.md` claims "95 Plugins" and tabulates agent_orchestration as 20 and data_engineering as 8; actual listings show ~32 and ~14. Generate counts or drop them.
- [ ] **P1 — Enforce or drop the coverage bar.** The ≥80% kernel/plugin coverage bar appears in AGENTS.md, but no coverage artifact or badge was verifiable. Confirm CI enforces it (e.g. `--cov-fail-under`) rather than it being aspirational. Related: the README badge is a static shields.io badge (`tests-2650%2B%20passed`), not a live CI status badge — it does not self-update. Make it live or regenerate it on release.
- [ ] **P1 — Verify the "2650+ passing tests" claim.** 350 test files at root (plus three subdirectories of unknown size) need only ~7.6 tests per file to reach 2,650, so the claim is plausible but unconfirmed. Verify by running `pytest --collect-only -q` and counting, ideally in CI itself.
- [ ] **P2 — Check exercises and scratch for rot.** `exercises/` contents could not be read (rate limit). Exercises rot fastest because nothing runs them unless wired up — verify they execute against the current API, or add them to CI. Check `.agents/scratch/` for committed stale temp files, generated briefs, or machine-local paths (same class of issue as the next item).
- [ ] **P2 — Fix the absolute local link in the TypeScript skill.** `ts-agent-harness-constructor/SKILL.md` links its "Interactive Visual Brief" to a `file:///C:/Users/spectre/AppData/Local/Temp/book-to-skill-forge-20261020-170234.html` path — dead on any other machine, and it breaks the repo's own relative-link rule (Rule 47). Replace with a relative link or remove it.
- [ ] **P2 — Treat skill-catalog growth as a routing problem.** 95 skills, 11 added in October 2026 alone. The binding constraint is no longer producing skills — it is routing to the right one. Invest in negative boundaries, the skill graph router, and retrieval quality rather than new-skill throughput. Watch the known overlap zone: system-design-architect vs python-diagrams-architect vs cloud-infrastructure-architect.

## 11. Verification backlog (blocked by rate limits during analysis)

Re-check these with fresh reads before acting on the items that depend on them. In priority order:

1. `src/harness/plugins/sandbox/factory.py` + `in_process.py` (trust gating).
2. `src/harness/kernel/runtime/plugins.py` vs `plugin_ops.py` + `src/harness/plugins/loader.py` + `catalog.py` (plugin-layer overlap map).
3. `src/harness/kernel/context/core.py` + `effects.py` (dispose/revoke, Rule 54).
4. `src/harness/kernel/reconciler.py` vs `runtime/reconcile.py` (reconciler contract).
5. `src/harness/events/bus/` full listing + core module (append-only guarantees).
6. `src/harness/plugins/base.py` + `sandboxed.py` + `bridge_runner.py` vs `transport.py` (naming/seam cleanup).
7. `src/harness/commands/icm.py`, `session.py`, `plugins.py`, `skills/cli.py` (Rule 6 single-declaration check).
8. `ui/server/` contents, especially `adapter.py` (CLI↔UI reuse), and `frontend/package.json`, `services/`, `types/`, `modals/`, `App.tsx`.
9. `.github/workflows/` contents (CI matrix, sharding, timeouts).
10. `docs/reference/`, `USER_MANUAL.md`, `walkthrough.md`, `exercises/` contents (drift checks).
11. `tests/plugins/`, `tests/skills/`, `tests/unit/` contents (suite size and layout).
12. `agent/session/exporter.py` vs `manager/export.py` (export duplication).
13. The service overlap clusters in §7 (read before merging anything).

## 12. Appendix — evidence index

| Area | What was read | Headline finding |
|---|---|---|
| Kernel / events / plugins | Directory maps for `kernel/`, `events/`, `plugins/`; README architecture | Well-factored shape; seam duplication risk across three plugin layers; trust/disposal invariants unverified |
| Agent / services | `agent/` loop, session, swarm; `services/` survey + central modules | Loop/service separation is clean; vault is write-only; skill guidance injected once; three DAG models |
| Ingestion / creator / bridges / MCP | Pipeline, fetcher, inspector, converter, creator, bridges, MCP server/client | Clean pipeline seams; Zip Slip + fail-open behaviors; "bridge" means four things; MCP version mismatch |
| CLI / UI / frontend | Full `cli.py` (219 lines), `commands/` listing, `ui/` and `frontend/src` structures | ~70 names for ~45 groups; stale docstring; two-UIs serving story unclear |
| Tests / CI / docs | `tests/` root listing (350 files), `pyproject.toml`, `docs/` layout, commit history | Flat layout vs mirroring convention; 73 decomposition tests; CI platform divergence is chronic; static test-count badge |
| Skills (Oct 2026 batch) | 11 new skills' SKILL.md + CARD.md checks | All meet craft standards (description length, anti-patterns, negative boundaries); one dead local link; routing is now the constraint |
| Knowledge vault | 28-item metadata sample from 281 items; full directory listing | Dual-file format holds; tags are labels not edges; dense self-architecture core; literature→skill lineage is the learning loop made visible |
| ICM push (`61476792`) | Service, plugin manifest, skill, CLI registration | Full vertical slice (service → plugin → CLI → skill → vault item); the pattern the repo's own rules prescribe |

## 13. Closing note

The through-line of this plan is simple: the harness already knows how to act, and it is learning how to learn. The work that matters most is making that learning *closed-loop* (vault items feeding back into decisions), *explicit* (typed edges instead of inferred relationships), and *honest* (claims with lifecycles, contradictions surfaced, security boundaries that hold against untrusted input). Everything else in this plan is consolidation that keeps the core honest as it grows.
