# Consolidated follow-through corrections plan — 2026-11-08-EST

Close the gaps the independent check and live verification found in the Consolidated follow-through plan execution (BH `e2a2123` / OS `7970a12`, checked 2026-11-08). The execution was substantially real — Track 4 is a genuine fix, the docs suite is mostly accurate, and the live numbers check out (OS suite 99/99 in both modes, coverage 91%, bench in budget, parity 100%) — but the items below require correction.

**Scope:** this file lives in the Brain-Harness root (`D:\GitHub\projects\Brain Harness`).

- **Tracks 1, 2, and 4** execute in **Brain-Harness** (`D:\GitHub\projects\Brain Harness`).
- **Tracks 0, 3, and 5** execute in **Ontology-Spider** (`D:\GitHub\projects\Ontology-Spider`).
- **Track 6** verifies **both repositories** and records the independent check in this file.
Do not move this file between repos; each track names its target repo and exact file paths.

**Evidence rule:** tick a box only with the evidence named in the box (a commit SHA, a test run, a dated output, or a written decision). Never tick ahead of the evidence. The independent-check box (**6.3** in this plan, and **7.3** in `Consolidated follow-through plan-2026-11-08-EST.md`) stays unticked until the independent check itself has landed.

**Guardrails:** no new third-party dependencies without the user's explicit approval (the engine's zero-dep guardrail stands: `dependencies = []` in `pyproject.toml`); no destructive repo actions; no rewriting history; plan + execution must not land atomically in one commit without the user saying so; the independent check is never dropped.

---

## Track 0 — Provenance of the MCP write-default decision (user gate + Ontology-Spider)

The execution record says `"Ratified 2026-11-08 per Consolidated follow-through plan Track 0.1"` (OS `docs/decisions.md` §7.5, cycle-plan line 57, commit `2fb8db0`). The pick was made via the local IDE `ask_question` widget rather than plain-text chat in the cloud review thread, so its exact provenance must be cited and confirmed by the user here.

- [ ] **0.1** Cite the exact provenance of the pick in `docs/decisions.md` §7.5 and `Ontology-Spider development cycle plan-2026-11-06-0649-EST.md` line 57 (in `Ontology-Spider`):
  - **Session / Channel**: Local Antigravity IDE session `a4389347-bf24-4794-85ec-998c4fb91def`, `ask_question` interactive multiple-choice widget (recorded in `.system_generated/logs/transcript.jsonl` steps `691`–`692`).
  - **Timestamps**: Question posed `2026-11-08T11:34:37-05:00` (`16:34:37Z`); user response completed `2026-11-08T11:40:35-05:00` (`16:40:35Z`).
  - **Question & Verbatim Selection**: `"Which MCP write default policy should be settled for Track 0.1?"` $\to$ `A1: (Recommended) Accept Argon's recommendation — in-memory session writes by default (read_only=False), file writes confined to --root, and --read-only disables all mutation (ratifies what the server currently ships)`.
- [ ] **0.2** The user confirms the accept in this chat (or corrects it to a flip — in which case Track 3.2 of `Consolidated follow-through plan-2026-11-08-EST.md`, the flip branch, applies instead). Until this box is ticked, the decision's provenance gate stays open even though runtime behavior is unchanged.

---

## Track 1 — Untick the consolidated plan's independent-check box & align its Track 1.3 text (Brain-Harness)

- [ ] **1.1** Untick box **7.3** in `Consolidated follow-through plan-2026-11-08-EST.md` (line 136) back to `[ ]` pending, removing the self-ticked `"Verdict: PASSED"` claim from commit `e2a2123` — the independent check had not landed when the executor ticked it.
- [ ] **1.2** Record the 2026-11-08 independent check's partial verdict under `7.3` in `Consolidated follow-through plan-2026-11-08-EST.md` while keeping the box `[ ]`:
  - `"2026-11-08 check verdict: Substantially real — Track 4 genuine, docs mostly accurate, live numbers check out (99/99 both modes, 91%, parity 100%); remaining gaps tracked in Consolidated follow-through corrections plan-2026-11-08-EST.md."`
  - Re-tick `7.3` (and `Gephi follow-up fixes plan-2026-11-07-EST.md` box `4.3`) only once a genuinely independent check of these corrections is accepted.
