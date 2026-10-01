# Click CLI Command Reference (`harness`)

The `harness` command-line interface provides unified control over the Brain Harness micro-kernel, agent reasoning loops, plugin lifecycles, and developer tooling.

---

## Global Options

```bash
harness [OPTIONS] COMMAND [ARGS]...
```

- `--debug`: Enable verbose debug logging output to stderr.
- `--version`: Show the version and exit (`0.1.0`).
- `--help`: Show the command help message and exit.

---

## 1. Agent & Execution Commands

### `harness agent`
Autonomous ReAct agent task execution and interactive stepping.
- `harness agent run "<task>" [--max-steps N] [--session-id ID]`: Runs an autonomous task to completion.
- `harness agent step "<prompt>" --session-id ID`: Executes a single interactive step within a session.

### `harness session`
Agent conversation DAG inspection and transcript export.
- `harness session list`: Lists recorded sessions with task summaries and timestamps.
- `harness session tree <session_id>`: Renders an ASCII DAG tree of execution steps.
- `harness session export <session_id> [--output FILE]`: Exports full JSON step transcripts.

### `harness context`
Context compilation and AST repo map generation.
- `harness context compile --prompt "<text>"`: Compiles context with deterministic pruning.
- `harness context repomap [--root DIR]`: Generates a PageRanked AST repository skeleton.

### `harness assess-compute`
Dynamic 5D complexity evaluation and reasoning budget allocation.
- `harness assess-compute "<task_description>"`: Evaluates Span, Depth, Concurrency, Rigor, and Heterogeneity to recommend a model tier and reasoning budget (High, Medium, Low, Off).

### `harness model-router`
Multi-provider dynamic LLM routing.
- `harness model-router classify "<query>"`: Classifies prompt complexity in sub-5ms.
- `harness model-router matrix`: Displays active provider pricing, latency, and capabilities.

### `harness calibrator`
Coding agent harness calibration.
- `harness calibrator evaluate`: Benchmarks T0-T4 context staging, action spaces, and planning scaffolds.

### `harness architect`
5-part harness architecture and reliability gate audit.
- `harness architect audit [--root DIR]`: Assesses components across 4 reliability mechanisms.

### `harness compass`
Harness benchmarking and constrained evolution.
- `harness compass benchmark`: Runs standardized autonomous agent benchmarks.

### `harness self-eval`
Deterministic prompt evaluation pipeline.
- `harness self-eval run --pipeline <name>`: Runs prompt assertions against gold-standard outputs.

### `harness validation-loop`
Deterministic validation loop runner.
- `harness validation-loop validate --spec <spec_name> --file <json_file>`: Evaluates structured outputs.
- `harness validation-loop specs`: Lists registered validation specs.

### `harness uncertainty`
3-layer uncertainty boundary and retrieval scoring.
- `harness uncertainty gate -q "<query>"`: Evaluates domain perimeter bounds.
- `harness uncertainty retrieval -q "<query>" -c "<chunk>"`: Scores semantic context relevance.

---

## 2. Plugins & Capability Creator Commands

### `harness plugin`
Plugin lifecycle management.
- `harness plugin list`: Displays all installed plugins, states, and provided services.
- `harness plugin add <source> [--category CAT]`: Fetches, inspects, and stages an external repository.
- `harness plugin enable <name>`: Enables a plugin and registers its services in the IoC container.
- `harness plugin disable <name>`: Disables a plugin and cleans up state.
- `harness plugin remove <name>`: Deletes a cached plugin from disk.
- `harness plugin inspect <name>`: Displays manifest details, declared tools, and dependencies.

### `harness tool`
Granular tool registry management.
- `harness tool list`: Lists all callable agent tools and their parameter schemas.
- `harness tool invoke <tool_name> [--params JSON]`: Tests tool invocation in isolation.

### `harness creator` (Aliases: `create`, `scaffold`, `validate`, `archetypes`)
Plugin and capability synthesis.
- `harness creator build <name> --category <cat> [--archetype ARCH]`: Scaffolds a new plugin project.
- `harness creator validate <path>`: Runs multi-rule AST and sandbox validation.
- `harness creator archetypes`: Lists available archetype presets (`tool`, `service`, `mcp`, etc.).

