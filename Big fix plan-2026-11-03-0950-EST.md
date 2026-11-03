# Big fix plan — cracks, seams, conflicts, dependencies — 2026-11-03 (0950 redraft)

**Supersedes:** `Big fix plan-2026-11-03-0840-EST.md` (archive it once this is accepted).
**Head:** `1a97c3b`. The sweeps ran at `9947119`. The only commits since then are docs-only
(`9041790` archived the 0406/0715 plans; `1a97c3b` added the 0840 plan), so every code
citation and count below still holds unless an item says otherwise.
**Built from:** five parallel read-only sweeps at `9947119` (code health, dependencies/CI,
docs/counts, vault data, security/trust), each reporting file:line evidence, plus a 0950
review pass that re-checked a sample of citations against code (sandbox factory, git
transaction service, loader exec order, joint-query matcher, plan archive state).
**Workflow note (read this first):** this plan goes to Gemini Argon for checking, and Muse
checks any redraft. Lesson from the last round, stated plainly so it is not repeated: the
0715-EST redraft silently weakened items (dock test holes dropped, lifecycle/Gephi reduced to
tests and briefs) and introduced wrong command lists that the executor then copied verbatim
into docs. A redraft of THIS plan must preserve every item below or explicitly record a
decision to decline it with a reason — weakening by rewording is not a fix, and a redraft
that invents command lists, counts, or capabilities without checking code will repeat the
integrated-toolkits failure. The "non-weakenable" items are marked **[NW]**.
**Boundary:** read-only analysis except this plan doc. No deletions except where a track
explicitly says delete-or-mount, and then only the named module. No new third-party
dependencies without the user's explicit approval (repo guardrail). Keep it simple: decide
first, smallest fix that closes the item, no upfront over-engineering.

## What changed from 0840, and why (no item declined)

Every 0840 item is still here. Changes are moves, corrections, and additions only:

1. **Track 10 split into 10 (live proofs, [NW]) and 10b (carried-over code fixes, [NW]).**
   0840 put dock test holes, the 7-tuple label, and the joint-query matcher under a
   "do not substitute a test" banner. Dock test holes *are* tests, so the banner contradicted
   its own items. Live proofs keep the no-substitute rule. Code fixes close with code + tests.
2. **"Two `trusted` flags disagreeing" moved from Track 8 to Track 0.** It is a trust-bypass
   defect in the same loader/factory code as Track 0's loader items, not dedup. Fixing them
   apart risks two conflicting trust models.
3. **Cross-track dependencies made explicit** (new section below). The important one:
   Track 4's absolute-path edge normalization "at the next backfill" cannot reach disk until
   Track 5 makes backfill write to `metadata.json`.
4. **Track 1 sharpened.** `git restore .` (`filesystem_git.py:343`) also throws away
   uncommitted edits to tracked user files, not only untracked files. There is also a
   `git reset --hard <target_hash>` branch (`:337-340`). Line citations corrected from
   `:339-347` to `:337-344`.
5. **Track 6 two-plans item updated to the current state.** The 0406/0715 archive move
   already happened in `9041790`. What is still open is listed. Added: the 0715 Track 6
   "rather than heuristic string substring matches" box is ticked, yet `joint_query.py:117`
   still does `sk_clean in target`. Same tick-without-evidence pattern.
6. **Verify lines completed.** In 0840, several tracks had fix items that their Verify line
   never checked (Track 0 bypasses and module-cache collision, Track 2 aliases/toggles/bundle,
   Track 3 PATH binary, and others). Each Verify now covers every item.
7. **Track 7 gates: measure before enforcing.** Turning on `ruff format --check`, mypy
   (`disallow_untyped_defs`), or a coverage floor without first recording a baseline could
   turn CI red all at once. Added a baseline-first step. It does not soften the decision.
8. **Track 9 de-duplicated.** Its "export/backfill log-and-count" clause repeated Track 5 item 2.
   That clause now lives only in Track 5. The silent-skip tail triage stays in Track 9.
9. **Section numbering fixed.** 0840 had both "Track 11" and "§11". The backlog is now §12.
   The dangling "Track 6's rationale record" in Track 11 now says it means the *0715 plan's*
   Track 6.
10. **Evidence rule added** (below). It targets the repeated "ticked without evidence" failure.

## Evidence rule (applies to every checkbox)

A box is ticked only alongside one of the following: a commit hash plus the test name that
proves the fix, a dated recorded output (Track 10), or a written decision with its reason
(for decide-items). "Decided" is a valid closure for decide-items. "Looks fine" is not.
Unticking a wrongly ticked box counts as progress, not regression.

## Current state, verified 2026-11-03 at `9947119` (unchanged at `1a97c3b`)

- 138 canonical plugins, 1 external bundle (35 entrypoints), 103 skill dirs, 301 vault items
  (all `ACTIVE`), 188 stored edges, 45 CLI groups + 10 standalone commands, 641 tool
  entrypoints (606 canonical + 35 external), ~381 test files / ~2,926 test functions.
- The Nov 3 execution round genuinely closed: derived drift gate, hyperframes manifest fix,
  status backfill (301/301), triad-forge creation default, informed dock approval,
  generic-dock SHA, hermetic dock CLI tests, joint-query typed-edge priority.
- What this plan covers is everything else the sweeps found: restrictions that do not
  restrict, destructive paths, trust accounting with no paper trail, capability claims the
  code does not implement, vault fields still missing, storage with three disagreeing
  authorities, docs that describe commands that do not exist, CI that never exercises the
  frontend or the lockfile, and a dependency-age question nobody has answered with a live
  check yet.

## Suggested order and cross-track dependencies

Tracks 0–2 first (security and data-loss class), then 3–5 (trust accounting, honesty of
claims, vault integrity), then 6–7 (docs regeneration, CI/dependencies), then 8–9 (dedup,
test hygiene), then 10/10b (live proofs and carried-over fixes). Tracks are pickable one at
a time; nothing here is started unasked. Respect these edges when picking:

| Before | After | Why |
| --- | --- | --- |
| §12 "does a default agent run include the git service?" | Track 1 item 1 | That answer sets how urgent the fix is and whether an opt-in gate is enough |
| Track 0 trust items (incl. moved "two flags") | Track 2 trust justification backfill | Justify grants under the final trust model, not the current split one |
| Track 2 `config.json` decision | Track 10 hyperframes item | If `config.json` is not policy, the disabled entry is moot |
| Track 5 item 1 (backfill writes to disk) | Track 4 absolute-path edge normalization | Today backfilled edges never reach `metadata.json` (`vault_operations.py:142`). The alternative is a direct one-off disk rewrite, recorded as such |
| Track 5 authority decision | Track 4 telemetry decision | Telemetry also writes from the throwaway `:memory:` fallback. Decide both together |
| Track 6 drift gates (build early) | Track 8 delete-or-mount decisions → final cli.md / toolkits regen | Track 8 may mount or delete `rol obligation_group`, `CommandRegistry`, `/api/rea/*`. Regen after those decisions, so the gate catches any later drift |
| Track 7 baseline measurements | Track 7 gate enforcement | See item 7 of the changelog |

## Track 0 — Sandbox and trust restrictions that do not restrict **[NW for the mechanism fixes]**

The network and isolation story is the weakest seam in the repo. Each item below is
verified in code, not inferred.

- [ ] Network restriction bypasses: `sandbox/subprocess.py:240-241` sets `HARNESS_NO_NETWORK=1`
      and `bridge_runner.py:219-236` patches only `socket.socket.connect`. Close the three
      verified bypasses: `connect_ex` (unpatched method), UDP/`sendto` and DNS/`getaddrinfo`
      (unpatched), and child processes (`curl`, fresh `python`) that never inherit the
      in-process patch. If a true network namespace is out of scope, record that the flag is
      cooperative-only and stop describing it as a restriction — do not leave the claim
      stronger than the mechanism. (Keep the loopback carve-out required by AGENTS.md
      Rule 56, or Windows proactor self-pipes break.)
- [ ] Venv path drops the restriction: `sandbox/factory.py:122-126` routes to `VenvExecutor`
      whenever `isolation == VENV` or the plugin declares any dependencies, and `VenvExecutor`
      takes no `network_disabled` argument (`sandbox/venv.py:74-78` builds a bare
      `SubprocessExecutor`). Pass the flag through, or stop silently upgrading
      subprocess→venv for plugins with dependencies.
- [ ] Docker fallback drops the restriction: `sandbox/factory.py:113-116` falls back to a bare
      `SubprocessExecutor(entrypoint)` with no `network_disabled` and no memory limit. Pass
      both through, matching the normal subprocess path (the WASM fallback at `:169-177`
      already passes the flag correctly — copy that shape).
- [ ] Subprocess plugins inherit the full host environment: `sandbox/subprocess.py:237`
      copies `os.environ` when no `_env` is set, and nothing in `sandboxed.py`, `transport.py`,
      or `services/tools/` ever sets `_env`. Extend the dock path's env scrubbing
      (`services/dock.py`) to the plugin sandbox transport, or set a minimal default env for
      untrusted plugins. The container executor already does this right (`container.py:39,165-169`
      defaults env to `{}` + declared config, network to `none`) — use it as the reference.
- [ ] Manifest-less `.py` plugins default to trusted: `plugins/loader.py:135-137,191-200`
      defaults `trusted=True` for the manifest-less scan path, bypassing the instance-trust
      check that the manifest path enforces. Default the scan path to untrusted (the ZIP path
      already passes `trusted=False` at `:256`) or require an explicit trust argument at
      `discover_all` and the watcher.
- [ ] Loader trust-check ordering: `plugins/loader.py:369-392` executes the module
      (`exec_module`, `:374`) BEFORE checking `instance.trusted`, so a blocked plugin's
      module-level code already ran in-process; blocking only prevents registration. Check
      trust before execution, or execute untrusted modules only under the sandbox transport.
      Also fix the module-cache collision at `:369-372` (`harness_plugin_{stem}` — every
      `main.py` collides, so the second manifest-less plugin with stem `main` silently
      returns `[]`).
- [ ] *(moved from 0840 Track 8)* Two `trusted` flags disagreeing: class default is
      `trusted=False` (`plugins/base.py:75-81`), but of 87 `in_process` manifests, 37
      entrypoints never override it — the loader's direct path blocks them while the
      factory's in-process path checks only the manifest flag, so they end up in-process
      anyway. Reconcile: one flag, one check, no silent default. (§12 lists confirming that
      none of the 37 is meant to be untrusted.)
- [ ] Verify: `connect_ex`, UDP `sendto`, `getaddrinfo`, and a child `python`/`curl` are each
      refused (or the flag is documented as cooperative-only); untrusted plugin with
      dependencies gets no network on the venv path; Docker fallback carries flag + memory
      limit; untrusted subprocess plugin sees a scrubbed env; manifest-less scan defaults
      untrusted; blocked plugin module code does not execute; two manifest-less `main.py`
      plugins both load; one trust flag decides in-process placement on every path.

## Track 1 — Destructive paths (data-loss class)

- [ ] ReAct transactional path: `agent/react/engine.py:76` routes every tool call through
      `invoke_tool_transactional`. On success it runs `git add -A` + commit
      (`services/filesystem_git.py:307-311`), which sweeps unrelated uncommitted user work
      into agent commits. On error it runs `git restore --staged .`, `git restore .`, AND
      `git clean -fd` (`:342-344`). That discards uncommitted edits to every tracked file
      and deletes ALL untracked files in the repo, not just the tool's. When a `target_hash`
      is passed, it runs `git reset --hard <target_hash>` (`:337-340`) instead. Scope all of
      these to the tool's own paths, or gate them behind an explicit opt-in. Also confirm
      whether default agent runs include the git service at all (no `ReActEngine(`
      construction exists outside `agent/react/` — that exposure question is currently
      unverified and must be settled, not assumed; see §12).