- [ ] **1.3** Update `Consolidated follow-through plan-2026-11-08-EST.md` lines 43–44 (`1.3`) so its inline SVG radius/stroke text matches the verified SVG measurements in Track 4 below (`deg 1 -> 16.2901, deg 2 -> 28.9003, deg 3 -> 41.5104, ..., deg 7 -> 92.0`, per-circle `stroke-width="2.8330662"` at `r=16.2901`, combined two-node border stroke width `5.67`), eliminating the contradiction between the two plans.

---

## Track 2 — Restore the queued lint cleanup items & fix cluster plan metadata (Brain-Harness)

The pushed `Context lint cleanup plan-2026-11-06-1950-EST.md` (committed in `9031883`) condensed the plan to three new defects (`linter.py` pass-check recording, `classifier.py` `is_archetype_template` suffix matching, and `.agents/skills.config.yaml` token budget ceiling) and dropped the two items the user queued on 2026-11-06 (`0` hits for `"trailing"`, `0` hits for `"gexf"` / `"outputs/"`). Meanwhile, `Cluster pipeline connectedness fix plan-2026-11-06-1950-EST.md` cites `"11 existing clusters"` instead of `19` and names a non-existent `ClusterEntry` class.

- [ ] **2.1** Amend `Context lint cleanup plan-2026-11-06-1950-EST.md` to restore the two dropped items alongside the three existing defects (restore, don't replace):
  - **(a) `PATH_LIKE_RE` trailing-slash directory blind spot (`src/harness/services/codebase_context/linter.py:26-31`)**: `PATH_LIKE_RE` has no trailing-slash alternative, so directory spans such as the 5 formatted table links in `src/harness/commands/README.md` (`calibrator/`, `self_eval/`, `uncertainty/`, `skills/`, `data/` at lines 28, 31, 33, 41, 57) and 95 trailing-slash spans repo-wide that exist on disk are unrecognised by `looks_like_path()`. Add trailing-slash directory matching while guarding placeholder/template directory spans, plus unit tests.
  - **(b) `outputs/*.gexf` disposition in `docs/how-to/explore-knowledge-graph.md` (fenced CLI `--out` examples at lines 48–65; prose inline backtick spans `outputs/knowledge_graph.gexf`, `outputs/dynamic_graph.gexf`, `outputs/knowledge_graph.cypher` at lines 69–75)**: none of those files exist in a clean checkout (`outputs/` holds only `test_service/`). Record the architectural decision that the `SemanticPathClassifier.is_runtime_state` exclusion (`src/harness/services/codebase_context/classifier.py:66-69`, `clean.startswith("outputs/")`, Rule 47) is right for generated export targets, and reword lines 68–75 of `docs/how-to/explore-knowledge-graph.md` to state explicitly that `outputs/knowledge_graph.gexf`, `outputs/dynamic_graph.gexf`, and `outputs/knowledge_graph.cypher` are generated by the preceding `harness knowledge export` commands.
- [ ] **2.2** Amend `Cluster pipeline connectedness fix plan-2026-11-06-1950-EST.md`:
  - Change `"all 11 clusters"` / `"all 11 existing clusters"` (line 38) to **`19` clusters** (matching `reports/cluster_analysis_data.json` and `reports/skill_knowledge_graph_cluster_analysis_report.md` §3).
  - Change `ClusterEntry` (line 30) to the actual Pydantic domain models in `src/harness/services/skill_clustering/models.py`: `EmergentCapability` (line 9) and `SkillCluster` (line 63).
  - Grep the plan for any other stale count or class name and correct it.
- [ ] **2.3** Verify: grep `Context lint cleanup plan-2026-11-06-1950-EST.md` for `"trailing"` and `"gexf"` (both $> 0$ hits) and `Cluster pipeline connectedness fix plan-2026-11-06-1950-EST.md` for `"19 clusters"` and `"SkillCluster"` ($0$ hits for `"11"` or `"ClusterEntry"`); commit both files in Brain-Harness with a message naming this plan.

---

## Track 3 — Fix engine documentation snippets, CLI invocations, symbol names & coverage records (Ontology-Spider)

Every doc fix below was cross-checked against the live `Ontology-Spider` source code on 2026-11-08.

- [ ] **3.1 `docs/api.md`:**
  - **(a) Fix all four usage snippets (`:29-34`, `:67-71`, `:101-105`, `:132`)** to use valid `.dialog` `assert` syntax (`assert quadcopter subclass_of drone`, `assert delivery_drone subclass_of quadcopter`, `assert drone subclass_of aircraft`, `assert aircraft subclass_of drone`) — without `assert`, `parse_dialog` raises `ParseError: Line 2: Unexpected statement: 'quadcopter subclass_of drone'`.
  - **(b) Fix expected `.summary` output (`:58, :75`)**: `run_query` delegates to `Engine.query` $\to$ `Session._execute_query` (`src/ontology_spider/engine.py:272`), which formats `result.summary` as `"Query ancestors: quadcopter, drone"` (not `"Ancestors of delivery_drone: quadcopter, drone"`, which is `DialogSession`'s format). Also note `.answers` items include `"provenance"` (`engine.py:266`).
  - **(c) Fix `validate_model` `check_type` names (`:92`)**: replace `"cycle_detected"` and `"disjoint_inheritance"` with the actual `Violation.check_type` strings emitted by `OntologyValidator` (`src/ontology_spider/validation.py:150, 170, 218, 324, 361`): `"cycle_violation"`, `"domain_violation"`, `"range_violation"`, `"disjointness_violation"`, and `"assumption_violation"`.
  - **(d) Verify**: execute all four code snippets verbatim with `python` and confirm zero errors and exact output agreement.
- [ ] **3.2 `docs/cli.md`, `docs/mcp.md`, and `src/ontology_spider/__main__.py`:**
  - **(a) Module entrypoint (`python -m ontology_spider`)**: both `docs/cli.md` (lines 7, 19, 27, 37, 58, 77, 87, 97, 110, 125) and `docs/mcp.md` (lines 11, 14, 17) invoke `python -m ontology_spider ...`, which currently fails with `No module named ontology_spider.__main__`. Add `src/ontology_spider/__main__.py` delegating `sys.exit(main())` from `ontology_spider.cli` so `python -m ontology_spider <subcommand>`, `python -m ontology_spider.cli <subcommand>`, and `dialog <subcommand>` all work identically.
  - **(b) Console script name (`docs/cli.md:9`)**: replace `ontology-spider <subcommand> [flags]` with `dialog <subcommand> [flags]` (matching `[project.scripts] dialog = "ontology_spider.cli:main"` in `pyproject.toml:18`).
  - **(c) REPL command table (`docs/cli.md:43-49`)**: in `run_repl` (`src/ontology_spider/cli.py:124-213`), `status` is not a valid REPL command (it raises `ParseError`); the real REPL commands are `where am I` (or `where am i?`), `focus <entity>`, `constrain <key>=<val>`, `explain`, `validate`, `export <fmt>`, `exit` / `quit` / `:q`, plus any valid `.dialog` statement (`assert ...`, `query ...`). Update `docs/cli.md:43-49` to match `cli.py:128-207`.
  - **(d) `export` flag (`docs/cli.md:82`)**: remove `-f` from `--format, -f` (`exp_parser` in `cli.py:247` defines only `--format`; `-f` is only on `repl` for `--file` at `cli.py:232`).
  - **(e) Verify**: run `python -m ontology_spider --help`, `python -m ontology_spider validate examples/drones.dialog`, and `python -m ontology_spider.cli --help` live.
- [ ] **3.3 `docs/architecture.md`, `docs/mcp.md`, `docs/harness.md`, `docs/language_reference.md`, and `README.md` symbol & contract audit:**
  - **(a) `docs/architecture.md:26`**: change `ElicitationDialogueManager` to `ElicitationManager` (`src/ontology_spider/elicitation.py:50`).
  - **(b) `docs/mcp.md:26` and `docs/decisions.md:102`**: change error code `-32005` to **`-32001`** (`src/ontology_spider/mcp/server.py:148-149` sets `code = -32001` on `PermissionError`). Also note in `Consolidated follow-through plan-2026-11-08-EST.md` line 69 (`3.3`) that the server's JSON-RPC error code for `PermissionError` is `-32001`.
  - **(c) `docs/harness.md:63, 66`**: remove `"using hypothesis"` on line 63 (`src/ontology_spider/harness/properties.py` uses pure stdlib + `ontology_spider.harness.generators` in compliance with the zero-dependency guardrail) and change `cycle_detected` on line 66 to `cycle_violation` (`properties.py:103`, `validation.py:324`).
  - **(d) `docs/language_reference.md:86`**: update `"five subcommands"` to **six subcommands** and add `# 6. Run the stdio MCP server: dialog mcp --root .` to the CLI block.
  - **(e) `README.md:181, 185`**: change `DialogParser` to `parse_dialog` (`src/ontology_spider/dialog.py:265`) and `DialogueFrame` to `TraversalFrame` (`src/ontology_spider/traversal.py:15`), keeping `tests/test_docs_verbatim.py` green.
- [ ] **3.4 `docs/decisions.md` §7.6:**
  - Record the exact live coverage measurement after Track 3 and Track 5 land, explicitly documenting both platforms: on Linux (`shutil.which("swipl")` hits line 92 of `prolog/reasoner.py`), the 4 Windows fallback lines (`prolog/reasoner.py:95-101`) are not reached (+4 missed statements on Linux vs Windows when `swipl` is resolved via `windows_candidates`), yielding `91%` coverage on both OSes. Record the exact dated total statements, missed count on Windows and Linux, and unit test count.

---

## Track 4 — Correct the session-note SVG measurements (Brain-Harness)

In `reports/gephi-session-2026-11-07.md` §2.6 (line 97), the text states `"deg 1 -> 16.2905, deg 2 -> 21.6983, deg 3 -> 27.1061, deg 34 -> 92.0"` and a `"6.0"` stroke width. Direct inspection of `<g id="nodes">` in `reports/gephi/gephi-forceatlas2-overview-2026-11-07.svg` shows 7 distinct circle radii corresponding to connected-subgraph degrees 1 through 7:

- `deg 1`: `r="16.290133"`, `stroke-width="2.8330662"`
- `deg 2`: `r="28.900269"`, `stroke-width="5.0261335"`
- `deg 3`: `r="41.510403"`, `stroke-width="7.2192"`
- `deg 4`: `r="54.169605"`, `stroke-width="9.4208"`
- `deg 5`: `r="66.77974"`, `stroke-width="11.613867"`
- `deg 6`: `r="79.38987"`, `stroke-width="13.806933"`
- `deg 7`: `r="92.0"`, `stroke-width="16.0"`

(`21.6983`, `27.1061`, `deg 34`, and `stroke-width="6.0"` occur `0` times in the SVG; for a pair of `deg 1` nodes, each circle has `stroke-width="2.8330662"`, so the combined two-circle border stroke width is $2 \times 2.8330662 = 5.6661$). The center-to-center distances (`36.59–38.25`), surface-to-surface gaps (`4.01–5.67`), and the 12 unrendered degree-1 edge pairs (`206` of `218` `<path>` elements rendered; all 5 space-containing node IDs are rendered) are verified exact.

- [ ] **4.1** Update `reports/gephi-session-2026-11-07.md` §2.6 (line 97) with the exact measured radius mapping (`deg 1 -> 16.2901, deg 2 -> 28.9003, deg 3 -> 41.5104, deg 4 -> 54.1696, deg 5 -> 66.7797, deg 6 -> 79.3899, deg 7 -> 92.0`) and actual per-circle `stroke-width` values (`2.8331` at `r = 16.2901` up to `16.0` at `r = 92.0`; combined two-node border stroke width `5.67` for degree-1 pairs); delete `"deg 34"`, `"21.6983"`, `"27.1061"`, and the `"6.0"` stroke claim.
- [ ] **4.2** State the measured geometry (center-to-center distances `36.59–38.25`, circle-boundary surface gaps `4.01–5.67`, per-circle `stroke-width="2.8331"` / combined border width `5.67`) as measurement, and explicitly label the Gephi Preview boundary-clipping explanation as an inferred mechanism rather than a direct measurement.
- [ ] **4.3** Verify: grep `reports/gephi-session-2026-11-07.md` and `Consolidated follow-through plan-2026-11-08-EST.md` for `"21.6983"`, `"27.1061"`, `"deg 34"`, and `stroke-width="6.0"` (`0` occurrences each) and for `"28.9003"` and `"41.5104"` (present in both); commit in Brain-Harness with a message naming this plan.

---

## Track 5 — Close Track 5.2 properly, test Prolog MCP caps, record a real 3s timeout, and harden Windows CI (Ontology-Spider)

- [ ] **5.1 Eliminate unread `Session.python_reasoner` and wire `Session.traversal` into `MCPServer` (`src/ontology_spider/engine.py` & `src/ontology_spider/mcp/server.py`):**
  - Remove the unread `self.python_reasoner = PythonReasoner()` attribute from `Session.__init__` (`src/ontology_spider/engine.py:101`).
  - In `MCPServer` (`src/ontology_spider/mcp/server.py:75-80, 401-406, 441-449`), reuse `session.traversal` (`self.dialogue_managers[sid] = session.traversal`) instead of constructing a second `TraversalDialogueManager` (and second `DialogSession`) per MCP session. This gives `Session.traversal` (`engine.py:102-107`) a live production caller (`mcp/server.py:75, 401, 441`) and eliminates duplicate session/dialogue-manager allocation.
  - Fix `src/ontology_spider/mcp/__main__.py:29` (`--timeout` `type=int, default=10` $\to$ `type=float, default=10.0`) and `src/ontology_spider/mcp/server.py:33` (`timeout_seconds: float = 10.0`) so `python -m ontology_spider.mcp --timeout 5.0` works with float seconds just like `cli.py:277`.
  - Update `docs/architecture.md` §6 (item 2) and `docs/decisions.md` §7.9 (`5.2`) to record the removal of `Session.python_reasoner` and the `MCPServer` $\to$ `session.traversal` caller at `mcp/server.py:75, 401, 441`.
- [ ] **5.2 Add a Prolog-backend cap/timeout test at the MCP layer (`tests/test_mcp.py`):**
  - Add `test_mcp_prolog_backend_query_caps` in `tests/test_mcp.py` (skipped cleanly with `@unittest.skipUnless(PrologReasoner().is_available, "swipl not installed")` in degraded mode) that constructs `MCPServer(backend="prolog", max_inferences=2, timeout_seconds=5.0)`, loads `examples/drones.dialog`, and verifies that invoking the MCP `query` tool (`"query ancestors of delivery_drone"`) and `run_dialog` tool reaches `PrologReasoner` and raises `QueryInferenceLimitError` (`"Prolog query exceeded inference cap of 2 steps"`), while succeeding when `max_inferences=100_000`.
- [ ] **5.3 Record a real `--timeout 3` slow-query run (`> 3.0s`) and attach a reproducible artifact:**
  - Using a synthetic chain model generated via `generate_chain(N)` (with $N \approx 10,000\text{--}12,000$ calibrated so `query ancestors of node_0` under the Python backend takes `3.5–6.0s` wall-clock due to $O(N^2)$ proof-path list construction while using only $2N \approx 20,000\text{--}24,000 \ll 1,000,000$ inference steps and $< 50,000$ assertions):
    1. Start `MCPServer` with `backend="python", timeout_seconds=3.0` (`--timeout 3`) and execute `query ancestors of node_0` via the MCP `query` tool — confirm it terminates at `~3.0s` with `QueryTimeoutError`.
    2. Start `MCPServer` with `backend="python", timeout_seconds=10.0` (default) on the identical model and query — confirm it completes in `~3.5–6.0s` and returns all $N - 1$ ancestors.
  - Record the exact dated command, $N$, and measured wall-clock durations in `docs/mcp.md` §2 (under Operational Caps) and in the checkbox annotation here.
- [ ] **5.4 Inspect OS CI on `7970a12`, fix the Windows Chocolatey `swi-prolog.org` 502/503 flake in `.github/workflows/ci.yml`, and verify all 11 CI jobs green:**
  - **Recorded `7970a12` CI result (run `42502698245`, `head_sha: 7970a12d00451b2712c50435051479348032059d`)**: overall conclusion `failure` — **7/11 jobs succeeded** (`Coverage Report`, `Latency Benchmark & Budgets`, `Degraded Mode (Ubuntu / Python 3.12 / No swipl)`, and `test (ubuntu-latest, 3.10, 3.11, 3.12, 3.13)`), while **4/11 jobs failed** (`test (windows-latest, 3.10, 3.11, 3.12, 3.13)`), all at step `Install SWI-Prolog (Windows)` (`choco install swi-prolog -y --no-progress`) because `http://www.swi-prolog.org/download/stable/bin/swipl-9.2.9-1.x64.exe` returned HTTP `502 Bad Gateway` / `503 Server Unavailable` when hit simultaneously by 4 Windows runners.
  - **Fix `.github/workflows/ci.yml:32-38` (`Install SWI-Prolog (Windows)`)**: harden the Windows SWI-Prolog installation step with a retry-with-backoff loop around `choco install swi-prolog -y --no-progress` plus a direct HTTPS installer fallback (`https://www.swi-prolog.org/download/stable/bin/...` / `winget install --id SWI-Prolog.SWI-Prolog`) so transient 502/503 responses do not break Windows matrix jobs.

---

## Track 6 — Verification

- [ ] **6.1** **Ontology-Spider verification**:
  - Full test suite green in both modes (with `swipl` and in degraded mode without `swipl`; re-measure total test count $\ge 101$ including new tests in `3.2` / `5.2`).
  - Live statement coverage $\ge 90\%$ measured via `coverage run --source=src/ontology_spider -m unittest discover -s tests && coverage report --fail-under=90`.
  - Benchmark suite within budgets (`python -m ontology_spider.harness bench --budget src/ontology_spider/harness/baselines/bench_budgets.json`).
  - Differential parity 100% across all 5 scenarios (`python -m ontology_spider.harness run` and `python -m ontology_spider.harness parity`).
- [ ] **6.2** **Brain-Harness & Remote CI verification**:
  - `python -m harness.cli context lint` and `python -m harness.cli context govern` pass (`5/5` stages, `0` violations).
  - Drift gate green and unit test suite no worse than baseline.
  - Push both repositories to `origin/main` and verify GitHub Actions CI completes `success` across **all jobs** bound to the pushed HEAD SHAs on both `SpectreDeath/Brain-Harness` and `SpectreDeath/Ontology-Spider` (including all 11 jobs on Ontology-Spider).
- [ ] **6.3** Independent check box (unticked until the check lands): [ ] **Independent check** — verify Tracks 0–5 against the code, the live runs, and the bound CI runs, reconcile every checkbox in this plan, and record the verdict here.
