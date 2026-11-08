# Consolidated follow-through corrections follow-up plan — 2026-11-08 EST

**Scope:** Close the remaining gaps from the independent audit of the corrections plan execution (Brain-Harness `b94237d` / Ontology-Spider `113c5de`, audited 2026-11-08). The audit verdict confirmed Tracks 0–5 were substantially real and verified live, but identified six concrete defects:

1. Self-asserted verification verdicts in `b94237d` (executor ticked its own independent check box).
2. Ghost commit citations (citing unresolvable SHA `a8ecf26` instead of `ddc94ab`, and conflating Windows installer fixes with test clock resolution).
3. Quadratic $O(N^2)$ memory explosion and unbounded formatting in large chain queries (OOM exit 137 on default timeout).
4. Lack of real wall-clock timeout test on the Prolog MCP backend.
5. Environment-dependent harness benchmark threshold (`lattice_10k_validate_ms`).
6. Unverified step-level causes for intermediate GitHub Actions CI run failures.

**Heads at plan time:** Brain-Harness `b94237d`, Ontology-Spider `113c5de`. Both repositories are clean and CI green.

**Evidence rule (strictly enforced):** Tick a box ONLY with a verified commit SHA, live test output, dated artifact, or recorded repository decision. A tick without verified primary evidence is invalid.

**Guardrails:**

- **Zero Third-Party Dependencies in Ontology-Spider**: `dependencies = []` in `pyproject.toml` remains strictly preserved (pure Python stdlib + SWI-Prolog subprocess IPC).
- **No Atomic Plan + Execution Commit**: This redrafted plan must be committed in its own standalone commit before execution begins.
- **Independent Check Integrity**: The final independent check box (**6.3**) must remain unticked (`[ ]`) throughout execution. It can only be ticked by a separate check commit/session with its own dated report.
- **Repository Domain Partitioning**: BH tracks execute in `Brain-Harness`; OS tracks execute in `Ontology-Spider`. All cross-repo citations must specify repo name and full/short SHA.

---

## Track 0 — Honesty Gate: Undo Self-Asserted Verdicts (Brain-Harness)

- [x] **0.1 Untick corrections-plan 6.3 back to pending (`[ ]`) in `Consolidated follow-through corrections plan-2026-11-08-EST.md`**:
  - Revert `[x] **6.3**` back to `[ ] **6.3**`.
  - Add explicit note in the report section that the self-asserted check in commit `b94237d` (66 insertions, 25 deletions across plan files only) was withdrawn because an executor cannot self-certify its own independent check without external verification.
- [x] **0.2 Untick consolidated-plan 7.3 back to pending (`[ ]`) in `Consolidated follow-through plan-2026-11-08-EST.md`**:
  - Revert line 136 (`[x] **7.3** Independent check box: **Verdict: PASSED**`) back to `[ ] **7.3** Independent check box`.
  - Record that the re-tick in `b94237d` rested on the self-asserted 6.3 and is withdrawn until the follow-up plan is independently checked.
- [x] **0.3 Untick Gephi follow-up plan 4.3 back to pending (`[ ]`) in `Gephi follow-up fixes plan-2026-11-07-EST.md`**:
  - Revert line 40 (`[x] **4.3** Independent check box: **Verdict: PASSED**`) back to `[ ] **4.3** Independent check box`.
- [x] **0.4 Commit the honesty gate unticks**:
  - Read all three plan files at HEAD to verify 6.3, 7.3, and 4.3 are pending (`[ ]`).
  - Commit the unticks as a docs-only commit in `Brain-Harness` without altering any other checkboxes.

---

## Track 1 — Fix Evidence Citations & Working Tree Hygiene (Brain-Harness)

- [x] **1.1 Re-cite ghost commit `a8ecf26` to valid commit `ddc94ab` (Ontology-Spider)**:
  - In `Consolidated follow-through corrections plan-2026-11-08-EST.md`, replace all occurrences of `a8ecf26` in boxes 0.1, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3, and the Track 6.3 report with the real commit SHA `ddc94ab` where the work landed.
  - Verify with `git -C "D:\GitHub\projects\Ontology-Spider" cat-file -t ddc94ab` (returns `commit`). Confirm `a8ecf26` produces 0 hits repo-wide.
