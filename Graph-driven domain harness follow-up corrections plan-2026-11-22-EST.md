# Graph-driven domain harness follow-up corrections plan — 2026-11-22 EST

Follow-up to `Graph-driven domain harness spawning plan-2026-11-21-EST.md` (BH `dc60d08`, 14/15 ticked, 5.2 ticked 2026-11-22 on the user's word). Independent check delivered 2026-11-22 by two separate review sessions plus a third prepared check, all at BH `dc60d08`: **substantially real** — Tracks 0–2 verified live, 3.1 numbers reproduce exactly, spawns reproduce — **but** one real failing test (also the macOS CI failure), an unrecorded scope expansion, and sandbox-only adoption evidence.

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick the independent-check box (`5.2`) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change the confirmed spawn defaults (`Q2–Q7`) or weaken the merge-back policy (zero silent auto-adoption; never raw-`git merge` a trimmed domain branch back into `main`).
- Do not delete or move `.agents/skills/` directories on `main`.
- Do not touch any unticked box in any other plan (`Spawn provenance 3.3`, `Spawn capability completion 5.2`, `Spawn completion follow-up 3.1`, etc.) and do not re-open any ticked box. Clarifying errata or annotations appended to already-ticked boxes in `Graph-driven domain harness spawning plan-2026-11-21-EST.md` (for `0.2`, `2.1`, `2.2`, `2.3`, `4.2`) do not count as re-opening them so long as no ticked box is unticked.

---

## Track 0 — Decision gate (do first)

- [x] **0.1 Record the Wave 1 scope decision.** The user picked tracer-2 in 0.2 ("repo distiller first, then security-forensics"), but all 4 Tier 1 harnesses were spawned; the expansion (`6db564a`, following `"continue"` after the `0.2` tracer-2 pick) carried no recorded user decision for keeping vs retiring the extra two (`harness-arch-modernizer`, `harness-context-economizer`).
  - **Recorded user decision (2026-11-22):** `"0.1: keep all four Tier-1 harnesses."` Both executor-expanded harnesses (`harness-arch-modernizer`, `harness-context-economizer`) are explicitly **kept**, so all four Tier-1 harnesses remain in scope for Tracks `2.1`, `3.2`, and `4.1`.
- [ ] **0.2 Record the ranking-order and scope-expansion notes.** The recommender's live score order puts security-forensics 6th (45.56), while the plan's Tier 1 order puts it 2nd — and the recommender scores a curated 8-spec catalog (`CANONICAL_SPECS`), it does not discover a 9th candidate. Annotate `0.2` in the parent plan with the recorded `2026-11-22` `0.1` decision keeping the executor-expanded pair (`6db564a`), and annotate `1.2`/`3.1` in the parent plan: Wave-1 order follows the user's Track 0.2 pick, not the score order, and the catalog is curated by design.

## Track 1 — CI failure: joint-query tie-break + ranking test

- [ ] **1.1 Make the joint-query cut and `_collect_kis` pool deterministic across filesystems.** `joint_query.py` iterates the vault with `iterdir()`, scores coarsely, then does a stable sort and truncates at `limit=8`. Both `"context"` (182 matches, 9-way tie at `6.0` in ranks 5–13) and `"token"` (86 matches, 9-way tie at `3.0` in ranks 4–12) suffer from `iterdir()` non-determinism on tie cuts. Make `src/harness/services/skill_graph/joint_query.py` use a total sort key `(-_score, ki_id)` AND harden `_collect_kis` in `src/harness/services/harness_spawner/blueprints.py` (widen candidate pool and/or credit explicit `became_skill` / `linked_pairs` edges to `spec.skills`) so flagship KIs do not depend on ASCII `ki-*` vs `ki_*` tie-break luck.
- [ ] **1.2 Preserve the `headroom` expectation and add a cross-filesystem determinism test.** Correct diagnosis: `tests/test_harness_spawner_blueprints.py::test_seeded_kis_rank_by_domain_relevance_and_skip_signature_dumps` (added in `8919e2a`) expects `ki_20261028_headroom_context_optimization` in `harness-context-economizer`'s top 6; it only fell to 10th (`~4.8`) when APFS/btrfs `iterdir()` dropped `headroom` from the unfixed `"context"` and `"token"` top-8 cuts. With total sort `(-_score, ki_id)` in `joint_query.py`, `headroom` already ranks 2nd (`14.50`). Keep the `headroom` top-6 assertion intact and add a determinism unit test that shuffles and reverses `iterdir()` order to prove identical `joint_query` and blueprint output on Linux, macOS, and Windows.
- [ ] **1.3 Make the dock-run entrypoints import-portable.** The 2.3 end-to-end tests fail on a box without an editable `harness` install: `dock run <name> icm-audit` raises `ModuleNotFoundError: No module named 'harness'` because `_build_scrubbed_env()` (`src/harness/services/dock/safety.py:73-91`) leaves inherited relative `PYTHONPATH` entries (such as `.:src` in `.github/workflows/ci.yml:87`) unresolved, so they resolve against the materialized `cwd=step_workdir` (which does **not** contain `src/harness`). Absolutize inherited relative `PYTHONPATH` entries against the parent process's `Path.cwd()` and/or append Prime's resolved package parent (`Path(harness.__file__).resolve().parent.parent`) *after* `repo_pp` (preserving target-repo precedence), and add a test simulating a non-editable checkout with relative `PYTHONPATH=src`.
- [ ] **1.4 Re-run the suites and get CI green.** Re-run the 9-file targeted suite (parent 5.1) and the full unit gate; record exact numbers. Note: verifying GitHub Actions CI green on `macos-latest` (`dc60d08` macOS 3.11 failure run 44961743767 as acceptance bar) requires explicit user authorization to `git push`.

## Track 2 — Record corrections

- [ ] **2.1 Correct the 3.2 security-forensics and refreshed `docs_sha256` digests.** The parent plan's 3.2 annotation records tree `ad69a698…`; live review gives `c8efd2fd…` — the `8919e2a` edit to `network_diagnostics.py` (a skill script inside that blueprint's tree) changed the tree hash. Note also that parent `3.2` item 3 (`harness-arch-modernizer`) omitted `docs_sha256`. Update `harness-security-forensics` tree SHA to `c8efd2fd…` (noting the cause), and once `2.4` makes `docs_sha256` reproducible and all four kept harnesses are re-materialized, refresh all four `docs_sha256` digests in `3.2` together.
- [ ] **2.2 Clarify the 0.3 quote without altering verbatim history.** The parent plan's 0.3 annotation quotes the user verbatim as `".3 yes, include all three docs in the check drift digest"`. Preserve the verbatim user quote per the Evidence Rule (do NOT silently mutate `".3"` into `"0.3"` inside quotes); clarify via editorial brackets (`"[0].3 ..."`) or an outside-the-quotes `(sic: 0.3)` note.
- [ ] **2.3 Reconcile the 4.1 "8-Point Cold Walk Test" vs "9/9" wording.** The track is titled `"8-Point ICM Cold Walk Test"` (canonical name in `.agents/skills/icm-workspace-architect/SKILL.md:104-117`) while the annotation claims `"9/9 invariants"`. Keep the canonical **"8-Point Cold Walk Test"** title (do not rename it); explicitly list the 8 canonical cold-walk points and distinguish them from `IcmAuditor`'s `10/10` invariants and `validate_harness_docs()`.
- [ ] **2.4 Make `docs_sha256` reproducible.** `TRACKED_DOC_PATHS` (`doc_bundle.py:32-38`) hashes both `README.md` and `docs/PROVENANCE.md`, and **both** embed `created_utc` (`_doc_templates.py:252` and `_doc_templates.py:332`), while `README.md` (`_doc_templates.py:249`) also embeds the per-run random `spawn_id`. Drop the timestamps from generated `README.md` and `docs/PROVENANCE.md` (or exclude timestamp lines—and specify whether `spawn_id` is fixed/reused or normalized—during `compute_docs_sha256()`), re-materialize twice, and verify the digest is identical across both runs.
- [ ] **2.5 Commit the dated 3.1 selection report.** The discovery numbers live only in the parent plan's annotation; no dated selection report file exists in the repo. Commit the `harness spawn blueprints --json` output at `docs/reports/spawn-blueprints-selection-2026-11-22.json` (and keep Rule 47 relative links if any companion `.md` is added) so scores, cohesion, skill counts, and seeded-KI lists are reproducible from the repo without re-running the command.