- [ ] `docks.json` corrupt-file erasure: `services/dock.py:554-556` catches all exceptions
      and returns `{}` with no log, no backup; the next `link()` then overwrites the file and
      permanently destroys every other dock record. Quarantine a corrupt file to
      `docks.json.corrupt-<ts>`, refuse to save over it, and write atomically.
- [ ] UI dismiss no-op: `ui/server/routes/knowledge.py:135-165` — only `supersede`/`contradict`
      write; `dismiss` falls through both branches yet returns `{"status": "ok"}`, while
      `GraphView.tsx:451` offers Dismiss as a peer action. Either record the dismissal or
      return an honest status.
- [ ] Session-store corrupt handling: `agent/session/store.py:90-91` returns `None` for a
      corrupt session (conflating corrupt with missing) and `:108-109` silently drops corrupt
      sessions from listings. Distinguish corrupt from missing and surface it.
- [ ] Verify: a failing tool no longer deletes unrelated untracked files or reverts unrelated
      tracked edits; a successful tool no longer commits unrelated work; the `reset --hard`
      branch is scoped or gated; a corrupt `docks.json` cannot be overwritten by `link()`;
      dismiss either persists or reports honestly; corrupt sessions are distinguishable from
      missing ones.

## Track 2 — Trust accounting (who is trusted, and why, on paper)

- [ ] `trusted=True` has no justification anywhere: ~90 canonical plugins carry it, the
      manifest schema (`plugins/manifest.py:142`) is a bare bool, yet it unlocks in-process
      execution (`sandbox/factory.py:88-103`) and network access. Add a justification field
      (or a per-plugin trust note) and backfill it for the in-process set, starting with
      TokenEconomizer (verified low-risk in practice: pure computation, advisory-only pruning,
      no file/network/env access — but nothing records why). Do this after Track 0's
      one-flag reconciliation.
- [ ] 12 subprocess-manifest plugins are imported in-process by CLI code (verified list:
      `deepselect_topk`, `garf_reporting_pipeline`, `rea_javascript`, `wiki_compiler`,
      `hf_doc_builder`, `gods_eye_view` (2 files), `context_compiler`, `memgraphrag`,
      `memory_decay_engine`, `rea_managed_runtime`, `rea_mobile_firmware`, `rea_native`).
      All are `trusted=True`, so this is within policy — but the manifest's subprocess
      declaration is not enforced on the CLI path. Decide per plugin: route through the sandbox
      transport, or record that CLI-path in-process import is intentional for trusted plugins.
      Same decision for skill-script adapters (`commands/calibrator/engine_adapter.py:23`,
      `self_eval`, `uncertainty`, `bigquery`, `compass`) that `sys.path.insert` skill scripts
      and import them unsandboxed.
- [ ] MCP approval gap: `mcp/server/router.py:71-85` invokes any registered tool with no
      allowlist, approval, or drift concept, and `commands/tools.py` enable/disable/toggle
      likewise have no confirm. Decide: an MCP allowlist/approval step, or an explicit
      documented statement that any connected MCP client may invoke any enabled tool. Also fix
      the list/call mismatch: `tools/list` advertises disabled tools (`enabled_only=False`,
      `:68`) while `tools/call` refuses them, and the 28 REA aliases are callable but not
      listed (only canonical `_tools` are enumerated).
- [ ] ToolRegistry alias layer completion: `services/tools/registry.py` — `unregister`
      (`:173-180`) looks up the raw name, so unregistering an alias returns `False` and leaves
      the canonical tool alive; `register` doesn't resolve, so registering under an alias
      creates a shadow entry `list_tools`/`get_schemas` advertise but `enable`/`invoke` never
      reach; neither `unregister` nor `unregister_all_from` removes aliases. Resolve aliases
      in `register`/`unregister` and prune stale aliases on unregister.
- [ ] CLI tool toggles are ephemeral and mis-matched: `commands/tools.py:69-87` builds a
      throwaway `:memory:` runtime and discards it, so a toggle cannot affect a running
      dashboard or later process (same pattern in `commands/plugins.py`). Either persist
      `ToolSpec.enabled` or remove the toggle illusion; and align CLI matching (substring over
      canonical names only) with registry alias resolution (exact), so `disable rea` stops
      toggling every REA tool by substring surprise.
- [ ] One enable = 35 tools: enabling the external Pocock bundle auto-mounts all 35 entrypoints
      (`sandboxed.py:190-209`) with no per-tool gating. Decide: per-tool approval on enable,
      or a recorded decision that bundle-enable is all-or-nothing.
- [ ] `.harness/config.json` disabled list is enforced by nothing: the only consumer of
      `disabled_plugins` in `src/` is CLI enable/disable bookkeeping
      (`commands/plugins.py:39-52`); the loader never reads it. The committed file lists 68
      disabled / 4 enabled, but 16 of the 68 match no manifest name or provides key (including
      stale `domain.pyrit_redteaming`, whose plugin directory was deleted Oct 27) and 3 of the
      4 enabled entries match nothing either — so the `hyperframes_renderer` disabled entry
      has no effect now that its manifest parses. Decide: is this file personal dev config that
      should not be the shared default, or intended policy that the loader must enforce?
      Either way, prune the stale entries and document the file (zero docs describe it today).
- [ ] Verify: every in-process grant has a recorded reason or an intentional-CLI-path note
      (12 CLI-path plugins + 5 skill-script adapters each decided); MCP list matches call
      behavior and aliases are listed (or the no-approval posture is documented); alias
      unregister removes the alias and alias register does not shadow; CLI toggles persist
      or are removed, and matching is exact; bundle-enable decision recorded; config.json
      either enforced or removed as policy, with stale entries pruned.

## Track 3 — Capability claims the code does not implement

