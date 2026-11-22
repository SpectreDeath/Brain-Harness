# Graph-driven domain harness follow-up corrections plan — 2026-11-22 EST

Follow-up to `Graph-driven domain harness spawning plan-2026-11-21-EST.md` (BH `dc60d08`, 14/15 ticked, 5.2 ticked 2026-11-22 on the user's word). Independent check delivered 2026-11-22 by two separate review sessions plus a third prepared check, all at BH `dc60d08`: **substantially real** — Tracks 0–2 verified live, 3.1 numbers reproduce exactly, spawns reproduce — **but** one real failing test (also the macOS CI failure), an unrecorded scope expansion, and sandbox-only adoption evidence.

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick the independent-check box (`5.2`) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change the confirmed spawn defaults (`Q2–Q7`) or weaken the merge-back policy (zero silent auto-adoption; never raw-`git merge` a trimmed domain branch back into `main`).
- Do not delete or move `.agents/skills/` directories on `main`.
- Do not touch any unticked box in any other plan (`Spawn provenance 3.3`, `Spawn capability completion 5.2`, `Spawn completion follow-up 3.1`, etc.) and do not re-open any ticked box.

---

## Track 0 — Decision gate (do first)

- [ ] **0.1 Record the Wave 1 scope decision.** The user picked tracer-2 in 0.2 ("repo distiller first, then security-forensics"), but all 4 Tier 1 harnesses were spawned; the expansion (`6db564a`) carries no recorded user decision and 0.2 still records only the tracer pick. Ask the user whether spawning all four was their pick or the executor's expansion; record their exact words and the date verbatim. If the tracer-2 pick stands, record the extra two as executor-expanded and note whether they are kept or retired.
- [ ] **0.2 Record the ranking-order note.** The recommender's live score order puts security-forensics 6th (45.56), while the plan's Tier 1 order puts it 2nd — and the recommender scores a curated 8-spec catalog (`CANONICAL_SPECS`), it does not discover a 9th candidate. Annotate 1.2/3.1 in the parent plan: Wave-1 order follows the user's Track 0.2 pick, not the score order, and the catalog is curated by design.

## Track 1 — CI failure: joint-query tie-break + ranking test

- [ ] **1.1 Make the joint-query cut filesystem-independent.** `joint_query.py` iterates the vault with `iterdir()`, scores coarsely, then does a stable sort and truncates at `limit=8`. For keyword `context`, 182 KIs match and ranks 5–13 are a 9-way tie at 6.0, so which KIs enter the pool is decided by vault iteration order (btrfs/APFS out, NTFS/overlayfs in). Make the sort total (tie-break by `ki_id`) or make `_collect_kis` rank-independent, so the same vault yields the same pool on every filesystem.
- [ ] **1.2 Fix the ranking test against the corrected ranking.** `tests/test_harness_spawner_blueprints.py::test_seeded_kis_rank_by_domain_relevance_and_skip_signature_dumps` (added in `8919e2a`) expects `ki_20261028_headroom_context_optimization` in the economizer's top 6; live it ranks 10th (score ~4.8 — title match on "headroom" only, domain `memory_and_epistemics`, no domain bonus). Either give the headroom KI domain/tag credit so it genuinely makes the top 6, or correct the test expectation to the ranking the fixed code actually produces. The test must pass on Linux, macOS, and Windows.
- [ ] **1.3 Make the dock-run entrypoints import-portable.** The 2.3 end-to-end tests fail on a box without an editable `harness` install: `dock run <name> icm-audit` raises `ModuleNotFoundError: No module named 'harness'` because `_build_scrubbed_env` keeps a relative `PYTHONPATH=src`, which resolves against the materialized cwd. Bootstrap an absolute PYTHONPATH from the materialized dir (or from the installed package) so the entrypoints work wherever Prime is checked out, not only where it is installed.
- [ ] **1.4 Re-run the suites and get CI green.** Re-run the 9-file targeted suite (parent 5.1) and the full unit gate; record exact numbers. CI must be green on head across all jobs (macOS included) — the `dc60d08` macOS 3.11 failure (run 44961743767) is the acceptance bar for this track.

## Track 2 — Record corrections

- [ ] **2.1 Correct the 3.2 security-forensics digest.** The parent plan's 3.2 annotation records tree `ad69a698…`; live review gives `c8efd2fd…` — the `8919e2a` edit to `network_diagnostics.py` (a skill script inside that blueprint's tree) changed the tree hash. Update 3.2 to `c8efd2fd…` and note the cause. (5.1 already records the new value; 3.2 was never updated.)
- [ ] **2.2 Fix the 0.3 typo.** The parent plan's 0.3 annotation reads `".3 yes, include all three docs…"` — restore the missing `0`.
- [ ] **2.3 Reconcile the 4.1 "8-Point" vs "9/9" mismatch.** The track is titled "8-Point ICM Cold Walk Test" but the annotation claims "9/9 invariants". Rename the track or recount with the actual invariant list, and list the invariants explicitly.
- [ ] **2.4 Make `docs_sha256` reproducible.** `README.md` embeds `| Generated (UTC) | … |` (`_doc_templates.py:252`), so every materialization hashes differently and the plan's `ff6f…`/`f722…` values are single-run observations. Drop the timestamp from the generated README (or exclude the timestamp line from the hash), re-materialize twice, and verify the digest is identical across both runs.
- [ ] **2.5 Commit the dated 3.1 selection report.** The discovery numbers live only in the parent plan's annotation; no dated selection report file exists in the repo. Commit the `harness spawn blueprints --json` output (dated) so the scores, cohesion, skill counts, and seeded-KI lists are reproducible from the repo without re-running the command.

## Track 3 — Cold-walk runner

- [ ] **3.1 Build a runnable cold-walk check.** No cold-walk runner exists anywhere in the repo (only mentions in the ICM skill docs and the plan); the "9/9 invariants" is a laptop-side checklist and the "≤2 reads" item is a human judgment with no recorded evidence. Build a script or test that verifies the invariants for a given spawned harness (AGENTS.md lines/tokens, CONTEXT.md tokens, `icm audit` 10/10, 0 broken links, `validate_harness_docs()` clean, `check-drift` clean) and records dated output.
- [ ] **3.2 Re-run it on all four spawned harnesses.** Record the dated results per harness. If the "≤2 reads" item cannot be automated, record it as a dated human judgment with the reader named, not as a test result.

## Track 4 — Adopted-KI evidence + gate reconciliation

- [ ] **4.1 Re-record the four 4.2 adoptions with committed artifacts.** The four adopted KIs (`ki-distill-karpathy-minimalism`, `ki-sec-dock-safety-baseline`, `ki-arch-service-layer-graph-seam`, `ki-econ-trimmed-domain-catalog`) are absent from the live vault — adoptions went to an isolated sandbox parent store (laptop-local), as did the source repos and use-case artifacts, so the specific runs cannot be verified from the repo. Either adopt the four KIs into the live vault, or commit the adoption logs, source-repo identity, and KI content so an independent check can verify the adoptions from the repo alone. Same evidence shape as the earlier spawn follow-up 3.2 gap.
- [ ] **4.2 Reconcile the 5.1 ruff format count.** Parent 5.1 claims 77 CI-scoped formatted files; the check found 79 formatted + 1 would-be-reformatted (`src/harness/kernel/README.md:56`, the known pre-existing venv-ruff-0.17.4 vs CI-0.11.0 skew, not in this diff). Correct the annotation or record the counting scope that yields 77.

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
