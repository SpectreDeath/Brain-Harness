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
Autonomous ReAct agent task execution.
- `harness agent run "<task>" [--max-steps N] [--session-id ID]`: Runs an autonomous task to completion.

### `harness session`
Agent conversation DAG inspection and transcript export.
- `harness session list`: Lists recorded sessions with task summaries and timestamps.
- `harness session get <session_id>`: Shows metadata, step count, and terminal status for a session.
- `harness session tree <session_id>`: Renders an ASCII DAG tree of execution steps.
- `harness session export <session_id> [--output FILE]`: Exports full JSON step transcripts.

### `harness context`
Context compilation, skeletonization, and governance.
- `harness context compile --prompt "<text>"`: Compiles context with deterministic pruning.
- `harness context skeletonize [--root DIR]`: Generates a PageRanked AST repository skeleton map.
- `harness context lint`: Lints codebase context files (AGENTS.md, CLAUDE.md) against line budgets.
- `harness context sync`: Synchronizes context definitions across agent configurations.
- `harness context govern`: Enforces context token boundaries and negative constraints.

### `harness assess-compute`
Dynamic 5D complexity evaluation and reasoning budget allocation.
- `harness assess-compute "<task_description>" [--files N] [--architecture] [--debugging] [--profile PROFILE] [--tier TIER] [--json] [--html]`: Evaluates Span, Depth, Concurrency, Rigor, and Heterogeneity to recommend a model tier and reasoning budget (High, Medium, Low, Off).

### `harness model-router` (Aliases: `router`)
Multi-provider dynamic LLM routing.
- `harness model-router route "<query>"`: Classifies prompt complexity in sub-5ms and routes to candidate model.
- `harness model-router profile`: Displays active provider pricing, latency, and capability profiles.
- `harness model-router simulate`: Simulates failover and load-balancing scenarios.
- `harness model-router brief`: Generates an interactive HTML visual routing brief.

### `harness calibrator` (Aliases: `calibrate`)
Coding agent harness calibration.
- `harness calibrator staging`: Benchmarks T0-T4 context staging, action spaces, and planning scaffolds.
- `harness calibrator recommend`: Evaluates and recommends optimal harness configuration.
- `harness calibrator repatch`: Applies self-repair patches to harness drift.
- `harness calibrator brief`: Renders an interactive calibration brief.

### `harness architect` (Aliases: `harness-architect`)
5-part harness architecture and reliability gate audit.
- `harness architect audit [--root DIR]`: Assesses components across 4 reliability mechanisms.
- `harness architect score`: Computes composite harness readiness scorecard.
- `harness architect bet`: Calculates architectural payoff bets and trade-offs.
- `harness architect brief`: Renders an interactive C4 architecture HTML brief.

### `harness compass` (Aliases: `harness-compass`)
Harness benchmarking and constrained evolution.
- `harness compass run`: Runs standardized autonomous agent benchmarks.
- `harness compass gate`: Evaluates 4-stage proactive feedback gates.
- `harness compass feedback`: Computes multi-stage feedback metrics.
- `harness compass merge`: Merges dual-track optimization candidates.
- `harness compass brief`: Generates compass evolution brief.

### `harness self-eval` (Aliases: `eval`)
Deterministic prompt evaluation and LLM-as-a-judge pipeline.
- `harness self-eval regression`: Runs regression test suites against gold standards.
- `harness self-eval judge`: Runs LLM-as-a-judge evaluation scoring.
- `harness self-eval kappa`: Calculates Cohen's kappa inter-rater agreement.
- `harness self-eval drift`: Detects prompt and evaluation drift across model versions.
- `harness self-eval gate`: Enforces pre-deployment evaluation gates.
- `harness self-eval brief`: Generates visual evaluation report.

### `harness validation-loop` (Aliases: `validate-loop`)
Deterministic validation loop runner.
- `harness validation-loop validate --spec <spec_name> --file <json_file>`: Evaluates structured outputs against JSON schemas.
- `harness validation-loop specs`: Lists registered validation specifications.
- `harness validation-loop run`: Runs automated validation test suites.
- `harness validation-loop brief`: Generates validation visual brief.

