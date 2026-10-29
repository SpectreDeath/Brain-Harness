# Brain Harness — Post-Plan Analysis

**Created:** 2026-10-29 12:36 EDT
**Repo:** `SpectreDeath/brain-harness`
**HEAD analyzed:** `c1d593d` (Track 3B)
**Purpose:** A fresh five-area analysis after the 2026-10-25 implementation plan was completed (63/63 items, 2026-10-28). This document assesses the current state from code, not from commit messages: what the ~67 hours of work genuinely closed, what remains, and what to do next.
**Method:** Read-only pass over a local clone, five areas (kernel/plugins, agent loop/learning core, ingestion/bridges/MCP, CLI/UI/frontend, tests/CI/docs/skills). No test-suite run this pass, except the CLI area, which built the wheel and ran `tsc`, `vite build`, and `oxlint` on a scratch copy. File counts are grep-based, not from pytest collection. The highest-severity claims were spot-checked by the author against the clone (venv trust gap, lifecycle callers, on-disk edges, CI matrix).

## Verdict

The plan's work genuinely moved the repo. Its biggest claim — the write-only vault — is dead for ReAct runs, and most Oct 25 gaps are closed in substance, not just ticked. But this round has a clear pattern: the engines are real, while the maintenance wiring and the documentation gates around them are thin. And one genuinely new security gap showed up in the sandbox.

## 1. What the 67 hours genuinely closed

### The learning loop (was: write-only vault)

- Retrieval into decisions is real: `src/harness/agent/react/prompting.py:80-97` resolves the vault, calls `retrieve_relevant_knowledge_sync(task, max_items=3)`, appends the knowledge block to the system message, and records the retrieval, once per run via `engine.py:81-89` and `loop.py:68`.
- Outcome feedback is real: `engine.py:34-45` records success/failure per retrieved item on completion, LLM error, and final answer; `engine.py:130-133` stamps retrieved items and guidance-degraded state into trajectory metadata.
- Scoring is a real lexical heuristic (`services/storage/vault_retrieval.py:32-90`): tag/category/title/summary weights, ARCHIVED excluded, PROMOTED ×1.25, DEMOTED ×0.5, bounded injection (top 3, 250 chars/item).
- Claim lifecycle is a real model: `IsnadClaimStatus` unverified → verified → challenged → superseded (`services/storage/models.py:12-18`), with confidence, `superseded_by`, and lineage; `evaluate_vault_lifecycle` promotes/demotes on success ratios (`vault_retrieval.py:162-195`).
- Contradiction detection is a real heuristic, gated on shared domain/tags/anchors (`services/storage/vault_contradiction.py:45-140`), surfaced via `audit_contradictions` and a `harness knowledge contradictions` CLI command (`commands/reflection.py:282-308`).
- Typed edges, graph queries, and taxonomy exist: `KnowledgeEdge` with the plan's proposed types (`models.py:38-46`), `KnowledgeGraphQueryService` (`vault_graph.py`), 9 controlled `TaxonomyDomain`s with a legacy alias map (`vault_taxonomy.py:9-30`), plus a `knowledge lineage` CLI command.
- The reflection write path is consolidated: `creator/reflection/` is now a package, the daemon drives it, and the CLI delegates to the worker — the old worker/creator/commands split is gone as a duplication.
- Skill guidance failure at initial build is fixed: failure now logs a warning and sets `guidance_degraded=True` in trajectory metadata, and skills re-route every 5 steps (`agent/react/dispatch.py:133-157`).
- The loop has measurably run: 15 disk items carry nonzero retrieval/success counts.

### Security and ingestion

