# Plugin portability fixes plan — 2026-11-03-1915-EST

Follow-up to the Ontology-Spider plugin integration (`3f86400`: plugin,
companion skill, `ModelSource` vault adapter, and dock entrypoint in
`plugins/memory_and_epistemics/ontology_spider/`). Review of that commit
found the integration real but not portable: it only works on the machine
it was built on. This plan fixes exactly that. It does not change plugin
behavior, the adapter's semantics, or any engine code (the Ontology-Spider
repo is untouched by this plan).

## The two gaps (what "portable" means here)

1. **Hardcoded author-machine paths in the tests.**
   `plugins/memory_and_epistemics/ontology_spider/test_ontology_spider_plugin.py`
   resolves the vault sample and the engine source tree from
   `D:/GitHub/projects/Ontology-Spider/...` and asserts those paths
   exist. On Linux CI or any other machine those paths never exist, so
   the fixture fails before anything is tested — including the dock's
   `verify-ontology` entrypoint, which runs exactly this file.
2. **No declared engine dependency and no missing-engine story.**
   The plugin imports `ontology_spider` directly, but `plugin.json`
   declares `requires: []`, nothing installs the engine, the plugin
   README gives no install step, and there is no graceful handling when
   the engine is absent (a bare import failure, not a message naming the
   fix). The plugin therefore loads only where the engine happens to
   already be installed.

## Evidence rule (applies to every checkbox)

A box is ticked only alongside one of the following: a commit hash plus
the test name that proves the fix, or a written decision with its reason
(for decide-items). "Decided" is a valid closure for decide-items. "Looks
fine" is not.

## Guardrails

- No new third-party dependencies without the user's explicit approval.
  The engine itself is the user's own package, not a third-party one —
  declaring it as a dependency is in scope, but how it is obtained (see
  Track 1) is a decision to record, not something to assume.
- No behavior changes to the adapter, service, or plugin beyond what
  this plan names. No engine changes. No Track 10 items.
- No destructive changes. No repository deletions, no history rewrites.

## Track 0 — Portable test paths (do first; it unblocks CI)

- [ ] Replace every hardcoded absolute path in
      `test_ontology_spider_plugin.py` (the `D:/GitHub/projects/...`
      fixture path and the engine-source path used by the
      zero-imports test) with a portable resolution. Acceptable
      approaches, executor's choice with the choice recorded: resolve
      the engine from its installed package location
      (`importlib.util.find_spec`), resolve it from an environment
      variable (e.g. `ONTOLOGY_SPIDER_ROOT`) with a clear skip when
      unset, or bundle a vault-sample fixture inside the plugin's own
      test directory so the test is self-contained. What is not
      acceptable: another machine-specific path, or a path that only
      exists on the author's machine.
- [ ] If the chosen approach makes the tests depend on the engine being
      installed, the tests skip cleanly (with the reason in the skip
      message) when it is absent — they must not fail with a bare
      import error or a missing-path assertion.
- [ ] Verify: `pytest
      plugins/memory_and_epistemics/ontology_spider/test_ontology_spider_plugin.py -v`
      passes on a Linux checkout that is not the author's machine
      (fresh clone + documented dependencies installed, no
      author-machine paths present). Record the run.
- [ ] Verify: no hardcoded absolute path remains in the plugin
      directory (grep for `D:/`, `C:/`, `/home/`, `/Users/` — the result
      is the evidence, not a claim).

## Track 1 — Declare the engine dependency and the missing-engine story

- [ ] Decide and record, with reasons: how the engine is obtained and
      declared. Check the repo's existing pattern first (the `wasmtime`
      optional-runtime-dependency pattern is the nearest precedent:
      optional dep + automatic fallback + documented absence). The
      record names the mechanism (installed package, git checkout,
      vendored copy — whichever fits the repo's conventions) and where
      it is declared (`plugin.json`, repo dependencies, plugin README,
      or a combination).
- [ ] Implement the decided mechanism: the dependency is declared
      wherever the repo declares such things, and the plugin README
      gains an install step a fresh user can follow before running the
      tests or loading the plugin.
- [ ] Implement the missing-engine behavior: when the engine is absent,
      loading the plugin (or running its tests) produces a clear
      message naming the install step — not a bare `ModuleNotFoundError`
      traceback. If the repo's precedent is fallback instead of failure,
      the fallback and its limits are documented in the same place.
- [ ] Verify: on a machine without the engine installed, the
      missing-engine behavior is observed (message shown, or documented
      fallback taken) and recorded; on a machine with it installed per
      the new README step, the plugin loads and the tests pass.

## Track 2 — Dock entrypoint and final verification

- [ ] Run the dock's `verify-ontology` entrypoint
      (`pytest plugins/memory_and_epistemics/ontology_spider/test_ontology_spider_plugin.py -v`)
      on a non-author machine and record the result. It must pass — it
      is the same file Track 0 fixed, and this is the check that proves
      the dock verification is real rather than author-machine-only.
- [ ] Verify: the plugin's documented testing command (its README
      "Testing" section) matches the command actually run here, and the
      README's install step precedes it.
- [ ] Verify: no behavior change beyond this plan's scope — the
      adapter's query answers, explanations, and provenance for the
      vault sample are unchanged (the existing transitive-query test
      passing is the evidence).

## Out of scope for this plan (do not build)

- Any change to the Ontology-Spider engine or its repo.
- Any change to what the plugin does (new entrypoints, new query
  kinds, new validation rules).
- A published package for the engine (PyPI or otherwise), unless the
  Track 1 decision record shows that is the repo's existing convention
  for its own packages. If it is not the convention, the decision is
  "not now" and the plan closes without it.

## Done when

- [ ] The plugin tests pass on a Linux checkout that is not the
      author's machine, with no hardcoded absolute path remaining in
      the plugin directory.
- [ ] The engine dependency is declared per repo convention, the README
      has a followable install step, and the missing-engine behavior is
      observed and recorded.
- [ ] The dock `verify-ontology` entrypoint passes on a non-author
      machine.