### `harness uncertainty` (Aliases: `uncertainty-guard`)
3-layer uncertainty boundary and retrieval scoring.
- `harness uncertainty gate -q "<query>"`: Evaluates domain perimeter bounds.
- `harness uncertainty retrieval -q "<query>" -c "<chunk>"`: Scores semantic context relevance.
- `harness uncertainty logprobs`: Evaluates token-level log probabilities.
- `harness uncertainty calibrate`: Calibrates confidence thresholds.
- `harness uncertainty brief`: Generates uncertainty telemetry report.

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
- `harness plugin card <name>`: Displays the plugin summary card.
- `harness plugin guide <name>`: Displays the plugin developer guide.
- `harness plugin enable-all`: Enables all discovered plugins.
- `harness plugin disable-all`: Disables all active plugins.

### `harness tool`
Granular tool registry management.
- `harness tool list`: Lists all callable agent tools and their parameter schemas.
- `harness tool enable <tool_name>`: Enables a registered tool.
- `harness tool disable <tool_name>`: Disables a registered tool.

### `harness creator` (Aliases: `create`, `scaffold`, `validate`, `archetypes`)
Plugin and capability synthesis.
- `harness creator build <name> --category <cat> [--archetype ARCH]`: Scaffolds a new plugin project.
- `harness creator validate <path>`: Runs multi-rule AST and sandbox validation.
- `harness creator archetypes`: Lists available archetype presets (`tool`, `service`, `mcp`, etc.).
- `harness creator remediate <path>`: Auto-repairs detected manifest and structure lint errors.

### `harness skills`
Skill Knowledge Graph routing and shortest-path chaining.
- `harness skills list`: Lists all registered agent skills in the knowledge graph.
- `harness skills route "<intent>"`: Ranks candidate skills matching an operational intent.
- `harness skills chain --from <skill_a> --to <skill_b>`: Finds the optimal directed execution chain.
- `harness skills graph`: Indexes and displays the workspace skill knowledge graph.
- `harness skills create <name>`: Scaffolds a high-precision agent skill with `SKILL.md` and `CARD.md`.
- `harness skills validate <skill_name>`: Validates an agent skill package against deep-module craft standards.
- `harness skills info <skill_name>`: Inspects topological dependencies and anti-patterns for a skill.
- `harness skills guidance "<intent>"`: Compiles and displays an end-to-end execution guidance plan.

### `harness mcp`
Model Context Protocol server integration.
- `harness mcp serve [--port PORT]`: Launches the local Harness MCP server.

### `harness pre-commit-security` (Aliases: `security-guard`, `shift-left`)
Pre-commit SAST scanning and credential leak prevention.
- `harness pre-commit-security scan [--dir DIR]`: Executes DevSkim SAST and Gitleaks rules.
- `harness pre-commit-security smoke-test`: Runs security smoke tests.
- `harness pre-commit-security audit-suppressions`: Audits security rule suppressions.
- `harness pre-commit-security brief`: Generates security audit visual brief.

---

## 3. Documentation & Data Commands

### `harness doc`
AST documentation coverage auditing and link drift verification.
- `harness doc audit [--root DIR] [--min-coverage PCT] [--output FILE]`: Audits doc coverage across Python modules.
- `harness doc drift [--root DIR] [--output FILE]`: Verifies all relative links and symbol names.
- `harness doc brief [--output FILE]`: Generates an interactive HTML coverage brief.
- `harness doc scaffold <module_path>`: Scaffolds standardized Diataxis documentation for a Python module.
- `harness doc stats`: Inspects AST parsing cache performance statistics.

### `harness doc-builder` (Alias: `hf-doc-builder`)
HuggingFace doc-builder AST compiler, link verifier, and MDX transpiler.
- `harness doc-builder verify [--docs-dir DIR] [--no-toc] [--no-anchors] [--json]`: Verifies internal documentation links, anchor targets, and TOC integrity.
- `harness doc-builder inspect --module <name> --object <symbol>`: Extracts structured signatures, parameters, and docstrings from Python AST.
- `harness doc-builder convert --src <file> [--target-format mdx]`: Transpiles Markdown, RST, or IPYNB into MDX with reactive Svelte tags.
- `harness doc-builder chunk --file <file> [--title TITLE] [--max-size N]`: Hierarchically partitions documentation along heading trees for retrieval/embeddings.
- `harness doc-builder lint --file <file> [--fix]`: Lints and formats code examples inside docstrings and MDX files.

