# Brain Harness — Plugin Integration Plan

**Created:** 2026-10-31 09:25 EDT
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `c1ec34e` (main)
**Purpose:** One big plan for the plugin-integration program: take the capable-but-buried plugins found in the 2026-10-31 survey and give them the same treatment as REA — examined, integrated, expanded — instead of fixing them one plan at a time. Same pattern as the previous plans: small, checkable items to pick through one at a time. This plan covers many plugins, so its tracks are ordered deliberately: correct the record first, then the biggest surfaces, then the learning core, then the consolidations, then the trust question, then the second tier.
**Baseline (measured 2026-10-31, local clone):** 134 plugin manifests, 625 entrypoints total. Surface check (CLI group, skill, UI route) on the largest plugins found the REA pattern repeatedly: rich toolsets with no surface beyond manifest auto-mount into the agent's `ToolRegistry` on enable plus the generic `harness tool list/enable/disable` CLI. The integrated examples to copy: `network_forensics` (real `harness network-forensics` CLI), `icm_architect` (CLI group + skill), and the three miners (brain-artifact, conversation-trajectory, temp-artifact — all with skills).
**What this plan is not:** It does not rewrite the plugins it covers, rename their tools, or change their isolation. It adds facades, CLI groups, skills, docs, and cross-links on top — the REA pattern. It adds no new third-party dependencies without explicit user approval, and it does not touch the knowledge-graph plan work currently in progress elsewhere.

## Guiding principles

- **Integrate before building new.** If a capability already exists somewhere in the repo, the plan wires it up before proposing a new implementation. Track 0 exists because this rule caught a live case.
- **Facade, not rewrite.** Each toolkit gets a thin front door (CLI group + routing + skill) delegating to existing engines, per repo Rule 49's thin-wrapper pattern. A facade that re-implements the engine is a bug.
- **Surface means three things.** A plugin counts as integrated when it has: a CLI group a human can run, a skill so the agent reaches for it on its own, and a docs page saying when to use it. ToolRegistry auto-mount alone is not integration — it is availability without discoverability.
- **Learning-core plugins get priority after the big surfaces.** Tools the agent should use constantly (memory, provenance, forgetting) matter more than tools used occasionally, even when their entrypoint counts are smaller.
- **Consolidation is a decision, not a default.** For the memory cluster and DAG trio, the plan first decides (documented, with reasons) whether multiplicity is intentional layering or accidental duplication — and only then consolidates or documents. The Pyrit history says: check before consolidating, never assume a stub.
- **Untrusted stays untrusted.** External/vendored content keeps subprocess isolation and gets a trust review before any deeper integration. Integration never upgrades trust silently.

## Track 0 — Correct the record (cheapest items first)

- [ ] Amend the REA toolkit plan (`REA toolkit plan-2026-10-31-0849-EDT.md`, Track 5): differential comparison already exists as `differential_facet_verifier` (`facet_compare`, `facet_claim_absence`) plus `reconstruction_obligation_ledger` (`rol_ingest_evidence`, `rol_verify_ledger`), both from 2026-10-17. Change Track 5 from "build `rea diff`" to "integrate the two existing plugins behind the REA facade" — same user-visible outcome, no duplicate implementation.
- [ ] Verify the two plugins' actual behavior before integrating: run `facet_compare` and `facet_claim_absence` on a fixture pair (or read their tests) and confirm they implement the three-valued outcomes (unchanged / changed / unobserved) and the absence gate from the REA vault items. If they do not, record the gap instead of assuming it.
- [ ] Record the correction in the REA plan's verification notes with the date, so the next reader sees why Track 5 changed shape.

## Track 1 — gods_eye_view toolkit (biggest surface, zero surface)