- [ ] Agent-reach overclaim: `agent_reach_service.py:50-92` builds in-memory envelopes with
      `ok=True` / `{"status": "executed"}` without fetching or executing anything — no HTTP,
      no browser, no CDP anywhere in the plugin or its engine script — while the plugin
      description advertises "stealth CloakBrowser CDP sessions". Either implement the fetch
      path or rewrite the description/skill to say envelope-building only, so an agent calling
      `reach_read` stops believing it extracted content it never fetched. Separately, audit
      `execute_sandboxed_cli` (service ~line 198), which runs an `"agent-reach"` binary from
      PATH with caller-supplied args — an unvetted external dependency and PATH-hijack surface.
      (Credit where due: URL/param credential scrubbing at `:57,81,97-99` is genuinely
      implemented — keep it.)
- [ ] Triad-forge "verification" is a no-op: `triad_pipeline.py:628` runs a hardcoded
      `sys.exit(0)` command and reports "All verification test commands passed successfully".
      Replace it with real verification (or rename the stage to what it actually does) so the
      forge report stops asserting false assurance. The forge otherwise only writes vault items
      and runs no repo-derived commands — confirm that stays true.
- [ ] R bridge nested execution: the subprocess/untrusted R plugin spawns R subprocesses
      itself (`r_editor_service.py:141`) outside the harness sandbox. Document the nesting or
      route it through the sandbox transport.
- [ ] Verify: no tool reports success for work it did not do; the `agent-reach` PATH binary
      call is removed, pinned, or documented with its risk; no forge report claims a
      verification suite that did not run, and the forge still runs no repo-derived commands;
      nested execution is documented or routed.

## Track 4 — Vault data integrity, second round

Track 2 of the last round fixed `status` only. The writer is still minimal, and the data
still has seams.

- [ ] Forge items still miss 4 fields: the 12 triad-forge items lack `category`, `created_at`,
      `retrieval_count`, and `edges` on disk (verified for all 12). `KnowledgeItemRecord`
      rejects them outright when constructed directly from disk (sync's healing normalizes
      them, but disk remains the broken source of truth and any future direct-load path
      silently loses 12 items). Extend the writer payload (`triad_pipeline.py`,
      `commit_vault_kis`) with `category` (or an explicit default) and `created_at`, and
      backfill the 12 on disk the same way `status` was backfilled. Note the writer's
      `meta_payload` also carries no `retrieval_count`/`edges` — decide whether those belong
      in the payload or stay sync-derived, and record the decision.
- [ ] Windows absolute path edges: 34 stored `references_code` targets are absolute paths
      from one dev machine (`D:/GitHub/cloned/...`, `d:/GitHub/projects/Brain Harness/...`),
      ~18% of all edges, non-portable and leaking local layout. Normalize them to repo-relative
      paths (or drop the machine-specific prefix). **Dependency:** "at the next backfill" only
      reaches disk after Track 5 item 1 makes backfill write to `metadata.json`. Otherwise, do
      a one-off direct disk rewrite and record it as such.
- [ ] Telemetry boundary: retrieval/outcome calls write `retrieval_count`,
      `last_retrieved_at`, `success_count` directly into `metadata.json`
      (`vault_retrieval.py:147-167`), including from the `:memory:` fallback, with failures
      debug-logged only. A clean tree and a used harness are therefore mutually exclusive, and
      the Nov 3 commit baking in its own run's telemetry was not an anomaly — it is what the
      system does on every run. Either document one paragraph stating this is intended, or
      decide to separate telemetry from `metadata.json` (decide together with Track 5's
      authority decision). Also fix the adjacent inconsistency: the fallback branches at
      `:150` and `:166` do unguarded `json.loads` on `metadata.json`, so a corrupt file
      crashes `record_knowledge_retrieval`/`record_knowledge_outcome` outright while the main
      path degrades silently.
- [ ] `_date_source` latent pollution: present in 0 files on disk and undocumented anywhere,
      but `vault_export.py:58-59` merges `model_extra` into exports and
      `vault_operations.py:103` injects `_date_source` at sync — so the next full export WILL
      write it (plus `distilled_learning`) into every `metadata.json`. Decide: document it as
      intended metadata, or keep sync-injected keys out of exports.
- [ ] Sync silent case: vault directories without a `metadata.json` are skipped with a bare
      `continue` (`vault_operations.py:87-90`) and no record, while per-item exceptions are now
      warned and exposed. Add a warning there to close the last silent case.
- [ ] Tag vocabulary: 1,253 distinct tags across 301 items, mostly single-use; the mega-tag cap
      (0.15) correctly excludes exactly the same two tags as ever (`endogenous_memory` 78,
      `self_reflection` 66). Not a defect — but if derivation coverage is ever meant to grow,
      tag canonicalization is the open seam. Record whether it is in or out of scope.
- [ ] Verify: all 12 forge items construct as records directly from disk; the
      `retrieval_count`/`edges` payload decision is recorded; zero stored edges point at
      absolute machine paths **on disk**; telemetry behavior is documented or separated, and a
      corrupt `metadata.json` no longer crashes the fallback branches; a full export does not
      write undocumented sync-injected keys; a metadata-less vault directory produces a
      warning; tag scope is recorded.

## Track 5 — Storage authority: one source of truth

