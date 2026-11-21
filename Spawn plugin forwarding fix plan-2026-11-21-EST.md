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

- [ ] **0.1 Add the missing forwards to `HarnessSpawnerPlugin`.**
  `spawn` gains `materialize_dir` and `approve_dock`;
  `propose_merge_back` gains `proposal_kind`; `adopt_merge_proposal`
  gains `reviewer`; add `reject_merge_proposal` and a `materialize`
  method. Each forwards to `self._service` with the same signature
  the engine already accepts. No engine behavior changes.
- [ ] **0.2 Route `harness spawn` through the plugin service.**
  `commands/spawn.py` constructs `HarnessSpawnerEngine` directly in
  every command. Make the CLI resolve the spawner through the plugin
  service (the IoC seam) instead. If any command cannot go through
  the service for a concrete reason, record that reason in the code
  comment and in the plan annotation — do not leave a silent bypass.
- [ ] **0.3 Tests.** Plugin-level tests proving each forwarded
  parameter reaches the engine (`materialize_dir`, `proposal_kind`,
  `reviewer`, reject, materialize), plus a test that the CLI path and
  the plugin path reach the same engine state. Marked
  `@pytest.mark.unit` where they belong in the unit gate. Existing
  spawn suites still pass.

## Track 1 — Verification

- [ ] **1.1 Re-run the gates with dated outputs.** Spawn test suites,
  drift gate, ruff check + format. Record numbers that reproduce on
  a fresh checkout; note any that are machine-specific.
- [ ] **1.2 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
