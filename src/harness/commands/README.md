# Harness CLI Commands Reference (`harness.commands`)

The `harness.commands` package provides pure async and synchronous command handlers powering the Brain Harness Click CLI entrypoint (`harness`). Each module encapsulates a single command group, delegating domain logic to underlying kernel services and IoC container protocols.

---

## Overview & Architecture

Commands are strictly decoupled from Click CLI option parsers:
- **Pure Async Entrypoints**: Command modules define reusable functions (`cmd_*`) that accept typed arguments or options, allowing programmatic invocation from scripts or test fixtures without shell spawning.
- **IoC Service Resolution**: Command handlers instantiate or connect to the `HarnessRuntime`, resolve typed `ServiceKey[T]` instances from the context, and execute transactional workflows.
- **Rule 6 Single-Source Consolidation**: CLI command groups are declared exactly once in a single co-located block in [`cli.py`](../cli.py) via `_CANONICAL_GROUPS` to prevent later definitions from shadowing subcommands.
- **AliasedGroup Resolution**: Legacy alternate names and shortcuts are routed via `AliasedGroup` and `CLI_ALIASES` in [`aliases.py`](aliases.py), preserving backward compatibility while keeping `--help` clean and free of duplicate rows.
- **Rule 10 Headless Introspection Seams**: All runtime execution trees, session transcripts, and context compilation graphs expose headless Click CLI inspection and export commands.

---

## Canonical Command Groups & Modules

### 1. Agent Execution & Session Introspection
| Module | Canonical Name | Aliases | Description |
|---|---|---|---|
| [`agent.py`](agent.py) | `harness agent` | — | Autonomous ReAct agent task execution (`harness agent run "<task>"`). |
| [`session.py`](session.py) | `harness session` | — | Session transcript inspection, lifecycle states, and ASCII DAG tree export. |
| [`context.py`](context.py) | `harness context` | — | 3-tier context compilation, AST RepoMap injection, and prompt pruning. |
| [`compute.py`](compute.py) | `harness assess-compute` | — | Dynamic 5D complexity evaluation and model tier reasoning budget recommendation. |
| [`model_router.py`](model_router.py) | `harness router` | `model-router` | Heuristic query complexity classification and dynamic multi-provider routing. |
| [`calibrator.py`](calibrator.py) | `harness calibrate` | `calibrator` | Empirical coding harness component calibration, staging simulation, and forecasting. |
| [`harness_architect.py`](harness_architect.py) | `harness architect` | `harness-architect` | 5-part harness architecture audit, reliability scoring, and stack analysis. |
| [`compass.py`](compass.py) | `harness compass` | `harness-compass` | Autonomous agent harness benchmarking and constrained evolution. |
| [`self_eval.py`](self_eval.py) | `harness eval` | `self-eval` | Deterministic prompt evaluation pipelines and 3-layer LLM quality evaluation. |
| [`validation_loop.py`](validation_loop.py) | `harness validation-loop`| `validate-loop` | Spec-first deterministic validation loop execution and report generation. |
| [`uncertainty/`](uncertainty/) | `harness uncertainty` | `uncertainty-guard` | 3-layer uncertainty gating, retrieval similarity scoring, and logprob validation. |
| [`tau.py`](tau.py) | `harness tau` | `coding-harness` | Pi-style coding agent harness commands (DAG trees, journals, repair, trust). |

### 2. Plugins & Capability Engineering
| Module | Canonical Name | Aliases | Description |
|---|---|---|---|
| [`plugins.py`](plugins.py) | `harness plugin` | — | Plugin lifecycle management (`list`, `enable`, `disable`, `info`, `inspect`). |
| [`creator.py`](creator.py) | `harness creator` | `create`, `scaffold`, `validate`, `archetypes` | Plugin scaffolding, archetype validation, and AST auto-remediation. |
| [`skills/`](skills/) | `harness skills` | — | Skill Knowledge Graph queries, topological shortest-path chaining, and authoring. |
| [`tools.py`](tools.py) | `harness tool` | — | Granular tool registry inspection, tool testing, and execution sandboxing. |
| [`mcp.py`](mcp.py) | `harness mcp` | — | Model Context Protocol (MCP) server launching and tool bridging. |
| [`gate.py`](gate.py) | `harness gate` | `ai-native-harness` | AI-native harness governance, 4 behavioral gates, and drift telemetry. |
| [`pre_commit_security.py`](pre_commit_security.py) | `harness pre-commit-security` | `security-guard`, `shift-left` | Shift-left SAST, Shannon entropy secret interception, and CI defense. |
| [`redteam.py`](redteam.py) | `harness redteam` | — | GenAI adversarial red-teaming, prompt fuzzing, and harm scorecards. |
| [`network_forensics.py`](network_forensics.py) | `harness network-forensics` | `network`, `net-diag` | Protocol reconnaissance, tri-state recon & 7-layer fault isolation. |
| [`facet.py`](facet.py) | `harness facet` | `differential-facet` | Differential evidence comparison and facet availability semantics. |
| [`rol.py`](rol.py) | `harness rol` | `obligation-ledger` | Software reverse-engineering evidence and verification proof system. |
| [`icm.py`](icm.py) | `harness icm` | `icm-architect` | Interpretable Context Methodology (ICM) workspace architecture & verification. |

