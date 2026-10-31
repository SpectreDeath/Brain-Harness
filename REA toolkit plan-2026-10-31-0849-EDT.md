# Brain Harness — REA Toolkit Plan

**Created:** 2026-10-31 08:49 EDT
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `fe76eb0` (main)
**Purpose:** Turn the REA reverse-engineering plugins from four separate toolboxes into one easy-to-access, integrated toolkit — and close the loop the harness is built for: a harness that learns from what you feed it. Same pattern as the previous plans: small, checkable items to pick through one at a time, with evidence cited per item.
**Baseline (measured 2026-10-31, local clone):** REA is the `morluto/rea` bridge as 4 plugins, 28 tools total, all subprocess-isolated with singletons and service keys:
- `plugin.rea_javascript` (`plugins/data_engineering/rea_javascript`, 5 tools): Wakaru bundle deobfuscation, Electron ASAR inspection, passive CDP observation, .NET inspection, HAR analysis.
- `plugin.rea_managed_runtime` (`plugins/security_and_forensics/rea_managed_runtime`, 5 tools): PE/CLI headers, P/Invoke boundaries, Unity IL2CPP metadata, GGUF/safetensors headers, CPython bytecode.
- `plugin.rea_mobile_firmware` (`plugins/security_and_forensics/rea_mobile_firmware`, 11 tools): APK inspection, JADX decompilation, class search, reference tracing, 5 ADB tools, Binwalk carving, Unblob extraction.
- `plugin.rea_native` (`plugins/security_and_forensics/rea_native`, 7 tools): Ghidra/Hopper/IDA batch decompile, call graphs, ELF layout, WASM, EVM interfaces, Ghidra annotation, load-image verification.
**How the tools are reachable today (verified, not assumed):** The loader takes the manifest path first — a directory with `plugin.json` loads via `_load_manifest_plugin` and returns before the Python-module scan (`loader.py:157-160`, and the module scan skips manifest-processed dirs) — so REA plugins load as `SandboxedPlugin`, which auto-mounts every manifest entrypoint into the agent's `ToolRegistry` on enable (`sandboxed.py:190-209`). Once enabled, a ReAct agent can call them, and the generic `harness tool list/enable/disable` CLI plus `runtime.tools.invoke('plugin.rea_native.rea_native_call_graph', …)` work. What does NOT exist: no `harness rea` command group, no REA skill, no UI panel, no MCP-specific surfacing, and inconsistent tool naming across the four plugins (`rea_javascript_*` vs `rea_*` vs `rea_native_*` vs `rea_mobile_*`). To use the tools today you must already know they exist and which of the four houses the one you want.
**Design philosophy already in the vault (use it, don't reinvent it):** `ki-rea-facet-availability-semantics` and `ki-rea-reconstruction-obligations` document REA's own rules — facet availability is three-valued (available / absent / unknown; never conflate "not observed" with "zero"), absence is an affirmative claim requiring complete traversal proof (`status == complete` AND `truncated == false` AND `omitted_count == 0`), and differential outcomes are three-valued (unchanged / changed / unobserved). REA tool outputs already are semantic signatures: EVM dispatch selectors, IPC channels, P/Invoke declarations, class and method references, call graphs, API surfaces, type hierarchies. Nothing today distills those signatures into vault knowledge.
**What this plan is not:** It does not rewrite the four plugins, rename their tools, or change their subprocess isolation (Rule 5). It adds a facade, a CLI group, a skill, and a learn loop on top. It adds no new third-party dependencies without explicit user approval (external binaries like Ghidra/JADX are environment tools, not Python dependencies, and are handled as optional providers, not requirements).

## Guiding decisions (settle in Track 0)

- **Facade, not rewrite.** The facade routes and unifies; the four plugins keep doing the work. Per repo Rule 49, elevation to the micro-kernel means a thin wrapper delegating to underlying engines plus a typed `ServiceKey[T]` and a plugin singleton — not a fifth re-implementation of decompilation.
- **Availability is part of every result.** Every facade result carries per-facet availability (available / absent / unknown, with a reason when unknown). A missing provider (no Ghidra installed, no device attached) yields `unknown`, never an empty result presented as a finding.
- **One result envelope.** All facade outputs share one shape: artifact identity (path, hashes, detected type), facets with availability, semantic signatures extracted, provider used, and provenance (tool + version where known). CLI, skill, UI, and learn-loop all consume this envelope; no per-surface re-shaping of tool output.
- **Offline by default.** Inspection never contacts recorded servers, never executes the target, and never phones home. HAR/CDP paths are already passive; keep every new path to that standard. Any future networked step is opt-in and named as such.
- **Learned signatures are vault citizens.** The learn loop writes through the existing reflection save path (which already wires `propose_links`), so learned signatures get edges, lifecycle, and retrieval like any other knowledge item — not a sidecar store.

## Track 0 — Foundations

- [ ] Artifact-type routing table: detection rules (magic bytes, extensions, container markers) mapping artifact kinds to plugin + tool — ELF → `rea_native`, PE/CLI → `rea_managed_runtime` (and `rea_javascript_dotnet_inspect` where it overlaps; record which wins and why), APK → `rea_mobile_firmware`, JS bundle → `rea_javascript`, WASM → `rea_native`, GGUF/safetensors → `rea_managed_runtime`, HAR → `rea_javascript`, firmware blob → `rea_mobile_firmware` (Binwalk/Unblob). Overlaps decided explicitly, not by accident.
- [ ] Facet availability model as shared types: `FacetAvailability` (available / absent / unknown + reason), the absence gate (complete + untruncated + zero omitted), and the three-valued differential outcome — implemented once in `src/harness/services/rea/` (or the facade module) and reused by CLI, skill guidance, and learn loop.
- [ ] Facade placement decision, recorded: thin `service.rea` wrapper + CLI group delegating to the four existing services (Rule 49 pattern), vs a fifth plugin. Default recommendation: service + CLI group, no new plugin dir, with a typed `ServiceKey` and a `resolve_rea_service` seam matching the `resolve_icm_architect_service` precedent.
- [ ] Runtime-path verification: confirm at runtime (not just by code read) which code executes a manifest-mounted REA tool call — SandboxedPlugin executor path vs the `main.py` service classes — and record the finding, since the plugins carry both a class and a manifest.
- [ ] Canonical naming alias scheme (design only; implementation in Track 7): `rea.*` aliases over existing names, with the alias table as data, not renames — existing tool names keep working.

## Track 1 — `harness rea` CLI group (Rule 10 headless seams)

- [ ] `harness rea inspect <artifact>`: auto-route by the Track 0 table, print the unified envelope (facets + signatures + availability), exit non-zero on undetectable type with a message naming what was tried.
- [ ] `harness rea list [--artifact-type TYPE]`: list tools grouped by artifact kind, not by plugin — the view a user actually wants when holding a file.
- [ ] `harness rea decompile <artifact> --symbols … [--provider ghidra|hopper|ida]`: thin wrapper over `rea_native_batch_decompile` with provider-missing → `unknown` facet, not a crash.
- [ ] `harness rea callgraph <artifact> --entry SYMBOL [--depth N] [--direction caller|callee]`: wrapper over `rea_native_call_graph`.
- [ ] `harness rea signatures <artifact>`: extract only the semantic-signature layer (selectors, IPC channels, P/Invoke decls, API surfaces, class/method refs, imports/exports) in the envelope format — the command the learn loop and humans both reuse.
- [ ] `harness rea devices`: ADB surface (`adb_list_devices`, `adb_list_packages`) for the mobile path, with no-device → clean `unknown`/empty handling, not a stack trace.
- [ ] Every command honors `--json` for scripting and prints the availability block by default in human output (a result without availability is a bug, per the guiding decisions).

## Track 2 — Unified facade service

- [ ] `service.rea` facade: `dissect(artifact)` returning the unified envelope, dispatching via the Track 0 table; `signatures(artifact)` returning the signature layer only; `providers()` reporting which external binaries are present (Ghidra, JADX, Binwalk, Unblob, adb, WABT) with versions where detectable.
- [ ] Provider-missing behavior specified and tested: missing provider → facet `unknown` with reason "provider not installed", never a fabricated empty result and never a hard failure of the whole dissection.
- [ ] Result envelope as typed models (pydantic, per repo code style): artifact identity + hashes, facets with availability, signatures, provider, provenance. The CLI (Track 1) renders this envelope; it does not re-derive it.
- [ ] Budgets honored from each plugin's `config.default.yaml` (timeouts, symbol caps, byte caps) through the facade, not bypassed — the facade passes budgets down, and reports when a budget truncated a result (which flips the relevant facet to `unknown` or partial per the absence gate, never to `absent`).

## Track 3 — REA skill

- [ ] `.agents/skills/rea-reverse-engineering/` skill (SKILL.md + CARD.md per Rule 37: single-pipe borders, exact `SKILL: <name>` header tag, `## Anti-Patterns` with `- **Name** — Description` items, `## Mandatory Invariants Checklist` with at least one `- [ ]` item).
- [ ] Selection logic: which tool for which artifact kind (the Track 0 table, in prose the agent can follow), including the overlap decisions (PE/CLI routing, JS vs managed .NET inspection).
- [ ] Facet availability semantics in the skill: the three-valued model, the absence gate, and the rule that a truncated run quarantines absence claims as `unresolved`.
- [ ] Operational guidance: budgets, subprocess isolation expectations, offline rule, what to do when a provider is missing (report `unknown`, try the next provider, never fabricate).
- [ ] Anti-patterns: executing the target, trusting a single provider's output as ground truth, treating an empty facet as absence, decompiling without a symbol budget, contacting recorded servers from a HAR.
- [ ] Skill validation suite (frontmatter 100–350 chars with action verbs and a "Do not use for…" boundary, per Rule 44) and registration in the skill catalog so the router can surface it.

## Track 4 — Learn loop (`rea learn`)

- [ ] `harness rea learn <artifact> [--dry-run]`: dissect, extract signatures, distill into vault knowledge items through the existing reflection save path (so `propose_links` edges, lifecycle, and retrieval apply automatically). Dry-run prints what would be learned without writing.
- [ ] Signature-node schema: what becomes a node (function signature, IPC channel set, ABI surface, API surface, class/method reference cluster) vs what stays an attribute of the artifact node; edges from signature nodes back to the source artifact node and to the provider.
- [ ] Dedupe: identical signatures from re-dissection do not duplicate nodes — match on signature hash + artifact identity, update provenance instead of duplicating.
- [ ] Retrieval check: after learning, a vault query for the signature's domain returns the learned item (the loop is only closed if the learned thing is retrievable — same standard as the knowledge-graph work).
- [ ] Learned-item review: learned items are marked derived with provider provenance, so a human can audit what the harness "learned" vs what it was told; a `rea learned` listing command (or `knowledge query` tag filter — decide and record) surfaces them.
- [ ] Feed the existing graph: learned signature nodes participate in the knowledge-graph exports (they are vault items like any other), so Gephi views and CLI graph queries show the dissection-derived subgraph.

## Track 5 — Differential comparison (`rea diff`)

- [ ] `harness rea diff <artifact> --providers ghidra,ida` (or any two available providers): run both, normalize facets, report per facet unchanged / changed / unobserved, with availability stated per side — the three-valued model from the vault items, implemented as a tool for the first time.
- [ ] Normalization rules recorded: what counts as identical across providers (normalized names, addresses excluded or mapped, comment text excluded) vs divergence; unobserved on either side blocks an `unchanged` verdict for that facet.
- [ ] Provider-missing handling: a requested provider that is not installed removes that side cleanly (reported, not failed) and the diff degrades to a single-provider report, labeled as such.
- [ ] Output in the unified envelope plus a facet table; `--json` for scripting. A diff that hides which side lacked a facet is a bug.

## Track 6 — Control-room panel + MCP

- [ ] Control-room panel (after confirming the frontend/dist story the knowledge-graph track resolved): submit an artifact path, pick a dissection, render the envelope — facets with availability badges, signature lists, provider used. Reuse the knowledge-graph view patterns; do not add a frontend dependency without approval.
- [ ] MCP surfacing decision, recorded: verify whether the MCP server exposes `ToolRegistry` tools generically (it holds a registry reference; generic exposure was not verified during planning). If generic: document that REA tools are MCP-available once enabled, and curate the set. If not: expose a curated `rea.*` toolset explicitly.
- [ ] Static-dashboard parity decision: whether the pip-served static fallback gets a link to the REA view (as the knowledge view did) or the panel is React-only — record the choice, don't leave it implicit.

## Track 7 — Naming aliases, docs, gates

- [ ] Canonical `rea.*` alias layer over existing tool names (data-driven table, both names callable, old names never broken). Document the alias table in one place.
- [ ] Docs page `docs/how-to/use-rea-toolkit.md`: the facade, the CLI commands, the skill, the learn loop, the availability model, provider setup (which external binaries, how the facade detects them).
- [ ] Update the four plugin READMEs to point at the facade as the front door (keeping their tool tables as reference).
- [ ] Update `docs/reference/cli.md` with the `rea` group (or generate from the catalog if that follow-up landed).
- [ ] Drift gate: a test asserting documented `rea` commands ⊆ live registry and alias table ⊆ mounted tool names, so docs and toolkit cannot silently diverge (same pattern as the knowledge-graph drift test).

## Track 8 — Hardening

- [ ] Fixture-based tests per artifact kind (tiny ELF, PE, APK, bundle, WASM, HAR fixtures — checked in or generated, not real malware, not real user binaries) covering routing, availability on missing providers, and envelope shape.
- [ ] Provider-missing test matrix: every facade path tested with each external binary absent, asserting `unknown` facets and no crashes.
- [ ] Offline test: dissection of a HAR/bundle fixture with network disabled asserting zero outbound contact (same standard as the sandbox network tests).
- [ ] Budget tests: symbol caps, byte caps, and timeouts honored through the facade (a truncated run flips facets per the absence gate — assert that, not just that it returns).
- [ ] Trust-boundary review: untrusted artifacts stay subprocess-isolated end to end (facade never loads target code in-process); the learn loop never writes target content into vault items beyond signatures and metadata (no embedded binaries, no credentials from dissected artifacts).

## Suggested order (the pick queue)

1. Track 0 (foundations) — routing table, availability model, placement decision, runtime-path verification. Everything else hangs off these.
2. Tracks 1 + 2 together (CLI group + facade service) — one door for humans and agents; the biggest accessibility win in a single build.
3. Track 3 (skill) — makes the agent reach for the tools on its own, with the facet semantics baked in.
4. Track 4 (learn loop) — turns REA from a toolbox into part of the harness's memory; this is the "learns from what you feed it" payoff.
5. Track 5 (differential comparison) — the one genuinely new capability, built on the availability model.
6. Track 7 (aliases + docs + gates) — locks the naming and documentation in place.
7. Track 6 (panel + MCP) — surfaces, after the core is solid.
8. Track 8 (hardening) — tests and boundaries throughout, with a final pass once the surfaces exist.

## §11 Verification backlog (not verified during planning)

- [ ] Verify: at runtime, which code executes a manifest-mounted REA tool call (SandboxedPlugin executor path vs `main.py` service classes) — code read says manifest path wins, runtime proof is still open.
- [ ] Verify: whether the MCP server exposes `ToolRegistry` tools generically over `tools/list` — the server holds a registry reference, but generic exposure was not confirmed.
- [ ] Verify: external binary availability in the environments that matter (dev machine, CI) for Ghidra, JADX, Binwalk, Unblob, adb, WABT — provider-missing behavior is designed, but the actual matrix is unmeasured.
- [ ] Verify: `harness tool` CLI behavior with REA plugins enabled end to end (list shows all 28, invoke round-trips) — the mount mechanism is code-verified, the live CLI path was not run during planning.
- [ ] Verify: whether any existing skill already covers reverse-engineering selection logic (no `rea*` skill dir exists, but a broader forensics skill may overlap — check before writing the new skill).
