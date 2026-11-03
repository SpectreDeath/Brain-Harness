# Follow-up fixes plan — 2026-11-03-1325-EST

Small, sequenced follow-up to the Big Fix execution (`d04428d`, Big fix plan
2026-11-03-0950-EST now 83/83 ticked). Review of that execution found three
things that should not have been called done. This plan closes them. It does
not reopen the Big Fix tracks.

## Evidence rule (applies to every checkbox)

A box is ticked only alongside one of the following: a commit hash plus the
test name that proves the fix, or a written decision with its reason (for
decide-items). "Decided" is a valid closure for decide-items. "Looks fine"
is not. Unticketing a wrongly ticked box counts as progress, not regression.

## Guardrails

- No new third-party dependencies without the user's explicit approval.
- No destructive changes (no repository deletions, no history rewrites,
  no `git clean -fd` outside a test's own temp dir).
- Do not touch the Gephi item's substance: the human render is out of scope
  for this plan (see Track 1). Do not substitute another headless check.

## Track 0 — Loader catalog regression (do first; it blocks a green suite)

Context: `tests/test_plugin_loader.py::test_list_catalog_and_manifest_lookups`
fails on a fresh checkout. It creates two fixture dirs — `alpha-plugin`
(with `plugin.json`) and `beta-plugin` (empty, manifest-less) — and expects
`list_catalog()` to return 2 entries. It returns 1. The Big Fix Track 0
loader change (manifest-less plugins default to untrusted instead of
trusted, `src/harness/plugins/loader.py`) dropped the manifest-less dir
from the catalog. That change also contradicts the Big Fix Track 0 Verify
claim of "25/25 tests passing" across `test_track0_sandbox_restrictions.py`
and `test_plugin_loader.py`.

- [ ] Find where the manifest-less dir drops out of the catalog (loader
      discovery vs catalog builder) and record the mechanism in one
      sentence in the commit message or a code comment.
- [ ] Decide, and record the decision with its reason: either restore
      manifest-less dirs to the catalog, or update the test's expectation
      to 1. Preferred direction: restore discovery, because listing a dir
      is not executing it — an untrusted entry in the catalog is not a
      security hole, and the execution gate (AST pre-check, fail-closed)
      is unchanged either way. If there is a concrete reason the test
      expectation is the right fix instead, that reason is the decision
      record.
- [ ] Verify: `tests/test_plugin_loader.py` and
      `tests/test_track0_sandbox_restrictions.py` pass in full on a fresh
      checkout with full dependencies installed (note: the Track 1
      dismiss test needs `fastapi` and `python-multipart`; the catalog
      test does not, but run the set with deps present so the result is
      unambiguous).
- [ ] Verify: the Big Fix Track 0 Verify claim is corrected to the actual
      counts (see Track 1 — the plan edit, not the code).

## Track 1 — Plan hygiene (paperwork, same round as Track 0)

- [ ] Untick the Big Fix Track 10 Gephi box. Replace its evidence note
      with: "Blocked on a human desktop session. Not done." Do not add
      another headless check, brief, or styling guide as evidence — the
      [NW] live-proof rule forbids that substitution, and it has now been
      substituted four times.
- [ ] Correct the Big Fix Track 0 Verify line ("25/25 tests passing") to
      the actual post-fix counts for `test_track0_sandbox_restrictions.py`
      and `test_plugin_loader.py`, with the commit hash of the Track 0 fix.

## Track 2 — Child-process network: document the boundary honestly

Context: the Big Fix Track 0 socket patch covers the in-process
primitives (`connect`, `connect_ex`, `sendto`, `getaddrinfo`, with the
Windows loopback carve-out, in `src/harness/plugins/bridge_runner.py`),
and the factory propagates `network_disabled` plus memory limits to the
venv and Docker-fallback paths. What it does not cover: a plugin spawning
a child process (`curl`, a fresh `python`) that never inherits the
in-process patch. No statement anywhere in code, docs, or tests currently
says the flag is cooperative-only, so the Big Fix Verify alternative
("refused, or the flag is documented as cooperative-only") is not
satisfied for child processes.

- [ ] State the boundary in `docs/reference/trust_and_isolation.md` and
      in the bridge runner's docstring: the network flag is cooperative
      for the plugin's own process and does not constrain child processes
      it spawns. One plain sentence in each place is enough.
- [ ] Soften any wording that overstates it — in particular the
      "strict memory/network controls" description of the
      `SubprocessExecutor` fallback — so it matches the cooperative-only
      boundary.
- [ ] Verify: no doc, docstring, or user-facing string still claims a
      child process's network is refused (grep for the claim, not just
      for the new sentence).
- [ ] Verify: the in-process primitive tests
      (`test_network_disabled_patches_primitives` and the rest of
      `tests/test_track0_sandbox_restrictions.py`) still pass.

## Out of scope for this plan (do not build)

- The Gephi render itself: opening `.harness/graph/knowledge_graph.gexf`
  in Gephi, applying a layout, running Louvain/modularity, and recording
  a render report with clusters and a screenshot. That is a human desktop
  task for the user, not an agent task.
- Real network-namespace enforcement for child processes (e.g.
  Docker `--network=none`, OS namespaces). Deferred unless a limitation
  is hit, per the user's simplicity rule.
- The soft §12 items from the review (dependency versions vs upstream
  latest; git-service default exposure). They are real but minor and
  belong in a later round, not this one.

## Done when

- [ ] Track 0 test failure fixed (or test expectation corrected by a
      recorded decision) and both test files green on a fresh checkout.
- [ ] Gephi box unticked with the blocked note; Track 0 Verify claim
      corrected to actual counts.
- [ ] Cooperative-only boundary stated in both places; no overstated
      network claim remains; in-process tests still green.