## Track 3 — Cold-walk runner

- [ ] **3.1 Build a runnable 8-Point Cold Walk check.** No cold-walk runner exists anywhere in the repo (only mentions in the ICM skill docs and the plan); the `"9/9 invariants"` is a laptop-side checklist and `"≤2 reads"` is a human judgment with no recorded evidence. Add a deterministic runner (e.g., `src/harness/services/harness_spawner/cold_walk.py` + unit tests; update `docs/reference/cli.md` for `test_cli_content_drift.py` parity if exposed as a CLI subcommand) mapping the canonical 8 Cold Walk points explicitly into automated checks (AGENTS.md lines/tokens, CONTEXT.md tokens `< 8,000`, `IcmAuditor` `10/10`, `IcmVerifier` `0` broken links, `validate_harness_docs()` clean, `check-drift` clean — distinct from each other) vs human-judged items (`#1 Where am I <=2 reads`, `#5 Single Source of Truth`, `#8 Broken Invariants Explained`) and recording dated output.
- [ ] **3.2 Re-run it on all four kept Tier-1 harnesses.** Per recorded decision `0.1`, all four Tier-1 harnesses (`harness-repo-distiller`, `harness-security-forensics`, `harness-arch-modernizer`, `harness-context-economizer`) remain in scope. Record the dated results per harness, with human-judged points (`#1`, `#5`, `#8`) recorded explicitly as dated human judgments naming the reader rather than automated test results.