- [ ] Three stores that only sometimes agree: `sync_knowledge_vault` is disk→KV only (never
      deletes KV items removed from disk, so stale items persist), and it calls
      `backfill_edges_mechanically` then `save_knowledge_item(ki)` WITHOUT `vault_dir`
      (`vault_operations.py:142`), so backfilled edges land in KV but are never written back
      to `metadata.json`. Edge-table sync (`vault_sqlite_graph.py:35-60`) covers edges only,
      never counts/status. Meanwhile nearly every UI/MCP/CLI knowledge request constructs a
      throwaway `:memory:` store and re-syncs from disk, while the persistent
      `~/.harness/storage.db` is written only by `knowledge sync` and read by nothing else.
      Decide the single authority (disk is the de-facto one today), then: write backfill edges
      to disk, prune stale KV items on sync, and stop the throwaway-store pattern or document
      why it exists. (Unblocks Track 4's edge normalization.)
- [ ] Export/backfill silent failures: `vault_export.py:53-56` turns a corrupt
      `metadata.json` into `{}` with no log and writes the file back (loss limited to
      disk-only keys, but silent); `vault_backfill.py:117-118` swallows per-item parse errors
      with `except Exception: pass`, losing `became_skill`/`became_plugin`/`references_code`
      edges with no log, counter, or trace in returned counts (a direct Rule 32 violation,
      which requires at least `logger.debug` in batch loops). Give both the sync-style
      treatment: log, count, expose, and fail under `--strict`. (Single home for this item;
      0840 also repeated it in Track 9.)
- [ ] `IsnadClaim` silent rebuild: `services/storage/models.py:105-107` rebuilds an invalid
      claim dict as `IsnadClaim(assertion=str(c))`, turning garbage provenance into a
      plausible-looking claim. Reject or quarantine invalid claims instead of laundering them.
- [ ] Event-bus replay visibility: `events/bus/persistence.py:90,120` skips corrupt JSONL
      lines with no counter/log during replay (append-only preserved — visibility gap, not
      loss). Add a counter/log. Same treatment for `services/storage/sqlite.py:48,64,113`,
      where `JSONDecodeError` returns the raw string where callers expect parsed data.
- [ ] Verify: the authority decision is recorded; a backfilled edge is visible on disk after
      sync; a disk-deleted item does not persist in KV; the throwaway-store pattern is gone or
      documented; export/backfill failures are logged, counted, and fail under `--strict`;
      invalid claims are not silently rebuilt; corrupt event-bus lines and SQLite JSON decode
      failures are counted/logged.

## Track 6 — Docs regeneration (stop hand-patching the reference)

Hand patching is what produced the current state: the last round fixed one row and broke two
others by copying the plan's wrong lists. Regenerate from code instead. **Sequencing:** build
the drift gates first. Run the final regeneration after Track 8's delete-or-mount decisions.

- [ ] Regenerate `docs/reference/cli.md` from the CLI: 6 groups have no section at all
      (`antigravity`, `config`, `gate`, `gemini-vercel`, `gradio`, `tau`) and 6 groups are
      documented with essentially fictional subcommands (`redteam`: docs `fuzz|audit|report`,
      real `scan|techniques|status`; `trajectory`, `facet`, `icm`, `rol`, `temp` — same
      pattern, near-total inversions). Partial gaps exist in 12 more groups (`creator`,
      `data`, `datasets`, `eval`, `network-forensics`, `plugin`, `pre-commit-security`,
      `skills`, `uncertainty`, `validation-loop`, and others — full list in the sweep).
      Also fix the backwards alias sections (`model-router`→`router`,
      `calibrator`→`calibrate`, `self-eval`→`eval` are registered under alias names with the
      canonical name demoted). Add a drift test that regenerates-or-diffs cli.md against the
      real CLI groups so this cannot recur.
- [ ] Fix `docs/reference/integrated-toolkits.md` against code, ALL rows (not just REA/dock):
      REA commands → `inspect|list|providers|decompile|callgraph|signatures|devices|diff|learn|learned`;
      dock commands → `inspect|link|list|tools|run`; network-forensics commands are entirely
      wrong (listed `dissect|scan|filter|eval|summary`, real
      `traceroute|scan-ports|decode-flags|cleartext|diagnose-7layer|subnet|brief` — zero
      overlap); skills key is `service.skill_knowledge_graph` (not `service.skill_graph`)
      and `get|match|export` do not exist as subcommands; okf's `status` is really `show`.
      Define the isolation column (seam vs plugin execution — `rea`, `gev`, `memory`, `wiki`
      say `in_process` while their plugins run `subprocess`) or split it. Add a CONTENT drift
      gate asserting service keys and subcommand lists against the real CLI groups — the
      links-only test let two consecutive wrong versions through. (Command lists above are
      sweep findings. The executor must re-derive them from the live CLI, not copy them.)
- [ ] Two-plans conflict, residue *(updated: the archive move is done in `9041790`; both
      0406 and 0715 now sit in `plan archive/`)*. Still open: the archived docs still
      contradict each other and carry errors with no banner (skills 103 vs 104; REA list
      direction; Track 5 holes dropped in 0715; Track 7 weakened in 0715; panel "annotate,
      don't tick" softened and then ticked). Add a superseded/errata banner to 0406 and 0715,
      or fix the 0715 errors at the source (104→103, REA/dock lists). Untick-or-evidence the
      REA runtime checks (0715 plan:300-301, no recorded Windows baseline anywhere) and the
      REA panel item (no dashboard view/link exists). Untick-or-evidence the 0715 Track 6
      "rather than heuristic string substring matches" box (`joint_query.py:117` still matches
      `sk_clean in target`; fix lives in Track 10b). Archived plans are currently unlinked
      orphans (nothing references `plan archive/` at all) — add one index line from the root
      README or accept that they are browse-only. Archive this plan's 0840 predecessor the
      same way.
- [ ] Fix the remaining stale counts and gate them: `plugins/README.md:15` "135 Plugins"
      (actual 138+1), `.agents/skills/README.md:3` "95" plus its D1–D4 diagram summing to 50
      (actual 103), `USER_MANUAL.md:80` "282 Verified Knowledge Items" (actual 301),
      `README.md:7` badge "2820+" (technically-true lower bound, stale figure — refresh or
      drop it). Extend the README count gate beyond root README (which is now gated and
      correct at 138/103) so the next plugin push cannot reopen these. Also state the category
      rule once: root README says "10 architectural categories" (excludes external) while
      plugins README says "11 Domain Plugin Categories" (includes external) — both defensible,
      neither rule stated.
- [ ] One canonical visual brief: `docs/reference/knowledge-graph-visual-brief.md` (119 lines)
      and `.harness/graph/visual_brief.md` (99 lines) are near-duplicates that ALREADY diverged
      in the commit that created them (mega-tag note + cluster breakdown only in the docs
      copy). Pick one canonical copy and delete or redirect the other before the next
      regeneration widens the split. Decide the graph-artifact steady state at the same time:
      the committed GEXF/Cypher/brief are accurate today (417 nodes / 188 edges verified) but
      will silently rot on the next vault change with no regeneration step in the repo, and
      docs point at `outputs/` while artifacts live in `.harness/graph/` — either remove the
      `.gitignore:57` `!.harness/graph/` exception and regenerate on demand, or add one
      documented regen command writing there, and make docs and artifacts agree on the path.
- [ ] Verify: cli.md diffs clean against the real CLI (gate in CI); every toolkit row's key
      and commands resolve against code (content gate in CI); archived plans carry banners or
      corrected errors, and the three named 0715 ticks are evidenced or unticked; all gated
      counts match disk, including plugins/skills READMEs and USER_MANUAL; the category rule
      is stated once; one visual brief; graph artifacts and docs agree on one path and one
      regen story.

## Track 7 — CI and dependencies (including the unanswered age question)

- [ ] CI never builds or tests the frontend: `.github/workflows/ci.yml` has only `lint` and
      `test` jobs — no Node setup, no `npm ci`, no `vite build`, no `oxlint` — while pip
      installs silently serve the embedded fallback (`ui/server/app.py:66-80`) when
      `frontend/dist` is unbuilt. Add a frontend job (build + lint; tests do not exist yet —
      `package.json` scripts are dev/build/lint/preview only — so note the zero-test state
      rather than inventing coverage).
- [ ] CI ignores `uv.lock`: the test job runs `pip install -e ".[dev]"`, resolving newest
      allowed versions, while `uv.lock` (101 packages, regenerated Nov 2) is never consulted —
      so a green CI run does not prove the locked set works. Either install from the lock in
      CI or document why the lock is advisory only. (Lockfiles themselves match their
      manifests — the drift is CI-vs-lock, not lock-vs-manifest. AGENTS.md Quick Start says
      `uv pip install`, CI uses pip — reconcile the two install paths or record the parity
      as untested.)
- [ ] Python 3.10 floor untested: `requires-python = ">=3.10"` but CI runs 3.11 everywhere +
      3.12 on Ubuntu only. Code looks 3.10-compatible (no 3.11+-only syntax found; `tomllib`
      use has a `tomli` fallback; ruff/mypy targets agree on 3.10) — but no job proves it.
      Add a 3.10 CI job or raise the floor to the tested version, with a reason.
- [ ] Baseline first (new, prerequisite for the next two items): run `ruff format --check .`,
      `mypy` with the committed config, and the suite with `--cov`. Record the counts (files
      that would reformat, mypy errors, coverage % for kernel + plugin system). Base the
      enforce-or-downgrade decisions below on those numbers. A ratchet (no new violations,
      fail-under = current) is an acceptable smallest fix.
- [ ] Coverage measured, never enforced: CI runs `--cov` with no `--cov-fail-under`, no
      upload, no gate, while AGENTS.md says "aim for ≥80% on kernel and plugin system". Decide:
      enforce a floor or downgrade the aim to a report.
- [ ] Lint gate is narrow: ruff selects only `E9` + `F`, CI runs only `ruff check .` — not
      `ruff format --check .` (which AGENTS.md prescribes) and mypy is configured
      (`disallow_untyped_defs = true`) but never invoked in CI. Add format + type checks to CI
      or record why they stay local-only.
- [ ] Slow-marker and gate shape: zero `@pytest.mark.slow` uses exist, so CI's `-m "not slow"`
      exclusion is vacuous, while `tests/test_neural_network_from_scratch.py:119-123` runs a
      subprocess training script marked `@pytest.mark.unit` inside the 60-second "Fast Unit
      Tests" gate. Marker census: 833 `unit`, 27 `integration`, ~2,000 unmarked (unmarked run
      only in gate 2). Fix the marking (slow test marked slow, or the marker removed from CI)
      and record which gate is the full suite.
- [ ] Distillation step can fail the build: the "Continuous Knowledge Distillation" step runs
      `harness reflect` on every main push with no `continue-on-error`, so a reflector failure
      marks CI red even when all tests pass. Decide: `continue-on-error`, or keep it failing
      and say so.
- [ ] Dependency age — the question this plan does NOT pretend to answer: the sweeps
      deliberately did not verify "latest" versions from memory or the web, so no dep is
      claimed outdated here. Do the live check as a track item: compare the locked set
      (pydantic, structlog, httpx, fastapi, pytest, and the exact pins `ruff==0.11.0`,
      `mypy==1.15.0`) against current releases, then bump where safe and record the result.
      Separately, decide the small cleanups that need no version data: add a `wasm` extra or a
      doc note for the `wasmtime` import in kernel code (`sandbox/wasm.py:61,90`, in neither
      pyproject nor lockfile); remove or document the vestigial `docker` extra (declared and
      locked at 7.2.0, SDK never imported — `container.py` shells out to CLI binaries);
      pin or document the 14 floating plugin `requirements.txt` files (e.g. bare `structlog`
      in `rea_native`) relative to the lock; add `.github/dependabot.yml` if dep-update
      automation as code is wanted (PRs #1/#2 merged implies settings-level enablement that
      cannot be verified from disk). Adding a `wasm` extra is a new declared dependency, so it
      needs the user's approval under the guardrail. A doc note does not.
- [ ] Verify: a frontend job exists in CI; CI installs from the lock (or the advisory-only
      decision is recorded) and the uv/pip install-path decision is recorded; a 3.10 job
      exists or the floor moved; baselines recorded; coverage enforced or the aim downgraded;
      format + type checks run (or local-only is recorded); the slow marker means something
      and the full-suite gate is named; the distillation-step decision is recorded; the live
      version check produced a bump-or-keep record; wasm/docker/requirements/dependabot each
      decided.

## Track 8 — Dedup and dead code (decide, then delete or wire)

- [ ] `disable_all_plugins` duplication: lifecycle layer (`kernel/lifecycle/manager/batch.py:119`)
      returns `dict[str, bool]` in reverse dependency order with no `keep_core`; runtime layer
      (`kernel/runtime/plugins.py:70`) returns `list[str]` in insertion order and silently
      skips core services under `keep_core=True`. Callers split (CLI/UI use runtime; lifecycle
      only via shutdown `unload_all`). Unify: runtime delegates to lifecycle with a
      `keep_core` filter. (The `enable_all` pair is a legitimate thin adapter — leave it.)
- [ ] `CommandRegistry` has no production caller: `commands/__init__.py:189` + auto-registered
      ~30 dotted handlers, called only by tests. Either wire a real consumer (MCP/introspection)
      or delete it — a second command surface drifting from the Click surface.
- [ ] REA router unmounted: `ui/server/routes/rea.py` (providers/tools/inspect) is imported in
      `ui/server/app.py:18` but never `include_router`'d (`:47-53` mounts plugins, creator,
      sessions, swarm, skills, knowledge only) — dashboard calls to `/api/rea/*` 404. Mount it
      (one line) or delete the module. Note this is distinct from the missing React panel.
