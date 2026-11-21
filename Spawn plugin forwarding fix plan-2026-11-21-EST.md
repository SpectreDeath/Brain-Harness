# Spawn plugin forwarding fix plan — 2026-11-21 EST

Fix the non-blocking observation from the spawn completion review:
`HarnessSpawnerPlugin` forwards the Step 1 methods but does not forward
the Step 2–4 parameters, and `harness spawn` (`commands/spawn.py`)
constructs `HarnessSpawnerEngine` directly in every command instead of
going through the plugin service.

## Verified starting state (BH `1f5a524`, 2026-11-21)

What the plugin forwards (`plugins/agent_orchestration/harness_spawner/
main.py`): `spawn` (spec + probe_fn only), `record_usage`, `complete`,
`retire`, `retire_all`, `get_spawn`, `list_spawns`, `propose_merge_back`
(task_id, cue, lesson, evidence, why, tree, ki_id), `adopt_merge_proposal`
(parent_library_root, parent_knowledge_root).

What it does NOT forward:

- `spawn`: no `materialize_dir`, no `approve_dock` (the engine's
  `spawn()` takes both; `spawn.py:154` passes them to a directly
  constructed engine).
- `propose_merge_back`: no `proposal_kind` (the engine takes it;
  `spawn.py:321`).
- `adopt_merge_proposal`: no `reviewer` (the engine takes it;
  `spawn.py:369`).
- `reject_merge_proposal`: no method at all (the engine has it;
  `merge_mixin.py:205`; `spawn.py:393` calls it on a directly
  constructed engine).
- `materialize`: no method at all (the engine path is
  `materialize_spawn_as_dock`, `materialize.py:76`).

Consequence: anything that reaches spawning through the IoC plugin
service — another plugin, the kernel service — cannot materialize, reject,
or pass `proposal_kind` / `reviewer` / `materialize_dir`. Only the CLI,
which bypasses the plugin, can. The plugin is not the single seam for
spawning.

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output,
or a written decision recorded verbatim from the user in chat. Never
record a user pick that did not happen in visible conversation. Never
tick the independent-check box (1.2) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change spawn defaults, merge-back policy, or the engine's
  behavior — this plan only forwards parameters that already exist.
- Do not touch spawn provenance 0.3/3.3, the spawn completion plan's
  5.2, the follow-up plan's 3.1 or 4.2, or any other unticked box. Do
  not re-open any ticked box.

## Track 0 — Forward the Step 2–4 surface

- [x] **0.1 Add the missing forwards to `HarnessSpawnerPlugin`.**
  `spawn` gains `materialize_dir` and `approve_dock`;
  `propose_merge_back` gains `proposal_kind`; `adopt_merge_proposal`
  gains `reviewer`; add `reject_merge_proposal` and a `materialize`
  method. Each forwards to `self._service` with the same signature
  the engine already accepts. No engine behavior changes.
  *(Done `2026-11-21`, commit `5718fa6`: updated `HarnessSpawnerProtocol` (`src/harness/services/harness_spawner/protocols.py`), `DefaultHarnessSpawnerService` (`plugins/agent_orchestration/harness_spawner/service.py`), and `HarnessSpawnerPlugin` (`plugins/agent_orchestration/harness_spawner/main.py`) to forward `spawn(..., materialize_dir, dock_service, approve_dock)`, `propose_merge_back(..., proposal_kind)`, `adopt_merge_proposal(..., reviewer, review_note)`, `reject_merge_proposal(..., reviewer, reason)`, `materialize(...)` -> `materialize_spawn_as_dock`, `check_drift(...)` -> `check_materialized_drift`, and `export_dag(...)`, plus `for_state_file(state_file)`. Zero engine behavior changes.)*