- [x] **1.2 Correct 5.4 commit citations in the plan**:
  - In `Consolidated follow-through corrections plan-2026-11-08-EST.md` box 5.4 and report: clarify that the Windows SWI-Prolog installer fix landed across `ddc94ab` (initial hardening), `ade6f78` (PowerShell variable interpolation fix), and `96ebb1f` (direct GitHub Releases NSIS installer download).
  - Clarify that subsequent commits `27c3361` and `113c5de` touched solely `tests/test_mcp.py` to resolve physical timer resolution flakiness on Windows runners.
- [x] **1.3 Disaggregate statement coverage reporting**:
  - Update the Track 6.3 report and `docs/decisions.md` references to qualify coverage by platform:
    - Windows: 3,566 statements, 318 missed (91%).
    - Linux: 3,566 statements, 322 missed (91%, +4 statements in `prolog/reasoner.py:95-101` Windows candidate registry unreached).
- [x] **1.4 Fix stale line citations and wording in prior plan**:
  - In box 5.1 disposition: update `mcp/server.py` line citations from 401/441 to live lines `396` and `431` (verified live).
  - In box 2.3: reword `"0 hits for '11'"` to state the true architectural intent: zero remaining references to `"11 clusters"` or `"ClusterEntry"` (accounting for legitimate occurrences such as `"Rule 11"`).
- [x] **1.5 Clean and commit working tree plan moves**:
  - Stage the moved files in `Brain-Harness`: `plan archive/Cluster pipeline connectedness fix plan-2026-11-06-1950-EST.md` and `plan archive/Context lint cleanup plan-2026-11-06-1950-EST.md` (deleting the root copies).
  - Commit all citation and hygiene fixes in `Brain-Harness`.

---

## Track 2 — Fix $O(N^2)$ Memory Explosion & Unbounded Formatting Kink (Ontology-Spider)

**Background & Live Audit Findings:**

1. *Query Target Confusion in Prior Benchmark*: In the previous session, the recorded 4.467s run on `generate_chain(10000)` executed `query ancestors of node_0`. Because `generate_chain` creates nodes named `c_0` through `c_{size-1}`, `node_0` did not exist in the model, returning 0 answers in 0.001s and masking the true scaling profile.
2. *Empirical Quadratic Growth*: Querying the true leaf `c_{N-1}` on a linear chain causes quadratic memory explosion:
   - $N=200$: $14\text{ MB}$ peak memory, $0.165\text{s}$ wall time.
   - $N=500$: $85\text{ MB}$ peak memory, $1.025\text{s}$ wall time.
   - $N=1,000$: $338\text{ MB}$ peak memory, $4.944\text{s}$ wall time.
   - $N=10,000$: Projects to $>33\text{ GB}$ peak memory, causing an out-of-memory crash (exit code 137).
3. *Root Causes in Code*:
   - **Reasoner Accumulation**: `_query_ancestors` and `_query_transitive` in `python_backend.py:153-182` and `dialog_runner.py:155-176` accumulate full subpaths (`path + [obj]`) and full assertion lists (`asrts + [a]`) for every answer $k \in [1, N-1]$, creating $\sum_{k=1}^{N-1} k = \frac{N(N-1)}{2} \approx 50,000,000$ assertion objects.
   - **Unbounded Formatting Loop**: In `engine.py:260-269`, `Session._execute_query` materializes `"provenance": [asrt.to_dict() for asrt in a.explanation.provenance_assertions]` across all answers without checking query deadline/timeout, allocating tens of millions of dictionary objects outside the reasoner's step guard.

- [ ] **2.1 Document live baseline measurements and query target correction**:
  - Record the empirical baseline numbers ($N=200 \to 14\text{MB}$, $N=500 \to 85\text{MB}$, $N=1,000 \to 338\text{MB}$, $N=10,000 \to \text{OOM}$) and document that the prior 4.467s measurement was an artifact of querying non-existent `node_0`.