### `harness data`
Relational data profiling and Open Data Contract verification.
- `harness data profile --table <name>`: Generates out-of-core statistical topology moments.
- `harness data validate --spec <spec_file>`: Validates datasets against Open Data Contracts (ODCS).
- `harness data pipeline --config <pipeline_yaml>`: Runs end-to-end data pipeline workflows.
- `harness data topk-analyze --tensor <tensor>`: Analyzes TopK selection efficiency.

### `harness datasets`
Large dataset streaming and Arrow memory mapping.
- `harness datasets inspect --dataset <id>`: Inspects dataset metadata, splits, and schemas.
- `harness datasets profile --dataset <id>`: Computes column-level dataset statistics.
- `harness datasets sample --dataset <id> [--limit N]`: Streams sample records using Arrow zero-copy memory mapping.
- `harness datasets transform --dataset <id> --script <path>`: Applies streaming transformation pipelines.
- `harness datasets convert --dataset <id> --format <parquet|jsonl>`: Converts datasets between lakehouse formats.

### `harness bigquery` (Alias: `bq`)
BigQuery augmented analytics and causal inference.
- `harness bigquery profile --table <table_id>`: Computes in-database distribution moments.
- `harness bigquery change-points --table <table_id> --metric <col>`: Detects metric anomalies via TVFs.
- `harness bigquery drivers --table <table_id> --target <col>`: Identifies multi-dimensional anomaly drivers.
- `harness bigquery causal --table <table_id> --treatment <col>`: Computes ARIMA_PLUS counterfactual causal inference.
- `harness bigquery pipeline --config <sql_pipeline_yaml>`: Executes declarative BigQuery analytical DAGs.
- `harness bigquery brief`: Generates BigQuery augmented analytics visual brief.

### `harness garf` (Alias: `garf-reporting`)
Declarative SQL reporting pipelines.
- `harness garf parse --query "<sql>"`: Parses declarative Garf SQL queries.
- `harness garf simulate --config <garf_yaml>`: Simulates report execution across mock endpoints.
- `harness garf export --config <garf_yaml> --format <csv|json|parquet>`: Exports declarative analytical reports.
- `harness garf workflow --config <garf_yaml>`: Executes reporting workflow DAGs.

### `harness gis` (Alias: `open-source-gis`)
Multi-engine geospatial processing and CRS verification.
- `harness gis route --task <task_type>`: Routes geospatial workloads to the optimal GIS engine across 14 engines.
- `harness gis validate --crs <crs_code> --layer <layer>`: Enforces Coordinate Reference System (CRS) safety gates.
- `harness gis architect --spec <pipeline_spec>`: Compiles geospatial analysis pipelines.

### `harness okf`
Open Knowledge Framework (OKF v0.2) Git-native episodic memory.
- `harness okf search "<query>"`: Sub-millisecond BM25 lexical search over memory concepts.
- `harness okf scope`: Scopes repository concepts before agent modification.
- `harness okf show <concept_id>`: Displays memory concept metadata and relations.
- `harness okf validate`: Validates memory concept graph against trust-ordered schemas.

---

## 4. System & Runtime Commands

### `harness init`
Initializes a new Brain Harness workspace in the current directory.
- `harness init [PATH]`

### `harness services`
Lists all services currently active in the micro-kernel IoC container.

### `harness events`
Inspects the immutable event bus log.
- `harness events [--type TYPE] [--limit N]`: Streams or dumps event records.

### `harness introspect`
Outputs live runtime diagnostics, memory usage, and the Mermaid dependency graph.

### `harness run`
Launches the interactive Brain Harness shell.

### `harness ui`
Starts the FastAPI web server and control dashboard (`http://127.0.0.1:8000`).
- `harness ui [--port PORT] [--host HOST] [--db-path PATH]`

### `harness watch`
Starts the autonomous file watcher daemon monitoring triggers for hot-reloading.

### `harness apply`
Applies a declarative workspace configuration manifest.
- `harness apply <config_file>`

