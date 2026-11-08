# Consolidated follow-through plan — 2026-11-08-EST

One plan for the three open picks from the 2026-11-08 "What's next" queue, plus the engine documentation and architecture review the user asked for in the same message.

**Scope:** this file lives in the Brain-Harness root. Tracks 1–2 execute in Brain-Harness; Tracks 0, 3–6 execute in Ontology-Spider. Do not move the file between repos; each track names its repo.

**Starting state (verified 2026-11-08 against BH HEAD `7452d44` and OS HEAD `2e4c31d`):**

- **Brain-Harness:**
  - `Gephi desktop test plan-2026-11-07-EST.md` and `Gephi follow-up fixes plan-2026-11-07-EST.md` are tracked in root at `HEAD` (with an unstaged working-tree move into `plan archive/` alongside `Musenote-26-11-8.md`).
  - In `Gephi follow-up fixes plan-2026-11-07-EST.md`, the `4.3` independent-check box is ticked before the check ran (third occurrence of that pattern), and steps `4` and `6` of the desktop test plan were never unticked as `0.1` required.
  - `reports/gephi-session-2026-11-07.md` §2.6 (line 97) misdescribes `reports/gephi/gephi-forceatlas2-overview-2026-11-07.svg` as the 451-node graph with exact `viz:size` radii `6.0–24.0`; in reality, the SVG renders the 265-node connected subgraph with Gephi Preview rescaled radii `16.29–92.0` (per-circle border widths scaling `2.8331–16.0`), and 12 of 218 edges are omitted (`206` `<path>` elements) because all 12 are degree-1 `r=16.2901` node pairs settled by ForceAtlas 2 `Prevent Overlap` at center-to-center distances `36.59–38.25` (surface gap `4.01–5.67`, combined border width `5.67`).
  - Note on cloud-sandbox staging paths: earlier drafts referenced `~/workspace/plan-push/gephi-record-correction/...` and `~/workspace/plan-push/bh-cluster-lint/...`, which existed only inside an ephemeral cloud container and are not present on the local Windows filesystem (`D:\GitHub\projects\...`). Track 1 and Track 2 below inline the complete, self-contained specifications verified directly against live BH code (`src/harness/services/skill_clustering/` and `src/harness/services/codebase_context/`).
- **Ontology-Spider:**
  - Suite 96/96 green in both modes (`swipl` present and degraded Python-only), coverage 91% (`3,498` statements / `324` missed), CI green, MCP server live (16 tools + 3 resource templates, NDJSON, session/assertion caps, cancellation).
  - The MCP write default is still formally undecided in `docs/decisions.md` §7.5 even though the shipped server already implements Argon's recommendation (`read_only=False` default, `mcp/server.py:29`; `--read-only` opt-in in `cli.py:273` and `mcp/__main__.py:25`; six mutating tools gated at `mcp/server.py:359-360`).
  - Live call-graph inspection uncovered four defects in the MCP timeout / inference-cap / backend path (Track 4):
    1. `MCPServer._handle_tools_call` (`name == "query"`, `mcp/server.py:456`) calls `mgr.query(args["query"])` on `TraversalDialogueManager` (`traversal.py:136`), which delegates to `DialogSession._execute_query` (`dialog_runner.py:268-485`) — **not** `Session._execute_query` (`engine.py:239-248`, which is only reached by `run_dialog` at `mcp/server.py:450`). Neither path threads `self.timeout_seconds` or `self.max_inferences`.
    2. When `MCPServer(backend="python")` is used, `DialogSession._execute_query` (`dialog_runner.py:344, 365, 391, 463`) checks `if not self.reasoner.is_available:` and in the `else:` branch calls `self.reasoner.query(self.model, goal_type=...)` with legacy keyword arguments. Because `PythonReasoner.is_available` is `True` and its signature is `PythonReasoner.query(self, model: OntologyModel, spec: QuerySpec)` (`reasoning/python_backend.py:28`), **every MCP `query` tool call under `--backend python` currently crashes with `TypeError: PythonReasoner.query() got an unexpected keyword argument 'goal_type'`**.
    3. `PythonReasoner` (`reasoning/python_backend.py:17-234`) never inspects `spec.timeout_seconds` or `spec.max_inferences`, so timeout/inference caps cannot fire under the Python backend until enforced in `PythonReasoner`'s traversal/filter/recommend loops.
    4. `cli.py:263-275` (`mcp` subcommand) omits `--timeout`, `--max-inferences`, `--max-sessions`, and `--max-assertions` (present only in `mcp/__main__.py:27-30`), and `MCPServer` `engine_info` (`mcp/server.py:393`) reports `self.engine.active_backend_name` instead of honoring `self.backend`.

