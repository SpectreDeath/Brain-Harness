# Harness spawning research — 2026-11-13 EST

## Summary (read this first)

**Recommended architecture, in one paragraph:** Do not build a new kernel or a new kind of runtime. A "little harness" is a **component tree** (`Tree` — a dict of relative path → file text) plus a **child `ServiceContext`** that inherits the parent's service registrations, plus a **session + DAG node + token budget** so the parent can observe and retire it. That is the whole first build: a `spawn` service (a plugin, not a kernel change) that takes a spawn spec, materializes a tree, validates it with the existing `validate()`, creates a child context, runs a ReAct loop in it, and disposes it when the task ends. Everything it needs already exists — the child-context seam, the tree model with inheritance built in, the trial/validation gates, the session and DAG supervision, and the budget ledgers. The only genuinely new pieces are the spawn spec format, the spawn service itself, and a real `HarnessProposer` (the protocol exists; only a scripted demo implements it). Everything else is wiring.

**The three biggest design decisions:**

1. **A child is a context + a tree, not a second kernel.** `ServiceContext.child()` with parent fallback already exists, and the tree model already has inheritance ("omitted paths are inherited, never deleted"). A second `HarnessRuntime` in-process is possible but buys little and shares module-level singletons; a subprocess-isolated runtime is the right call only when a child must be untrusted or long-lived. Start with the child context.
2. **"Create a harness from a description" is a proposer over the tree, not a new compiler.** The `HarnessProposer` protocol (an agentic session that edits a harness directory) already exists, and `refine demo` already produces a harness directory on disk. The missing piece is a live proposer implementation — everything downstream of it (validation, trial identity, evidence isolation, blind selection, the experience library) is built.
3. **Nothing a child learns merges back silently.** A child writes to its own experience-library partition and drafts vault items; the parent adopts them through an explicit, reviewable step. This mirrors the existing guardrails (no silent LLM in the engine, no silent learning into VERIFIED vault items) and the repo's own history of catching wrong learnings after the fact.

**Terminology flag — read before the rest:** the user called the parent "Brain Harness Prime". **"Prime" is NOT a repo concept.** I grepped the repo — there is no `Prime` class, service, config, or doc concept (only incidental phrases like "primes the agent"). This report treats "Prime" as the user's term for the **top-level/parent harness instance that spawns children**, and every recommendation below uses "parent" in that sense. If the user means something else — a distinct Prime edition, deployment, or role — say so; it is open question #1 below, and it matters for the inheritance design.

## What a harness instance is, concretely in this codebase

A harness is not one thing; it is five things that already have separate, named representations. A spawn design must say which of the five a child gets fresh and which it inherits.

| Piece | Concrete representation | Where |
|---|---|---|
| **Component tree** | `Tree = dict[str, str]`, relative path → file text. "Omitted paths are inherited, never deleted." | `src/harness/services/recursive_harnessing/models.py:13-16` |
| **Editable surface** | `SurfaceSpec`: always-on files + char cap, skill dir, subagent dir, scripts dir, trigger line. `BRAIN_SURFACE` is the brain's own surface (always-on `AGENTS.md`, cap 32,000). | `models.py:19-48` |
| **Kernel / IoC container** | `HarnessRuntime` (context + lifecycle + event bus + loader + plugin dirs) and `ServiceContext` (typed `ServiceKey[T]` registrations, parent-child scoping, isolation realms, dispose stack). | `src/harness/kernel/runtime/coordinator.py:36-71`, `src/harness/kernel/context/core.py` |
| **Plugin set** | Manifests declaring `provides`/`requires`; lifecycle states DISCOVERED → VALIDATED → LOADED → ENABLED; topological enable waves. | `src/harness/kernel/lifecycle/manager/core.py:49-144` |
| **Knowledge scope** | The vault (`.harness/knowledge/`, 322 items at HEAD, dual-file `metadata.json` + `summary.md` per Rule 40) and MemGraphRAG partitions via `save_dir` (default `outputs/default`). | `src/harness/services/memgraphrag.py:54,89,116` |
| **Budgets** | `TokenGovernor` (per-agent token allocation in swarms); `BudgetLedger` (R = 4k rollouts, P = 3k sessions per mode); per-plugin `config.default.yaml` budgets (Rule 44). | `src/harness/agent/swarm/governor.py:9`, `src/harness/services/recursive_harnessing/ledger.py:1-20` |
| **Identity** | Fingerprints of harness dirs/trees; `.refine_complete` markers; trial identity. | `src/harness/services/recursive_harnessing/identity.py` (via `service.py`) |