### `harness reflect`
Executes endogenous autobiographical memory distillation into verified Knowledge Items.
- `harness reflect [--vault-dir DIR] [--conv-id ID] [--category CAT]`

### `harness bridge`
Diagnostics for external ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel).
- `harness bridge list`: Lists active bridges.
- `harness bridge status`: Checks connectivity and sync status.

### `harness network-forensics` (Aliases: `network`, `net-diag`)
Packet capture dissection and network isolation audits.
- `harness network-forensics decode-flags --tcp-flags <flags>`: Analyzes TCP flags and handshake anomalies.
- `harness network-forensics scan-ports --target <host>`: Executes tri-state port evaluation.
- `harness network-forensics traceroute --target <host>`: Traces network hops and latency.
- `harness network-forensics cleartext --pcap <pcap_file>`: Audits packet captures for unencrypted secrets.
- `harness network-forensics diagnose-7layer --target <host>`: Performs systematic 7-layer fault isolation.
- `harness network-forensics brief`: Generates network diagnostics visual brief.

### `harness icm` (Aliases: `icm-architect`)
Interpretable Context Methodology (ICM) workspace architecture and formal verification.
- `harness icm verify`: Verifies workspace conformance against ICM invariants.
- `harness icm scaffold`: Scaffolds ICM context trees and boundary definitions.
- `harness icm brief`: Renders an interactive HTML visual brief for ICM workspace state.

### `harness brain-miner` (Aliases: `miner`, `artifact-miner`)
Brain workspace archaeology, scratch tool salvage, and transcript introspection.
- `harness brain-miner scan [--root DIR]`: Scans and catalogs reusable Python scratch tools.
- `harness brain-miner triage [--dir DIR]`: Triages background task logs for exit failures.
- `harness brain-miner step <step_id>`: Fetches specific steps via O(1) binary seek.
- `harness brain-miner brief [--output FILE]`: Generates an HTML visual brief summarizing scratch tools.

### `harness trajectory` (Aliases: `trajectory-miner`, `conversation-miner`)
Autobiographical execution trajectory archaeology, friction metrics, and cognitive bifurcation.
- `harness trajectory analyze <conv_id>`: Calculates friction metrics, error loops, and tool recovery rates.
- `harness trajectory bifurcate <conv_id>`: Separates epistemic learnings from procedural tool execution.
- `harness trajectory export <conv_id>`: Exports normalized trajectory steps to JSONL.
- `harness trajectory brief`: Generates an interactive HTML visual brief.

### `harness temp` (Aliases: `temp-miner`, `ephemeral-miner`)
Ephemeral workspace archaeology, HTML visual brief extraction, and sandbox triage.
- `harness temp scan [--dir DIR]`: Scans temporary directories and sandboxes for architecture records.
- `harness temp triage [--pattern PATTERN]`: Triages failed test outputs and proactor crash logs.
- `harness temp brief`: Extracts and aggregates ephemeral HTML visual briefs.

### `harness rol` (Aliases: `obligation-ledger`)
Reconstruction Obligation Ledger — Software reverse-engineering evidence proof system.
- `harness rol verify <ledger_path>`: Validates reconstruction claims and cryptographic hashes.
- `harness rol audit <ledger_path>`: Checks isnad provenance and evidence completeness.
- `harness rol brief`: Synthesizes visual ledger graphs and completion status.

### `harness facet` (Aliases: `differential-facet`)
Differential Facet Verifier — Multi-provider evidence comparison and facet availability semantics.
- `harness facet compare --p1 <p1> --p2 <p2>`: Performs 3-valued differential outcome evaluation.
- `harness facet gate --claim <claim>`: Assesses absence claimability gates.
- `harness facet brief`: Generates differential facet visualization briefs.

### `harness redteam`
Microsoft PyRIT AI Red Teaming & Harm Evaluation Engine.
- `harness redteam fuzz --prompt "<text>"`: Fuzzes prompts with adversarial mutations.
- `harness redteam audit`: Executes structured jailbreak evaluations (crescendo, TAP).
- `harness redteam report`: Generates vulnerability scorecards from recent red-team scans.

---

## Overlapping Domain Boundaries & Substrate Partitioning

To maintain clean single-responsibility boundaries (Rule 18), several specialized groups operate on distinct physical substrates:

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