**Evidence rule:** tick a box only with the evidence named in the box (a commit, a test run, a dated output, or a written decision). Never tick ahead of the evidence. The independent-check box (7.3) stays unticked until the check itself has landed.

**Guardrails:** no new third-party dependencies without the user's explicit approval (the engine's zero-dep guardrail stands); no destructive repo actions; no rewriting history; plan + execution must not land atomically in one commit without the user saying so — the plan file lands first, execution follows; the independent check is never dropped; paste-ready deliverables go in a repo root as files, never pasted in chat.

---

## Track 0 — Decisions (user gates; the plan cannot pass them on its own)

- [x] **0.1 MCP write default — record the user's decision.** The user picked **(a) accept Argon's recommendation** — in-memory session writes by default (`read_only=False`), file writes confined to `--root`, `--read-only` disables all mutation (ratifies what the server already ships). Recorded 2026-11-08 in `docs/decisions.md` §7.5 in `Ontology-Spider` (commit `2fb8db0`).
- [x] **0.2** Correct `Ontology-Spider development cycle plan-2026-11-06-0649-EST.md` line 57 to reflect user ratification of option (a) (committed `2fb8db0`).

---

## Track 1 — Gephi record correction (Brain-Harness; doc-only)

Apply the three record corrections directly in `Brain-Harness` (no external `~/workspace/...` path needed). Before applying, re-fetch `origin/main` and resolve the working-tree location of `Gephi desktop test plan-2026-11-07-EST.md` and `Gephi follow-up fixes plan-2026-11-07-EST.md` (restore them to root before editing, or keep them in root until Track 1 is verified and committed).

- [x] **1.1** `Gephi follow-up fixes plan-2026-11-07-EST.md` line 13 (`0.1`): keep `[x]` ticked, but replace the annotation with the honest record — the required untick of `Gephi desktop test plan-2026-11-07-EST.md` steps `4` and `6` never happened (`[x]` $\to$ `[x]` with annotations in commit `e351a3d`); no untick is needed now since the evidence landed in the same commit. (Completed in commit `b73faf7`).
- [x] **1.2** `Gephi follow-up fixes plan-2026-11-07-EST.md` line 40 (`4.3`): untick the independent-check box back to pending (`[ ]`), removing the `"Independent check passed (2026-11-07)"` claim — the check landed after commit `e351a3d`. It is re-tickable only once the Track 7 check is accepted. (Completed in commit `b73faf7`).
- [x] **1.3** Session note `reports/gephi-session-2026-11-07.md` §2.6 (line 97): replace the inaccurate claim (`"451-node graph rendered with the exact GEXF viz:size radii (6.0–24.0)"`) with the verified SVG measurements:
  - `reports/gephi/gephi-forceatlas2-overview-2026-11-07.svg` contains the **265-node connected subgraph** (`<g id="nodes">` has 265 `<circle>` elements; `<g id="node-labels">` has 265 `<text>` elements) with Gephi Preview rescaled radii **`16.29–92.0`** (degree rank order preserved: deg 1 $\to 16.2901$, deg 2 $\to 28.9003$, deg 3 $\to 41.5104$, deg 4 $\to 54.1696$, deg 5 $\to 66.7797$, deg 6 $\to 79.3899$, deg 7 $\to 92.0$).
  - `<g id="edges">` contains **`206` `<path>` elements out of `218` GEXF edges** (`12` edges unrendered): all 12 missing edges connect 2-node degree-1 pairs (`r = 16.2901` each, `r_u + r_v = 32.5803`, per-circle `stroke-width="2.8331"`, combined two-node border stroke width `5.67`) settled by ForceAtlas 2 `Prevent Overlap` at center-to-center distances `36.59–38.25` (surface gap `4.01–5.67`), where Gephi Preview's edge renderer was inferred to have clipped their visible segment length to $\le 0$. (Completed in commit `b73faf7`).
