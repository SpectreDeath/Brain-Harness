# Brain Harness How-To Guides

This guide provides practical, step-by-step solutions for common development, extension, and operational tasks in Brain Harness.

---

## Table of Contents

1. [Authoring a Custom Plugin](#authoring-a-custom-plugin)
2. [Registering Tools for Autonomous Agents](#registering-tools-for-autonomous-agents)
3. [Crafting Production-Grade Agent Skills](#crafting-production-grade-agent-skills)
4. [Orchestrating Multi-Agent Swarms](#orchestrating-multi-agent-swarms)
5. [Ingesting External Repositories into Sandboxed Plugins](#ingesting-external-repositories-into-sandboxed-plugins)
6. [Auditing Documentation Coverage & Drift](#auditing-documentation-coverage--drift)

---

## Authoring a Custom Plugin

### Goal
Create a new in-process domain plugin that registers a typed service into the IoC container.

### Step 1: Scaffold the Plugin Directory
Create your plugin under the appropriate domain category in `plugins/<category>/<plugin_name>`:

```bash
harness creator build my_analytics --category data_engineering --archetype tool
```

### Step 2: Declare the Manifest (`plugin.json`)
Ensure `plugin.json` specifies capabilities and dependencies:

```json
{
  "name": "my_analytics",
  "version": "0.1.0",
  "category": "data_engineering",
  "entrypoint": "main.py",
  "provides": ["data_engineering.my_analytics"],
  "requires": ["core.storage"],
  "trusted": true
}
```

### Step 3: Implement the Plugin Entrypoint (`main.py`)
In `main.py`, subclass `HarnessPlugin`, register your service in `on_load`, and export a module singleton (Rule 45):

```python
from harness.plugins.base import HarnessPlugin
from harness.kernel.context import ServiceContext, ServiceKey

MY_ANALYTICS_KEY = ServiceKey["MyAnalyticsService"]("data_engineering.my_analytics")

class MyAnalyticsService:
    def compute_summary(self, numbers: list[float]) -> dict[str, float]:
        return {"count": len(numbers), "sum": sum(numbers)}

class MyAnalyticsPlugin(HarnessPlugin):
    @property
    def provides(self) -> list[str]:
        return ["data_engineering.my_analytics"]

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(MY_ANALYTICS_KEY, MyAnalyticsService())

# Mandatory module-level singleton export (Rule 45)
plugin = MyAnalyticsPlugin()
```

### Step 4: Validate the Plugin
Verify your plugin adheres to architectural standards:

```bash
harness creator validate plugins/data_engineering/my_analytics
```

---

## Registering Tools for Autonomous Agents

### Goal
Expose a callable Python function as a typed, schema-validated tool for ReAct agent step execution.

### Step 1: Define Tool Function and Schema
Tools declare typed Pydantic parameters or standard type annotations:

```python
from pydantic import BaseModel, Field
from harness.services.tools import TOOL_REGISTRY_KEY

class FilterQuery(BaseModel):
    pattern: str = Field(..., description="Regex pattern to search for")
    max_results: int = Field(10, description="Maximum items to return")

def grep_files(query: FilterQuery) -> list[str]:
    """Search for matching strings in workspace files."""
    return ["file1.py: match", "file2.py: match"]
```

### Step 2: Register into Tool Registry
Register the tool in your plugin's `on_load` lifecycle hook:

```python
async def on_load(self, context: ServiceContext) -> None:
    tools = context.require(TOOL_REGISTRY_KEY)
    tools.register_tool(
        name="grep_files",
        description="Search for regex patterns within files.",
        handler=grep_files,
        schema=FilterQuery.model_json_schema(),
    )
```

---

## Crafting Production-Grade Agent Skills

### Goal
Author an agent skill in `.agents/skills/<skill-name>/` conforming to SDLC craft standards.

### Step 1: Scaffold Skill Structure
Create the skill directory with both `SKILL.md` and `CARD.md`:

```bash
harness skills scaffold my-analysis-skill
```

### Step 2: Write Frontmatter with Explicit Boundaries (Rule 44)
In `SKILL.md`, keep the description between 100 and 350 characters and define negative boundaries:

```markdown
---
name: my-analysis-skill
description: Execute structured dataset profiling and metric anomaly detection. Do not use for generic prose generation or unstructured web crawling.
---

# Analysis Skill Architecture
...
## Anti-Patterns
- **Ad-Hoc Scripting** — Executing uncontrolled mutations without dry-run validation.
```

### Step 3: Format `CARD.md` Single-Pipe Metadata Box (Rule 37)
In `CARD.md`, format the header box using standard single-pipe borders (`|`):

```markdown
┌────────────────────────────────────────────────────────┐
│ SKILL: my-analysis-skill                               │
│ Primary Domain: Data Engineering                       │
│ Complexity Tier: Medium                                │
└────────────────────────────────────────────────────────┘

## Mandatory Invariants Checklist
- [ ] Must validate input schema before execution.
```

---

## Orchestrating Multi-Agent Swarms

### Goal
Execute parallel subagent waves with token governance and multi-agent consensus deliberation.

### Step 1: Define Swarm DAG Nodes
Define subtasks with explicit dependencies and persona instructions:

```python
from harness.agent.swarm import SWARM_COORDINATOR_KEY, SwarmDAG, SwarmNode

async def run_swarm(context):
    coordinator = context.require(SWARM_COORDINATOR_KEY)
    
    dag = SwarmDAG()
    dag.add_node(SwarmNode(
        node_id="researcher",
        task="Extract architectural constraints from RFC documents.",
        role="Researcher",
    ))
    dag.add_node(SwarmNode(
        node_id="critic",
        task="Audit researcher findings for security vulnerabilities.",
        dependencies=["researcher"],
        role="Security Critic",
    ))
    
    result = await coordinator.execute_swarm(dag, token_budget=50000)
    print("Swarm consensus outcome:", result.final_answer)
```

---

## Ingesting External Repositories into Sandboxed Plugins

### Goal
Ingest a public GitHub repository, analyze its structure, and package it as a sandboxed Harness plugin.

### Step 1: Run Ingestion Command
```bash
harness plugin add https://github.com/example-org/fast-tokenizer.git --category software_engineering
```

The ingestion pipeline automatically:
1. Clones the repository to an isolated staging directory.
2. Analyzes AST signatures and dependencies.
3. Generates `plugin.json` and a JSON-RPC 2.0 subprocess wrapper.
4. Isolates third-party dependencies in a sandboxed virtual environment.

---

## Auditing Documentation Coverage & Drift

### Goal
Audit documentation coverage across Python modules and detect broken relative links or stale symbols.

### Step 1: Audit AST Coverage
```bash
harness doc audit --root . --min-coverage 95.0 --output scratch/coverage.json
```

### Step 2: Check for Broken Links and Stale Symbols
```bash
harness doc drift-check --root . --output scratch/drift.json
```

If drift is detected, inspect `scratch/drift.json` to identify broken relative links or stale class names.
