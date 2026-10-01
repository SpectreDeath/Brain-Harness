# Brain Harness Getting Started Tutorial

Welcome to Brain Harness. This tutorial takes you step-by-step through installing the runtime, initializing your workspace, dispatching your first autonomous agent task, and inspecting execution trees.

---

## Prerequisites

Before starting, ensure you have:
1. Python 3.10 or higher installed.
2. Git installed and accessible in your system PATH.
3. Access to an LLM provider API key (e.g. OpenAI, Anthropic, or OpenRouter), or a local LLM runner (e.g. Ollama).

---

## Lesson 1: Environment Setup & Workspace Initialization

Brain Harness operates within an isolated workspace containing your custom configurations, cached plugins, knowledge items, and session history.

### 1.1 Create and Activate a Virtual Environment

```bash
# Clone the repository
git clone https://github.com/SpectreDeath/Brain-Harness.git
cd "Brain-Harness"

# Create and activate a Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows PowerShell: .venv\Scripts\Activate.ps1

# Install runtime dependencies in editable mode
pip install -e .
```

### 1.2 Initialize the Harness Workspace

Run `harness init` to scaffold the `.harness/` directory structure:

```bash
harness init
```

This creates the local state directories:
- `.harness/config.yaml`: Core runtime configuration file.
- `.harness/plugins/`: Staged external plugins and sandboxed virtualenvs.
- `.harness/knowledge/`: Epistemic Knowledge Vault storing verified facts and heuristics.
- `.harness/sessions/`: SQLite relational store tracking agent conversation DAGs and step transcripts.

---

## Lesson 2: Running Your First Autonomous Agent Task

Brain Harness includes a production-grade ReAct (Reasoning + Acting) execution engine. In this lesson, we will ask an agent to inspect the local workspace.

### 2.1 Set Up Your API Key

Export your provider API key as an environment variable:

```bash
# Example for OpenRouter or OpenAI
export OPENROUTER_API_KEY="sk-or-v1-..."
# On Windows PowerShell:
# $env:OPENROUTER_API_KEY = "sk-or-v1-..."
```

### 2.2 Dispatch a Task via the CLI

Run an autonomous task with `harness agent run`:

```bash
harness agent run "Inspect the plugins directory and report how many domain categories exist."
```

During execution, you will observe the ReAct engine's progress:
1. **Thought**: The agent analyzes your instruction and determines the required tool.
2. **Action**: The agent executes a tool inside an atomic context transaction.
3. **Observation**: The tool returns structured output back to the model.
4. **Final Answer**: Once the task is satisfied, the agent returns the conclusive response.

---

## Lesson 3: Inspecting Execution Trees & Transcripts

Brain Harness records every step, tool invocation, and token metric into an authoritative session graph.

### 3.1 View the Session DAG Tree

To view the hierarchical ASCII tree of steps for a completed task:

```bash
# List recent session IDs
harness session list

# Render the step execution tree
harness session tree <session_id>
```

The output renders an ASCII DAG depicting step transitions:
```
Session: sess_94a2b1 [COMPLETED]
├── [Step 1] Thought: Inspect available plugin categories on disk.
│   └── Tool: list_dir(DirectoryPath="plugins") -> OK
├── [Step 2] Thought: Count distinct category folders.
│   └── Tool: count_items(...) -> 11 categories
└── [Step 3] Final Answer: There are 11 domain plugin categories.
```

### 3.2 Export the Machine-Readable Transcript

Export the full execution trajectory to JSON:

```bash
harness session export <session_id> --output trajectory.json
```

### 3.3 Launch the Web Dashboard

Launch the embedded single-page control dashboard to view the live Mermaid dependency graph and telemetry:

```bash
harness ui --port 8000
```
Open `http://127.0.0.1:8000` in your web browser.

---

## Lesson 4: Querying the Skill Knowledge Graph

Brain Harness maintains an in-memory directed knowledge graph indexing all agent skills declared in `.agents/skills/`.

### 4.1 Route an Intent to Candidate Skills

To determine which skill is suited for a developer task:

```bash
harness skills route "We need to verify code changes before creating a pull request"
```

The skill router evaluates semantic relevance and returns ranked matches:
```
Rank 1: pre-commit-security-guard (score: 0.88)
Rank 2: adversarial-agent-verifier (score: 0.82)
```

### 4.2 Compute a Directed Execution Chain

To find the optimal multi-stage sequence between two capabilities:

```bash
harness skills chain --from code-review --to tdd
```

The graph executes BFS topological pathfinding and outputs the validated execution sequence.

---

## Next Steps

Now that you understand workspace initialization, task execution, session inspection, and skill routing:
- Learn how to build custom capabilities in the [How-To Guides](HOWTO.md).
- Understand the micro-kernel internals in the [Architecture Explanation](EXPLANATION.md).
- Look up specific service protocols in the [Reference Documentation](reference/README.md).