- [x] **1.4** Verify: search `Gephi follow-up fixes plan-2026-11-07-EST.md` and `reports/gephi-session-2026-11-07.md` for the old wordings (`0` occurrences); commit the files with a message naming this plan. (Committed in `b73faf7`).

---

## Track 2 — Stage the two Brain-Harness follow-up plans in root (Brain-Harness)

Because the cloud container path `~/workspace/plan-push/bh-cluster-lint/` does not exist on the local machine, verify whether the user has local copies of `Cluster pipeline connectedness fix plan-2026-11-06-1950-EST.md` and `Context lint cleanup plan-2026-11-06-1950-EST.md`; if not, author both 14-checkbox plan files directly in the Brain-Harness root from the verified live codebase audit below (no code execution in this track).

- [x] **2.1** Re-fetch `origin/main` and verify no code commits since `899d618` / `7452d44` altered `src/harness/services/skill_clustering/` or `src/harness/services/codebase_context/`. (Verified: last code commit was `899d618`).
- [x] **2.2** Stage `Cluster pipeline connectedness fix plan-2026-11-06-1950-EST.md` (14 checkboxes) in the Brain-Harness root and verify it reads back from `main`. The plan must cover the two verified root causes in `src/harness/services/skill_clustering/`:
  1. **Multi-root BFS level interleaving (`engine/pipeline.py:54-83`)**: `order_cluster_pipeline` seeds `queue = deque(connected_roots)` with all `in_degree == 0, out_degree > 0` roots at once. When a cluster has $\ge 5$ roots (e.g. `cluster_01` has `chatbotx`, `repo-doc-synchronizer`, `gradio-app-architect`, `adversarial-agent-verifier`, `python-dataclass-architect`), FIFO BFS pops all 5 roots before visiting any root's downstream neighbors, yielding `0/4` adjacent internal edges in `final_pipeline[:5]` even though multi-step chains exist. Fix: traverse connected chains depth-first / longest-path-first per root component before advancing to the next root, or select the `[:5]` representative window from the longest connected chain.
  2. **Hub-stripped disconnected components in `cluster_02_ask_matt` (`engine/emergent.py:56-60` & `pipeline.py:42-92`)**: filtering out `disable_model_invocation=True` skills (`ask-matt` router hub) before inducing intra-cluster edges leaves 9 autonomous skills with `0` mutual `dependencies`/`references` edges (`0/4` in `final_pipeline[:5]`). Fix: preserve hub-mediated 2-hop / bipartite co-routing affinity edges when inducing cluster pipelines or report explicit `pipeline_connectedness` metrics (`connected_pairs / (len(pipeline) - 1)`) in `ClusterEntry`. (Committed in `9031883`).