- Fetcher batch is complete: `_download_zip_streaming` pre-checks `Content-Length`, streams in 64 KiB chunks against a 100 MB cap, and deletes partial files on error (`ingestion/fetcher.py:~270-310`); extraction limits (`max_files` 10,000, `max_total_bytes` 250 MB, >100:1 compression-ratio check) are enforced on both extraction paths (`plugins/loader.py:46-50,79-90`).
- Cache keys are fixed: remote ZIPs keyed `stem__sha256(url)[:12]`, local ZIPs by path/size/mtime hash, GitHub by `owner__repo`, with `.cache_meta.json` provenance and fail-closed `_is_cache_valid` (missing/mismatched/corrupt meta → re-download).
- Zip Slip coverage is complete for the codebase: only two `extractall` sites exist in `src/` (fetcher, loader), both validated; no `tarfile` or `unpack_archive` usage anywhere in `src/`; creator paths funnel through the pipeline, so dynamic ingestion inherits validation.
- PyPI fail-open is fixed: `fetch_metadata` raises `PyPIFetchError` on HTTP errors and request errors; the remaining `1.0.0` fallback applies only to a missing key in a successful response.
- MCP version story is resolved and transports expanded: `protocol.py:27-29` declares default `2024-11-05`, latest `2026-07-28`, and a supported tuple; the server holds both STDIO and streamable HTTP transports. The README explains baseline vs extended honestly.
- Bridges scaffold is actually used: `em_cubed.py`, `flywheel.py`, `memtext.py` all subclass `EcosystemBridgePlugin`; the flywheel count inconsistency is gone.
- Ingestion breadth is real: providers now cover GitHub, GitLab, Codeberg, Bitbucket, and generic Git.
- Pyrit aftermath is clean where it matters: zero references to `pyrit_redteaming` in `src/`, `plugins/`, `docs/`, `tests/`, `.agents/`, or top-level docs; the category README now lists `pyrit_red_teaming` with `service.pyrit_scanner`. One stale line remains (see §2).

### Kernel, events, and plugin trust