- [ ] Catalog phantoms: `plugins/catalog.py:214-227` indexes directories with no manifest (and
      manifest parse failures at `:210-213`) under the directory name, while the loader has no
      equivalent entries — so catalog counts, `/api/catalog`, and the MCP catalog can disagree
      with what actually loads. Stop indexing phantoms or mark them explicitly unloadable.
- [ ] Manifest unknown-key policy: `PluginManifest` has no `extra` config, so unknown keys are
      silently dropped — 6 manifests carry `source_repo`/`verified_commit`/`isnad_lineage`
      provenance that vanishes on load, and 1 carries `execution_mode` + a `tools` list that
      is never mounted (tools mount only from `entrypoints`). Either preserve unknown keys
      (and surface provenance) or reject them loudly.
- [ ] *(The "two `trusted` flags" item moved to Track 0. It is a trust defect, not dedup.)*
- [ ] Phantom entrypoint names: `differential_facet_verifier` advertises `facet_compare` /
      `facet_claim_absence` but `main.py` implements `validate_absence_claim` /
      `compare_observations`; same pattern in `reconstruction_obligation_ledger`. Not a runtime
      break (trusted in-process plugins load the class directly; entrypoints mount only via
      `ToolMountMixin`, which neither calls) — but `harness tool list` will never show them.
      Rename manifest entries to the real method names or add mount calls.