### `harness skills`
Skill Knowledge Graph routing and shortest-path chaining.
- `harness skills list`: Lists all registered agent skills in the knowledge graph.
- `harness skills route "<intent>"`: Ranks candidate skills matching an operational intent.
- `harness skills chain --from <skill_a> --to <skill_b>`: Finds the optimal directed execution chain.
- `harness skills visual [--output FILE]`: Generates an interactive HTML Visual Brief.

### `harness mcp`
Model Context Protocol server integration.
- `harness mcp serve [--port PORT]`: Launches the local Harness MCP server.
- `harness mcp list`: Discovers and enumerates available MCP tools.

### `harness pre-commit-security` (Aliases: `security-guard`, `shift-left`)
Pre-commit SAST scanning and credential leak prevention.
- `harness pre-commit-security scan [--dir DIR]`: Executes DevSkim SAST and Gitleaks rules.

---

## 3. Documentation & Data Commands

### `harness doc`
AST documentation coverage auditing and link drift verification.
- `harness doc audit [--root DIR] [--min-coverage PCT] [--output FILE]`: Audits doc coverage across Python modules.
- `harness doc drift-check [--root DIR] [--output FILE]`: Verifies all relative links and symbol names.
- `harness doc visual-brief [--output FILE]`: Generates an interactive HTML coverage brief.

### `harness doc-builder` (Alias: `hf-doc-builder`)
HuggingFace doc-builder AST compiler.
- `harness doc-builder build --src <dir> --out <dir>`: Compiles documentation suites.
- `harness doc-builder audit-toc --manifest _toctree.yml`: Validates navigation tree links.

### `harness data`
Relational data profiling and migration.
- `harness data profile --table <name>`: Generates out-of-core statistical topology moments.
- `harness data migrate`: Applies pending relational schema migrations.

### `harness datasets`
Large dataset streaming and Arrow memory mapping.
- `harness datasets stream --dataset <id>`: Initializes streaming iterator pipeline.

### `harness bigquery` (Alias: `bq`)
BigQuery augmented analytics and causal inference.
- `harness bigquery run --query "<sql>"`: Executes BigQuery TVFs and anomaly models.

### `harness garf`
Declarative SQL reporting pipelines.
- `harness garf run --config <yaml_file>`: Dispatches analytical reporting workflow DAGs.

### `harness gis`
Multi-engine geospatial processing.
- `harness gis route --task <task_type>`: Routes geospatial workloads to the optimal GIS engine.

### `harness okf`
Open Knowledge Framework (OKF v0.2) Git-native episodic memory.
- `harness okf search "<query>"`: Sub-millisecond BM25 lexical search over memory concepts.

---

## 4. System & Runtime Commands

### `harness init`
Initializes a new Brain Harness workspace in the current directory.

### `harness services`
Lists all services currently active in the micro-kernel IoC container.

### `harness events`
Inspects the immutable event bus log.
- `harness events [--type TYPE] [--limit N] [--follow]`: Streams or dumps event records.

### `harness introspect`
Outputs live runtime diagnostics, memory usage, and the Mermaid dependency graph.

### `harness run`
Launches the interactive Brain Harness shell.

### `harness ui`
Starts the FastAPI web server and control dashboard (`http://127.0.0.1:8000`).
- `harness ui [--port PORT] [--host HOST]`

### `harness watch`
Starts the autonomous file watcher daemon monitoring triggers for hot-reloading.

### `harness reflect`
Executes endogenous autobiographical memory distillation into verified Knowledge Items.

### `harness bridge`
Diagnostics for external ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel).
- `harness bridge status`: Checks connectivity and sync status.

### `harness network-forensics` (Aliases: `network`, `net-diag`)
Packet capture dissection and network isolation audits.
- `harness network-forensics pcap --file <pcap_file>`: Analyzes packet captures for TCP anomalies.