- [ ] **2.2 Architecture Decision & Memory-Safe Query Implementation**:
  - Record formal decision in `docs/decisions.md` §7.11: *Bounded Explanation Provenance & Guarded Result Formatting*.
  - **Reasoner Bounding (`python_backend.py` & `dialog_runner.py`)**: For transitive closure and ancestor graph traversals, decouple the answer entity (`obj`) from unbounded path copying. Store the 1-hop justifying assertion (`a`) directly on the explanation, and bound accumulated explanation path depth (default cap `max_depth=50` or compact parent pointer) to guarantee $O(N)$ memory scaling instead of $O(N^2)$.
  - **Formatting Timeout Guard (`engine.py`)**: In `Session._execute_query`, apply deadline checking during the answer formatting loop and cap per-answer materialized provenance dictionaries to a safe upper bound (e.g. 10 assertions per answer). If formatting exceeds the deadline, raise `QueryTimeoutError`.
- [ ] **2.3 Verification of Large Chain Queries Under Default and Small Timeouts**:
  - Run `generate_chain(10000)` querying `c_9999` under `timeout_seconds=3.0`: confirm it terminates at $\approx 3.0\text{s}$ with `QueryTimeoutError` (peak memory $< 50\text{MB}$).
  - Run `generate_chain(10000)` querying `c_9999` under default `timeout_seconds=10.0`: confirm it returns all 9,999 ancestors in $< 5.0\text{s}$ with peak memory strictly bounded ($\le 100\text{MB}$), completely eliminating the OOM crash.
- [ ] **2.4 Fix `docs/mcp.md` §2 off-by-one**:
  - Correct the text in `docs/mcp.md` §2 (under Operational Caps): a 10,000-node chain generated by `generate_chain(10000)` consists of 9,999 assertions and returns 9,999 ancestors (`c_0` through `c_9998`), not 10,000.
- [ ] **2.5 Author Regression Contract**:
  - Add unit test `test_large_chain_query_memory_bounded` in `tests/test_reasoning.py` or `tests/test_mcp.py` asserting that a 10,000-node chain query completes within memory budget ($\le 100\text{MB}$) and returns 9,999 answers in both Python and Prolog modes.

---

## Track 3 — Prolog Timeout at the MCP Layer (Ontology-Spider)

**Background:** `test_mcp_prolog_backend_query_caps` (`tests/test_mcp.py:522`) exercises only the inference step cap (`max_inferences=2` $\to$ `QueryInferenceLimitError`). While `timeout_seconds=5.0` is passed, it is never challenged by an actual long-running query. Furthermore, the existing timeout test (`test_mcp_query_timeout_and_inference_caps`) uses mocked clock ticks (`side_effect=[100.0] + [200.0]*50`), verifying plumbing rather than true wall-clock timeout enforcement.

- [ ] **3.1 Author Real Wall-Clock Timeout Test for Prolog MCP Backend**:
  - Add `test_mcp_prolog_backend_wall_clock_timeout` in `tests/test_mcp.py` (marked `@unittest.skipUnless(PrologReasoner().is_available, "swipl not installed")`).
  - Construct a complex/dense model (or cyclic/deep structure) and execute a query via MCP `query` tool with `timeout_seconds=0.2`.
  - Assert that the response returns an error payload with code `-32000` containing `"timeout"`, and assert measured wall-clock duration is strictly bounded ($\le 1.0\text{s}$).
- [ ] **3.2 Document Clock Mocking as Plumbing Guard**:
  - In `tests/test_mcp.py`, add explicit docstring comments to `test_mcp_query_timeout_and_inference_caps` explaining that mocking `time.monotonic` verifies internal deadline state mechanics across coarse OS timer ticks, whereas `test_mcp_prolog_backend_wall_clock_timeout` verifies genuine subprocess wall-clock timeout handling.
- [ ] **3.3 CI & Local Verification**:
  - Confirm both tests pass locally and in GitHub Actions CI without timing flakiness.

---

## Track 4 — Benchmark Calibration & Environment Governance (Ontology-Spider)

**Background:** `python -m ontology_spider.harness bench --budget ...` can fail locally (`Budget exceeded for lattice_10k_validate_ms: 1126.36ms > 1000.0ms`) while passing in CI, because budgets in `bench_budgets.json` were calibrated to a specific high-spec host (AMD Ryzen 9 7950X, Windows 11 Pro, Python 3.13).

- [ ] **4.1 Document Machine Calibration Baseline**:
  - In `docs/harness.md` and `src/ontology_spider/harness/baselines/bench_budgets.json`, document the reference hardware baseline.
  - State explicitly that local runs on standard or battery-throttled laptops may exhibit $\pm 20\text{--}30\%$ variance, while CI runners enforce the authoritative gate.