### 3. Documentation, Data & Analytics
| Module | Canonical Name | Aliases | Description |
|---|---|---|---|
| [`doc.py`](doc.py) | `harness doc` | — | Repository documentation auditing, AST symbol drift verification, and sync. |
| [`doc_builder.py`](doc_builder.py) | `harness doc-builder` | `hf-doc-builder` | HF Doc Builder — Documentation compilation, link verification, and MDX transpilation. |
| [`data.py`](data.py) | `harness data` | — | Enterprise data management, contracts, quality profiling, and Medallion pipelines. |
| [`datasets.py`](datasets.py) | `harness datasets` | — | Hugging Face Datasets inspection, streaming, transformation, and lakehouse conversion. |
| [`bigquery.py`](bigquery.py) | `harness bigquery` | `bq` | BigQuery in-database augmented analytics TVF execution suite. |
| [`garf.py`](garf.py) | `harness garf` | `garf-reporting` | Google Garf Declarative SQL Reporting & Analytical Workflow DAGs. |
| [`gis.py`](gis.py) | `harness gis` | `open-source-gis` | Open-Source GIS analytical engine selection, CRS safety & topology auditing. |
| [`okf.py`](okf.py) | `harness okf` | — | Manage, scope, and query Git-native OKF agent memory bundles. |
| [`gemini_vercel.py`](gemini_vercel.py) | `harness gemini-vercel` | `streaming-chatbot`, `gemini-chat` | Plain-text chunk streaming, edge architecture, and chatbot deployment. |
| [`gradio_app.py`](gradio_app.py) | `harness gradio` | `gradio-app` | Production AI interface engineering & AST diagnostics. |

### 4. Memory, Mining & System
| Module | Canonical Name | Aliases | Description |
|---|---|---|---|
| [`brain_miner.py`](brain_miner.py) | `harness brain-miner` | `miner`, `artifact-miner` | Brain workspace archaeology, scratch tool salvage, and transcript introspection. |
| [`trajectory_miner.py`](trajectory_miner.py) | `harness trajectory` | `trajectory-miner`, `conversation-miner` | Autobiographical execution trajectory archaeology and cognitive bifurcation. |
| [`temp_miner.py`](temp_miner.py) | `harness temp` | `temp-miner`, `ephemeral-miner` | Ephemeral workspace archaeology, HTML visual brief extraction, and sandbox triage. |
| [`reflection.py`](reflection.py) | `harness knowledge`, `reflect` | — | Knowledge Vault inspection, Isnad lineage, and endogenous reflection loop. |
| [`bridges.py`](bridges.py) | `harness bridge` | — | Inspect and manage ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel). |
| [`antigravity.py`](antigravity.py) | `harness antigravity` | — | Google Antigravity SDK & CLI headless inspection seams. |
| [`runtime.py`](runtime.py) | `harness config`, `apply`, `run`, `ui` | — | Configuration tree validation, declarative apply, interactive run, and web UI. |
| [`system.py`](system.py) | `harness introspect`, `services` | — | Live system diagnostics, memory stats, dependency graph, and IoC service list. |
| [`events.py`](events.py) | `harness events` | — | Immutable event bus log inspection, filtering, and streaming replay. |
| [`workspace.py`](workspace.py) | `harness init`, `watch` | — | Workspace initialization and filesystem hot-reloading watcher daemon. |

---

## Overlapping Domain Boundaries & Substrate Partitioning

To prevent tool sprawl and maintain clean single-responsibility boundaries (Rule 18), several specialized groups operate on distinct physical substrates:

### 1. Workspace Archaeology & Mining Substrates
- **`brain-miner`**: Operates strictly on persistent user brain artifacts (`<appDataDir>/brain/<cid>/`), salvaging reusable Python scripts from `scratch/` and extracting walkthrough briefs.
- **`trajectory`**: Operates on relational SQLite conversation stores (`conversations/<cid>.db`), inspecting protobuf step payloads, friction metrics, and cognitive bifurcation logs.
- **`temp`**: Operates on ephemeral system temporary directories and pytest sandboxes (`AppData/Local/Temp/pytest-*`), triaging crash logs and ephemeral HTML visual briefs.

### 2. Documentation Engineering
- **`doc`**: Repository codebase documentation hygiene (`repo-doc-synchronizer`), auditing AST docstring coverage, detecting stale code symbols, and updating relative links.
- **`doc-builder`**: Multi-package documentation suite compilation using Hugging Face doc-builder patterns (`hf-doc-builder-architect`), verifying anchor graphs and transpiling MDX.

### 3. Harness Architecture vs. Compass Evolution
- **`architect`**: Static structural evaluation of agent harnesses using 5-part architecture and 4-mechanism reliability gates (`agent-harness-architect`).
- **`compass`**: Dynamic empirical multi-armed benchmark discovery, constrained harness mutation, and R3 integration (`harness-compass`).

### 4. Data & Analytics Engines
- **`gis`**: Coordinate reference systems (CRS), spatial topology, and geometry analysis across 14 dedicated GIS libraries (`open-source-gis-architect`).
- **`datasets`**: Zero-copy Arrow memory mapping and streaming iteration for massive datasets (`hf-datasets-engineer`).
- **`data`**: Enterprise data lifecycles, Open Data Contracts (ODCS), quality profiling, and Medallion lakehouses (`data-management-architect`).
- **`bigquery`**: Google BigQuery table-valued functions (TVFs) and in-database machine learning queries (`bigquery-augmented-analytics`).

---

## CLI Usage Examples

### Running an Autonomous Task
```bash
harness run "Audit codebase documentation coverage and detect stale links"
```

### Exporting Execution Session Trees
```bash
# Export hierarchical ASCII DAG tree of agent execution steps
harness session tree <session_id>

# Export full session transcript JSON
harness session export <session_id> --output transcript.json
```

### Querying Skill Knowledge Graph
```bash
# Find optimal skill execution chain between two domain capabilities
harness skills chain --from code-review --to tdd
```

---

## Related Documentation

- [CLI Reference Guide](../../../docs/reference/cli.md)
- [Kernel Architecture](../kernel/README.md)
- [User Manual](../../../USER_MANUAL.md)