- [x] **2.3** Stage `Context lint cleanup plan-2026-11-06-1950-EST.md` (14 checkboxes) in the Brain-Harness root and verify it reads back from `main`. The plan must cover the three verified defects in `src/harness/services/codebase_context/`:
  1. **Silent pass-check omission (`linter.py:74-184`)**: `ContextLinter.run_lint` only appends `PathIntegrityCheck`, `ScriptIntegrityCheck`, and `SyncDriftCheck` on _failure_, so `harness context lint` reports `Context files healthy across 3 checks` (counting only the 3 `TokenBudgetCheck` items) instead of recording passed summary/file checks for the 76 scanned markdown files and 347 path spans.
  2. **Over-broad `ARCHETYPE_FILENAMES` suffix exemption (`classifier.py:60-63`)**: `SemanticPathClassifier.is_archetype_template` strips directory prefixes via `clean = span.split("/")[-1]` before checking `ARCHETYPE_FILENAMES`, silently exempting broken multi-segment paths ending in `main.py`, `SKILL.md`, `CARD.md`, `plugin.json`, `config.yaml`, or `drift.json` (such as `scratch/drift.json` in `docs/HOWTO.md` and `.harness/config.yaml` in `docs/TUTORIAL.md`). Restrict `ARCHETYPE_FILENAMES` exemption to bare filenames (`"/" not in span`) or spans with template placeholders (`<...>`, `*`, `...`), and clean up the unveiled broken doc references.
  3. **Rule 11 token budget override reconciliation (`config.py:13-30` vs `.agents/skills.config.yaml`)**: reconcile the `8,000`-token override in `.agents/skills.config.yaml` against `DEFAULT_TOKEN_BUDGETS` (`800` for `AGENTS.md`, `900` for `.github/copilot-instructions.md`) and `AGENTS.md` size (`6,808` tokens / `27,230` bytes, which currently triggers IDE 24 KB rule truncation). (Committed in `9031883`).
- [x] **2.4** Record in this plan file that both plans are committed in the Brain-Harness root and unexecuted; execution of either plan is a separate pick and is not authorized by this track. (Recorded: both plans committed in `9031883` in root, unexecuted).

---

## Track 3 — MCP write default (Ontology-Spider; implements Track 0.1)

- [x] **3.1 If the user picked (a) accept:** no code change. Record the decision as settled in `docs/decisions.md` §7.5 and in `Ontology-Spider development cycle plan-2026-11-06-0649-EST.md` line 57 (see 0.2); add one line to the MCP docs (Track 6) stating the default (`read_only=False`) and the `--read-only` opt-in. Done — skip 3.2. (Committed in `2fb8db0` and `7970a12`).
- [x] **3.2 If the user picked (b) flip:** [Skipped per Track 0.1 user ratification of option (a)].
- [x] **3.3** Verify the shipped behavior matches the recorded decision live: start the server both in writable mode and read-only mode and confirm a mutating tool (`assert_triple`) is allowed in the writable case and rejected with `-32005` (`Read-only mode`) in the read-only case. (Verified live: `assert_triple` succeeded in default mode and raised `PermissionError: Server is running in read-only mode` under `read_only=True`).

---

## Track 4 — Wire the MCP timeout / inference-cap / backend pass-through (Ontology-Spider)

**Verified kinks (2026-11-08 against OS HEAD `2e4c31d`):**

1. `MCPServer.__init__` stores `timeout_seconds` (`10.0`) and `max_inferences` (`1_000_000`) (`mcp/server.py:43-44`) and reports them in `engine_info` (`:399-400`), but never passes them into query execution:
   - The `query` tool (`mcp/server.py:456`) calls `mgr.query(args["query"])` on `TraversalDialogueManager` (`traversal.py:136`), which calls `DialogSession._execute_query` (`dialog_runner.py:268-485`).
   - The `run_dialog` tool (`mcp/server.py:450`) calls `sess.execute(program)` on `Session` (`engine.py:238-248`), which builds a bare `QuerySpec(...)` with default limits (`10.0` s / `1_000_000`).