- [x] **0.2 Route `harness spawn` through the plugin service.**
  `commands/spawn.py` constructs `HarnessSpawnerEngine` directly in
  every command. Make the CLI resolve the spawner through the plugin
  service (the IoC seam) instead. If any command cannot go through
  the service for a concrete reason, record that reason in the code
  comment and in the plan annotation — do not leave a silent bypass.
  *(Done `2026-11-21`, commit `5718fa6`: added `get_spawner_service(*, save_dir=None, context=None)` in `src/harness/commands/spawn.py` resolving `HARNESS_SPAWNER_SERVICE_KEY` from `ServiceContext` first, then `plugins.agent_orchestration.harness_spawner.main.plugin.for_state_file(save_dir / "registry.json")` (with `ImportError`-only fallback if `plugins` is absent), and routed `run`, `list`, `retire`, `propose`, `adopt`, `reject`, and `check-drift` (with partial-mock fallback to `check_materialized_drift`) through it. Exception documented inline in `review_cmd`: `harness spawn review` stays on `build_tree_diff_review` because it is a stateless pre-spawn tree diff/digest preview with no engine or registry state.)*
- [x] **0.3 Tests.** Plugin-level tests proving each forwarded
  parameter reaches the engine (`materialize_dir`, `proposal_kind`,
  `reviewer`, reject, materialize), plus a test that the CLI path and
  the plugin path reach the same engine state. Marked
  `@pytest.mark.unit` where they belong in the unit gate. Existing
  spawn suites still pass.
  *(Done `2026-11-21`, commit `5718fa6`: added `tests/test_harness_spawner_plugin_forwarding.py` (`4` `@pytest.mark.unit` tests covering parameter forwarding + `execute()`, `ServiceContext` IoC priority, bidirectional CLI ↔ plugin engine-state parity, and plugin-dispatch spies across `run`/`list`/`propose`/`adopt`/`reject`/`check-drift`), plus `@pytest.mark.unit` `test_plugin_singleton_forwards_step2_to_4_methods` in `plugins/agent_orchestration/harness_spawner/test_harness_spawner_plugin.py`. All `28` spawn/plugin tests pass alongside `60/60` in `test_service_recursive_harnessing.py`.)*

## Track 1 — Verification

- [x] **1.1 Re-run the gates with dated outputs.** Spawn test suites,
  drift gate, ruff check + format. Record numbers that reproduce on
  a fresh checkout; note any that are machine-specific.
  *(Done `2026-11-21`, head `5718fa6`: `7` spawn/plugin suites -> `28 passed in 4.57s`; drift gate `test_plugin_integration_drift.py` + `test_cli_content_drift.py` -> `14 passed in 9.15s`; `ruff check .` -> `All checks passed!`; `ruff format --check` on the `6` touched `.py` files -> `6 files already formatted`; CI-scoped `ruff format --check` -> `73 files already formatted`; full unit gate `pytest -m "unit" -q --timeout=60` -> `2325 passed, 885 deselected, 2 warnings in 269.39s` (+4 from the new forwarding unit tests; `269.39s` runtime is machine-specific; an unrelated unit test mutated `.harness/config.json`, restored via `git checkout -- .harness/config.json`). Pre-commit at identical code: `test_service_recursive_harnessing.py` -> `60 passed in 4.27s`, `mypy` (`kernel` + `protocols.py`, `28` files; `spawn.py` + `main.py` + `service.py`, `3` files) -> `Success: no issues found`, `harness context lint` -> `PASS`, `uv lock --check` -> exit `0`.)*
- [x] **1.2 Independent check.** Verified `2026-11-21` by a genuinely
  separate check session at `HEAD` (`b543ab3`) and ticked on the user's
  word (`"Tick it"`): execution substantially real — forwards verified in
  code (zero engine behavior changes), CLI routed through
  `get_spawner_service` (IoC-first), 7 suites `26 passed + 2 deselected`
  (engine absent in this box's venv; `26+2=28` collected, matching the
  laptop's `28 passed`), drift gate `14 passed`, `ruff check` clean,
  `6` touched `.py` files formatted, full unit gate `9 failed / 2226
  passed / 90 skipped / 885 deselected` (`2226+90+9=2325` collected
  exactly; the 9 failures are the known pre-existing set, no new ones),
  CI green on `b543ab3` (run `44905823911`). Nits: this box's ruff
  0.17.4 flags pre-existing `kernel/README.md:56` (not in the diff; CI's
  pinned 0.11.0 does not); the laptop's mypy "no issues found" does not
  reproduce from the repo root (1 pre-existing import-not-found at
  `main.py:44` + pre-existing transitive errors).
