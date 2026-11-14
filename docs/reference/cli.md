# Brain Harness — CLI Reference Manual

> [!NOTE]
> This reference is automatically compiled from the live Click CLI command definitions in `src/harness/cli.py`.
> Run `pytest tests/test_cli_content_drift.py` to assert content drift alignment.

## Overview

The Brain Harness Click command interface provides headless execution seams, runtime diagnostics, and domain workflows across all micro-kernel services.

```text
harness [OPTIONS] COMMAND [ARGS]...
```

## Top-Level Shortcuts & Command Groups

### Command Groups
| Command Group | Subcommands | Description |
| :--- | :--- | :--- |
| [`harness agent`](#harness-agent) | `run` | Run and manage autonomous agent loops. |
| [`harness antigravity`](#harness-antigravity) | `policy`, `status`, `telemetry` | Google Antigravity SDK & CLI headless inspection seams. |
| [`harness architect`](#harness-architect) | `audit`, `bet`, `brief`, `score` | Agent harness architecture audit, reliability scoring, and bet classification. |
| [`harness bigquery`](#harness-bigquery) | `brief`, `causal`, `change-points`, `drivers`, `pipeline`, `profile` | BigQuery in-database augmented analytics TVF execution suite. |
| [`harness brain-miner`](#harness-brain-miner) | `brief`, `scan`, `step`, `triage` | Brain workspace archaeology, scratch tool salvage, and transcript introspection. |
| [`harness bridge`](#harness-bridge) | `list`, `status` | Inspect and manage ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel). |
| [`harness calibrate`](#harness-calibrate) | `brief`, `recommend`, `repatch`, `staging` | Empirical coding harness component calibration, staging simulation, and forecasting. |
| [`harness compass`](#harness-compass) | `brief`, `feedback`, `gate`, `merge`, `run` | HarnessCompass CLI — Automatic harness discovery, calibration & R3 integration. |
| [`harness config`](#harness-config) | `validate` | Manage and validate declarative configuration trees. |
| [`harness context`](#harness-context) | `add`, `assemble`, `compile`, `govern`, `ledger`, `lint`, `skeletonize`, `snapshot`, `sync`, `transform`, `validate-tool` | Manage 3-tier AST reachability compilation and context optimization. |
| [`harness creator`](#harness-creator) | `archetypes`, `build`, `init`, `remediate`, `scaffold`, `validate` | Creator Mode tools for plugin authoring. |
| [`harness data`](#harness-data) | `maturity`, `pipeline`, `profile`, `resolve`, `topk-analyze`, `topk-bounds`, `topk-recommend`, `validate` | Enterprise data management, contracts, quality profiling, and Medallion pipelines. |
| [`harness datasets`](#harness-datasets) | `commit-vault`, `convert`, `inspect`, `profile`, `sample`, `strategy`, `transform` | Hugging Face Datasets inspection, streaming, transformation, and lakehouse conversion commands. |
| [`harness doc`](#harness-doc) | `audit`, `brief`, `drift`, `scaffold`, `stats`, `wiki-compile`, `wiki-lint` | Repository documentation auditing, AST symbol drift verification, and scaffolding. |
| [`harness doc-builder`](#harness-doc-builder) | `chunk`, `convert`, `inspect`, `lint`, `verify` | HF Doc Builder — Documentation compilation, link verification, and MDX transpilation. |
| [`harness dock`](#harness-dock) | `inspect`, `link`, `list`, `run`, `tools` | Agent Dock — workstation port for plugging agents into repositories. |
| [`harness eval`](#harness-eval) | `brief`, `drift`, `gate`, `judge`, `kappa`, `layer1`, `regression` | Self-Evaluating AI Pipeline — 3-layer LLM quality evaluation & statistical gating. |
| [`harness facet`](#harness-facet) | `claim-absence`, `compare`, `export`, `verify` | Differential Facet Verifier — Multi-provider evidence comparison and facet availability semantics. |
| [`harness garf`](#harness-garf) | `export`, `parse`, `simulate`, `workflow` | Google Garf Declarative SQL Reporting & Analytical Workflow DAGs. |
| [`harness gate`](#harness-gate) | `audit`, `brief`, `drift`, `evaluate`, `mcp`, `mine` | AI-native harness governance, 4 behavioral gates, and drift telemetry. |
| [`harness gemini-vercel`](#harness-gemini-vercel) | `brief`, `inspect`, `scaffold`, `verify` | Gemini & Vercel Streaming Chatbot CLI — Plain-text chunk streaming & edge architecture. |
| [`harness gev`](#harness-gev) | `brief`, `flights`, `hazards`, `render`, `spatial`, `status`, `vessels` | God's Eye View — Planetary OSINT, real-time telemetry feeds, and 3D geospatial rendering. |
| [`harness gis`](#harness-gis) | `architect`, `route`, `validate` | Open-Source GIS analytical engine selection, CRS safety & topology auditing. |
| [`harness gradio`](#harness-gradio) | `brief`, `inspect`, `scaffold` | Gradio App Architect CLI — Production AI interface engineering & AST diagnostics. |
| [`harness icm`](#harness-icm) | `audit`, `index`, `links`, `quotes`, `scaffold` | Interpretable Context Methodology (ICM) workspace architecture & verification. |
| [`harness knowledge`](#harness-knowledge) | `backfill`, `contradictions`, `dependents`, `export`, `hygiene`, `joint-query`, `lifecycle`, `lineage`, `list`, `neighbors`, `orphans`, `path`, `query`, `reflect`, `resolve`, `stats`, `sync`, `timeline`, `topic`, `verify` | Manage and query the distilled Knowledge Vault and Isnad lineage. |
| [`harness mantis`](#harness-mantis) | `audit`, `calibrate-risk`, `chain-exploits`, `critic-filter`, `dedupe`, `dir-summary`, `gate`, `history-scan`, `plan-review`, `report` | Google Mantis — Autonomous security review, AST taint audit, deduplication ladder, and risk triage. |
| [`harness mcp`](#harness-mcp) | `serve` | Model Context Protocol (MCP) server commands. |
| [`harness memory`](#harness-memory) | `benchmark`, `recall`, `register`, `route`, `snapshot`, `status`, `step`, `working-set` | Manage working-memory decay, Ebbinghaus retention, and 5-store routing. |
| [`harness network-forensics`](#harness-network-forensics) | `brief`, `cleartext`, `decode-flags`, `diagnose-7layer`, `scan-ports`, `subnet`, `traceroute` | Network Forensics CLI — Protocol reconnaissance, tri-state recon & 7-layer fault isolation. |
| [`harness okf`](#harness-okf) | `scope`, `search`, `show`, `validate` | Manage, scope, and query Git-native OKF agent memory bundles. |
| [`harness plugin`](#harness-plugin) | `add`, `card`, `disable`, `disable-all`, `enable`, `enable-all`, `guide`, `info`, `inspect`, `list`, `remove` | Manage plugins. |
| [`harness pre-commit-security`](#harness-pre-commit-security) | `audit-ci`, `audit-suppressions`, `brief`, `scan`, `smoke-test` | Pre-Commit Security Guard CLI — Shift-left SAST, secret interception & CI defense. |
| [`harness rea`](#harness-rea) | `callgraph`, `decompile`, `devices`, `diff`, `inspect`, `learn`, `learned`, `list`, `providers`, `signatures` | REA — Reverse-engineering toolkit, multi-provider dissection, and signature learning. |
| [`harness redteam`](#harness-redteam) | `scan`, `status`, `techniques` | GenAI adversarial red-teaming and prompt vulnerability audits. |
| [`harness refine`](#harness-refine) | `budget`, `demo`, `fingerprint`, `scan`, `validate` | Recursive agent harness refinement, rollouts budget, and verification. |
| [`harness rol`](#harness-rol) | `export`, `ingest`, `obligation`, `verify` | Reconstruction Obligation Ledger — Software reverse-engineering evidence and verification proof system. |
| [`harness router`](#harness-router) | `brief`, `profile`, `route`, `simulate` | Dynamic Model Router CLI — 3-tier switching & resilient failover commands. |
| [`harness session`](#harness-session) | `export`, `get`, `list`, `tree` | Manage and inspect agent execution sessions and hierarchical trees. |
| [`harness skills`](#harness-skills) | `bridges`, `capabilities`, `chain`, `check-chain`, `clusters`, `create`, `graph`, `guidance`, `index`, `info`, `intercept`, `joint-query`, `list`, `prereqs`, `route`, `run`, `select`, `validate` | Manage and query the agent skill knowledge graph. |
| [`harness spawn`](#harness-spawn) | `adopt`, `list`, `propose`, `retire`, `run` | Spawn, inspect, retire, and adopt learnings from isolated child harnesses. |
| [`harness tau`](#harness-tau) | `append-journal`, `repair-history`, `resolve-path`, `tree`, `trust-check` | Pi-style coding agent harness commands (DAG trees, journals, repair, trust). |
| [`harness temp`](#harness-temp) | `bifurcate`, `salvage`, `sandbox`, `scan`, `tail` | Ephemeral workspace archaeology, HTML visual brief extraction, and sandbox triage. |
| [`harness tool`](#harness-tool) | `disable`, `enable`, `list` | Inspect and manage granular tool and skill enablement. |
| [`harness trajectory`](#harness-trajectory) | `bifurcate`, `friction`, `inspect`, `scan` | Autobiographical execution trajectory archaeology, friction metrics, and cognitive bifurcation. |
| [`harness uncertainty`](#harness-uncertainty) | `brief`, `calibrate`, `gate`, `logprobs`, `pipeline`, `retrieval` | Uncertainty-Aware AI Pipeline — 3-Layer Interception & Overconfidence Mitigation. |
| [`harness validation-loop`](#harness-validation-loop) | `brief`, `run`, `specs`, `validate` | Spec-first deterministic validation loop commands. |

### Standalone Commands
| Command | Description |
| :--- | :--- |
| [`harness apply`](#harness-apply) | Apply and reconcile a declarative configuration tree against Harness. |
| [`harness assess-compute`](#harness-assess-compute) | Assess task surface complexity and recommend optimal model tier & reasoning budget. |
| [`harness events`](#harness-events) | Show the event log. |
| [`harness init`](#harness-init) | Initialize a harness workspace. |
| [`harness introspect`](#harness-introspect) | Display runtime system diagnostics and dependency graph. |
| [`harness reflect`](#harness-reflect) | Run endogenous reflection loop across internal reports and transcripts. |
| [`harness run`](#harness-run) | Start the harness (interactive mode). |
| [`harness services`](#harness-services) | List registered services and their provider plugins. |
| [`harness ui`](#harness-ui) | Launch the real-time web control room dashboard. |
| [`harness watch`](#harness-watch) | Run the harness with live filesystem hot-reloading enabled. |

### Declared Aliases
| Alias | Canonical Target Command |
| :--- | :--- |
| `harness ai-native-harness` | `harness gate` |
| `harness artifact-miner` | `harness brain-miner` |
| `harness bq` | `harness bigquery` |
| `harness calibrator` | `harness calibrate` |
| `harness coding-harness` | `harness tau` |
| `harness conversation-miner` | `harness trajectory` |
| `harness differential-facet` | `harness facet` |
| `harness dissect` | `harness rea` |
| `harness ebbinghaus` | `harness memory` |
| `harness ephemeral-miner` | `harness temp` |
| `harness garf-reporting` | `harness garf` |
| `harness gemini-chat` | `harness gemini-vercel` |
| `harness gods-eye` | `harness gev` |
| `harness gradio-app` | `harness gradio` |
| `harness harness-architect` | `harness architect` |
| `harness harness-compass` | `harness compass` |
| `harness hf-doc-builder` | `harness doc-builder` |
| `harness icm-architect` | `harness icm` |
| `harness memory-decay` | `harness memory` |
| `harness miner` | `harness brain-miner` |
| `harness model-router` | `harness router` |
| `harness net-diag` | `harness network-forensics` |
| `harness network` | `harness network-forensics` |
| `harness obligation-ledger` | `harness rol` |
| `harness open-source-gis` | `harness gis` |
| `harness osint` | `harness gev` |
| `harness reverse-engineering` | `harness rea` |
| `harness security-guard` | `harness pre-commit-security` |
| `harness security-review` | `harness mantis` |
| `harness self-eval` | `harness eval` |
| `harness shift-left` | `harness pre-commit-security` |
| `harness streaming-chatbot` | `harness gemini-vercel` |
| `harness temp-miner` | `harness temp` |
| `harness trajectory-miner` | `harness trajectory` |
| `harness uncertainty-guard` | `harness uncertainty` |
| `harness validate-loop` | `harness validation-loop` |

---

## `harness agent`

Run and manage autonomous agent loops.

### Subcommands

#### `harness agent run`
```text
Execute an autonomous task using the active agent loop.
```

**Options:**
- `--max-steps`: Maximum thought/action steps [default: 10]

---

## `harness antigravity`

Google Antigravity SDK & CLI headless inspection seams.

### Subcommands

#### `harness antigravity policy`
```text
Evaluate tool execution against Antigravity declarative policy gates.
```

**Options:**
- `--tool`: Tool name to test [default: run_command]
- `--cmd`: Command line argument to test [default: echo hello]
- `--json-output`: Output in JSON format [default: False]

#### `harness antigravity status`
```text
Inspect Antigravity proactor and trigger runtime status.
```

**Options:**
- `--json-output`: Output status in JSON format [default: False]

#### `harness antigravity telemetry`
```text
Generate Antigravity dynamic statusline IPC payload.
```

**Options:**
- `--mode`: UI mode: idle, tool, review [default: idle]
- `--json-output`: Output statusline JSON payload [default: False]

---

## `harness architect`

Agent harness architecture audit, reliability scoring, and bet classification.

### Subcommands

#### `harness architect audit`
```text
Run comprehensive 5-part architecture and 4-layer stack boundary audit.
```

**Options:**
- `--target`, `-t`: Target directory to audit (defaults to workspace root)
- `--json`: Output report as structured JSON [default: False]

#### `harness architect bet`
```text
Classify team operational bottleneck into one of four architectural bets.
```

**Options:**
- `--bottleneck`, `-b`: Description of team operational bottleneck
- `--json`: Output classification as structured JSON [default: False]

#### `harness architect brief`
```text
Generate interactive HTML visual brief with Mermaid topology and reliability scorecard.
```

**Options:**
- `--target`, `-t`: Target directory to audit (defaults to workspace root)
- `--output`, `-o`: Destination file path for generated HTML brief
- `--open`: Open generated HTML brief in default browser [default: False]

#### `harness architect score`
```text
Evaluate 4 reliability mechanisms across Level 0 to Level 2.
```

**Options:**
- `--config`, `-c`: Path to harness configuration YAML/JSON
- `--json`: Output scorecard as structured JSON [default: False]

---

## `harness bigquery`

BigQuery in-database augmented analytics TVF execution suite.

### Subcommands

#### `harness bigquery brief`
```text
Generate and view interactive HTML visual brief with Mermaid DAG.
```

**Options:**
- `--table`: Target BigQuery table identifier [default: sample_dataset.metrics]
- `--metric-col`: Metric column name [default: total_trips]
- `--timestamp-col`: Timestamp column name [default: trip_date]
- `--dims`: Comma-separated dimension columns [default: subscriber_type,bike_type]
- `--output`: Optional output path for HTML visual brief [default: Sentinel.UNSET]
- `--open`: Open HTML brief in web browser [default: False]

#### `harness bigquery causal`
```text
Stage 4: Counterfactual causal lift estimation via AI.CAUSAL_EFFECT.
```

**Options:**
- `--table` *(required)*: Target BigQuery table identifier [default: Sentinel.UNSET]
- `--data-col` *(required)*: Data column name [default: Sentinel.UNSET]
- `--timestamp-col` *(required)*: Timestamp column name [default: Sentinel.UNSET]
- `--intervention` *(required)*: Intervention timestamp (e.g. 2026-02-15) [default: Sentinel.UNSET]
- `--output-ts`: Output time-series confidence intervals [default: True]
- `--dry-run`: Output compiled BigQuery TVF SQL without executing [default: False]
- `--json`: Output JSON result [default: False]

#### `harness bigquery change-points`
```text
Stage 2: Structural regime shift isolation via ML.DETECT_CHANGE_POINTS.
```

**Options:**
- `--table` *(required)*: Target BigQuery table identifier [default: Sentinel.UNSET]
- `--data-col` *(required)*: Metric column name [default: Sentinel.UNSET]
- `--timestamp-col` *(required)*: Timestamp column name [default: Sentinel.UNSET]
- `--min-prob`: Min change point probability (default: 0.95) [default: 0.95]
- `--dry-run`: Output compiled BigQuery TVF SQL without executing [default: False]
- `--json`: Output JSON result [default: False]

#### `harness bigquery drivers`
```text
Stage 3: Combinatorial driver attribution via AI.KEY_DRIVERS.
```

**Options:**
- `--table` *(required)*: Target BigQuery table identifier [default: Sentinel.UNSET]
- `--metric-col` *(required)*: Metric column name [default: Sentinel.UNSET]
- `--dims` *(required)*: Comma-separated dimension columns [default: Sentinel.UNSET]
- `--interest-cond` *(required)*: SQL boolean condition for interest period [default: Sentinel.UNSET]
- `--min-support`: Min Apriori support (default: 0.01) [default: 0.01]
- `--top-k`: Top K drivers (default: 20) [default: 20]
- `--dry-run`: Output compiled BigQuery TVF SQL without executing [default: False]
- `--json`: Output JSON result [default: False]

#### `harness bigquery pipeline`
```text
Execute complete 5-Stage BigQuery Augmented Analytics pipeline end-to-end.
```

**Options:**
- `--table` *(required)*: Target BigQuery table identifier [default: Sentinel.UNSET]
- `--metric-col` *(required)*: Metric column name [default: Sentinel.UNSET]
- `--timestamp-col` *(required)*: Timestamp column name [default: Sentinel.UNSET]
- `--dims` *(required)*: Comma-separated dimension columns [default: Sentinel.UNSET]
- `--intervention`: Optional intervention timestamp (isolated automatically if omitted) [default: Sentinel.UNSET]
- `--min-support`: Min Apriori support (default: 0.01) [default: 0.01]
- `--top-k`: Top K drivers (default: 20) [default: 20]
- `--dry-run`: Execute dry-run investigation with synthetic simulation [default: False]
- `--brief`: Optional path to output HTML visual brief [default: Sentinel.UNSET]
- `--json`: Output JSON result [default: False]

#### `harness bigquery profile`
```text
Stage 1: Temporal profiling via ML.TREND and ML.SEASONALITY.
```

**Options:**
- `--table` *(required)*: Target BigQuery table identifier [default: Sentinel.UNSET]
- `--data-col` *(required)*: Metric column name [default: Sentinel.UNSET]
- `--timestamp-col` *(required)*: Timestamp column name [default: Sentinel.UNSET]
- `--seasonalities`: Comma-separated seasonality periods (e.g. WEEKLY,MONTHLY) [default: Sentinel.UNSET]
- `--dry-run`: Output compiled BigQuery TVF SQL without executing [default: False]
- `--json`: Output JSON result [default: False]

---

## `harness brain-miner`

Brain workspace archaeology, scratch tool salvage, and transcript introspection.

### Subcommands

#### `harness brain-miner brief`
```text
Generate an HTML visual brief summarizing scratch tools and background tasks.
```

**Options:**
- `--brain-dir`: Path to brain workspace [default: C:\Users\spectre\.gemini\antigravity-ide\brain]
- `--out`: Output HTML file path

#### `harness brain-miner scan`
```text
Scan and catalog reusable Python scratch tools across conversation workspaces.
```

**Options:**
- `--brain-dir`: Path to brain workspace [default: C:\Users\spectre\.gemini\antigravity-ide\brain]
- `--depth`: Maximum directory scan depth [default: 3]
- `--json-output`: Output results in JSON format [default: False]

#### `harness brain-miner step`
```text
Fetch a specific step via O(1) binary seek with optional truncation dereference.
```

**Options:**
- `--dereference`: Auto-dereference truncated steps against transcript_full.jsonl [default: True]
- `--json-output`: Output raw JSON step payload [default: False]

#### `harness brain-miner triage`
```text
Triage background subprocess task logs for exit failures and deadlocks.
```

**Options:**
- `--brain-dir`: Path to brain workspace [default: C:\Users\spectre\.gemini\antigravity-ide\brain]
- `--depth`: Maximum directory scan depth [default: 4]
- `--json-output`: Output results in JSON format [default: False]

---

## `harness bridge`

Inspect and manage ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel).

### Subcommands

#### `harness bridge list`
```text
List all registered ecosystem bridges and their availability.
```

#### `harness bridge status`
```text
Check discovery status of peer ecosystem repositories.
```

---

## `harness calibrate`

Empirical coding harness component calibration, staging simulation, and forecasting.

### Subcommands

#### `harness calibrate brief`
```text
Generate interactive HTML visual brief with Mermaid topology and empirical scorecard.
```

**Options:**
- `--model`, `-m`: Target model identifier [default: Claude-3.7-Sonnet]
- `--params`, `-p`: Model parameter size in billions [default: 550.0]
- `--workload`, `-w`: Workload: terminal_cli | codebase_repo | mixed [default: terminal_cli]
- `--output`, `-o`: Destination file path for generated HTML brief
- `--open`: Open generated HTML brief in default browser [default: False]

#### `harness calibrate recommend`
```text
Derive optimal empirical harness configuration across model tiers and workloads.
```

**Options:**
- `--model`, `-m`: Target model identifier [default: Claude-3.7-Sonnet]
- `--params`, `-p`: Model parameter size in billions (e.g. 30, 120, 550) [default: 550.0]
- `--workload`, `-w`: Workload type: terminal_cli | codebase_repo | mixed [default: codebase_repo]
- `--budget`, `-b`: Context window usable budget in tokens [default: 131072]
- `--json`: Output recommendation as structured JSON [default: False]

#### `harness calibrate repatch`
```text
Predict re-patch churn, action granularity, and cost reduction using Fan et al. empirical laws.
```

**Options:**
- `--model-scale`, `-m`: Model scale: weak_30b | mid_120b | strong_550b [default: strong_550b]
- `--action-space`, `-a`: Action space: predefined_tools | bash_only [default: bash_only]
- `--workload`, `-w`: Workload: terminal_cli | codebase_repo | mixed [default: terminal_cli]
- `--json`: Output prediction as structured JSON [default: False]

#### `harness calibrate staging`
```text
Simulate Two-Tier Context Staging ($T_4$) over an execution transcript.
```

**Options:**
- `--budget`, `-b`: Usable context window budget [default: 100000]
- `--turns`, `-t`: Number of turns to simulate [default: 10]
- `--json`: Output simulation result as structured JSON [default: False]

---

## `harness compass`

HarnessCompass CLI — Automatic harness discovery, calibration & R3 integration.

### Subcommands

#### `harness compass brief`
```text
Generate interactive standalone HTML visual brief.
```

**Options:**
- `--output`, `-o`: Output file path for HTML brief

#### `harness compass feedback`
```text
Ground agent usability feedback against execution traces.
```

**Options:**
- `--desired`: Desired change [default: Increase capability]
- `--kind`: Feedback kind [default: improve_existing]
- `--component`: Component surface [default: tool_impl]
- `--trace-refs`: Comma-separated cited turn IDs (e.g. turn_1,turn_4) [default: turn_1]
- `--attribution`: Failure attribution source [default: harness]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness compass gate`
```text
Validate a candidate harness edit against Content and Placement invariants.
```

**Options:**
- `--id`: Edit identifier [default: chg-01]
- `--surface`, `-s`: Target component surface [default: systemprompt]
- `--description`, `-d`: Edit description [default: Candidate edit]
- `--file`: Destination file [default: systemprompt.md]
- `--advisory`: Whether edit contains behavioral advice [default: True]
- `--executable`: Whether edit contains deterministic executable code [default: False]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness compass merge`
```text
Execute R3 integration: Revision, Recombination, and Occam's Razor Refinement.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

#### `harness compass run`
```text
Simulate a complete 5-stage evolution round with acceptance gating.
```

**Options:**
- `--round-num`, `-r`: Evolution round index [default: 1]
- `--baseline`, `-b`: Starting baseline Pass@1 [default: 0.54]
- `--structural-score`, `-s`: Track A (Structural) score [default: 0.66]
- `--guidance-score`, `-g`: Track B (Guidance) score [default: 0.62]
- `--json-output`: Emit raw JSON output [default: False]

---

## `harness config`

Manage and validate declarative configuration trees.

### Subcommands

#### `harness config validate`
```text
Validate syntax and schema of a declarative configuration file.
```

---

## `harness context`

Manage 3-tier AST reachability compilation and context optimization.

### Subcommands

#### `harness context add`
```text
Register a typed context item into session origin ledger.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--type`, `-t` *(required)*: Semantic channel context type [default: Sentinel.UNSET]
- `--content`, `-c` *(required)*: Content text [default: Sentinel.UNSET]
- `--source`: Origin source identifier
- `--priority`, `-p`: Priority score [default: 0]
- `--json`: Emit JSON output [default: False]

#### `harness context assemble`
```text
Render structured prompt partitioned by typed semantic channels.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--budget-tokens`: Maximum token budget for assembled prompt [default: 4000]
- `--json`: Emit JSON output [default: False]

#### `harness context compile`
```text
Compile 3-tier AST reachability context starting from a target file.
```

**Options:**
- `--repo-root`, `-r`: Root directory of the repository
- `--max-hops`, `-h`: Maximum reachability hop depth [default: 2]

#### `harness context govern`
```text
Execute complete 5-stage context governance audit and compute tier assessment.
```

**Options:**
- `--root`, `-r`: Repository root path [default: .]
- `--complexity`, `-c`: 5D complexity score (0.0 to 1.0) [default: 0.5]
- `--json`: Output as JSON [default: False]
- `--silent`: Suppress output on pass [default: False]

#### `harness context ledger`
```text
Audit origin ledger or trace multi-hop Isnad lineage for a session.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--id`: Inspect specific item derivation lineage
- `--json`: Emit JSON output [default: False]

#### `harness context lint`
```text
Verify repository context files across 4 quality dimensions.
```

**Options:**
- `--root`, `-r`: Repository root path [default: .]
- `--json`: Output as JSON [default: False]
- `--silent`: Suppress output on pass [default: False]

#### `harness context skeletonize`
```text
Extract structural interface skeleton from Python source file.
```

#### `harness context snapshot`
```text
Export or restore a context session snapshot.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--export`: File path to export snapshot JSON
- `--import`: File path to import snapshot JSON
- `--json`: Emit JSON output [default: False]

#### `harness context sync`
```text
Synchronize downstream vendor files against canonical source.
```

**Options:**
- `--root`, `-r`: Repository root path [default: .]
- `--source`, `-s`: Canonical source filename [default: AGENTS.md]
- `--dry-run`: Check for drift without writing changes [default: False]
- `--silent`: Suppress output on success [default: False]

#### `harness context transform`
```text
Explicitly transition a context item across permitted policy boundaries.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--id` *(required)*: Target item request ID [default: Sentinel.UNSET]
- `--to-type` *(required)*: Target context type [default: Sentinel.UNSET]
- `--source`: Source identifier
- `--json`: Emit JSON output [default: False]

#### `harness context validate-tool`
```text
Validate tool output and promote to verified evidence.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--id`: Existing tool_output item request ID
- `--tool-name`: Tool name if creating new tool_output item [default: tool]
- `--output-json`: Raw tool output payload if creating new item
- `--strict`: Enforce strict validation [default: False]
- `--json`: Emit JSON output [default: False]

---

## `harness creator`

Creator Mode tools for plugin authoring.

### Subcommands

#### `harness creator archetypes`
```text
List all available plugin archetypes and templates.
```

#### `harness creator build`
```text
Scaffold a new plugin project.
```

**Options:**
- `--description`, `-d`: Plugin description
- `--target-dir`: Output directory
- `--language`, `-l`: Implementation language [default: python]
- `--tools`, `-t`: Comma-separated tool handler names [default: execute]
- `--deps`: Comma-separated external dependencies
- `--isolation`, `-i`: Sandbox isolation mode [default: subprocess]
- `--category`, `-c`: Domain category [default: general]
- `--preset`, `-p`: Plugin archetype preset [default: general]
- `--author`, `-a`: Plugin author [default: Harness Developer]

#### `harness creator init`
```text
Interactive wizard for scaffolding a new plugin project.
```

#### `harness creator remediate`
```text
Auto-repair missing manifest, boilerplate functions, and dependency files.
```

#### `harness creator scaffold`
```text
Scaffold a new plugin project.
```

**Options:**
- `--description`, `-d`: Plugin description
- `--target-dir`: Output directory
- `--language`, `-l`: Implementation language [default: python]
- `--tools`, `-t`: Comma-separated tool handler names [default: execute]
- `--deps`: Comma-separated external dependencies
- `--isolation`, `-i`: Sandbox isolation mode [default: subprocess]
- `--category`, `-c`: Domain category [default: general]
- `--preset`, `-p`: Plugin archetype preset [default: general]
- `--author`, `-a`: Plugin author [default: Harness Developer]

#### `harness creator validate`
```text
Validate a plugin manifest, source files, and sandbox execution.
```

**Options:**
- `--dry-run`: Boot sandbox and execute entrypoints [default: False]
- `--timeout`: Sandbox dry-run timeout in seconds [default: 15.0]
- `--fix`, `--remediate`: Automatically repair detected issues [default: False]

---

## `harness data`

Enterprise data management, contracts, quality profiling, and Medallion pipelines.

### Subcommands

#### `harness data maturity`
```text
Evaluate Level 0–5 Data Management Maturity.
```

**Options:**
- `--scores`, `--survey`: JSON/YAML string or path with capability level scores (0 to 5) [default: Sentinel.UNSET]
- `--target`: Target maturity level (default: 4) [default: 4]
- `--org`: Organization name [default: Enterprise Organization]
- `--summary`: Print markdown summary to stdout [default: False]
- `--output`: Optional output JSON report path [default: Sentinel.UNSET]
- `--json`: Output JSON result to stdout [default: False]

#### `harness data pipeline`
```text
Execute end-to-end Medallion lakehouse pipeline (Bronze -> Silver -> Gold).
```

**Options:**
- `--raw`, `--data`, `--dataset` *(required)*: Path to raw dataset JSON/YAML [default: Sentinel.UNSET]
- `--contract` *(required)*: Path to contract JSON/YAML [default: Sentinel.UNSET]
- `--quality`, `--rules`: Path to quality rules JSON/YAML [default: Sentinel.UNSET]
- `--source`: Source system name [default: Sentinel.UNSET]
- `--key`, `--keys`: Match/primary key fields [default: Sentinel.UNSET]
- `--out-gold`: Path to output Gold curated marts JSON [default: Sentinel.UNSET]
- `--out-quarantine`: Path to output quarantined records JSON [default: Sentinel.UNSET]
- `--json`: Output JSON result to stdout [default: False]

#### `harness data profile`
```text
Profile dataset across 6 DAMA quality dimensions.
```

**Options:**
- `--data`, `--dataset` *(required)*: Path to dataset JSON/YAML file [default: Sentinel.UNSET]
- `--rules`, `--config`: Path to quality rules YAML/JSON file [default: Sentinel.UNSET]
- `--key`: Primary key field [default: id]
- `--threshold`: Pass score threshold (0-100) [default: 70.0]
- `--markdown`: Output Markdown report to stdout [default: False]
- `--out-markdown`: Optional output Markdown report file path [default: Sentinel.UNSET]
- `--output`: Optional output JSON report path [default: Sentinel.UNSET]
- `--json`: Output JSON result to stdout [default: False]

#### `harness data resolve`
```text
Resolve multi-source records into canonical Golden Records.
```

**Options:**
- `--data`, `--dataset` *(required)*: Path to input entity records JSON/YAML [default: Sentinel.UNSET]
- `--key`, `--keys`: Match key fields [default: Sentinel.UNSET]
- `--source`, `--sources`: Source system priority order [default: Sentinel.UNSET]
- `--output`: Optional output JSON path for golden records [default: Sentinel.UNSET]
- `--json`: Output JSON result to stdout [default: False]

#### `harness data topk-analyze`
```text
Analyze DeepSelect TopK workload feasibility and kernel variant dispatch.
```

**Options:**
- `--batch-size`: Batch size [default: 4]
- `--vocab-size`: Vocab / sequence length [default: 129280]
- `--topk`: TopK value [default: 512]
- `--dtype`: Data type (bfloat16 or float32) [default: bfloat16]
- `--scenario`: Scenario (lightning_indexer or sampling) [default: lightning_indexer]
- `--json`: Output JSON result [default: False]

#### `harness data topk-bounds`
```text
Compute mathematical bounds on TopK candidate volume and speedup.
```

**Options:**
- `--batch-size`: Batch size [default: 4]
- `--vocab-size`: Vocab / sequence length [default: 129280]
- `--topk`: TopK value [default: 512]
- `--block-size`: Block size B [default: 1024]
- `--compact-threshold`: Compaction threshold B2 [default: 1024]
- `--dtype`: Data type [default: bfloat16]
- `--json`: Output JSON result [default: False]

#### `harness data topk-recommend`
```text
Recommend optimal DeepSelect kernel configurations.
```

**Options:**
- `--batch-size`: Batch size [default: 4]
- `--vocab-size`: Vocab / sequence length [default: 129280]
- `--topk`: TopK value [default: 512]
- `--dtype`: Data type [default: bfloat16]
- `--json`: Output JSON result [default: False]

#### `harness data validate`
```text
Validate dataset against an Open Data Contract.
```

**Options:**
- `--contract` *(required)*: Path to contract JSON/YAML file [default: Sentinel.UNSET]
- `--data`, `--dataset` *(required)*: Path to dataset JSON/YAML file [default: Sentinel.UNSET]
- `--max-quarantine`: Max quarantine ratio before failure [default: 0.05]
- `--output`: Optional output JSON path [default: Sentinel.UNSET]
- `--json`: Output JSON result to stdout [default: False]

---

## `harness datasets`

Hugging Face Datasets inspection, streaming, transformation, and lakehouse conversion commands.

### Subcommands

#### `harness datasets commit-vault`
```text
Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40).
```

**Options:**
- `--split`: Dataset split [default: train]
- `--vault-root`: Custom Knowledge Vault directory root

#### `harness datasets convert`
```text
Convert dataset file between CSV, JSON, Arrow, and Parquet lakehouse formats.
```

**Options:**
- `--format`: Target format: parquet, arrow, json, jsonl, csv [default: parquet]

#### `harness datasets inspect`
```text
Inspect dataset metadata, splits, row count, and schema.
```

**Options:**
- `--split`: Dataset split to inspect [default: train]

#### `harness datasets profile`
```text
Extract column schemas, Arrow data types, nullability, and sample values.
```

#### `harness datasets sample`
```text
Sample records from a local or streaming dataset without RAM blowout.
```

**Options:**
- `--split`: Dataset split [default: train]
- `--n`: Number of records to sample [default: 5]

#### `harness datasets strategy`
```text
Evaluate dataset footprint and select between memory-mapped Arrow and streaming.
```

**Options:**
- `--split`: Dataset split [default: train]
- `--threshold-mb`: Threshold in MB to trigger streaming strategy [default: 500]

#### `harness datasets transform`
```text
Execute lazy filtering, column projection, and batch transformation.
```

**Options:**
- `--filter-field`: Field to filter on
- `--filter-op`: Filter operator: eq, neq, gt, gte, lt, lte, contains, in
- `--filter-val`: Filter value to match
- `--select-cols`: Comma-separated column names to select
- `--batch-size`: Chunk batch size [default: 100]

---

## `harness doc`

Repository documentation auditing, AST symbol drift verification, and scaffolding.

### Subcommands

#### `harness doc audit`
```text
Audit Python codebase and calculate documentation coverage metrics.
```

**Options:**
- `--target`, `-t`: Target directory to audit (defaults to workspace root)
- `--min-coverage`, `-m`: Minimum acceptable documentation coverage percentage [default: 80.0]
- `--exclude`, `-e`: Patterns to exclude from scanning [default: Sentinel.UNSET]
- `--json`: Output report as structured JSON [default: False]

#### `harness doc brief`
```text
Render interactive HTML visual brief with Mermaid topology and coverage metrics.
```

**Options:**
- `--target`, `-t`: Target directory to inspect
- `--output`, `-o`: Destination HTML visual brief path

#### `harness doc drift`
```text
Inspect markdown documents for broken relative links and stale AST symbol references.
```

**Options:**
- `--docs-dir`, `-d`: Markdown docs directory to verify (defaults to workspace docs/ and READMEs)
- `--no-symbols`: Disable AST code symbol drift checking [default: False]
- `--json`: Output report as structured JSON [default: False]

#### `harness doc scaffold`
```text
Scaffold standardized Diataxis documentation for a Python module.
```

**Options:**
- `--type`: Diataxis documentation archetype [default: api]
- `--output`, `-o`: Destination markdown output path

#### `harness doc stats`
```text
Inspect AST parsing cache performance statistics.
```

**Options:**
- `--json`: Output cache statistics as JSON [default: False]

#### `harness doc wiki-compile`
```text
Compile raw markdown notes into a cross-referenced Wiki knowledge base.
```

**Options:**
- `--incremental`: Only recompile and write changed files [default: False]
- `--no-lint`: Disable post-compilation link and orphan linter [default: False]
- `--json`: Emit JSON output [default: False]

#### `harness doc wiki-lint`
```text
Audit compiled markdown wiki for broken links, missing entities, and orphans.
```

**Options:**
- `--json`: Emit JSON output [default: False]

---

## `harness doc-builder`

HF Doc Builder — Documentation compilation, link verification, and MDX transpilation.

### Subcommands

#### `harness doc-builder chunk`
```text
Hierarchically partition documentation along heading trees for vector search.
```

**Options:**
- `--text`, `-t`: Markdown text to chunk
- `--file`, `-f`: Path to markdown file to chunk
- `--title`: Top-level title of document [default: Documentation]
- `--max-size`: Maximum character size per chunk [default: 1500]
- `--json`: Output results as JSON [default: False]

#### `harness doc-builder convert`
```text
Transpile Markdown, RST, or IPYNB into MDX with Svelte tags.
```

**Options:**
- `--source`, `-s` *(required)*: Path to source document or raw markdown string [default: Sentinel.UNSET]
- `--format`, `-f`: Target output format [default: mdx]
- `--output`, `-o`: Optional output file path
- `--json`: Output results as JSON [default: False]

#### `harness doc-builder inspect`
```text
Extract structured signatures, parameters, and docstrings from Python objects.
```

**Options:**
- `--package`, `-p` *(required)*: Target Python package name [default: Sentinel.UNSET]
- `--object`, `-o` *(required)*: Target class, function, or method name [default: Sentinel.UNSET]
- `--mock-heavy`: Intercept heavy dependencies via sys.meta_path [default: True]
- `--source-file`, `-s`: Optional Python source file for static AST parsing
- `--json`: Output results as JSON [default: False]

#### `harness doc-builder lint`
```text
Lint and format code examples inside docstrings and MDX files.
```

**Options:**
- `--file`, `-f` *(required)*: Path to documentation file to lint [default: Sentinel.UNSET]
- `--fix`: Automatically format and fix issues [default: False]
- `--json`: Output results as JSON [default: False]

#### `harness doc-builder verify`
```text
Verify internal documentation links, anchor targets, and TOC completeness.
```

**Options:**
- `--docs-dir`, `-d`: Path to documentation root directory [default: docs]
- `--anchors`: Verify heading anchor fragments [default: True]
- `--toc`: Verify table-of-contents integrity and orphan pages [default: True]
- `--json`: Output results as JSON [default: False]

---

## `harness dock`

Agent Dock — workstation port for plugging agents into repositories.

### Subcommands

#### `harness dock inspect`
```text
Inspect repository dock manifest without linking or state changes.
```

**Options:**
- `--json`: Output inspection report as JSON [default: False]

#### `harness dock link`
```text
Link an agent dock and record its approval digest.
```

**Options:**
- `--name`: Custom alias for the linked dock
- `--approve`: Approve declared permissions and boundaries [default: False]
- `--json`: Output link record as JSON [default: False]

#### `harness dock list`
```text
List all linked agent docks and their approval status.
```

**Options:**
- `--json`: Output dock list as JSON [default: False]

#### `harness dock run`
```text
Execute a declared procedure on a linked agent dock.
```

**Options:**
- `--dry-run`: Simulate execution without running commands [default: False]
- `--json`: Output run results as JSON [default: False]

#### `harness dock tools`
```text
List tools exposed by a linked dock (declared tools, unverified against host registry).
```

**Options:**
- `--json`: Output tools list as JSON [default: False]

---

## `harness eval`

Self-Evaluating AI Pipeline — 3-layer LLM quality evaluation & statistical gating.

### Subcommands

#### `harness eval brief`
```text
Generate standalone interactive HTML visual brief in %TEMP%.
```

**Options:**
- `--result` *(required)*: Path to regression JSON result [default: Sentinel.UNSET]
- `--gate`: Optional path to statistical gate JSON
- `--output`: Destination HTML file path

#### `harness eval drift`
```text
Audit automated LLM judge drift against human calibration ratings.
```

**Options:**
- `--human` *(required)*: Path to JSON file of human scores [default: Sentinel.UNSET]
- `--judge` *(required)*: Path to JSON file of judge scores [default: Sentinel.UNSET]
- `--max-drift`: Maximum allowable drift [default: 0.5]
- `--json`: Output as JSON payload [default: False]

#### `harness eval gate`
```text
Run Stage 5 paired Student's t-test statistical significance deployment gate.
```

**Options:**
- `--before` *(required)*: Path or JSON string of pre-change scores [default: Sentinel.UNSET]
- `--after` *(required)*: Path or JSON string of post-change scores [default: Sentinel.UNSET]
- `--alpha`: Statistical significance alpha [default: 0.05]
- `--json`: Output as JSON payload [default: False]

#### `harness eval judge`
```text
Execute Layer 2 anchored semantic evaluation with median consensus.
```

**Options:**
- `--model`: Judge model identifier [default: gpt-4o-mini]
- `--judges`: Number of consensus judges [default: 3]
- `--threshold`: Minimum passing score [default: 3.5]
- `--json`: Output as JSON payload [default: False]

#### `harness eval kappa`
```text
Calculate Layer 3 Cohen's Kappa human inter-annotator agreement.
```

**Options:**
- `--json`: Output as JSON payload [default: False]

#### `harness eval layer1`
```text
Execute sub-millisecond Layer 1 deterministic sanity checks on raw text.
```

**Options:**
- `--schema`: Expected schema format (json, xml)
- `--min-len`: Minimum character length [default: 10]
- `--max-len`: Maximum character length [default: 5000]
- `--whitelist`: Comma-separated authorized URL domains
- `--syntax`: Language syntax validator (e.g. python)
- `--json`: Output as JSON payload [default: False]

#### `harness eval regression`
```text
Execute CI/CD regression suite across curated golden test dataset.
```

**Options:**
- `--golden` *(required)*: Path to golden dataset JSON [default: Sentinel.UNSET]
- `--min-score`: Minimum passing score [default: 3.5]
- `--json`: Output as JSON payload [default: False]

---

## `harness facet`

Differential Facet Verifier — Multi-provider evidence comparison and facet availability semantics.

### Subcommands

#### `harness facet claim-absence`
```text
Evaluate whether an absence claim is legally valid under declared traversal coverage.
```

#### `harness facet compare`
```text
Compare two observation dossiers and emit a 3-valued DifferentialReport.
```

**Options:**
- `--provider-differ`: Explicitly toggle cross-provider syntax decoupling
- `--format`: Output format [default: rich]

#### `harness facet export`
```text
Export machine-parseable JSON certificate from a differential report.
```

#### `harness facet verify`
```text
Audit report integrity and verify absence claim validity.
```

**Options:**
- `--strict`: Exit non-zero if overall status is 'unknown' [default: False]

---

## `harness garf`

Google Garf Declarative SQL Reporting & Analytical Workflow DAGs.

### Subcommands

#### `harness garf export`
```text
Execute query simulation and export tabular report to destination file.
```

**Options:**
- `--query`, `-q`: SQL query string to execute.
- `--query-file`, `-f`: Path to .sql file.
- `--dest-type`, `-t`:  [default: json]
- `--dest-path`, `-p`: Path for output file. [default: output.json]
- `--rows`, `-r`: Number of rows to simulate. [default: 5]
- `--seed`, `-s`: PRNG seed for simulation reproducibility. [default: 42]
- `--json-out`: Output execution receipt as JSON. [default: False]

#### `harness garf parse`
```text
Parse a reporting API SQL query into structured components.
```

**Options:**
- `--query`, `-q`: SQL query string to parse.
- `--query-file`, `-f`: Path to .sql file.
- `--json-out`: Output parsed query specification as JSON. [default: False]

#### `harness garf simulate`
```text
Simulate a synthetic tabular report from a query specification.
```

**Options:**
- `--query`, `-q`: SQL query string to simulate.
- `--query-file`, `-f`: Path to .sql file.
- `--rows`, `-r`: Number of synthetic rows to generate. [default: 5]
- `--seed`, `-s`: PRNG seed for simulation reproducibility. [default: 42]
- `--json-out`: Output simulated rows as JSON. [default: False]

#### `harness garf workflow`
```text
Execute a multi-step analytical workflow DAG from configuration.
```

**Options:**
- `--config`, `-c` *(required)*: Path to YAML or JSON workflow configuration file. [default: Sentinel.UNSET]
- `--param`, `-p`: Context parameters formatted as key=value. [default: Sentinel.UNSET]
- `--json-out`: Output execution receipt as JSON. [default: False]

---

## `harness gate`

AI-native harness governance, 4 behavioral gates, and drift telemetry.

### Subcommands

#### `harness gate audit`
```text
Run comprehensive AI-native harness governance audit across all 3 pillars.
```

**Options:**
- `--target`, `-t`: Target directory to audit (defaults to workspace root)
- `--json`: Output report as structured JSON [default: False]

#### `harness gate brief`
```text
Render interactive HTML visual brief with Mermaid topology and telemetry tables.
```

**Options:**
- `--target`, `-t`: Target directory to audit (defaults to workspace root)
- `--output`, `-o`: Path where generated HTML brief will be saved
- `--open`: Open generated visual brief in default web browser [default: False]

#### `harness gate drift`
```text
Calculate Git code-to-doc commit drift count and status badges.
```

**Options:**
- `--target`, `-t`: Target directory to audit (defaults to workspace root)
- `--json`: Output drift report as structured JSON [default: False]

#### `harness gate evaluate`
```text
Evaluate the 4 Behavioral Verification Gates.
```

**Options:**
- `--target`, `-t`: Target directory to evaluate
- `--json`: Output evaluation as structured JSON [default: False]

#### `harness gate mcp`
```text
Audit MCP server posture for zero credentials, PAT forwarding, and uniform leak defense.
```

**Options:**
- `--config`, `-c`: Optional path to MCP configuration
- `--json`: Output security check as structured JSON [default: False]

#### `harness gate mine`
```text
Mine unanswered assistant queries into a demand-ranked documentation backlog.
```

**Options:**
- `--logs`, `-l`: Optional path to query logs file
- `--json`: Output mined backlog as structured JSON [default: False]

---

## `harness gemini-vercel`

Gemini & Vercel Streaming Chatbot CLI — Plain-text chunk streaming & edge architecture.

### Subcommands

#### `harness gemini-vercel brief`
```text
Generate interactive standalone HTML visual brief.
```

**Options:**
- `--output`, `-o`: Output file path for HTML brief

#### `harness gemini-vercel inspect`
```text
Run static analysis against Johnson Samuel's 5 production streaming rubrics.

TARGET can be a path to a serverless/client file or raw code string.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

#### `harness gemini-vercel scaffold`
```text
Scaffold a 3-tier production Gemini & Vercel streaming application.
```

**Options:**
- `--name`, `-n`: Application name identifier [default: my_streaming_chatbot]
- `--framework`, `-f`: Frontend framework [default: react]
- `--language`, `-l`: Programming language [default: javascript]
- `--model`, `-m`: Gemini model identifier [default: gemini-2.5-flash]
- `--output-dir`, `-o`: Target directory to write files [default: .]
- `--write`: Write files to disk or display manifest [default: False]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness gemini-vercel verify`
```text
Simulate unbuffered plain-text chunk streaming with latency metrics.
```

**Options:**
- `--prompt`, `-p`: Prompt to simulate streaming [default: Explain streaming HTTP chunking in simple terms]
- `--chunks`, `-c`: Number of chunks to simulate [default: 5]
- `--json-output`: Emit raw JSON output [default: False]

---

## `harness gev`

God's Eye View — Planetary OSINT, real-time telemetry feeds, and 3D geospatial rendering.

### Subcommands

#### `harness gev brief`
```text
Generate composite multi-domain situation overview for an area.
```

**Options:**
- `--lat` *(required)*: Center latitude [default: Sentinel.UNSET]
- `--lon` *(required)*: Center longitude [default: Sentinel.UNSET]
- `--radius-km`: Search radius in kilometers [default: 250.0]
- `--query`: Optional text query or analyst focus
- `--json`: Emit raw JSON payload [default: False]

#### `harness gev flights`
```text
Fetch live or simulated aviation transponder vectors.
```

**Options:**
- `--lat` *(required)*: Center latitude [default: Sentinel.UNSET]
- `--lon` *(required)*: Center longitude [default: Sentinel.UNSET]
- `--radius-km`: Search radius in km [default: 150.0]
- `--callsign`: Callsign filter
- `--military`: Filter strictly for military flights [default: False]
- `--limit`: Maximum flights to return [default: 50]
- `--json`: Emit raw JSON payload [default: False]

#### `harness gev hazards`
```text
Fetch environmental telemetry: earthquakes, active fires, cyclones, and weather.
```

**Options:**
- `--lat` *(required)*: Center latitude [default: Sentinel.UNSET]
- `--lon` *(required)*: Center longitude [default: Sentinel.UNSET]
- `--radius-km`: Search radius in km [default: 300.0]
- `--kind`: Hazard category [default: all]
- `--json`: Emit raw JSON payload [default: False]

#### `harness gev render`
```text
Render 3D Cesium globe snapshots, satellite orthomosaics, or Street View headings.
```

**Options:**
- `--lat` *(required)*: Center latitude [default: Sentinel.UNSET]
- `--lon` *(required)*: Center longitude [default: Sentinel.UNSET]
- `--mode`: Rendering engine [default: globe]
- `--output`: Output destination path
- `--json`: Emit raw JSON payload [default: False]

#### `harness gev spatial`
```text
Query tactical awareness, orbital satellite passes, infrastructure, or CCTV assets.
```

**Options:**
- `--lat` *(required)*: Center latitude [default: Sentinel.UNSET]
- `--lon` *(required)*: Center longitude [default: Sentinel.UNSET]
- `--radius-km`: Radius in km [default: 250.0]
- `--kind`: Spatial query kind [default: infra]
- `--query`: Text query filter
- `--json`: Emit raw JSON payload [default: False]

#### `harness gev status`
```text
Probe runtime environment, Node.js bridge availability, and cache configuration.
```

**Options:**
- `--json`: Emit raw JSON status payload [default: False]

#### `harness gev vessels`
```text
Retrieve real-time maritime AIS vessel records.
```

**Options:**
- `--lat` *(required)*: Center latitude [default: Sentinel.UNSET]
- `--lon` *(required)*: Center longitude [default: Sentinel.UNSET]
- `--radius-km`: Search radius in km [default: 200.0]
- `--name`: Vessel name filter
- `--limit`: Maximum vessels to return [default: 50]
- `--json`: Emit raw JSON payload [default: False]

---

## `harness gis`

Open-Source GIS analytical engine selection, CRS safety & topology auditing.

### Subcommands

#### `harness gis architect`
```text
Execute end-to-end spatial architecture interrogation and print structured receipt.
```

**Options:**
- `--profile-json`, `-p` *(required)*: Workload JSON profile [default: Sentinel.UNSET]
- `--pipeline-json`, `-d`: Optional pipeline steps JSON
- `--generate-brief`: Render Stage 5 HTML visual brief [default: True]

#### `harness gis route`
```text
Route spatial workload to optimal primary and secondary open-source GIS engines.
```

**Options:**
- `--domain`, `-d` *(required)*: Spatial analytical domain (e.g. lidar_hydrology, terrain_morphometry) [default: Sentinel.UNSET]
- `--geometry-type`, `-g`: Geometry structure (point_cloud, raster_dem, etc.) [default: vector_polygon]
- `--format`, `-f`: Input data formats (LAS, GeoTIFF, etc.) [default: Sentinel.UNSET]
- `--sector`, `-s`: Operational sector [default: civilian]
- `--analysis`, `-a`: Specific analytical operation (twi, moran_i, etc.)
- `--has-lidar`: Workload contains LiDAR point clouds [default: False]
- `--needs-statistics`: Requires spatial econometrics [default: False]
- `--needs-mobile`: Requires field GPS / mobile surveying [default: False]
- `--generate-brief`: Render Stage 5 interactive HTML visual brief [default: False]
- `--json-out`: Emit raw JSON output [default: False]

#### `harness gis validate`
```text
Validate spatial execution pipeline DAG for CRS projection safety.
```

**Options:**
- `--pipeline-file`, `-f` *(required)*: Path to pipeline JSON file [default: Sentinel.UNSET]

---

## `harness gradio`

Gradio App Architect CLI — Production AI interface engineering & AST diagnostics.

### Subcommands

#### `harness gradio brief`
```text
Generate interactive standalone HTML visual brief.
```

**Options:**
- `--output`, `-o`: Output file path for HTML brief

#### `harness gradio inspect`
```text
Run AST static analysis against Eva J Patel's 5 production Gradio rubrics.

TARGET can be a path to a Python file or raw Python code string.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

#### `harness gradio scaffold`
```text
Scaffold a decoupled 3-layer production Gradio application.
```

**Options:**
- `--name`, `-n`: Application name identifier [default: my_gradio_app]
- `--topology`, `-t`: Interface layout topology [default: blocks]
- `--concurrency-limit`, `-c`: Queued concurrent execution bound [default: 5]
- `--output-dir`, `-o`: Target directory to write files [default: .]
- `--write`: Write files to disk or display manifest [default: False]
- `--json-output`: Emit raw JSON output [default: False]

---

## `harness icm`

Interpretable Context Methodology (ICM) workspace architecture & verification.

### Subcommands

#### `harness icm audit`
```text
Audit an ICM workspace against the 10 invariants and token limits.
```

**Options:**
- `--json`: Output raw JSON results [default: False]

#### `harness icm index`
```text
Rebuild _index.md files across specified shelves and record folders.
```

**Options:**
- `--root`: Root workspace directory anchor [default: .]
- `--json`: Output raw JSON results [default: False]

#### `harness icm links`
```text
Verify all relative links, contract inputs, and pointer lines.
```

**Options:**
- `--skip`, `-s`: Folders to skip [default: Sentinel.UNSET]
- `--graph`, `-g`: Output path for JSONL graph
- `--json`: Output raw JSON results [default: False]

#### `harness icm quotes`
```text
Verify quote provenance against raw sources and keep-out lists.
```

**Options:**
- `--show-cuts`: List text dropped by cuts [default: False]
- `--json`: Output raw JSON results [default: False]

#### `harness icm scaffold`
```text
Scaffold a new production-grade ICM workspace from one of the 5 canonical forms.
```

**Options:**
- `--form`:  [default: pipeline]
- `--name`: Workspace name or title
- `--json`: Output raw JSON results [default: False]

---

## `harness knowledge`

Manage and query the distilled Knowledge Vault and Isnad lineage.

### Subcommands

#### `harness knowledge backfill`
```text
Mechanically backfill references_code, became_skill, became_plugin, supersedes, and same_domain edges.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--dry-run`: Display proposed backfill edges without modifying disk [default: False]
- `--commit`: Commit backfilled edges non-destructively to metadata.json on disk [default: False]
- `--max-tag-freq`: Tag frequency threshold for mega-tag exclusion [default: 0.15]

#### `harness knowledge contradictions`
```text
Audit Knowledge Vault for contradictory claims, polarity antinomies, and supersessions.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge dependents`
```text
List inbound dependents pointing to a specific Knowledge Item, skill, or code path.
```

**Options:**
- `--transitive`: Traverse multi-hop inbound dependents using SQLite recursive CTE [default: False]
- `--max-depth`: Maximum search hops when --transitive is set (default: 6) [default: 6]
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge export`
```text
Export derived knowledge graph to JSON, GEXF, GraphML, or standalone interactive HTML.
```

**Options:**
- `--format`, `-f`: Export serialization format (default: json) [default: json]
- `--out`, `-o`: Target file path (defaults to outputs/knowledge_graph.<format> or %TEMP% for --open)
- `--nodes`: Materialize all entities or filter strictly to Knowledge Items [default: all]
- `--include-single-tag-edges`: Derive edges between items sharing a single non-mega tag [default: False]
- `--include-shared-source`: Derive edges between items citing the same code or repository source [default: False]
- `--max-tag-freq`: Tag frequency ratio (0.0 - 1.0) above which tags are excluded as mega-tags [default: 0.15]
- `--min-confidence`: Minimum edge confidence threshold [default: 0.0]
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--dynamic`: Enable dynamic temporal attributes (start/end dates) for GEXF export [default: False]
- `--open`: Automatically open generated HTML brief or export in browser/viewer [default: False]

#### `harness knowledge hygiene`
```text
Audit and mechanically triage uncategorized items and untagged items.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--suggest-categories`: Propose canonical TaxonomyDomain for uncategorized items [default: True]
- `--suggest-tags`: Propose 2-5 high-signal domain tags for untagged items [default: True]
- `--apply`: Persist proposed category and tag updates to metadata.json on disk [default: False]
- `--json`: Output hygiene proposals in JSON format [default: False]

#### `harness knowledge joint-query`
```text
Execute unified dual-graph query across Knowledge Vault and Skill Graph.
```

**Options:**
- `--limit`, `-l`: Maximum items to return per graph [default: 5]
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--skills-root`: Root directory for skills discovery [default: .]
- `--json`: Emit raw JSON payload [default: False]

#### `harness knowledge lifecycle`
```text
Evaluate retrieval success rates and update item lifecycle status (PROMOTED / DEMOTED).
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--min-retrievals`: Minimum retrievals before evaluating promote/demote [default: 5]
- `--promote-ratio`: Success ratio threshold for promotion [default: 0.75]
- `--demote-ratio`: Success ratio threshold for demotion [default: 0.25]
- `--show-contradictions`: Display contradiction queue alongside lifecycle audit [default: True]
- `--apply-contradictions`: Apply contradiction/supersession resolutions to on-disk vault [default: False]
- `--yes`, `-y`: Skip confirmation when applying non-automatic resolutions [default: False]

#### `harness knowledge lineage`
```text
Trace all Knowledge Items that contributed to or were distilled into a skill.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge list`
```text
List all Knowledge Items in storage (hydrates from disk if DB is empty).
```

**Options:**
- `--tag`, `-t`: Filter by tag
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge neighbors`
```text
List adjacent Knowledge Items, skills, plugins, and code paths connected to a node.
```

**Options:**
- `--depth`, `-d`: Neighborhood traversal depth (1..4) [default: 1]
- `--edge-type`, `-t`: Filter by specific edge relationship type
- `--exclude-derived`: Exclude automatically derived edges [default: False]
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge orphans`
```text
Identify isolated Knowledge Items and report missing-field triage profiles.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--include-single-tag-edges`: Include 1-shared-tag derived same_domain edges [default: False]
- `--include-shared-source`: Include shared_source derived edges [default: False]
- `--max-tag-freq`: Tag frequency threshold for mega-tag exclusion [default: 0.15]
- `--json`: Output orphan diagnostics in JSON format [default: False]

#### `harness knowledge path`
```text
Find the BFS shortest path between two graph entities (Rule 55: zero synthetic edges).
```

**Options:**
- `--max-depth`: Maximum search hops (default: 6) [default: 6]
- `--exclude-derived`: Exclude automatically derived edges [default: False]
- `--directed`: Enforce strict directional edge traversal [default: False]
- `--engine`: Pathfinding engine (bfs or sqlite recursive CTE) [default: bfs]
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge query`
```text
Search Knowledge Items by keyword, tag, or Isnad status.
```

**Options:**
- `--tag`, `-t`: Filter by tag
- `--status`, `-s`: Filter by Isnad status (e.g. VERIFIED)
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge reflect`
```text
Reflect on internal history (HTML reports, transcripts, test runs) and distill Knowledge Items.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--since`: Filter memory artifacts created on or after this ISO date/timestamp
- `--conv-id`: Filter transcript harvesting to a specific conversation ID
- `--category`: Filter distilled heuristics by category (e.g. architecture, performance)
- `--test-report`: Path to JUnit XML test report or CI artifacts to distill
- `--min-confidence`: Minimum confidence threshold (0.0 - 1.0) [default: 0.8]
- `--limit`: Maximum number of reports/transcripts to harvest [default: 50]
- `--daemon`: Run continuous background reflection daemon [default: False]
- `--interval`: Interval in seconds between daemon distillation cycles [default: 300.0]
- `--no-html`: Disable generating interactive HTML visual brief [default: False]
- `--no-commit`: Do not commit distilled items into the knowledge vault [default: False]

#### `harness knowledge resolve`
```text
Resolve a contradiction or antinomy between two Knowledge Items on disk.
```

**Options:**
- `--action` *(required)*: Resolution action: supersede (ki_a supersedes ki_b), contradict (mutual conflict), dismiss (ignore) [default: Sentinel.UNSET]
- `--reason`: Optional notes or justification for resolution
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge stats`
```text
Print comprehensive knowledge graph census metrics, node kinds, edge types, and components.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--json`: Output raw census metrics in JSON format [default: False]
- `--include-single-tag-edges`: Include 1-shared-tag derived same_domain edges [default: False]
- `--include-shared-source`: Include shared_source derived edges [default: False]
- `--max-tag-freq`: Tag frequency threshold for mega-tag exclusion [default: 0.15]

#### `harness knowledge sync`
```text
Sync all on-disk Knowledge Items from .harness/knowledge/ into the storage database.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--db`: Path to SQLite storage database (defaults to ~/.harness/storage.db)
- `--strict`: Fail with exit code 1 if any vault items fail validation [default: False]

#### `harness knowledge timeline`
```text
Report data-driven temporal growth metrics, weekly velocity, and domain emergence order.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--json`: Output timeline metrics in JSON format [default: False]

#### `harness knowledge topic`
```text
Explore the topic neighborhood: matching KIs, linked skills, and referenced code paths.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

#### `harness knowledge verify`
```text
Audit Isnad lineage nodes and primary source file existence for a Knowledge Item.
```

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]

---

## `harness mantis`

Google Mantis — Autonomous security review, AST taint audit, deduplication ladder, and risk triage.

### Subcommands

#### `harness mantis audit`
```text
Execute AST taint and static analysis audit on target file.
```

**Options:**
- `--cwe`: Focus CWE identifiers [default: Sentinel.UNSET]
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis calibrate-risk`
```text
Calibrate risk score based on asset exposure, environmental controls, and blast radius.
```

**Options:**
- `--criticality`: Asset criticality [default: high]
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis chain-exploits`
```text
Compose isolated findings into multi-stage exploit chains.
```

**Options:**
- `--objective`: Target adversary objective or exploit goal
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis critic-filter`
```text
Screen candidate finding through critic filter for false positives.
```

**Options:**
- `--strict`: Enforce strict assertion checks [default: True]
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis dedupe`
```text
Deduplicate findings through the Mantis deduplication ladder.
```

**Options:**
- `--mode`: Deduplication mode [default: syntactic_and_ast]
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis dir-summary`
```text
Generate structural security architecture summary of a directory.
```

**Options:**
- `--no-recursive`: Disable recursive directory traversal [default: False]
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis gate`
```text
Evaluate review gate on findings. Exits non-zero if severity threshold is breached.
```

**Options:**
- `--fail-on`: Severity threshold that fails the gate [default: HIGH]
- `--source-file`: Optional source code path for context verification
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis history-scan`
```text
Scan VCS history for high-churn hotspots, vulnerability fixes, and security commit signatures.
```

**Options:**
- `--max-commits`: Maximum commits to scan back [default: 100]
- `--pattern`: Regex filter for commit subjects/files
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis plan-review`
```text
Evaluate architectural review plan against threat models and CWE vectors.
```

**Options:**
- `--threat-model` *(required)*: Threat model JSON or path to threat model file [default: Sentinel.UNSET]
- `--target`, `-t` *(required)*: Target file/directory paths under review [default: Sentinel.UNSET]
- `--cwe`: Focus CWE identifiers (e.g. CWE-79, CWE-89) [default: Sentinel.UNSET]
- `--json`: Emit raw JSON payload [default: False]

#### `harness mantis report`
```text
Synthesize final security review audit dossier and remediation report.
```

**Options:**
- `--chains`: Optional exploit chains JSON input
- `--summary`: Optional executive summary text
- `--output`: Output destination file
- `--json`: Emit raw JSON payload [default: False]

---

## `harness mcp`

Model Context Protocol (MCP) server commands.

### Subcommands

#### `harness mcp serve`
```text
Start the MCP STDIO server exposing Harness tools to external agents.
```

---

## `harness memory`

Manage working-memory decay, Ebbinghaus retention, and 5-store routing.

### Subcommands

#### `harness memory benchmark`
```text
Run comparative simulation comparing Ebbinghaus decay vs recency baseline.
```

**Options:**
- `--turns`, `-t`: Number of turns to simulate [default: 30]
- `--items`, `-i`: Total memories to inject [default: 25]
- `--seed`: Simulation RNG seed [default: 42]
- `--json`: Emit JSON output [default: False]

#### `harness memory recall`
```text
Recall an active memory item, reinforcing stability non-linearly.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--json`: Emit JSON output [default: False]

#### `harness memory register`
```text
Register a new memory item into the Ebbinghaus memory session.
```

**Options:**
- `--key`, `-k` *(required)*: Unique memory key [default: Sentinel.UNSET]
- `--content`, `-c` *(required)*: Memory content text [default: Sentinel.UNSET]
- `--session`, `-s`: Session identifier [default: default]
- `--channel`: Semantic memory channel [default: memory]
- `--stability`: Initial Ebbinghaus stability S [default: 5.0]
- `--foundational`: Mark item as foundational (exempt from eviction) [default: False]
- `--json`: Emit JSON output [default: False]

#### `harness memory route`
```text
Route a developer or agent memory inquiry to the authoritative store.
```

**Options:**
- `--json`: Emit JSON output [default: False]

#### `harness memory snapshot`
```text
Export or restore an Ebbinghaus working-memory session snapshot.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--export`: File path to export snapshot JSON
- `--import`: File path to import snapshot JSON
- `--json`: Emit JSON output [default: False]

#### `harness memory status`
```text
Inspect status and paradigms across all 5 partitioned memory stores.
```

**Options:**
- `--json`: Emit JSON output [default: False]

#### `harness memory step`
```text
Advance session time by N turns, applying channel decay and soft-evicting expired items.
```

**Options:**
- `--turns`, `-t`: Number of turns to advance [default: 1]
- `--session`, `-s`: Session identifier [default: default]
- `--json`: Emit JSON output [default: False]

#### `harness memory working-set`
```text
Query items residing in the active working-memory set.
```

**Options:**
- `--session`, `-s`: Session identifier [default: default]
- `--include-evicted`: Include soft-evicted items in inspection [default: False]
- `--ranked`: Sort by multi-criteria composite score [default: False]
- `--limit`, `-l`: Max items to return
- `--json`: Emit JSON output [default: False]

---

## `harness network-forensics`

Network Forensics CLI — Protocol reconnaissance, tri-state recon & 7-layer fault isolation.

### Subcommands

#### `harness network-forensics brief`
```text
Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%.
```

**Options:**
- `--output-path`: Target HTML file path

#### `harness network-forensics cleartext`
```text
Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities.
```

**Options:**
- `--proto` *(required)*: Protocol name (e.g. HTTP, FTP, Telnet) [default: Sentinel.UNSET]
- `--port` *(required)*: Port number (e.g. 80, 21, 23, 443) [default: Sentinel.UNSET]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness network-forensics decode-flags`
```text
Decode hexadecimal TCP flags and detect evasion patterns (Null, Xmas, SYN-FIN).
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

#### `harness network-forensics diagnose-7layer`
```text
Execute systematic 7-layer fault isolation chain against a target.
```

**Options:**
- `--port`: Target port (defaults to 80) [default: 80]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness network-forensics scan-ports`
```text
Evaluate port reachability into tri-state classification (open/closed/filtered).
```

**Options:**
- `--ports` *(required)*: Comma-separated list of ports or scan JSON [default: Sentinel.UNSET]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness network-forensics subnet`
```text
Compute network address, broadcast address, and host capacity for an IPv4 CIDR prefix.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

#### `harness network-forensics traceroute`
```text
Parse traceroute output from file path or raw text string.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

---

## `harness okf`

Manage, scope, and query Git-native OKF agent memory bundles.

### Subcommands

#### `harness okf scope`
```text
Pre-edit governance scoping for a target code path before editing.
```

**Options:**
- `--bundle-dir`: Root directory of knowledge bundle (default: 'knowledge')
- `--json`: Output raw JSON results [default: False]

#### `harness okf search`
```text
Search knowledge bundle via BM25 lexical ranking.
```

**Options:**
- `--limit`, `-l`: Maximum matching concepts to return (default: 3) [default: 3]
- `--bundle-dir`: Root directory of knowledge bundle (default: 'knowledge')
- `--json`: Output raw JSON results [default: False]

#### `harness okf show`
```text
Inspect full Markdown body and metadata for a specific concept.
```

**Options:**
- `--bundle-dir`: Root directory of knowledge bundle (default: 'knowledge')
- `--json`: Output raw JSON record [default: False]

#### `harness okf validate`
```text
Validate knowledge bundle against OKF v0.2 specifications.
```

**Options:**
- `--strict`: Enforce zero warnings (fail if any warnings found) [default: False]
- `--bundle-dir`: Root directory of knowledge bundle (default: 'knowledge')
- `--json`: Output raw JSON report [default: False]

---

## `harness plugin`

Manage plugins.

### Subcommands

#### `harness plugin add`
```text
Fetch a GitHub repository and register it as a plugin.

SOURCE can be a GitHub URL, owner/repo shorthand, or local ZIP path.
```

**Options:**
- `--ref`: Git ref (branch/tag) to fetch [default: main]
- `--force`: Re-download even if cached [default: False]
- `--token`: GitHub API token [default: Sentinel.UNSET]

#### `harness plugin card`
```text
Show the standardized summary card for an installed plugin.
```

#### `harness plugin disable`
```text
Disable a plugin by name or pattern.
```

#### `harness plugin disable-all`
```text
Disable all active plugins.
```

**Options:**
- `--keep-core`: Keep core infrastructure services active [default: True]

#### `harness plugin enable`
```text
Enable a plugin by name or pattern.
```

#### `harness plugin enable-all`
```text
Enable all discovered plugins.
```

#### `harness plugin guide`
```text
Show the Quick Start and Agent Usage Guide for an installed plugin.
```

#### `harness plugin info`
```text
Show the standardized summary card for an installed plugin.
```

#### `harness plugin inspect`
```text
Inspect a plugin directory and show its manifest card.
```

#### `harness plugin list`
```text
List all installed plugins.
```

#### `harness plugin remove`
```text
Remove a cached plugin.
```

**Options:**
- `--yes`: Confirm the action without prompting. [default: False]

---

## `harness pre-commit-security`

Pre-Commit Security Guard CLI — Shift-left SAST, secret interception & CI defense.

### Subcommands

#### `harness pre-commit-security audit-ci`
```text
Audit remote CI workflow for dual-gate parity (fetch-depth: 0, SARIF upload).
```

**Options:**
- `--workflow`: Path to CI workflow YAML [default: .github/workflows/security.yml]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness pre-commit-security audit-suppressions`
```text
Audit repository for unjustified comment suppressions and blanket directory exclusions.
```

**Options:**
- `--root`: Root directory to inspect [default: .]
- `--json-output`: Emit raw JSON output [default: False]

#### `harness pre-commit-security brief`
```text
Generate interactive HTML visual brief with Mermaid diagrams.
```

**Options:**
- `--output`: Destination HTML file path

#### `harness pre-commit-security scan`
```text
Scan staged files or paths for SAST vulnerabilities and secret leaks.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]
- `--sarif-output`: Path to write SARIF v2.1.0 report

#### `harness pre-commit-security smoke-test`
```text
Execute deliberate synthetic failure tests verifying commit-blocking gates.
```

**Options:**
- `--json-output`: Emit raw JSON output [default: False]

---

## `harness rea`

REA — Reverse-engineering toolkit, multi-provider dissection, and signature learning.

### Subcommands

#### `harness rea callgraph`
```text
Traverse caller or callee call-graph relationships from an entrypoint.
```

**Options:**
- `--entry`, `-e` *(required)*: Procedure entrypoint symbol [default: Sentinel.UNSET]
- `--depth`, `-d`: Traversal depth (default: 3) [default: 3]
- `--direction`: Direction of traversal [default: callee]
- `--json`: Emit result as JSON [default: False]

#### `harness rea decompile`
```text
Decompile procedure symbols concurrently via headless decompiler.
```

**Options:**
- `--symbols`, `-s` *(required)*: Comma-separated list of symbols to decompile [default: Sentinel.UNSET]
- `--provider`, `-p`: Decompiler provider [default: ghidra]
- `--json`: Emit result as JSON [default: False]

#### `harness rea devices`
```text
Enumerate attached ADB devices, emulators, and device package trees.
```

**Options:**
- `--packages`: Device serial to query installed packages from
- `--json`: Emit output as JSON [default: False]

#### `harness rea diff`
```text
Compare two providers on an artifact and emit a 3-valued DifferentialReport.
```

**Options:**
- `--providers`, `-p`: Two comma-separated providers to compare (default: ghidra,hopper) [default: ghidra,hopper]
- `--symbols`, `-s`: Symbols to compare (default: main) [default: main]
- `--json`: Emit DifferentialReport JSON [default: False]

#### `harness rea inspect`
```text
Inspect and dissect an artifact into unified facets with availability semantics.
```

**Options:**
- `--artifact-type`, `-t`: Explicit artifact kind override (e.g. elf, pe_managed, apk, wasm, har)
- `--json`: Emit raw JSON DissectionEnvelope [default: False]

#### `harness rea learn`
```text
Dissect artifact and distill semantic signatures into the Knowledge Vault and ROL ledger.
```

**Options:**
- `--dry-run`: Preview learned signatures without writing to vault [default: False]
- `--vault`: Path to Knowledge Vault root [default: .harness/knowledge]
- `--ledger`: Path to ROL ledger state file [default: .harness/reconstruction_ledger.json]
- `--domain`: Domain category for the Knowledge Item [default: security_and_forensics]
- `--tag`, `-t`: Optional tags for the Knowledge Item [default: Sentinel.UNSET]
- `--json`: Emit learning report as JSON [default: False]

#### `harness rea learned`
```text
List distilled REA knowledge items stored in the Knowledge Vault.
```

**Options:**
- `--query`, `-q`: Filter by keyword
- `--vault`: Path to Knowledge Vault root [default: .harness/knowledge]
- `--json`: Emit results as JSON [default: False]

#### `harness rea list`
```text
List REA tools grouped by artifact kind.
```

**Options:**
- `--artifact-type`, `-t`: Filter tool list by artifact kind
- `--json`: Emit tool catalog as JSON [default: False]

#### `harness rea providers`
```text
Report external reverse-engineering binary availability, paths, and versions.
```

**Options:**
- `--json`: Emit providers status as JSON [default: False]

#### `harness rea signatures`
```text
Extract and deduplicate semantic signatures from an artifact.
```

**Options:**
- `--kind`, `-k`: Filter signature kind (e.g. evm_selector, pinvoke, ipc_channel, export, import)
- `--json`: Emit signatures as JSON [default: False]

---

## `harness redteam`

GenAI adversarial red-teaming and prompt vulnerability audits.

### Subcommands

#### `harness redteam scan`
```text
Run an adversarial probe scan against a target prompt or agent loop.
```

**Options:**
- `--technique`: Attack technique (crescendo, roleplay_jailbreak, encoding_fuzz) [default: crescendo]
- `--intensity`: Attack intensity from 1 to 5 [default: 3]
- `--target-type`: Target type (system_prompt, agent_loop, tool_interface) [default: system_prompt]

#### `harness redteam status`
```text
Show sandbox virtual environment status and isolation metrics.
```

#### `harness redteam techniques`
```text
List all supported adversarial red-teaming techniques.
```

---

## `harness refine`

Recursive agent harness refinement, rollouts budget, and verification.

### Subcommands

#### `harness refine budget`
```text
Print the expected rollout/session budget: R = 4k rollouts, P = 3k stages.
```

#### `harness refine validate`
```text
Validate a harness directory against the editable surface; exit 1 with every problem.
```

#### `harness refine scan`
```text
Run the answer-key and grader-verdict tripwires over an evidence tree; exit 1 on a leak.
```

#### `harness refine fingerprint`
```text
Print the stable trial-identity fingerprint of a harness directory.
```

#### `harness refine demo`
```text
Run both recursion modes on a deterministic task; no model credentials required.
```

---

## `harness rol`

Reconstruction Obligation Ledger — Software reverse-engineering evidence and verification proof system.

### Subcommands

#### `harness rol export`
```text
Emit machine-parseable JSON reconstruction certificate.
```

#### `harness rol ingest`
```text
Ingest observation, compute canonical SHA-256 digest, and save CanonicalEvidence record.
```

**Options:**
- `--ledger`: Path to ledger state file [default: .harness\reconstruction_ledger.json]
- `--provider`: Provider ID (e.g. ghidra, rizin, wakaru) [default: generic]
- `--format`: Subject format (e.g. elf, pe, wasm, json) [default: json]

#### `harness rol obligation`
```text
Manage obligations in the ledger.
```

##### Nested `obligation` Subcommands
* **`harness rol obligation add`**: Register a new behavioral obligation with unowned disposition.
* **`harness rol obligation transition`**: Transition an obligation along the valid 8-state FSM.

#### `harness rol verify`
```text
Compute ReconstructionProof closure digest and emit tabular audit.
```

**Options:**
- `--strict`: Exit non-zero if ledger is not fully closed [default: False]
- `--json-output`: Output results in JSON format [default: False]

---

## `harness router`

Dynamic Model Router CLI — 3-tier switching & resilient failover commands.

### Subcommands

#### `harness router brief`
```text
Generate interactive HTML visual brief with routing telemetry.
```

**Options:**
- `--output`, `-o`: Destination file path for HTML brief

#### `harness router profile`
```text
Deterministically profile prompt complexity (<5ms, zero-LLM).
```

**Options:**
- `--tools`: Comma-separated candidate tool names (e.g. bash,grep,sql)
- `--json-output`: Emit raw JSON output [default: False]

#### `harness router route`
```text
Resolve primary and fallback models asserting provider diversity.
```

**Options:**
- `--complexity`, `-c`: Target complexity tier [default: simple]
- `--cost-ceiling`: Optional cost budget ceiling per 1k tokens
- `--json-output`: Emit raw JSON output [default: False]

#### `harness router simulate`
```text
Simulate end-to-end routing execution with automated failover.
```

**Options:**
- `--fail-primary`: Simulate primary provider outage (HTTP 429/503/timeout) [default: False]
- `--fail-all`: Simulate complete provider outage across all candidates [default: False]
- `--json-output`: Emit raw JSON output [default: False]

---

## `harness session`

Manage and inspect agent execution sessions and hierarchical trees.

### Subcommands

#### `harness session export`
```text
Export agent session trajectory to Markdown or JSON.
```

**Options:**
- `--format`, `-f`:  [default: markdown]
- `--output`, `-o`: Output file path

#### `harness session get`
```text
Get details of a specific agent session.
```

#### `harness session list`
```text
List agent execution sessions.
```

**Options:**
- `--status`, `-s`: Filter by session status
- `--limit`, `-n`: Limit number of sessions [default: 20]
- `--root-only`: List only root-level sessions [default: False]

#### `harness session tree`
```text
Show hierarchical session execution tree and rollups.
```

---

## `harness skills`

Manage and query the agent skill knowledge graph.

### Subcommands

#### `harness skills bridges`
```text
Discover cross-domain macro-bridges connecting distinct skill clusters.
```

**Options:**
- `--json`: Output raw JSON format [default: False]
- `--path`: Root directory to scan [default: .]

#### `harness skills capabilities`
```text
Display novel emergent macro-capabilities discovered from the skill graph.
```

**Options:**
- `--query`: Filter capabilities by keyword or domain
- `--path`: Root directory to scan [default: .]

#### `harness skills chain`
```text
Find directed execution path between two skills.
```

#### `harness skills check-chain`
```text
Evaluate whether an execution sequence of skills is feasible with all preconditions met (Rule 10).
```

**Options:**
- `--verify-prereqs`: Verify topological prerequisite closure [default: True]
- `--json`: Output raw JSON format [default: False]
- `--path`: Root directory to scan for skills [default: .]

#### `harness skills clusters`
```text
Cluster workspace skills into functional domains and display emergent capabilities.
```

**Options:**
- `--min-size`: Minimum cluster size [default: 2]
- `--path`: Root directory to scan [default: .]

#### `harness skills create`
```text
Scaffold a high-precision agent skill with SKILL.md and CARD.md specifications.
```

**Options:**
- `--description`, `-d`: Skill description and trigger bounds
- `--category`, `-c`: Skill domain category [default: engineering / meta-skills]
- `--target-dir`, `-t`: Destination directory (defaults to .agents/skills/<name>)
- `--trigger`, `-g`: Trigger phrases for skill routing [default: Sentinel.UNSET]
- `--validate`: Validate skill specifications on creation [default: False]

#### `harness skills graph`
```text
Index and display the workspace skill knowledge graph.
```

**Options:**
- `--visual`: Generate interactive HTML visual brief in %TEMP% [default: False]
- `--path`: Root directory to scan for skills [default: .]

#### `harness skills guidance`
```text
Compile and display an end-to-end execution guidance plan for an agent task (Rule 10).
```

**Options:**
- `--max-skills`: Maximum skills to include in pipeline [default: 4]
- `--json`: Output raw JSON payload [default: False]
- `--path`: Root directory to scan for skills [default: .]

#### `harness skills index`
```text
Scan and index all workspace skills into the skill knowledge graph (Rule 35).
```

**Options:**
- `--path`: Root path to index skills from [default: .]
- `--json`: Output raw JSON format [default: False]

#### `harness skills info`
```text
Inspect topological dependencies and anti-patterns for a skill.
```

#### `harness skills intercept`
```text
Evaluate a proposed agent action against anti-patterns and AST security gates (Rule 10).
```

**Options:**
- `-p`, `--param`: Action parameters in key=value format [default: Sentinel.UNSET]
- `--code`: Code block to inspect via AST scanner
- `-s`, `--skill`: Active skill names guarding this action [default: Sentinel.UNSET]
- `--json`: Output raw JSON observation [default: False]
- `--path`: Root directory to scan for skills [default: .]

#### `harness skills joint-query`
```text
Execute unified dual-graph query across Knowledge Vault and Skill Graph.
```

**Options:**
- `--limit`, `-l`: Maximum items to return per graph [default: 5]
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--skills-root`: Root directory for skills discovery [default: .]
- `--json`: Emit raw JSON payload [default: False]

#### `harness skills list`
```text
List all registered agent skills with category, stages, and invariants.
```

**Options:**
- `--path`: Root directory to scan for skills [default: .]
- `--category`: Filter by domain category

#### `harness skills prereqs`
```text
Inspect full transitive prerequisite closure for a skill in topological order.
```

**Options:**
- `--json`: Output raw JSON format [default: False]
- `--path`: Root directory to scan for skills [default: .]

#### `harness skills route`
```text
Route natural language task intent to matching skills.
```

**Options:**
- `--top-k`: Max matches to return [default: 3]

#### `harness skills run`
```text
Headlessly execute an automated skill pipeline driver (Rule 10).
```

**Options:**
- `--path`: Workspace root [default: .]
- `--source`: Source document or target argument for skill execution

#### `harness skills select`
```text
Intelligently select skills and compile an execution plan for a given task.
```

**Options:**
- `--max-skills`: Maximum skills to include [default: 5]
- `--no-verifier`: Disable automatic tail verifier injection [default: False]
- `--path`: Root directory to scan [default: .]

#### `harness skills validate`
```text
Validate an agent skill package against deep-module craft standards.
```

---

## `harness spawn`

Spawn, inspect, retire, and adopt learnings from isolated child harnesses.

### Subcommands

#### `harness spawn adopt`
```text
Explicitly review and adopt a staged child proposal into parent stores.
```

**Options:**
- `--save-dir`: Root directory containing registry state. [default: .harness\spawns]
- `--library-root`: Parent ExperienceLibrary root to adopt into. [default: .harness\experience]
- `--knowledge-root`: Parent Knowledge Vault root to adopt the dual-file KI into. [default: .harness\knowledge]

#### `harness spawn list`
```text
List registered child harnesses and their lifecycle state / budget usage.
```

**Options:**
- `--save-dir`: Root directory containing registry state. [default: .harness\spawns]
- `--state`: Filter records by lifecycle state.

#### `harness spawn propose`
```text
Stage a reviewed learning and dual-file KI draft in the child partition.
```

**Options:**
- `--task-id` *(required)*: Task identifier associated with the lesson.
- `--cue` *(required)*: Transferable cue triggering this lesson.
- `--lesson` *(required)*: Distilled transferable lesson.
- `--evidence` *(required)*: Supporting empirical evidence.
- `--why`: Rationale for adoption review. [default: ]
- `--ki-id`: Optional KI slug identifier. [default: ]
- `--save-dir`: Root directory containing registry state. [default: .harness\spawns]

#### `harness spawn retire`
```text
Retire a spawned child harness (or all active ones) and close its DAG edge.
```

**Options:**
- `--all`: Retire all active child harnesses. [default: False]
- `--save-dir`: Root directory containing registry state. [default: .harness\spawns]

#### `harness spawn run`
```text
Validate, probe-gate, and spawn an isolated child harness.
```

**Options:**
- `--name` *(required)*: Short identifier for the spawned child harness.
- `--domain` *(required)*: Domain partition for isolated ExperienceLibrary storage.
- `--task`: Assigned task summary. [default: spawned_harness]
- `--harness-dir`: Optional harness directory to read initial editable tree from.
- `--max-tokens`: Token budget ceiling. [default: 16000]
- `--k`: Recursion scale parameter k (R=4k rollouts, P=3k sessions). [default: 1]
- `--max-depth`: Maximum recursion depth allowed (hard cap 3). [default: 1]
- `--depth`: Caller depth (0 for Prime). [default: 0]
- `--parent-spawn-id`: Optional parent spawn ID when nesting.
- `--lifetime`: Child lifetime policy. [default: persistent]
- `--save-dir`: Root directory for child harness artifacts and registry state. [default: .harness\spawns]

---

## `harness tau`

Pi-style coding agent harness commands (DAG trees, journals, repair, trust).

### Subcommands

#### `harness tau append-journal`
```text
Append a session entry to an advisory locked JSONL journal.
```

**Options:**
- `--file`, `-f` *(required)*: Path to the JSONL session journal. [default: Sentinel.UNSET]
- `--id`, `-i` *(required)*: Session node ID. [default: Sentinel.UNSET]
- `--parent`, `-p`: Parent session node ID.
- `--role`, `-r`: Message role. [default: user]
- `--content`, `-c` *(required)*: Message text or observation content. [default: Sentinel.UNSET]

#### `harness tau repair-history`
```text
Normalize tool message history to guarantee model provider parity.
```

**Options:**
- `--file`, `-f` *(required)*: JSON file containing the message array. [default: Sentinel.UNSET]
- `--output`, `-o`: Optional path to save repaired messages.

#### `harness tau resolve-path`
```text
Resolve linear conversation ancestry from root to target entry.
```

**Options:**
- `--file`, `-f` *(required)*: Path to the JSONL session journal. [default: Sentinel.UNSET]
- `--target`, `-t` *(required)*: Target session entry ID to trace back to root. [default: Sentinel.UNSET]

#### `harness tau tree`
```text
Render deterministic ASCII DAG tree of a session journal.
```

**Options:**
- `--file`, `-f` *(required)*: Path to the JSONL session journal. [default: Sentinel.UNSET]
- `--root`, `-r`: Optional root entry ID to start traversal.

#### `harness tau trust-check`
```text
Evaluate workspace boundary trust, git root, and sensitive assets.
```

**Options:**
- `--trusted-root`, `-t`: Explicitly trusted directory root. [default: Sentinel.UNSET]

---

## `harness temp`

Ephemeral workspace archaeology, HTML visual brief extraction, and sandbox triage.

### Subcommands

#### `harness temp bifurcate`
```text
Execute dual-lens cognitive bifurcation: Knowledge Vault dual-files + permanent docs.
```

**Options:**
- `--vault-dir`: Target Knowledge Vault directory. [default: .harness\knowledge]
- `--docs-dir`: Target repository documentation directory. [default: docs\architecture]
- `--json-output`: Output results in JSON format. [default: False]

#### `harness temp salvage`
```text
Synthesize high-density Markdown salvage index of visual briefs and sandboxes.
```

**Options:**
- `--temp-dir`: Path to temporary directory. [default: C:\Users\spectre\AppData\Local\Temp]
- `--out`: Output markdown file path.

#### `harness temp sandbox`
```text
Triage ephemeral pytest test sandbox environments and mock fixtures.
```

**Options:**
- `--temp-dir`: Path to temporary directory containing pytest sandboxes. [default: C:\Users\spectre\AppData\Local\Temp]
- `--depth`: Maximum directory scan depth. [default: 3]
- `--json-output`: Output results in JSON format. [default: False]

#### `harness temp scan`
```text
Scan and catalog HTML visual briefs across temporary directories.
```

**Options:**
- `--temp-dir`: Path to temporary directory containing visual HTML briefs. [default: C:\Users\spectre\AppData\Local\Temp]
- `--depth`: Maximum directory scan depth. [default: 2]
- `--heavy-threshold`: Byte threshold for heavy topologies. [default: 100000]
- `--json-output`: Output results in JSON format. [default: False]

#### `harness temp tail`
```text
Stream trailing lines from an ephemeral diagnostic log into a bounded ring buffer.
```

**Options:**
- `--lines`: Maximum trailing lines to read. [default: 50]

---

## `harness tool`

Inspect and manage granular tool and skill enablement.

### Subcommands

#### `harness tool disable`
```text
Disable a specific tool by name.
```

#### `harness tool enable`
```text
Enable a specific tool by name.
```

#### `harness tool list`
```text
List all registered tools with their active status.
```

**Options:**
- `--provider`: Filter tools by provider plugin name [default: Sentinel.UNSET]
- `--enabled-only`: Only list currently enabled tools [default: False]

---

## `harness trajectory`

Autobiographical execution trajectory archaeology, friction metrics, and cognitive bifurcation.

### Subcommands

#### `harness trajectory bifurcate`
```text
Bifurcate session learning into Knowledge Vault items and procedural skill rules (Rule 41).
```

**Options:**
- `--corpus-dir`: Path to conversations directory. [default: C:\Users\spectre\.gemini\antigravity-ide\conversations]
- `--vault-dir`: Output directory for canonical Knowledge Vault item. [default: .harness\knowledge]
- `--skills-dir`: Optional output directory for learned skill scaffold.
- `--json-output`: Output results in JSON format. [default: False]

#### `harness trajectory friction`
```text
Compile aggregate friction scorecard and failure mode clusters.
```

**Options:**
- `--corpus-dir`: Path to conversations directory. [default: C:\Users\spectre\.gemini\antigravity-ide\conversations]
- `--max-dbs`: Maximum databases to analyze. [default: 50]
- `--json-output`: Output results in JSON format. [default: False]

#### `harness trajectory inspect`
```text
Deep inspect a specific conversation ID.
```

**Options:**
- `--corpus-dir`: Path to conversations directory. [default: C:\Users\spectre\.gemini\antigravity-ide\conversations]
- `--json-output`: Output results in JSON format. [default: False]

#### `harness trajectory scan`
```text
Scan and catalog conversation database manifests across session stores.
```

**Options:**
- `--corpus-dir`: Path to conversations directory containing SQLite WAL databases. [default: C:\Users\spectre\.gemini\antigravity-ide\conversations]
- `--max-dbs`: Maximum conversation databases to scan. [default: 50]
- `--json-output`: Output results in JSON format. [default: False]

---

## `harness uncertainty`

Uncertainty-Aware AI Pipeline — 3-Layer Interception & Overconfidence Mitigation.

### Subcommands

#### `harness uncertainty brief`
```text
Generate interactive HTML visual brief in %TEMP%.
```

**Options:**
- `--query`, `-q`: Query [default: Configure internal VPN]
- `--output`, `-o`: Custom output HTML path [default: Sentinel.UNSET]

#### `harness uncertainty calibrate`
```text
Cluster under-retrieved queries to uncover missing documentation debt.
```

**Options:**
- `--query`, `-q` *(required)*: Under-retrieved or failing queries to cluster [default: Sentinel.UNSET]

#### `harness uncertainty gate`
```text
Evaluate Layer 1 input domain boundary gating.
```

**Options:**
- `--query`, `-q` *(required)*: User input query [default: Sentinel.UNSET]
- `--threshold`, `-t`: Cosine boundary threshold (default: 0.45) [default: 0.45]
- `--domain`, `-d`: Custom operational domain centroid [default: Sentinel.UNSET]

#### `harness uncertainty logprobs`
```text
Evaluate Layer 3 token log probabilities and sequence perplexity.
```

**Options:**
- `--logprob`, `-l` *(required)*: Sequence of token log probabilities [default: Sentinel.UNSET]
- `--threshold`, `-t`: Logprob safety threshold (default: -0.35) [default: -0.35]

#### `harness uncertainty pipeline`
```text
Execute end-to-end 3-layer request interception lifecycle.
```

**Options:**
- `--query`, `-q` *(required)*: User input query [default: Sentinel.UNSET]
- `--chunk`, `-c`: Retrieved context chunks [default: Sentinel.UNSET]
- `--logprob`, `-l`: Token log probabilities [default: Sentinel.UNSET]
- `--response`, `-r`: Draft LLM generation [default: Verified response]

#### `harness uncertainty retrieval`
```text
Evaluate Layer 2 retrieval relevance and context sufficiency.
```

**Options:**
- `--query`, `-q` *(required)*: User input query [default: Sentinel.UNSET]
- `--chunk`, `-c` *(required)*: Retrieved document chunks to score [default: Sentinel.UNSET]
- `--threshold`, `-t`: Minimum context relevance threshold (default: 0.60) [default: 0.6]

---

## `harness validation-loop`

Spec-first deterministic validation loop commands.

### Subcommands

#### `harness validation-loop brief`
```text
Generate an interactive HTML visual brief for validation.
```

**Options:**
- `--output`, `-o`: Output HTML file path
- `--spec`, `-s`: Specification preset [default: deployment_config]

#### `harness validation-loop run`
```text
Run a deterministic validation loop with state machine execution.
```

**Options:**
- `--request`, `-r` *(required)*: Generation task request/objective [default: Sentinel.UNSET]
- `--spec`, `-s`: Preset name (deployment_config, plugin_manifest) or schema file [default: deployment_config]
- `--attempts`, `-a`: Max retry ceiling before give-up triage (default 3) [default: 3]
- `--simulate`: Simulation mode: success on turn 1, recovery on turn 2, or exhausted retries [default: retry_recovery]
- `--json`: Output raw JSON [default: False]

#### `harness validation-loop specs`
```text
List available validation specification presets.
```

**Options:**
- `--name`, `-n`: Inspect specific preset schema

#### `harness validation-loop validate`
```text
Validate a structured JSON payload against a specification.
```

**Options:**
- `--spec`, `-s`: Preset name (deployment_config, plugin_manifest) or path to schema file [default: deployment_config]
- `--data`, `-d`: Inline JSON payload string
- `--file`, `-f`: Path to JSON payload file
- `--json`: Output raw JSON [default: False]

---

## `harness apply`

Apply and reconcile a declarative configuration tree against Harness.

**Options:**
- `-f`, `--file` *(required)*: Path to declarative config file (.yaml/.json) [default: Sentinel.UNSET]

---

## `harness assess-compute`

Assess task surface complexity and recommend optimal model tier & reasoning budget.

**Options:**
- `--files`, `-f`: Number of files in target task scope [default: 1]
- `--arch`, `-a`: Mark task as architectural refactoring [default: False]
- `--debug-task`, `-d`: Mark task as debugging / diagnostic investigation [default: False]
- `--profile`, `-p`: Scoring profile heuristic preset [default: balanced]
- `--override`, `-o`: Force specific model tier override
- `--json`: Output raw assessment in JSON format [default: False]
- `--html`: Generate interactive HTML visual review brief in %TEMP% [default: False]

---

## `harness events`

Show the event log.

**Options:**
- `--type`: Filter by event type
- `--limit`: Max events to show [default: 50]

---

## `harness init`

Initialize a harness workspace.

---

## `harness introspect`

Display runtime system diagnostics and dependency graph.

---

## `harness reflect`

Run endogenous reflection loop across internal reports and transcripts.

**Options:**
- `--vault`, `-v`: Path to knowledge vault root directory [default: .harness/knowledge]
- `--since`: Filter memory artifacts created on or after this ISO date/timestamp
- `--conv-id`: Filter transcript harvesting to a specific conversation ID
- `--category`: Filter distilled heuristics by category (e.g. architecture, performance)
- `--test-report`: Path to JUnit XML test report or CI artifacts to distill
- `--min-confidence`: Minimum confidence threshold (0.0 - 1.0) [default: 0.8]
- `--limit`: Maximum number of reports/transcripts to harvest [default: 50]
- `--daemon`: Run continuous background reflection daemon [default: False]
- `--interval`: Interval in seconds between daemon distillation cycles [default: 300.0]
- `--no-html`: Disable generating interactive HTML visual brief [default: False]
- `--no-commit`: Do not commit distilled items into the knowledge vault [default: False]

---

## `harness run`

Start the harness (interactive mode).

---

## `harness services`

List registered services and their provider plugins.

---

## `harness ui`

Launch the real-time web control room dashboard.

**Options:**
- `--host`: Host interface to bind [default: 127.0.0.1]
- `--port`: Port to listen on [default: 8080]
- `--db`: SQLite database path (default: :memory:) [default: :memory:]

---

## `harness watch`

Run the harness with live filesystem hot-reloading enabled.

---