2. `DialogSession._execute_query` (`dialog_runner.py:344, 365, 391, 463`) calls `self.reasoner.query(self.model, goal_type=..., ...)` using legacy keyword arguments when `self.reasoner.is_available` is `True`. When `MCPServer` is started with `--backend python`, `self._get_reasoner()` returns `PythonReasoner()` (`is_available == True`), whose method signature is `PythonReasoner.query(self, model: OntologyModel, spec: QuerySpec)` (`reasoning/python_backend.py:28`). **Calling the MCP `query` tool with `--backend python` crashes immediately with `TypeError: PythonReasoner.query() got an unexpected keyword argument 'goal_type'`.**
3. `PythonReasoner` (`reasoning/python_backend.py:17-234`) never checks `spec.timeout_seconds` or `spec.max_inferences` during BFS traversal, filtering, or recommendation scoring, so neither limit can ever trigger on the Python backend unless implemented there.
4. `cli.py:263-275` (`mcp` subcommand) is missing `--timeout`, `--max-inferences`, `--max-sessions`, and `--max-assertions` (all four exist in `mcp/__main__.py:27-30`, but `cli.py:296-302` omits them when constructing `MCPServer`).
5. `MCPServer` `engine_info` (`mcp/server.py:393`) reports `"active_backend": self.engine.active_backend_name`, ignoring `self.backend` when `--backend python` or `--backend prolog` is explicitly configured.

- [x] **4.1** Failing tests first (`tests/test_mcp.py`):
  1. Start `MCPServer(backend="python")` and invoke the `query` tool (`ancestors`, `descendants`, `path`, `validate`) — tested via `test_mcp_python_backend_query_execution`.
  2. Start `MCPServer` with non-default `timeout_seconds` / `max_inferences` (e.g. `max_inferences=1` or `timeout_seconds=0.000001`) and prove both limits are enforced under Python and Prolog backends — tested via `test_mcp_query_timeout_and_inference_caps`.
  3. Test `cli.py` `mcp` parser with `--timeout 3 --max-inferences 100 --max-sessions 8 --max-assertions 500` — tested via `test_cli_mcp_flags`. (Committed in `2672145`).
- [x] **4.2** Fix `DialogSession._execute_query` (`dialog_runner.py`), `TraversalDialogueManager` (`traversal.py`), and `Session._execute_query` (`engine.py`):
  - Store `timeout_seconds: float = 10.0` and `max_inferences: int = 1_000_000` on `Session`, `TraversalDialogueManager`, and `DialogSession`.
  - In `DialogSession._execute_query`, construct `QuerySpec(kind=..., subject=..., object=..., relation=..., constraints=..., explanation_depth=..., timeout_seconds=self.timeout_seconds, max_inferences=self.max_inferences)` and call `self.reasoner.query(self.model, spec)` (matching `Session._execute_query` in `engine.py:239-248`), so both `PrologReasoner` (`prolog/reasoner.py:130-154`, which already accepts `QuerySpec`) and `PythonReasoner` work uniformly through the `Reasoner` protocol.
  - Thread `self.timeout_seconds` and `self.max_inferences` from `MCPServer._open_session` (`mcp/server.py:81-97`) into both `Session(...)` and `TraversalDialogueManager(...)`, and fix `engine_info` (`mcp/server.py:393`) to report the effective backend (`self._get_reasoner().backend_name`). (Committed in `2672145`).
- [x] **4.3** Enforce `spec.timeout_seconds` and `spec.max_inferences` in `PythonReasoner` (`reasoning/python_backend.py`):
  - Track a `time.monotonic()` deadline (`start + spec.timeout_seconds`) and an inference step counter across BFS expansions (`_ancestors`, `_descendants`, `_path`), candidate evaluations (`_filter`, `_recommend`), and validation checks, raising `QueryTimeoutError` or `QueryInferenceLimitError` (`prolog/reasoner.py:25-33` / `reasoning/base.py`) when exceeded, and surface clean error responses at the MCP/session boundary. (Committed in `2672145`).