- [ ] Survey first: read `plugins/geospatial_and_osint/gods_eye_view/` fully — all 24 entrypoints, README, config budgets, external data sources (live flights, AIS vessels, earthquakes, FIRMS hotspots, satellite passes, streetview, globe rendering, weather). Record which tools need network access and which are offline-capable; the network-dependent ones need an explicit note, since the harness's sandbox story is air-gap-first for untrusted code.
- [ ] Facade + CLI group following the REA pattern: `harness gev` (or `harness gods-eye`) with subcommands grouped by domain (live feeds, spatial analysis, rendering), not one flat list of 24. A flat list is the current discoverability problem restated.
- [ ] Skill `.agents/skills/gods-eye-view/` (SKILL.md + CARD.md per Rule 37): when to reach for planetary/OSINT tools, which feed for which question, rate-limit and freshness caveats for live feeds (a flight position is stale the moment it is read — the skill must say so), and anti-patterns (treating a snapshot as live, querying military-awareness data without stating the source's limits).
- [ ] Docs page `docs/how-to/use-gods-eye-view.md` with the command list, one worked example per domain, and the network/freshness caveats.
- [ ] Decide and record: does the globe-rendering output belong in the control room as a view (like the knowledge-graph view), or stay CLI/HTML-export only? Do not build the view until this decision is recorded.

## Track 2 — Security and forensics toolkit unification

- [ ] `mantis_security_review` facade + CLI: `harness mantis` wrapping the 10-tool pipeline (history scan, directory summary, plan review, research audit, dedupe ladder, review gate, critic filter, exploit chaining, risk calibration, report generation) as stages a human can run stepwise, not just as one pipeline — stepwise matters because review gates are decision points, not batch jobs.
- [ ] Skill for mantis: when a security review is warranted, how the stages compose, what the review gate means (and does not mean — a gate passing is not a proof of security), and anti-patterns (reviewing without history, calibrating risk on a single sample).
- [ ] Cross-link the security cluster: document how mantis (review), REA (dissection), `differential_facet_verifier` (comparison), `reconstruction_obligation_ledger` (evidence closure), and `network_forensics` (already CLI-integrated: `harness network-forensics`) compose into one workflow — dissect → review → compare → close evidence. One docs page, `docs/how-to/security-forensics-workflow.md`, with the composition, not five separate pages pretending the others don't exist.
- [ ] Verify `network_forensics`' CLI pattern and copy it (command structure, service resolution, output format) for the mantis CLI instead of inventing a second CLI style inside one cluster.

## Track 3 — Skill graph + knowledge graph unification

- [ ] Surface `skill_knowledge_graph` (9 tools: select skills for a task, cluster the graph, emergent capabilities, cross-cluster bridges, catalog indexing, router queries, chains, topology, visual export) with a CLI group and a skill of its own — the engine that routes skills currently has no route to itself.
- [ ] Joint-query design, recorded before building: what a unified query means across the two graphs — the KI graph (knowledge items, from the 2026-10-31 graph work) and the skill graph (skill cards, router, chains). Minimum viable unification: one command that, for a topic, returns matching KIs *and* matching skills with their relationship (which skills were distilled from which KIs, via `became_skill` lineage where it exists).
- [ ] Implement the joint query (CLI command first; UI second only if the knowledge-graph view work makes it cheap) reusing both existing query services — no third graph implementation.
- [ ] Docs: one page explaining the two graphs, how they relate, and which query to use for which question. The current state (two graphs, two vocabularies, no map between them) is the problem this track removes.

## Track 4 — Learning-core surface (memory, provenance, forgetting)

- [ ] `context_type_system` (8 tools: provenance, type-channel separation, origin ledger, token budgeting, prompt assembly) — CLI group + skill. This is the harness's answer to "where did this context come from and can I trust it," which deserves to be callable, not just importable.
- [ ] `memory_decay_engine` (8 tools: Ebbinghaus forgetting curves, working-set ranking, session persistence, benchmarks) — CLI group + skill. Forgetting is a feature with parameters (curves, multipliers); the skill must document how to tune them and what "forgotten" means operationally (demoted, not deleted — verify this against the implementation before writing it).
- [ ] Wire both into the agent's working loop story in docs: provenance (context_type_system) → retrieval (vault) → forgetting (memory_decay_engine) → lifecycle (knowledge lifecycle command) as one lifecycle narrative, with a diagram or a sequenced list, not four separate tool references.
- [ ] Verify the forgetting semantics empirically before documenting: does decay demote, archive, or delete? The docs must state the true behavior; the Oct 29 analysis did not establish it.

## Track 5 — Consolidations (decide first, then act)

- [ ] Memory cluster decision: `okf_memory`, `memgraphrag`, `graphiti_memory` — still three standalone services. Read all three, write the decision (unify behind one memory service, keep three with documented partitions, or deprecate one/two) with reasons tied to actual overlap, not names. If unify: facade first, migration second, deletion last and only with explicit approval. If keep: document the partitions in one place (which memory question goes to which service).
- [ ] DAG trio decision: `services/agent_graph.py`, `SwarmDAG` (`agent/swarm/models.py`), session tree/exporter — still three models. Decide whether this is intentional layering (if so, document the layers and which model owns what) or duplication (if so, consolidate behind one model with adapters). The Oct 29 analysis left this undocumented; this track closes it either way.
- [ ] Record both decisions in the docs where the next reader will find them (not just in this plan file): the memory page and the agent-graph page, respectively.

## Track 6 — External bundle: trust and counting

- [ ] Trust review for `mattpocock-skills` (`plugins/external/`, 35 entrypoints, marked untrusted, subprocess-isolated): what it contains (ask-matt router + skill flows for grilling, spec/ticket flows, TDD, code review, domain modelling), what it can touch from subprocess isolation, and whether anything in it warrants concern beyond the isolation already applied. Record the review outcome.
- [ ] Counting rule, decided and recorded: do vendored external bundles count in the repo's plugin totals? The totals currently wobble (134 manifests vs 135 dirs) partly because of this bundle's nested metadata. Pick a rule (count harness plugins only; count bundles separately and say so) and apply it to the READMEs.
- [ ] `ask-matt` routing decision: integrate the router (route a task description to a skill/flow) as a documented entrypoint, or leave the bundle as reference-only. Do not half-integrate it (mounted but undocumented, or documented but unmounted).

## Track 7 — Second tier (survey, then surface where justified)

- [ ] `wiki_compiler` (8 tools): survey what it compiles and for whom; add CLI/skill only if a real user path exists (compiled wiki output consumed by whom?).
- [ ] `paperless_ngx` (7 tools): survey; same bar — surface only with a real consumer.
- [ ] `filesystem_git` (7 tools): survey; note the overlap question with the harness's own git checkpoint/transaction machinery (is this duplicative, or the user-facing side of it?).
- [ ] `critic_loop` (7 tools): survey; note the relationship to `mantis`'s critic filter and the evaluator-critic plugin (three critic-ish things — check for overlap before surfacing any of them further).
- [ ] For each second-tier plugin, the outcome is either a facade/CLI/skill (same pattern) or a recorded "leave as is, because…" — a survey that concludes "no surface needed" is a completed item, not a skipped one.

## Track 8 — Docs, counts, and gates

- [ ] Docs index update: one page listing every integrated toolkit (REA, gods_eye_view, mantis/security cluster, skill+knowledge graphs, learning core) with its commands and its skill, so the integrations are discoverable from one place.
- [ ] Update `docs/reference/cli.md` with every new command group from this plan (or generate from the catalog if that follow-up landed).
- [ ] Fix the stale README counts found in the survey (skills "50" vs 95 actual; plugins "134" vs 135 dirs) under the Track 6 counting rule, and exclude nested `.claude-plugin` metadata from future counts.
- [ ] Extend the drift gate pattern (from the knowledge-graph work) to the new CLI groups: documented commands ⊆ live registry for each new group, so the next integration cannot silently drift.
- [ ] Update this plan file's progress notes as tracks land, with commit references — the paperwork gap the last round flagged (RESOLVED markers without hashes).

## Suggested order (the pick queue)

1. Track 0 (correct the record) — cheapest, and it stops the REA plan from misleading the next reader.
2. Track 1 (gods_eye_view) — biggest buried surface, same proven pattern as REA.
3. Track 2 (security cluster) — mantis facade + the composition doc; the facet-verifier integration from Track 0 pays off here.
4. Track 3 (graph unification) — connects directly to the knowledge-graph work just completed, while it is still fresh.
5. Track 4 (learning core) — the tools the agent should use constantly, surfaced at last.
6. Track 5 (consolidations) — decisions first; these are the only tracks where "decide to keep" is a complete outcome.
7. Track 6 (external bundle) — trust review + counting rule; small, but it removes a standing ambiguity.
8. Track 7 (second tier) — survey-driven; several items may legitimately conclude "leave as is."
9. Track 8 (docs, counts, gates) — throughout, with a final pass at the end.

## §11 Verification backlog (not verified during planning)

- [ ] Verify: `differential_facet_verifier`'s actual three-valued behavior on a fixture pair (Track 0 assumes the description holds; behavior proof is still open).
- [ ] Verify: `memory_decay_engine`'s forgetting semantics (demote vs archive vs delete) before Track 4 documents it.
- [ ] Verify: `gods_eye_view`'s network dependencies per tool (which tools need live network, which are offline) — the survey recorded the tool list, not the network profile.
- [ ] Verify: whether `filesystem_git` duplicates or complements the harness's git transaction machinery (Track 7 overlap question).
- [ ] Verify: the critic overlap (`critic_loop` vs mantis critic filter vs evaluator-critic) before surfacing any of them further.
- [ ] Verify: `mattpocock-skills`' runtime behavior beyond its manifest (35 entrypoints claimed; what actually runs under subprocess isolation).