## Track 4 — Adopted-KI evidence + gate reconciliation

- [ ] **4.1 Re-record the four 4.2 adoptions with committed repo artifacts (no live-vault adoption).** The four adopted KIs (`ki-distill-karpathy-minimalism`, `ki-sec-dock-safety-baseline`, `ki-arch-service-layer-graph-seam`, `ki-econ-trimmed-domain-catalog`) went to an isolated sandbox parent store alongside local source-repo runs and use-case artifacts, so they cannot be verified from the repo alone.
  - **Recorded user decision (2026-11-22):** `"4.1: commit adoption evidence only — do not adopt the KIs into live .harness/knowledge."`
  - Commit self-contained adoption evidence for all four kept Tier-1 harnesses (`0.1`)—including proposal IDs, adoption logs, source-repo commit identities, and the adopted KI payloads—at `docs/reports/spawn-wave1-adoptions-2026-11-22.md` (or paired `.json`/`.md`), leaving `.harness/knowledge/` untouched (`382` KIs, preserving `test_readme_and_manual_knowledge_item_count_matches_live` and avoiding `_write_ki_dual_file` strict-sync schema drift).
- [ ] **4.2 Reconcile the 5.1 ruff format count.** Verified live: `.venv` runs `ruff 0.11.0`, matching `pyproject.toml:34` and `.github/workflows/ci.yml:31,39`, where the 8 CI-scoped paths contain `77` `.py` files (`77 files already formatted`) plus `3` `.md` files (`src/harness/kernel/README.md`, `src/harness/kernel/context/README.md`, `plugins/software_engineering/deep_repo_auditor/README.md`). The reviewer's `79 + 1` (`80`, flagging `src/harness/kernel/README.md:56`) came from `ruff 0.17.4` scanning `.md` files. Annotate parent `5.1` to record `ruff==0.11.0` alongside `77` and explain the `77` `.py` vs `80` (`.py` + `.md`) count scope.

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