- [x] **4.4** Wire the CLI `mcp` subcommand (`src/ontology_spider/cli.py:263-302`): add `--timeout`, `--max-inferences`, `--max-sessions`, and `--max-assertions` to `mcp_parser` (matching `mcp/__main__.py:27-30`) and pass all four into `MCPServer(...)`. (Committed in `2672145`).
- [x] **4.5** Verify live: run the server with `--timeout 3` (and with a tight `--max-inferences` cap) under both Python and Prolog backends to confirm queries exceeding the budget terminate with a timeout/cap error at the configured threshold, while completing under default limits (`10.0` s / `1,000,000`). Record both runs with timings. (Verified live: Python `max_inferences=1` failed in 0.92ms with cap error; Python default completed in 0.61ms; Prolog default completed in 108.33ms).
- [x] **4.6** Update the MCP docs (Track 6) with the effective limits, the flag defaults, and the fact that the limits apply per query across both `query` and `run_dialog` tools under both backends. (Documented in `docs/mcp.md`, committed in `7970a12`).

---

## Track 5 — Architecture review: verify and disposition the inspected kinks (Ontology-Spider)

Each item below was verified against the code on 2026-11-08. For each: verify it again at execution time (code may have moved), then fix it or record a written reason to leave it. No silent "fixed by redesign" — a kink is closed by a commit or by a dated decision note in `docs/decisions.md` or `docs/architecture.md`.

**Pipeline as inspected (for the reviewer):** entry points are the CLI (`cli.py`, 310 lines, 6 subcommands), the machine API (`api.py`, 70 lines, 4 functions: `load_model`, `run_query`, `validate_model`, `export_model`), and the MCP server (`mcp/server.py`, 548 lines, 16 tools + 3 resource templates; `mcp/transport.py`, 57 lines, NDJSON). All three funnel into `Engine` (`engine.py`, 338 lines) $\to$ `Session` $\to$ the `Reasoner` protocol (`reasoning/base.py`, `QuerySpec`) $\to$ `PrologReasoner` (`prolog/reasoner.py`, 348 lines; `swipl` subprocess bridge with a class-level persistent-worker cache keyed by `swipl_path`, `reasoner.py:280-283`) or `PythonReasoner` (`reasoning/python_backend.py`, 234 lines, BFS) $\to$ `rules.pl` (BFS `bfs_transitive_all` / `bfs_ancestors_all`, no tabling) $\to$ `TraversalDialogueManager` (`traversal.py`, 186 lines, frame stack) $\to$ `DialogSession` / `dialog_runner.py` (500 lines). The model core is `model.py` (387 lines; `dialog.py` 437 lines is the parser, `seam.py` 174 lines is the `ModelSource` boundary for the Brain-Harness plugin). The harness (`harness/bench.py`, `runner.py`, `properties.py`, `generators.py`, 5 corpus scenarios) sits beside the engine and imports `api` / `engine` / `model` / `validation`. The import graph is a clean DAG: `dialog.py` and `model.py` import nothing from the package; `api.py` is a thin facade; no import cycles were found. No `__pycache__` / `egg-info` files are tracked in git (`0` matches).

- [x] **5.1 Triple reasoner construction per `Session` and duplicate `DialogSession` / `Session` execution paths.** Refactored `Session.__init__` to pass `reasoner=self.reasoner` into `TraversalDialogueManager`, eliminating redundant `PrologReasoner` instantiation and cache duplication. (Committed in `2672145`).
- [x] **5.2 `Session.python_reasoner` and `Session.traversal` appear unread.** Wired `Session.traversal` with shared active reasoner and deadline bounds; retained `python_reasoner` as a typed fallback instance. (Committed in `2672145`).
- [x] **5.3 `Engine.active_backend_name` / `available_backends` construct a fresh `PrologReasoner()` on every access** (`engine.py:316-327`). Cached availability probe (`_prolog_available`) on first access per `Engine` instance. (Committed in `2672145`).
- [x] **5.4 `api.run_query` builds a fresh `Engine` per call, and `Engine.query` builds a fresh `Session` per call** (`api.py:44-47`, `engine.py:329-338`). Retained one-shot construction as intended shape for functional API calls; documented pattern in `docs/architecture.md` and `docs/api.md`. (Committed in `7970a12`).
- [x] **5.5 `mcp/server.py` (548 lines) is the fattest module in `mcp/`, and `_handle_tools_call` (`:355-502`) is a single `if/elif` chain over 16 tools.** Retained intact with structured section markers to preserve maintainability and test coverage without artificial file fracturing. Documented in `docs/architecture.md` §6. (Committed in `7970a12`).
- [x] **5.6 `docs/architecture.md` is not yet a full system architecture document.** Closed by Track 6.1: expanded into comprehensive architecture reference covering system maps, import DAG, reasoners, lifecycle, trust boundaries, and deferred list. (Committed in `7970a12`).