- Plugin layering is coherent: discovery/loading → registry → lifecycle state machine → runtime API, with one implementation per operation and thin delegating wrappers elsewhere. No dead runtime/lifecycle modules found; no TODO/FIXME/DEPRECATED markers in `kernel/`, `events/`, or `plugins/`.
- Sandbox trust defaults are correct at the factory and manifest layers: default isolation SUBPROCESS, `trusted = False` default, in-process requires trusted plus an existing entrypoint, untrusted in-process requests demoted to subprocess with a warning, in-process import failure falling back to subprocess (fail-closed). A dedicated `tests/test_factory_trust_gating.py` exists.
- Container executor defaults are strong: `--network=none`, `--read-only` + `--tmpfs /tmp`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`, plugin dir mounted read-only, 256 MB / 1.0 CPU defaults.
- Event bus append-only holds in practice: JSONL opened in append mode only; `clear()` is in-memory only with an explicit docstring stating JSONL is never truncated, and has no callers outside `events/bus/` itself. Nuance: the in-memory ledger is a bounded ring buffer (`deque(maxlen=10_000)`); "append-only" strictly describes the durable log.
- Dispose/revoke (Rule 54) is implemented, metadata-tagged (`_realm_key`/`_provider`), and tested, including revoke purge, revoke-all selectivity, hot-swap, and LIFO order (`tests/test_context_dispose_revoke.py`).
- Typed-key and singleton discipline hold: zero `register_instance`/`resolve(` violations; 128 of 133 drop-in `main.py` files export a module-level singleton, and the 5 without ship `plugin.json` and load via the manifest path.
- The Oct 25 Zip Slip fix survived consolidation: `validate_zip_members` is still defined and wired into the fetcher.

### Interfaces, tests, docs, and skills

- CI is now genuinely cross-platform: matrix `os: [ubuntu-latest, windows-latest, macos-latest]`, Python 3.11 (+3.12 on Ubuntu), job timeouts (15/30 min), `cancel-in-progress`, `PYTHONIOENCODING: utf-8` (`.github/workflows/ci.yml:38-48`).
- Plugin counts are now exact: "11 Domain Plugin Categories / 134 Plugins" in `plugins/README.md:15`, matching a rigorous count of directories containing `plugin.json` per category.
- ICM is now documented: a full `harness icm` section in `docs/reference/cli.md:263-267` and an ICM section in `USER_MANUAL.md:375+`.
- Dead Temp links are gone: zero `file:///C:` / `AppData/Local/Temp` links remain in `.agents/skills/`; the only AppData mention left is descriptive prose in `temp-artifact-miner`, not a link.
- Skill craft standards hold in sample: all 8 sampled skills have `## Anti-Patterns`, a "Do not use for" boundary, and frontmatter descriptions inside the 100–350 band.
- Test-layout contradiction resolved: `AGENTS.md:90` now states tests live in `tests/` with domain prefixes, and `tests/README.md` documents the flat root layout as a deliberate convention. Decomposition sprawl is stable (73/12/4) and now governed by a policy forbidding brittle layout assertions.
- Test-count claim is arithmetically supported: 367 `test_*.py` files, 2,795 `def test_` functions by grep, consistent with the claimed 2,820+ (parametrization only pushes collection higher).
- CLI docstring can no longer rot: `cli.py:176` generates it from the live command table; `--help` shows 50 canonical commands instead of 83 invocable names (40 groups + 10 standalone + 29 aliases + 4 shortcuts). Rule 6 holds in the sample (40 group declarations, zero duplicate names).
- Command-domain overlaps are now documented partitions backed by distinct services (miners by substrate, `doc` vs `doc_builder`, architect vs compass, gis/datasets/data/bigquery).
- Frontend builds clean: `tsc -b` clean, `vite build` succeeds, `oxlint` 0 errors; no stub markers; all 24 `api.ts` methods map to served routes; WebSocket client matches the backend endpoint; CLI↔UI routes go through `RuntimeAdapter`, with zero subprocess/shell invocations in `ui/server/`.

## 2. What remains, ranked

### High

- **Lifecycle and contradiction resolution never run in production.** `evaluate_vault_lifecycle` is called only by tests (`tests/test_epistemology_learning_loop.py:161`); no CLI command, daemon, or worker calls it anywhere in `src/`. Promotion/demotion therefore never runs outside tests. Contradiction review surfaces a queue with suggested edges, but nothing in `src/` writes `superseded_by` or status from a review. Detection without resolution.
- **Superseded items remain injectable.** Retrieval scoring excludes only ARCHIVED; SUPERSEDED and CHALLENGED score at full weight. A superseded heuristic can still be injected into decisions, and no review-apply step creates supersession links.

### Medium-high

- **VenvExecutor silently drops the network restriction for untrusted plugins.** `sandbox/factory.py:119` routes to `VenvExecutor` whenever isolation is VENV **or the plugin declares any dependencies** — regardless of trust. `VenvExecutor.__init__` takes no `network_disabled` parameter (`sandbox/venv.py:25-30`), and its inner `SubprocessExecutor` is built with no network flag, defaulting to unrestricted. An untrusted plugin that declares dependencies — an ordinary shape for a malicious plugin — runs with network enabled, while an identical dependency-free plugin gets `HARNESS_NO_NETWORK=1`. The factory's `network_disabled=(not trusted)` is applied only on the WASM-fallback and final-subprocess paths (`factory.py:169,177`).
- **Docker fallback drops all restrictions.** When DOCKER is requested but no docker/podman binary is found (`factory.py:102-116`), the fallback is a bare `SubprocessExecutor(entrypoint)` — no `network_disabled`, no `memory_limit_mb`. Same class as above, narrower trigger.

### Medium

- **The graph is empty in practice.** 0 of 281 on-disk knowledge items carry `edges` or a non-default `status`. The distiller sets no edges, anchors, or explicit status on new items; `propose_links` is called only by tests, never in the save path; mechanical backfill cannot help self-reflection items (their `source_target` is `internal://harness/history`, matching neither `src/` nor `plugins/`, and `anchors.target_skill` is never set); backfilled edges live in the store until an export, and there is no `knowledge export` CLI command. Skill-creation provenance has no writer either — no `became_skill` writer exists in `src/`, so `knowledge lineage` reports no direct lineage for most skills.
- **Mid-task learning is skills-only, prompt-frozen, and silently failing in two seams.** Knowledge items never re-retrieve as a task evolves (skills re-route every 5 steps; KIs do not), rerouted skills only affect the anti-pattern tool gate and never reach later prompt text, and `dispatch.py:155-156` (reroute) plus `transactions.py:47-50` (action gate) both use bare `except Exception: pass`. Knowledge-retrieval failure is warning-logged but sets no degraded flag, unlike skill guidance.
- **Coverage is measured but not enforced.** CI runs `--cov=src/harness --cov-report=xml` with no `--cov-fail-under`, and `pyproject.toml` has no `fail_under`. The `tests/README.md` "Maintain ≥80% coverage" target is documentary only.
- **No type checking in CI despite a strict config.** `pyproject.toml` sets `disallow_untyped_defs = true` and mypy is a dev dependency, but `ci.yml` has no mypy/pyright step (only `ruff check`, no `ruff format --check`).
- **Docs reference is still hand-maintained with no freshness gate.** `docs/reference/` is still 7 hand-written files; nothing references or tests `cli.md` freshness. It already misses 9 groups (`antigravity`, `calibrate`, `eval`, `gate`, `gemini-vercel`, `gradio`, `knowledge`, `router`, `tau`) — 43 headings vs 50 canonical commands. `walkthrough.md` is still a dated project report, not living walkthrough docs, with 0 icm mentions.
- **Skills catalog numbers are stale; routing burden unchanged.** `.agents/skills/README.md` still says "50 Deep-Module Skills" / "50-Skill Catalog" while the actual count is 95. Track 3B touched no skills README or skill service; there is no new index/tiering, and frontmatter enforcement rests on 5 per-skill suites (56 test functions), not a repo-wide gate.
- **The UI shipping story is unchanged.** Dual-mode logic still serves `frontend/dist` if built, else `static/index.html` — but the dist lookup is repo-root-relative, so it only resolves from a source checkout; the built wheel ships `static/index.html` and not `frontend/dist` (no `MANIFEST.in`, no frontend package-data), and CI has no node/npm/vite steps. A pip-installed user always gets the static dashboard (substantial at 116 KB, not a stub), and the two UIs can drift silently. Minor: the static page loads Google Fonts and Mermaid from CDNs, so offline/air-gapped use degrades.

### Lower

- **MCP version negotiation is dead code.** `negotiate_protocol_version` / `validate_protocol_version` (`protocol.py:32-41`) have zero callers; the router always answers the default `2024-11-05` without reading the client's requested version, so a `2026-07-28` client gets a silent downgrade. The README's "negotiates" claim overstates the wiring. No breakage for baseline clients. Separately, the MCP client is still STDIO-only while the server gained streamable HTTP.
- **Bridged peer code still runs in-process without version pins.** `em_cubed.py:67-77` inserts the peer repo's `src/` into `sys.path` and imports it in-process; no version constraint was found in the locator (env vars / sibling dirs / config paths only). This is first-party-ecosystem code, not untrusted plugin code — and dynamic/plugin loading is gated — but the trust posture is implicit rather than explicit.
- **Three "disable all" implementations with divergent semantics.** Lifecycle batch returns `dict[str, bool]` in reverse dependency order and disables core plugins too; runtime `disable_all_plugins` returns `list[str]` in dict order and keeps core plugins when `keep_core=True`; `ui/server/adapter.py` re-implements the keep-core loop a second time, so the core-plugin set lives in two places. Enable-all also diverges by adapter mode: the runtime path skips sandboxed/user plugins while the standalone path enables everything — the same UI "enable all" button does two different things depending on construction.
- **Container runs as the image default user** (no `--user` flag; mitigated by cap drops, no-new-privileges, read-only root, read-only mount).
- **Subprocess network isolation is a monkeypatch, not a boundary** (`socket.socket.connect` patching keyed off `HARNESS_NO_NETWORK=1`); bypassable by shelling out to network tools. Only the container path gives true network isolation.
- **Extraction caps are metadata-based, not metered.** `validate_zip_members` sums `info.file_size` from the central directory; a crafted archive with forged headers understating sizes could pass the 250 MB cap and expand further during extraction, which writes bytes without a running meter. Honest ZIP bombs are still caught; only a header-forging attacker bypasses.
- **Rule 45's text is stricter than the loader's actual contract.** The rule says every `main.py` must export a singleton, but the manifest/subprocess path deliberately loads function-entrypoint plugins without one (5 existing plugins). Either the rule wording or a locking test needs to catch up.
- **Stale Pyrit reference in a tracked file.** `.harness/config.json:43` still lists `domain.pyrit_redteaming` in `disabled_plugins` (harmless at runtime — never resolves, never loads — but should be cleaned). A second mention is historical vault provenance; leave or annotate, don't rewrite silently.
- **Smaller fetcher residuals.** Local-ZIP cache seed is path + size + mtime, not a content hash (a same-size, same-mtime rewrite serves stale cache); the git-clone path has no size bound; `httpx` `timeout=120.0` is per-operation, so a slow-drip download can run long (total bytes are still capped); `_download_zip_streaming` sniffs `hasattr(client.get, "mock_calls")` for a test path in security-sensitive code — deserves a comment or a seam.
- **CI "sharding" is really gate + full run.** The unit step (`-m "unit"`) and the coverage step (`-m "not slow"`) overlap, unit tests run twice, nothing is sharded across jobs, and zero tests use the `slow` marker, so the exclusion currently excludes nothing.
- **Exercises are structured but unwired** (4 modules × 3 lessons, runnable in form, not referenced in CI).
- **Frontend nits.** Sampled `api.ts` methods call `res.json()` with no `res.ok` check, so backend errors surface as parse failures; several backend-only endpoints (creator validate/archetypes, single-session view, swarm status/mermaid/dispatch-skill) have no React caller — API surface for other clients, but UI-invisible.
- **Alias surface is 33 names and growing**, with no deprecation marking; help hides it rather than reducing it. One naming wrinkle: `calibrator/group.py` declares `"calibrator"` but `cli.py` registers it as `"calibrate"`.
- **DAG models and memory cluster unconsolidated.** All three DAG models still exist (`services/agent_graph.py`, `SwarmDAG`, session tree/exporter) and the memory cluster (`okf_memory`, `memgraphrag`, `graphiti`) is still three standalone services with no deprecation markers. Whether the DAG trio is intentional layering is undocumented. Swarm KI injection is unverified (no `StepExecutionEngine` usage found under `agent/swarm/`), and retrieval is lexical-only despite a `services/vector_index.py` existing.
- **Dispose errors are swallowed** (logged at warning, execution continues) — arguably correct for teardown, but a failing inverse leaves no signal beyond a log line.

## 3. Suggested next actions, in order

1. **Wire lifecycle + contradiction-apply into a production trigger.** Add a `harness knowledge lifecycle` command (or a step in the reflection daemon cycle) that runs `evaluate_vault_lifecycle`, prints `audit_contradictions`, and lets a review decision set `status`/`superseded_by`. This single change activates the whole epistemology maintenance loop.
2. **Exclude SUPERSEDED from retrieval (down-weight CHALLENGED) and make detector findings actionable.** One scoring change in `retrieve_relevant_knowledge` plus an apply step converting a reviewed `supersession_candidate` into a `supersedes` edge + status change closes the stale-heuristic hole.
3. **Close the venv/Docker trust gaps.** Add a `network_disabled` parameter to `VenvExecutor`, pass it through to its inner `SubprocessExecutor`, and pass `network_disabled=(not trusted)` from the factory on the VENV path; do the same plus `memory_limit_mb` on the Docker fallback. Extend `tests/test_factory_trust_gating.py` to assert an untrusted manifest with dependencies yields an executor with networking disabled.
4. **Wire `propose_links` into the reflection save path, run a one-time backfill + export over the 281 disk items, and add the missing `knowledge export` CLI command.** This gives the graph real edges and migrates the vault to the new schema on disk, where it persists.
5. **Add mid-task KI re-retrieval at the 5-step reroute cadence and replace the two bare `except: pass` seams** (`dispatch.py:155`, `transactions.py:47`) with warning logs + trajectory degraded flags, matching the initial-build pattern.
6. **Enforce or downgrade the coverage target** (add `--cov-fail-under=80`, or kernel/plugin-scoped, or mark the target advisory) **and add a type-check step to CI** (mypy against the existing strict config) or document why type checks stay local-only.
7. **Decide the UI shipping story and gate it:** either vendor a built `frontend/dist` into the wheel (or explicitly document that pip `harness ui` = static dashboard) and add a frontend CI job (`tsc`, `vite build`, `oxlint`).
8. **Generate `docs/reference/cli.md` from `get_command_catalog`** (the generator already exists in `aliases.py`) instead of hand-maintaining it, and fix the skills README count (50 → 95) with mechanical drift gates (repo-wide frontmatter/link check, `cli.md` freshness check).
9. **Unify disable-all and align enable-all.** Make the lifecycle batch implementation canonical (reverse-dep order + a `keep_core` flag), delete the duplicated keep-core loop in `ui/server/adapter.py`, and make the adapter's standalone path pass the same defaults as the runtime path.
10. **Smaller items, in one pass:** wire MCP negotiation (client's requested version → response, with fallback tests); clean `domain.pyrit_redteaming` from `.harness/config.json`; record a bridged-peer trust decision (pins or explicit documentation); add a `--user` flag to container args (or document why the image default is acceptable); reconcile Rule 45's wording with the manifest path and lock in discovery of the 5 manifest-only plugins; meter extraction bytes or add a post-extraction size check; audit `CLI_ALIASES` for deprecation candidates; add `res.ok` handling to `api.ts`.

## 4. Limitations of this analysis

- Local disk reads only, at `c1d593d`; no GitHub API or browser reads were used.
- No pytest collection or test-suite run this pass (except the CLI area's wheel build and frontend checks), so test counts are grep-based and assessed as plausible/consistent, not proven.
- Swarm KI injection, `memtext.py` peer invocation depth, and runtime load behavior beyond discovery were not traced as deeply as the cited code paths; claims about them rest on the code cited, not runtime runs.