- [ ] Unreachable commands and orphan routes: `rol`'s `obligation_group` (`add`,
      `transition`) is defined but never mounted in `cli.py` — mount or delete. UI route
      orphans (no view calls them in React or the static fallback, which is what actually
      serves today since `frontend/dist/` is not in the repo): `/api/catalog`,
      `/api/creator/validate`, `/api/creator/archetypes`, `/api/projection/status`,
      `/api/sessions/{id}`, `/api/events`, `/api/swarm/status`, `/api/swarm/runs/{id}`,
      `/api/swarm/runs/{id}/mermaid`, `/api/skills/{skill_name}/topology`. Prune them or
      document them as API-only. Check the reverse drift too: the static fallback's fetch list
      lacks routes React uses (`/api/creator/validate`, `/api/creator/archetypes`,
      `/api/skills/clusters/mermaid`, `/api/sessions/{id}/export`). Note the two lists overlap
      on `/api/creator/validate` and `/api/creator/archetypes`. They are orphans only for the
      fallback, not for React, so re-check before pruning. Also decide MCP HTTP reachability:
      `HarnessMCPServer.handle_http_post` has no caller outside the MCP package; the only CLI
      surface is stdio.
- [ ] Verify: one `disable_all` implementation; `CommandRegistry` wired or gone; `/api/rea/*`
      answers or the module is gone; catalog counts equal loader counts; unknown manifest keys
      are preserved or rejected; facet/ROL entrypoints appear in `harness tool list`;
      `rol obligation_group` mounted or gone; no orphan route is undocumented and the fallback
      covers React's routes (or the gap is recorded); MCP HTTP decision recorded. Then trigger
      Track 6's final regeneration.

## Track 9 — Test hygiene

- [ ] In-process instantiation of subprocess/untrusted plugins in tests: 174 test files import
      `plugins.*` directly (294 references); 110 references are to plugins whose manifests are
      NOT `in_process`. The unexamined exceptions (untrusted + subprocess run in the test
      process with no justification): `cellcog`, `mantis_sandbox_verifier`,
      `youtube_transcript_fetcher`. The ~100 trusted+subprocess references are within the
      letter of Rule 5 but bypass the manifest's explicit subprocess choice, so sandbox-path
      bugs in those plugins are invisible to their own tests. Justify each exception in a
      comment or route those tests through the sandbox transport.
- [ ] AgentWikis suite unconditionally skipped on Linux/CI: 5 files skip on a Windows-only
      `D:\AgentWikis` path (67 test functions), so the entire AgentWikis surface is untested
      outside one Windows machine. Relocate the corpus, gate the suite to Windows CI, or
      record that it is Windows-only by design.
- [ ] Conditional skips that pass on a fresh checkout (`test_service_knowledge_lifecycle.py:198`,
      `test_service_vault_graph_derivation.py:274`, `test_service_storage_vault_integrity.py:31`
      "live vault not found", plus a symlink skip) — confirm they are intentional and not
      masking a broken fixture. Also refresh the stale docstring at
      `test_service_vault_graph_derivation.py:271` ("282 on-disk vault items", vault is 301;
      assertion `>= 282` still passes — cosmetic).
- [ ] Triage the silent-skip tail (export/backfill itself lives in Track 5 item 2): 107
      single-`pass` handlers, 11 `continue`, 54 single `return` across ~60 files (0 bare
      `except:` — the one grep hit is a comment citing Rule 32). Named items beyond Track 5:
      `vault_taxonomy.py:173-174` (mtime fallback to `now()`, source recorded — acceptable,
      keep), import-time UTF-8 reconfigure `except: pass` in `services/dock.py:37-38` and
      `commands/dock.py:32-33` (best-effort, keep). The plugin loader's warn-on-skip pattern
      (`loader.py:164-184,283-284,375-376,405-406`) is the model to copy.