**The smallest thing that counts as a "little harness":** a `SurfaceSpec` + a `Tree` that passes `validate()` (always-on text present and under cap, skills named in the always-on text, scripts checked, sub-agents gated — `surface.py:170-193`) + a child `ServiceContext` + a ReAct loop running in it. The minimal kernel shape already exists as a factory: `HarnessRuntime.create_diagnostic()` builds a runtime with only storage + session + tools (`factory.py:88-109`). A child that needs less than that — a swarm mini-harness — needs no new kernel at all: a child context + a session is enough (see option A).

## Existing machinery it builds on (with evidence)

### 1. The kernel already supports children — the seam is `child()`, not a new API

- `ServiceContext.child()` returns `ServiceContext(parent=self)` (`core.py:175`). Lookups fall back to the parent: `require`/`has` walk up the hierarchy (`context/lookup.py:25-26, 44-45, 54-55`). A child therefore **inherits every parent registration by default** and overrides only what it provides locally.
- `ServiceContext.isolate(key, realm)` derives a child context with an isolated coeffect realm for one key (`core.py:79-80`; `context/realms.py:29-44`). One key can be isolated while the rest are inherited — exactly the shape a child needs for mutable services (e.g. its own storage or LLM session) while sharing the rest.
- The event bus is inherited by default (`core.py:39-42`: a child takes the parent's bus unless given its own). That is the observation channel: a child's events land on the parent's bus unless the spawn deliberately gives it a separate bus.
- `ServiceContext.dispose()` runs the dispose stack (`core.py:112-113`; Rule 54 requires dispose closures to carry realm/provider metadata so targeted revocation purges them).
- **Doc drift to note:** `docs/reference/kernel.md:25` documents `create_child_context() -> ServiceContext` ("Spawns a child context inheriting parent registrations"). That method **does not exist** in the code — the real method is `child()`. The claim is true in substance, wrong in name. Any spawn design that cites the docs should use `child()` and the drift should be fixed.
- **Unverified:** whether `dispose()` on a parent cascades to child contexts. I did not trace the dispose path into children. The spawn service must either verify this or track live children itself and dispose them on parent stop — do not assume the cascade.

### 2. A second runtime is already constructible — no factory work needed

- `HarnessRuntime.create()` (standard, default plugins), `create_diagnostic()` (minimal: storage + session + tools), `from_config()` (declarative config tree) — `coordinator.py:74-130`, implemented in `factory.py:28-137`.
- `create_runtime_from_config` parses a config into a `HarnessConfigTree` and reconciles the runtime against it (`factory.py:113-137`; `kernel/reconciler.py:34-100` — `HarnessConfigTree`, drift detection, `reconcile()`). A declarative "spawn spec" is therefore a small step from an existing pattern, not a new invention.
- `start()` / `stop()` are already async-context-manager lifecycle: start provides the event bus + dock service, discovers user plugins, reconciles the config tree, enables all plugins in topological order, emits `HARNESS_STARTED`; stop unloads all plugins, disposes the context, emits `HARNESS_STOPPED`, closes the bus (`kernel/runtime/lifecycle_runner.py`).

### 3. The dock is a place to drive, not a live harness — spawning is not docking

- A dock is a declarative `dock.yaml` manifest: permissions, boundaries, tools, entrypoints (`dock.yaml` at repo root). The manifest is **parsed, never executed**.
- `link()` records an approval digest (SHA-256 of the manifest) in `.harness/docks.json` (`services/dock.py:628-657`); `list_docks()` reports approval drift (`:659-697`); `run()` executes declared procedures after an approval gate, a permission gate, and boundary checks (`:709-987`).
- What `run()` actually does is execute shell commands with `shell=True` in a subprocess, with string-pattern command safety (`check_command_safety`), a scrubbed environment, and git rollback on failure. That is procedure execution in a repo — **not a running harness instance**. A dock-linked repo has no kernel, no event bus, no session, no budget.
- What spawning adds that the dock does not: a live kernel/context, a session with a lifecycle, budgets that can be exhausted, supervision via the DAG, and knowledge that can merge back. The dock is still the right *destination* for a durable, human-inspectable harness (materialize the tree as files, link it, drive it via entrypoints) — but it is not a substitute for spawning.

### 4. Recursive harnessing already models "a harness" as an editable tree

- `Tree` + `SurfaceSpec` + `validate()` (above) is the formal model. `BRAIN_SURFACE` shows the shape for the parent itself.
- `DefaultRecursiveRefinerService` exposes `validate_harness`, `new_ledger`, `open_library`, `refine` (Propose-Probe-Compose), and `select` (blind selection) (`service.py:52-106`).
- `ExperienceLibrary` persists per-domain learnings: `add(task_id, tree, why, label, run_id, experience)`, `retain`, `forget`, `tree_of`, `entries` (`library.py:63-147`). This is the merge-back mechanism in waiting: a child can write to its own library partition, and the parent can adopt entries explicitly.
- `BudgetLedger` enforces the R = 4k / P = 3k identity with duplicate-label detection before count checks (`ledger.py:1-20`; Rule 59).
- Evidence isolation is fail-closed (`guards.py` via `service.py:14-50`): depth-bounded chunked scanning for grader verdicts and answer-key leaks.
- **The gap:** `HarnessProposer` is a protocol — "an agentic session that edits `<evidence_root>/harness` in place" (`protocols.py:59-63`) — and the **only implementation is `ScriptedProposer`** in the demo (`demo.py:88-107`), which merges skills from a pool into a harness directory. There is no live proposer. Likewise `harness refine run` does not exist: it was deferred by design in Track 5, recorded at `docs/explanation/recursive-harnessing.md:137` with the reopening trigger "scheduling of automated multi-turn live evaluation benchmark suites within the CI pipeline". The `refine` CLI today is budget / validate / scan / fingerprint / demo (`commands/refine.py:40-102`).
- The demo already shows the full "description → harness directory" loop in miniature: a base tree (`{"AGENTS.md": "Summarize the report. Verify the numbers."}`), a proposer that adds skills, blind selection, and a library entry (`demo.py:122-152`).

### 5. Sub-agents are the closest existing analogue — and they are sessions, not kernels

- `SwarmCoordinator` decomposes an objective into a `SwarmDAG` and executes nodes in topological waves (`agent/swarm/coordinator/core.py:42-163`), with a `TokenGovernor` allocating token budgets per agent (`governor.py:9-35`).
- `AgentSessionManager.create_child_session(parent_session_id, task, ...)` creates and links a child session (`agent/session/manager/creation.py:121-139`); the child is registered in the authoritative Thread DAG (Rule 17) and emits `AGENT_TASK_STARTED` on the event bus. `session_scope()` is the context manager for a full agent execution lifecycle (`creation.py:24-61`).
- **What a sub-agent gets:** a session record, a DAG node, a token allocation, and the parent's kernel and context. **What it does not get:** its own kernel, its own plugin set, its own event bus, or its own knowledge scope. That is precisely the delta spawning adds: a sub-harness is a sub-agent *plus* a bounded kernel surface (its own tree, its own context, optionally its own plugin set and knowledge partition).
- Supervision already exists for this shape: `harness session tree` export (Rule 10 headless seams), `AgentExecutionGraphService` thread states (Open/Closed/Completed/Failed), and token rollups.

### 6. Ingestion turns repos into plugins — the feedstock for spawned harnesses

- `PluginIngestionPipeline.ingest()` resolves a source (GitHub URL, local path, zip, PyPI, OpenAPI spec), inspects it, synthesizes a manifest, applies an isolation override, and converts it into a `HarnessPlugin` ready for lifecycle registration (`ingestion/pipeline.py:75-146`). It also has `trial_run()` and `validate()` (`:178-238`).
- The user is currently having the harness ingest repositories to learn from. Ingested knowledge becomes usable by a spawned harness through three existing channels: (a) the ingested plugin enters the child's plugin set; (b) the distillation seam (Rule 41) turns ingested material into vault items and into skills (`SKILL.md` + `CARD.md`) that enter the child's tree; (c) MemGraphRAG partitions (`save_dir`) scope the knowledge the child can read.
- Rule 18 (domain-partitioned plugin synthesis) constrains this: a monorepo ingestion must be partitioned into single-responsibility plugins, not bundled into one monolith. A spawn spec that pulls in an ingested monorepo as one plugin would violate it.

### 7. Skill assembly and harness evaluation already exist as workflows

- 106 skill directories in `.agents/skills/`; skills are created by **combining different sets of skills into different creation workflows** (not fixed pipelines) — the `crafting-skills` family. A "domain-specific harness" is therefore largely a *selection* problem (which skills, in which order, named in the always-on text) plus a *knowledge* problem (which vault partition) — not a new kind of object.
- `PluginCreator.scaffold / from_functions / from_code / validate / infer_manifest / scaffold_skill` (`creator/creator.py:46-362`) already scaffolds plugins and skills from archetypes. A spawn service should reuse `scaffold`/`scaffold_skill` rather than inventing a second scaffolder (Rule 20, in-place deepening over tool sprawl).
- The `agent-harness-architect` skill already carries a design vocabulary for "what a harness is": 5-part harness architecture, 4-mechanism reliability gate, 4-layer stack (MCP / Harness / Orchestration / Observability-Sandbox), with a `harness architect` CLI (`audit` / `score` / `bet`, `commands/harness_architect.py:107-248`). A spawn spec should be auditable against that vocabulary — it is the repo's own checklist for whether a harness is well-formed.

### 8. Control surface: MCP is the natural protocol for process-isolated children

- `HarnessMCPServer` handles requests, batches, and stdio (`mcp/server/server.py:28-101`); `MCPRegistry` manages resources and prompts (`mcp/server/registry.py:20-162`). Rule 24 requires heavy engines behind stateless MCP servers with JSONSchema validation rather than in-process singletons.
- For in-process children (options A/B below), control is direct: method calls on the child runtime/context plus the shared event bus. For subprocess children (option C), MCP over stdio is the existing, rule-conformant transport. Do not invent a third protocol.

## Design options compared

### What a child inherits vs what is fresh (applies to all options)

The tree model already answers half of this: a child's tree **inherits** every path the parent's tree has and overrides only the paths it defines (`models.py:13-16`). The context model answers the other half: a child context **inherits** every parent service registration and overrides only what it provides locally (`lookup.py:25-26`). So inheritance is not a design problem to solve — it is a declaration problem: the spawn spec must say *which* paths and *which* services the child overrides. Recommended declaration (see "Spawn spec" below).

| | Inherits by default | Fresh per child |
|---|---|---|
| Tree | All parent paths (always-on text, skills, scripts) | Paths the child's tree defines |
| Services | All parent registrations (LLM, tools, storage, skill graph) | Services the child provides (or isolates via a realm) |
| Knowledge | Read access to the parent vault | Its own MemGraphRAG partition (`save_dir`) for writes |
| Budgets | Nothing — budgets are allocated per child | TokenGovernor allocation / ledger, from the parent's budget |
| Events | Parent's bus (observation) | Its own run/session IDs on that bus |
| Identity | Parent's fingerprint lineage | Its own fingerprint + trial ID |

### Option A — Child context, same kernel (recommended first build)

- **How:** `parent_context.child()` → provide/override the child's services (or `isolate()` the mutable ones into realms) → `create_child_session()` → run a ReAct loop in the child context → `complete_session()` / `fail_session()` → `context.dispose()`.
- **Cost:** near-zero startup (no plugin loading, no process spawn); memory is one extra context + one session. Failure is contained by session failure, not by a process boundary — a child that crashes the process crashes the parent.
- **Isolation:** realms per key; the child cannot see services the parent does not provide, but it shares the parent's module-level state. **Concrete risk, verified:** the skill-graph resolver holds module-level mutable globals (`_DEFAULT_REGISTRY`, `_DEFAULT_GRAPH` — `services/skill_graph/service/resolvers.py:24,34`). Two in-process contexts share that state unless the child gets its own registry. Any in-process design must audit module-level singletons before claiming isolation.
- **Best for:** swarm mini-harnesses — ephemeral, task-scoped, budget-limited children that need to start fast and die fast.
- **What it is not:** it is not a separate harness process, and it cannot run a different plugin set from the parent (plugins are enabled on the shared kernel's lifecycle).

### Option B — Second runtime, in-process

- **How:** `HarnessRuntime.create()` (or `create_diagnostic()`) with the child's own `plugin_dirs`, `db_path`, and `builtins`; `start()` / `stop()` lifecycle; optionally share the parent's event bus for observation.
- **Cost:** plugin discovery + load + topological enable on every spawn (mitigated by `lazy_external_plugins`, Rule 7). Memory is a second plugin set. Startup is seconds, not milliseconds.
- **Isolation:** own context, own lifecycle, own plugin set — but the same process, so the same module-singleton caveat as option A, and a child that corrupts shared state can still affect the parent.
- **Best for:** domain-specific harnesses that need a *different plugin set or kernel config* from the parent (e.g. a domain harness that enables only 6 of 142 plugins, or a different LLM). If the only difference is skills + knowledge, option A is enough and B is over-engineering.
- **What it is not:** it is not process isolation. Do not use it for untrusted children.

### Option C — Subprocess-isolated runtime (defer until a limitation fires)

- **How:** spawn a second `harness` process — either as a sandboxed plugin via `SubprocessExecutor` / `VenvExecutor` / `ContainerExecutor` (`plugins/sandbox/`), or as a `harness` CLI process driven over MCP stdio. Control via `HarnessMCPServer`; supervision via the parent's bus (the child emits events to it) and the DAG.
- **Cost:** process spawn + venv staging (lazy staging, Rule 7, exists precisely to avoid cold-start timeouts) + IPC overhead. Strongest isolation: a child cannot crash or corrupt the parent; network and filesystem boundaries are enforceable (Rule 5, Rule 56 loopback preserve, container `--network=none` for complete isolation — the dock's `shell=True` string filtering is *not* a substitute).
- **Best for:** untrusted children (a harness built from an arbitrary description, or from ingested code the parent has not vetted), long-lived children, and children that must survive the parent's restart.
- **What it is not:** it is not cheap. Do not pay this cost for swarm mini-harnesses.

### Option D — Materialized dock-linked repo harness (the durable artifact)

- **How:** the proposer's tree is written to disk as a repo (always-on file + skills + scripts + `dock.yaml`), validated with `validate()`, then `dock link --approve`, and driven via `dock run` entrypoints.
- **Cost:** file I/O plus shell execution. No live kernel at all — the "harness" is data, not a process. The cheapest durable form and the most inspectable: a human can read the whole child.
- **Best for:** "create a harness from a description" as a *deliverable* — a domain harness the user keeps, audits, and reuses — and for anything that must be version-controlled.
- **What it is not:** it is not a running harness. A dock-linked repo cannot supervise itself, enforce budgets while running, or merge knowledge back. It becomes a live harness only when something (option A, B, or C) loads it. Note `refine demo` already produces exactly this artifact (a harness directory on disk) — option D is largely "make the demo's output a first-class, linkable thing".

### Comparison

| | A: child context | B: 2nd runtime, in-process | C: subprocess runtime | D: dock-linked repo |
|---|---|---|---|---|
| Startup | ~0 | seconds (plugin load) | seconds + venv staging | file I/O only |
| Isolation | realms only; shared singletons | own context/lifecycle; shared process | process boundary; strongest | none (data, not a process) |
| Own plugin set | no | yes | yes | n/a (declared in tree) |
| Own knowledge partition | yes (save_dir) | yes | yes | yes (repo vault) |
| Supervision | DAG + session + bus | DAG + session + bus | DAG + bus + MCP | approval digest only |
| Failure blast radius | process | process | child only | n/a |
| Best for | swarm minis | domain harnesses, different plugins | untrusted / long-lived | durable, auditable artifacts |
| Build size | smallest | small | medium | smallest |

## Recommended architecture and sequencing

**Architecture:** a `spawn` service as a **plugin** (Rule 1 — everything is a plugin; Rule 19 — do not mutate `ServiceContext` constructor contracts or kernel signatures). It owns a registry of live children and exposes a typed `ServiceKey`. It does not fork the kernel and does not break the model-import seam.

**The spawn spec** (new, small, pydantic — Rule 12/Rule 43 style, like `HarnessConfigTree`):

```python
# Sketch only — names to be settled in the plan, not asserted here.
class SpawnSpec(BaseModel):
    name: str
    parent: str = "prime"            # see open question 1
    surface: SurfaceSpec             # always-on files, caps, skill/subagent/script dirs
    tree: Tree                       # overrides only; omitted paths inherit from the parent
    plugin_set: list[str] | None = None   # None = parent's set (option A); a list forces option B
    knowledge_partition: str         # MemGraphRAG save_dir for the child's writes
    budgets: ...                     # token cap (TokenGovernor), rollout/session ledger (R/P)
    lifetime: Literal["task", "session", "persistent"]
    isolation: Literal["context", "runtime", "subprocess", "dock"]
    proposer: str | None = None      # which HarnessProposer built the tree, if any
```

Validation before a child runs (all existing gates, composed): `validate(spec.surface, spec.tree)` → a **trial run** — a k=1 deterministic probe task through the child's loop, using the trial-identity + `.refine_complete` markers and the evidence-isolation guards — → only then `start()`. The trial seam is the honest gate: a child that cannot complete a probe task does not get a live session.

**Communication:** in-process children talk to the parent by direct calls + the shared event bus (child events carry the child's run/session ID so the parent can filter). Subprocess children talk over MCP stdio (Rule 24). The parent observes through the Thread DAG + `session tree` export + token rollups — no new observability system.

**Lifecycle (state machine, mirroring the plugin lifecycle):** `SPAWNED → VALIDATED (tree + trial) → RUNNING → COMPLETED | FAILED | RETIRED`, with `dispose()` + `unload` on every terminal transition and a parent-stop rule that retires all live children (verify the dispose cascade first — see §1). Kill conditions, in order: task complete, budget exhausted (governor/ledger fail-closed), error (session failure recorded, context disposed), parent shutdown. **Merge-back is never automatic:** the child writes to its own `ExperienceLibrary` partition and drafts vault items (dual-file, Rule 40); adoption into the parent is an explicit, reviewable step — the same discipline the repo already applies to vault corrections.

**Sequencing (smallest thing first, limitations drive the next step):**

1. **Spawn service + `harness spawn` CLI, option A only.** Child context + session + DAG node + token budget + retire/dispose. No proposer, no second runtime. The acceptance test is a swarm mini-harness that spawns, runs a task, and retires cleanly. This is the smallest thing that is recognizably "spinning off a little harness".
2. **A live `HarnessProposer`.** Implement the existing protocol with an LLM-backed proposer (agentic session editing a harness directory), behind the existing evidence-isolation guards. This is what turns "create a harness from a description" from a demo into a capability. Validate every proposed tree with `validate()` + a trial run before it can spawn.
3. **Materialize as a dock-linked repo (option D).** `harness spawn --materialize` writes the tree + `dock.yaml` and links it, so a description can produce a durable, auditable domain harness. This is mostly `refine demo`'s output made first-class.
4. **Merge-back policy.** Child library partition → parent review → vault adoption, with the same citation discipline as any other vault write.
5. **Only on a demonstrated limitation:** option B (a child needs a different plugin set), then option C (a child must be untrusted or long-lived), each behind the same spawn spec with `isolation` selecting the mechanism. Do not build B or C speculatively.

**What to defer (explicitly):** `refine run` as a live-evaluation command (already deferred by design with a stated reopening trigger — do not re-open it inside the spawn work); a session store or database for children (files under `--root` only, per the persistent-sessions shape); multi-user persistence; children spawning children without a depth limit (see open question 6); any new protocol besides MCP for cross-process control.

## What is already possible today vs genuinely missing

**Already possible, no build needed:**

- Dock-link a repo and drive it via entrypoints (a place to drive, not a live harness).
- `harness refine demo` — produce a harness directory and run Propose-Probe-Compose on it end to end.
- Spawn sub-agents — child sessions, swarm DAGs, token governance, Thread DAG supervision.
- Construct a second runtime in-process — `HarnessRuntime.create()` / `create_diagnostic()` / `from_config()` (a factory call, not a service).
- Create a child context inheriting parent registrations — `ServiceContext.child()` + `isolate()`.
- Scaffold a plugin or skill from an archetype — `PluginCreator.scaffold` / `scaffold_skill`.
- Turn an ingested repo into a plugin — `PluginIngestionPipeline.ingest()`.
- Persist per-domain learnings — `ExperienceLibrary.add` / `retain` / `forget`.
- Audit a harness design — `harness architect audit` against the 5-part architecture.

**Genuinely missing (the actual delta):**

- A `spawn` verb anywhere: no spawn service, no spawn CLI, no spawn spec format. (Verified: no `spawn` in `src/harness/commands/`; `create_child_session` is sessions, not kernels.)
- A live `HarnessProposer` (only `ScriptedProposer` in the demo).
- Child lifecycle management: a registry of live children, budget supervision across children, retire/merge-back policy, parent-stop cascade.
- A trial gate for a spawned harness before it runs (the pieces exist; no composed "spawn trial").
- A knowledge merge-back policy (child library partition → parent adoption).
- `refine run` (deferred by design — not missing by accident).

## Risks

- **Shared module-level singletons** in the in-process options (skill-graph `_DEFAULT_REGISTRY` / `_DEFAULT_GRAPH`). Audit all module-level mutable state before claiming any in-process isolation; a child that mutates shared state corrupts the parent.
- **Shared event bus by default.** A child's events land on the parent's bus. That is the observation channel, but it is also noise and a potential leak channel (child events carrying sensitive payloads into the parent's append-only log — Rule 4 makes the log immutable, so a leak cannot be retracted). Namespace child events by run/session ID and scrub payloads the way the dock scrubs environments.
- **Dispose cascade unverified.** If parent `dispose()` does not cascade to child contexts, orphaned children outlive the parent. Verify or track children explicitly.
- **Budget accounting across children.** `TokenGovernor` is per-swarm-run and `BudgetLedger` is per-refine-mode. A spawn service needs a parent-level ledger, or one runaway child can exhaust the parent's budget. Fail closed: no budget, no spawn.
- **The dock is not a sandbox.** `dock run` executes shell commands with `shell=True` behind string-pattern filtering. Never route an untrusted child's execution through `dock run`; use `SubprocessExecutor` / `VenvExecutor` / `ContainerExecutor` (Rule 5).
- **Identity and trial integrity.** Children need fingerprints and trial IDs from the first spawn, or two children with the same name become indistinguishable in the library and the DAG. Use the existing `identity.py` machinery, don't invent a second scheme.
- **Rule 19 (non-invasive extensibility).** The spawn service must be a plugin + service with typed keys. Any design that mutates `ServiceContext.__init__`, the kernel constructor contracts, or the lifecycle signatures is out of bounds.
- **Rule 20 (in-place deepening).** Reuse `PluginCreator.scaffold`, `validate()`, the trial seam, and the experience library. A second scaffolder, a second validator, or a second library is tool sprawl.
- **The "description → harness" step is the trust boundary.** A proposer that can write arbitrary tree content can write arbitrary always-on guidance — including guidance that disables safety checks. Proposed trees must pass `validate()` *and* a human-readable diff review before they can spawn with write permissions. Treat a proposed tree the way the dock treats a manifest: parsed, approved by digest, and drift-checked.

## Open questions for the user

1. **What is "Prime"?** Parent instance, or a distinct edition/deployment/role? This decides whether inheritance is "child context of the running parent" or "child of a Prime deployment".
2. **Should a spawned harness be able to spawn?** If yes, what is the recursion depth limit and who enforces it (the spawn service, the ledger, or the DAG)?
3. **Knowledge merge-back: automatic, reviewed, or never?** The recommendation is reviewed (explicit adoption). If the user wants automatic, say so — it changes the design (merge becomes a service, not a step).
4. **Budget currency:** tokens (TokenGovernor), dollars (BudgetLedger cost_usd), rollouts/sessions (R/P), or all three? And what is the default budget for a swarm mini-harness?
5. **Lifetime:** should a child ever outlive its parent? If yes, it needs its own persistence (option C or D), not a child context.
6. **Visibility:** should spawned harnesses appear in the control-room UI and `session tree`, or stay headless until the user asks?
7. **"Create a harness from a description" — who writes the description?** The user in chat, an agent in a swarm, or another harness? The answer decides whether the proposer needs a chat-facing front end or only a service API.
