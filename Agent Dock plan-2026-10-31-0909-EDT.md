# Brain Harness — Agent Dock Plan

**Created:** 2026-10-31 09:09 EDT
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `901996e` (main)
**Purpose:** Turn the "Agent Dock" sketch into a buildable plan. Same pattern as the previous plans: small, checkable items to pick through one at a time. Deliberately kept simpler than the previous plans, because the idea itself says simplicity is the hallmark — this plan has an explicit deferred list (Track 7) for everything that only gets built if a real limitation demands it.
**The idea, as sketched 2026-10-31:** Inspired by the Muse GitHub App connection, a dock is a place in a repository that lets an agent link to it. Workstation dock, not boat dock: one connection and the agent gains power, monitors, network, peripherals — it plugs in and works from inside the repo. A dock is distinct from a bridge: a bridge translates between two different worlds (the harness's Em-Cubed and Memtext bridges do this); a dock is a port *in* the repository that says "an agent plugs in here." Once docked, the agent clones/links the repo and drives it — uses the repository to do stuff.
**Status of the idea:** Early sketch, not yet designed in detail. Nothing in this plan is settled except the direction. Track 0 exists to confirm or overturn the working assumptions below; a Track 0 result that overturns one is a successful outcome, not a failure.
**What exists today that the dock builds on (verified 2026-10-31):** The GitHub App connector (repo access + push from an agent); local clone workflow (the harness is already developed by cloning and reading repos locally); `plugin.json` manifests declaring what a plugin offers; `SandboxedPlugin` auto-mounting manifest entrypoints into the agent's `ToolRegistry` on enable; the generic `harness tool list/enable/disable` CLI; `AGENTS.md` as repo-side prose guidance for agents. The dock is the repo-level equivalent of the plugin manifest: one declared place to plug in, for a whole repository instead of one plugin.

## Guiding principles (the plan's constitution — do not drift from these without a recorded reason)

- **Simplicity first.** Build the smallest dock that works. Add nothing — no schema police, no policy engine, no registry — until a real limitation points at it. Track 7 holds everything deferred; it is not a backlog to burn through, it is a list of things to *not* build yet.
- **Repo declares, harness falls back (proposed, to confirm in Track 0).** The repo declares its dock; the harness provides a generic dock (clone, read, run, push) for repos that declare none. A declared dock overrides the generic one.
- **Declaration is data, not logic.** The dock manifest is YAML data — tools, entrypoints, permissions, procedures — not Prolog-style rules and not code. It can be read without being run. Any logic-style reasoning (policy, inference) lives underneath as an interpreter, not in the file. (This was genuinely ambiguous wording during the sketch; the data reading is the settled one.)
- **YAML because procedures live there.** GitHub Actions, Ansible, CI configs — procedural instructions as data is YAML's home turf. A dock manifest holds both static declarations and procedures, and humans can read it. JSON is valid YAML, so machine tooling can emit JSON and humans can write YAML.
- **Read without running.** Nothing about a dock may require executing untrusted code just to learn what the dock offers. The manifest is parsed, never executed, to discover the dock.
- **Dock ≠ bridge ≠ plugin.** A bridge translates between worlds. A plugin is a capability inside the harness. A dock is a repo-level port an agent plugs into. Keep the three concepts separate in docs and code; conflating them is how the design gets muddy.
- **No new dependencies without explicit approval** (repo guardrail). The dock v0 must be buildable from what the harness already has.

## Track 0 — Settle the design (confirm or overturn)

- [ ] Confirm the repo-declares direction: repo declares its dock, harness provides a generic fallback. If this is overturned (harness-provides instead), record why and re-scope Tracks 1–2 before building anything.
- [ ] Decide the manifest location and name: candidates are repo-root `dock.yaml` (most discoverable) vs `.harness/dock.yaml` (namespaced, consistent with the vault location). Pick one; the other becomes a documented non-option, not a second supported location.
- [ ] Define "drive" concretely: the operations a docked agent may perform, at minimum — read repo content, run declared procedures, write changes, push. State which of these are in v0 and which are later, and what "drive" explicitly excludes (e.g., destructive repo operations follow the existing no-destructive-action boundary and need explicit direction + confirmation).
- [ ] Define the dock's relationship to existing repo declarations: what belongs in `dock.yaml` vs `plugin.json` (per-plugin) vs `AGENTS.md` (prose guidance). Write one paragraph each; if two files would say the same thing, one of them is wrong.
- [ ] Define the permission model at sketch level: who declares what the dock exposes (repo owner, via the manifest), who approves a docking (the person connecting the agent, per declaration, not blanket), and what a dock may never declare (destructive operations, credential access, execution of untrusted code to discover the dock).
- [ ] Decide the first transport: GitHub App connection (the inspiration — already working) vs local clone path (already working) vs both. Default recommendation: both, since both already exist; the dock layer sits above transport, not inside it.
- [ ] Write the one-paragraph dock definition for the docs, and check it against the sketch: workstation dock, repo-declared port, agent drives from inside. If the paragraph needs a bridge or a plugin to make sense, the design has drifted.

## Track 1 — Minimal dock manifest spec (v0)

- [ ] Define the v0 field set, and only the v0 field set: `name`, `description`, `entrypoints` (named procedures with steps), `tools` (what the agent may call, by reference to existing harness tools or repo scripts), `permissions` (read / run / write / push, as simple flags), `boundaries` (paths or operations explicitly out of scope). Anything not on this list is Track 7 until a limitation demands it.
- [ ] Procedures as data: a procedure is an ordered list of steps (command, working directory, expected outputs) in the manifest, executed by a runner — the GitHub Actions model, kept to sequential steps only in v0 (no conditionals, no loops, no matrix).
- [ ] Write an example manifest for brain-harness itself: dock name, the procedures a visiting agent would actually use (read the plan docs, run tests, check the vault), and boundaries (no destructive git operations, no credential access). The example must be real enough to dock against in Track 4, not a toy.
- [ ] Manifest parsing: a loader that reads the manifest file, parses YAML, and returns the dock description — without executing anything in the repo. Malformed YAML yields a clear error naming the file and the problem, not a stack trace.
- [ ] Loose validation only (per the simplicity rule): required fields present, types roughly right, unknown fields ignored with a warning — not rejected. Strict schema validation is Track 7, on evidence of need.

## Track 2 — Docking client in the harness

- [ ] Dock discovery: on clone or connect, look for the manifest at the Track 0 location; if present, report the dock (name, entrypoints, tools, permissions, boundaries); if absent, fall back to the generic dock silently but visibly (the agent should know it is on the generic dock, not a declared one).
- [ ] `harness dock link <repo>`: link an agent to a repo's dock — resolve transport (GitHub App or local clone), read the manifest, print what the dock offers and its boundaries, and ask for approval before driving (the approval is per declaration, shown to the user, not blanket).
- [ ] `harness dock list`: show linked docks and, per dock, whether it is declared or generic.
- [ ] `harness dock run <dock> <procedure>`: execute a declared procedure's steps through the runner, in the repo, with output streamed and boundaries enforced (a step outside the declared boundaries refuses, with a message naming the boundary).
- [ ] `harness dock tools <dock>`: list the tools the dock exposes, by reference, so an agent (or user) can see what driving this repo actually means before doing it.
- [ ] Generic dock definition, written down: exactly what an undeclared repo offers (clone, read, run tests if a standard runner exists, write, push) and its default boundaries (same no-destructive-operation rule as everywhere else).

## Track 3 — Permissions and trust

- [ ] Boundary enforcement in the runner: a declared procedure step that touches a boundary-listed path or operation is refused before execution, not cleaned up after.
- [ ] Approval record: linking a dock records what was approved (the declaration, as shown at link time), so a later change to the manifest re-prompts instead of silently widening access. A manifest change without re-approval is a bug.
- [ ] Untrusted-dock handling: a dock from a repo the user does not control is treated as untrusted content — parsed, never executed for discovery; its procedures run subprocess-isolated (Rule 5's spirit: untrusted code does not run in-process).
- [ ] Credential rule: a dock manifest may never declare credential access, and the docking client never hands credentials to a docked procedure. State this in the docs and enforce it in the runner (a step requesting credentials fails).
- [ ] Write the trust paragraph for the docs: who declares, who approves, what is never allowed, what happens when the manifest changes. One paragraph, plain language.

## Track 4 — Dogfood: dock brain-harness itself

- [ ] Add a real `dock.yaml` to brain-harness (the Track 1 example, promoted from example to actual), declaring its genuine entrypoints and boundaries.
- [ ] Demonstrate the loop: a fresh agent links to brain-harness's dock via the GitHub App path, lists its tools and procedures, and runs one declared procedure (e.g., run the knowledge-graph stats or the test suite) through `harness dock run`.
- [ ] Demonstrate the fallback: link to a repo with no manifest and confirm the generic dock is reported as generic, with generic boundaries, and still works.
- [ ] Record what broke or confused during dogfooding, and fold exactly those items into Tracks 1–3 as fixes — dogfooding that produces no changes means it wasn't really exercised.

## Track 5 — Procedures as YAML, done properly (still simple)

- [ ] Step model v0, locked: sequential steps, each with a command, a working directory, and an optional expected-output note. No conditionals, no loops, no templating in v0 — a procedure that needs those is two procedures, or it waits for a limitation to justify the complexity.
- [ ] Step output handling: stdout/stderr streamed, exit codes checked, a failed step stops the procedure by default (no silent continuation), and the failure names the step.
- [ ] Procedure composition: a procedure may call another declared procedure by name (the only composition in v0). No imports, no includes, no remote procedure references.
- [ ] Document three real procedures for brain-harness in its dock manifest (not toy examples): one read-only (e.g., vault stats), one verification (e.g., run a test subset), one write-path (e.g., a docs update flow) — each actually runnable through `harness dock run`.

## Track 6 — Docs and light gates

- [ ] Docs page `docs/how-to/agent-dock.md`: what a dock is (workstation metaphor, dock ≠ bridge ≠ plugin), the manifest format with the brain-harness example, the link/run/list commands, the trust paragraph from Track 3, and the generic dock.
- [ ] Update the repo's concept docs (or AGENTS.md pointer) so a newcomer meets the dock in the same place they meet plugins and bridges, with the three concepts distinguished in one paragraph.
- [ ] Light gate only: a test asserting the brain-harness example manifest parses and its declared procedures exist as runnable steps (no drift between manifest and reality for the dogfood repo). A repo-wide drift gate for arbitrary docks is Track 7, on evidence of need.

## Track 7 — Deferred: only if a real limitation demands it (do NOT build these preemptively)

- [ ] Strict schema validation for manifests (build when malformed docks cause a real failure, not before).
- [ ] Policy engine / rule evaluation for permissions (build when simple permission flags prove insufficient for a real dock, not before).
- [ ] Dock registry or discovery service (build when there are enough docks that finding them is a real problem, not before).
- [ ] Multi-harness dock spec / cross-harness portability testing (build when a second harness wants to dock, not before).
- [ ] MCP exposure of docked tools (build when an outside agent needs dock access over MCP, not before).
- [ ] Conditional/loop/matrix procedure steps (build when a real procedure cannot be expressed sequentially, not before).
- [ ] Dock versioning and migration (build when a manifest format change breaks a real dock, not before).

## Suggested order (the pick queue)

1. Track 0 (settle the design) — confirm or overturn the working assumptions before anything is built on them.
2. Track 1 (minimal manifest spec) — the smallest declarative surface that could work.
3. Track 2 (docking client) — link, list, run, tools; generic fallback included.
4. Track 3 (permissions and trust) — boundaries enforced, approvals recorded, credentials excluded.
5. Track 4 (dogfood brain-harness itself) — the loop proved on the home repo, fixes folded back.
6. Track 5 (procedures done properly) — still simple, but real procedures, not toys.
7. Track 6 (docs and light gates) — the idea written down where the next person will find it.
8. Track 7 (deferred) — only on evidence of a limitation. This track is complete when it stays empty.

## §11 Verification backlog (not verified during planning)

- [ ] Verify: whether the GitHub App transport or the local-clone transport is the better first dogfood path (both exist; the plan proposes both, but the dogfood run in Track 4 will decide which one actually gets exercised first).
- [ ] Verify: manifest location conventions — repo-root `dock.yaml` vs `.harness/dock.yaml` — against how the repo already treats root-level vs `.harness/` files (root holds plan docs; `.harness/` holds vault and config; the choice should follow the repo's own grain, decided in Track 0).
- [ ] Verify: whether any existing concept in the repo already covers part of the dock (a bridge scaffold, a plugin manifest, a skill) closely enough that the dock should reuse it rather than add a new file — check before Track 1 finalizes the field set.
- [ ] Verify: the exact approval UX for `harness dock link` against the runtime's approval-card patterns (the plan assumes a per-declaration approval card; the mechanism needs confirming at build time).