- [ ] Verify: every untrusted/subprocess test import is justified or routed (the 3 named
      exceptions first); AgentWikis has a stated home; each conditional skip is confirmed
      intentional and the 282 docstring is refreshed; the silent-skip tail is triaged
      (each handler: log, keep-with-reason, or reraise).

## Track 10 — Live proofs (need a human or a live run) **[NW: do not substitute a test or a brief]**

These items have now been "closed" twice by substitutes. They stay open until the literal
thing happens.

- [ ] Gephi, actually opened: load `.harness/graph/knowledge_graph.gexf` in Gephi (and
      GraphML in Cytoscape/yEd) and record a render report — what rendered, layout used,
      clusters observed, screenshot or log. A Louvain analysis, a styling guide, and a
      headless schema validation are all previous substitutes and do not count.
- [ ] Live lifecycle evaluation: 3 items are currently demotion-eligible (ratio 0.00:
      `ki_20260824_repo_03`, `ki_20260830_django_01`, `ki_20260831_em3_02`) and 0 are
      promotion-eligible (best ratio 0.71, bar 0.75) — all still `ACTIVE`. Run a real
      `evaluate_vault_lifecycle` against the live vault and record the transitions (or the
      reason none fired). A `tmp_path` proof test does not count.
- [ ] Hyperframes loader run + disabled-entry confirmation: load the fixed manifest through
      the manifest path and record it; confirm the committed `config.json` disabled entry for
      `hyperframes_renderer` is intentional (see Track 2 — if config.json is not policy, this
      entry is moot).
- [ ] Skill-graph numbers live-verified: the 0715 plan's "138 Skill Graph nodes / 72
      categories / 1,036 edges (reproduced live by `harness skills graph`)" was never
      reproduced in a verifiable run, and 138 nodes vs 103 standalone skill dirs rests on an
      unconfirmed plugin-skills scan. Run it and record the output, or correct the numbers.
- [ ] Verify: each item above has a dated, human- or live-run-produced record — not a test,
      not a brief, not a styling guide.

## Track 10b — Carried-over code fixes **[NW: do not drop or reword away; close with code + tests]**

Moved out of Track 10 because these close with code changes and tests, not live runs.
That is a fix to 0840's banner, not a downgrade. The dock leftovers were dropped once
before (0715), so they keep [NW].

- [ ] 7-tuple label: the Cypher exporter sets exactly seven IsnadClaim properties
      (`assertion`, `status`, `confidence`, `evidence_type`, `source`, `verified`,
      `verified_by`) — none temporal. Either add the temporal property or rename the
      "7-tuple temporal evidence" label to match what is emitted.
- [ ] Joint-query substring match: `joint_query.py:117` (`or sk_clean in target`) counts a
      `became_skill`/`distilled_from`/`implements` edge to any target CONTAINING the skill
      name as a match, weaker than the exact/`.agents/skills/` prefix/`endswith` checks before
      it. The 0715 Track 6 box claiming substring matching was replaced is ticked but not
      true (see Track 6). Tighten it if exactness matters, or record why substring matching
      is intended.
- [ ] Dock leftovers from Nov 1 (not in the 0715 Track 5, still open): the 5 remaining test
      holes (env scrubbing, step-failure-stops, `expected_output` mismatch, boundary refusal
      through `run()`, generic fallback via CLI `inspect`); the traversal claim limited to cwd
      confinement / boundary tokens (the doc sentence still overclaims for arguments); the
      explicit "approval means approving shell" sentence; `service.dock` IoC registration
      (ServiceKey exists, nothing provides it).
- [ ] Verify: the Cypher label matches the emitted properties; the joint-query matcher is
      exact, or the substring rationale is written in `joint_query.py`; each of the 5 dock
      test holes has a named passing test; both dock doc sentences are corrected; something
      provides `service.dock`.

## Track 11 — Deferred by design (no action unless a limitation is hit)

- Dock Track 7 items (strict schema rejection, policy engine, central registry, multi-harness
  spec, MCP exposure, conditional/loop/matrix steps, manifest versioning) stay unbuilt.
- Memory cluster stays partitioned behind the router (decision recorded Nov 1); DAG trio stays
  layered by lifecycle phase; graph engines stay dual (in-memory BFS vs SQLite CTE, user
  selects); joint-query direct reads stay IF the 0715 plan's Track 6 rationale record (the
  "document the rationale in `joint_query.py`" box) actually exists in code and the
  substring item in Track 10b is decided.
- The user's rule stands throughout: simplicity first, no upfront over-engineering. If any
  deferred item gets built without a documented limitation, that is scope drift and should be
  called out in the next review round.

## §12 — Verification backlog (things this plan asserts that a reviewer should re-check)

- [ ] Live version check results for the locked set (Track 7) — the one finding class in this
      plan that no sweep verified from disk.
- [ ] Whether default agent runs include the git service (Track 1) — mechanism verified,
      default exposure unverified. **Do this first; it gates Track 1's urgency.**
- [ ] Whether `.env` files in mined temp stores can be ingested into vault items (unexamined
      in the sweeps — grep found no `.env` special-casing in miners/ingestion). Security
      class: if yes, it becomes a Track 0 item.
- [ ] Whether the fetcher token source is env or config (redacted in one sweep's read —
      unconfirmed, not a finding).
- [ ] Plugin-bundled skills count behind the 138-node skill-graph claim (Track 10).
- [ ] The 37 manifest entrypoints that never override class-level `trusted` (Track 0, moved
      from Track 8) — silent defaults, not explicit contradictions; confirm none is meant to
      be untrusted.
- [ ] Whether the 0715 Track 6 "document the rationale in `joint_query.py`" box is backed by
      an actual rationale comment in code (Track 11 depends on it).