- [ ] **4.2 Calibrate `lattice_10k_validate_ms` Threshold**:
  - Formally record the decision in `docs/decisions.md` §7.12: adjust `lattice_10k_validate_ms` from `1000.0ms` to `1500.0ms`.
  - *Justification*: $1500\text{ms}$ accommodates variable CPU thermal throttling and VM noisy neighbors while remaining 10x below quadratic degradation thresholds ($>10,000\text{ms}$), preserving strong regression protection without false-positive CI/local failures.
- [ ] **4.3 Re-Run Benchmark Suite**:
  - Execute `python -m ontology_spider.harness bench --budget src/ontology_spider/harness/baselines/bench_budgets.json` locally and confirm all 6 benchmarks pass within budget.

---

## Track 5 — Document Exact Causes for Past CI Failures (Ontology-Spider)

**Background:** CI failed on `7970a12`, `96ebb1f`, and `27c3361` before achieving 11/11 green on `113c5de`. The exact step-level causes have now been verified via GitHub Actions REST API logs.

- [ ] **5.1 Record Verified Step-Level CI Run History in `docs/decisions.md` §7.10**:
  - **Run `42502698245` (commit `7970a12`)**: Conclusion `failure` (7/11 passed, 4 failed). Failed jobs: `test (windows-latest, 3.10, 3.11, 3.12, 3.13)`. Failing step: `Install SWI-Prolog (Windows)`. Root cause: Chocolatey package download failed because `http://www.swi-prolog.org/download/stable/bin/swipl-9.2.9-1.x64.exe` returned HTTP 502/503. Test steps were skipped.
  - **Run `42517758361` (commit `96ebb1f`)**: Conclusion `failure` (8/11 passed, 3 failed). `Install SWI-Prolog (Windows)` via GitHub Releases succeeded across all Windows runners. Failing step: `Run Tests` on Windows 3.10, 3.11, 3.12 due to `test_mcp_query_timeout_and_inference_caps` physical timer tick granularity on Windows VMs.
  - **Run `42518002144` (commit `27c3361`)**: Conclusion `failure` (8/11 passed, 3 failed). Windows 3.13 passed; Windows 3.10, 3.11, 3.12 failed at `Run Tests` on the same sub-millisecond timer resolution issue.
  - **Run `42518342625` (commit `113c5de`)**: Conclusion `success` (**11/11 jobs passed**). Deterministic clock mocking in `tests/test_mcp.py` eliminated timer tick dependency, achieving full matrix green.
- [ ] **5.2 Commit Historical CI Dispositions**:
  - Commit the documented CI findings to `docs/decisions.md` §7.10 in `Ontology-Spider`.

---

## Track 6 — Final Verification & Independent Check Protocol (Both Repos)

- [ ] **6.1 Ontology-Spider Verification**:
  - Full test suite green in both modes:
    - Normal mode (with SWI-Prolog): $\ge 102$ tests passing.
    - Degraded mode (without SWI-Prolog): 88 tests passing, 14 skipped cleanly.
  - Live statement coverage $\ge 90\%$ verified via `coverage report --fail-under=90` (record Windows and Linux statistics separately).
  - Benchmark suite passes within calibrated budgets (`bench_budgets.json`).
  - Scenario parity 100% (5/5 scenarios matching across Python and Prolog backends).
  - Memory-safe chain query regression test (Track 2) and Prolog wall-clock timeout test (Track 3) verified green.
- [ ] **6.2 Brain-Harness Verification**:
  - Context lint (`python -m harness.cli context lint`) and governance (`python -m harness.cli context govern`) pass with 5/5 stages and 0 violations.
  - Repository working tree clean (plan files properly archived in `plan archive/`).
  - Remote CI: GitHub Actions CI green across all matrix jobs on both repositories bound to new HEAD SHAs.
- [ ] **6.3 Independent Check Box (LEAVE UNTICKED)**:
  - [ ] **Independent check**: This box MUST REMAIN UNTICKED (`[ ]`). It is reserved for an independent auditor in a subsequent, separate session to verify all primary evidence and record the final check verdict. An executor must never tick this box.