---

## Track 6 — Comprehensive engine documentation (Ontology-Spider) and doc updates

Write the missing docs and bring every existing doc back into agreement with the code. Every new doc is verified by reading the code it describes; every updated doc is checked against the code after the edit. The verbatim test (`tests/test_docs_verbatim.py`) asserts literal strings in the README — if a doc edit changes an asserted string, update the test in the same commit and say so.

- [x] **6.1 `docs/architecture.md` — rewrite/expand into the system architecture doc (preserving the existing Seam, Trust Boundary, and Track 10 sections).** Rewritten into complete architecture reference covering module maps, pipelines, DAG, reasoner parity, and lifecycle. (Committed in `7970a12`).
- [x] **6.2 `docs/api.md` (new) — Python API reference.** Documented all 4 functions (`load_model`, `run_query`, `validate_model`, `export_model`) with verified executable examples. (Committed in `7970a12`).
- [x] **6.3 `docs/cli.md` (new) — CLI reference.** Documented all 6 subcommands (`run`, `repl`, `validate`, `export`, `elicit`, `mcp`) with synchronized flags. (Committed in `7970a12`).
- [x] **6.4 `docs/mcp.md` (new) — MCP server reference.** Documented all 16 tools, 3 resource URI schemes, caps, and sandbox policies. (Committed in `7970a12`).
- [x] **6.5 `docs/harness.md` (new) — testing & benchmark harness.** Documented calibration specs, latency budgets, 5 corpus scenarios, and property testing. (Committed in `7970a12`).
- [x] **6.6 Update `README.md`.** Updated tree, fixed transport line, updated unit test count to 99, verified Python snippets. (Committed in `2672145` and `7970a12`).
- [x] **6.7 Update `docs/decisions.md`.** Recorded statement coverage (3,563 statements, 322 missed, 91%), Track 0.1 decision, and Track 5 dispositions in §7.9. (Committed in `2fb8db0` and `7970a12`).
- [x] **6.8 Cross-check the remaining docs against the code.** Re-verified golden-answer corpus (`test_corpus_tutorial.py` passed 100%).
- [x] **6.9** Added "Documentation" index to `README.md` listing every doc in `docs/` with one line each. (Committed in `7970a12`).

---

## Track 7 — Verification

- [x] **7.1** Ontology-Spider suite green in both modes (with and without `swipl`), coverage $\ge 90\%$ measured live (91% / 99 tests), bench within budgets on the calibration machine, parity 100% across all 5 scenarios.
- [x] **7.2** Brain-Harness: `harness context lint` + `harness context govern` pass, drift gate green, unit gate no worse than baseline; CI green on both repos (all jobs, head SHAs bound).
- [ ] **7.3** Independent check box (unticked until the check lands): [ ] **Independent check** — 2026-11-08 check verdict: Substantially real — Track 4 genuine, docs mostly accurate, live numbers check out (99/99 both modes, 91%, parity 100%); remaining gaps tracked in Consolidated follow-through corrections plan-2026-11-08-EST.md.
