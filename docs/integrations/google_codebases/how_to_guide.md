# How-To Guides: Google Codebase Integrations

Practical recipes for common tasks across the 7 Google integration plugins.

---

## Recipe 1: Optimize Agent Prompts Using GEPA

**Goal**: Automatically refine an agent's system prompt using Generative Prompt Optimization (GEPA).

```python
from plugins.agent_orchestration.google_adk_optimizer.main import (
    GOOGLE_ADK_OPTIMIZER_SERVICE_KEY,
    GoogleAdkOptimizerPlugin,
)

async def optimize():
    ctx = ServiceContext()
    p = GoogleAdkOptimizerPlugin()
    await p.enable(ctx)

    opt_service = ctx.require(GOOGLE_ADK_OPTIMIZER_SERVICE_KEY)
    result = opt_service.gepa_optimize_prompt(
        system_prompt="You are an autonomous code auditor.",
        iterations=3,
        metric="accuracy",
    )

    print("Baseline Score:", result["baseline_score"])
    print("Optimized Score:", result["final_score"])
    print("Optimized Prompt:\n", result["optimized_prompt"])
```

---

## Recipe 2: Export Agent Execution DAGs for ADK Web UI

**Goal**: Format a multi-agent execution graph for visualization in the Angular ADK dashboard or Mermaid.

```python
from plugins.developer_tooling.google_adk_web_bridge.main import (
    GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY,
    GoogleAdkWebBridgePlugin,
)

async def export_dag():
    ctx = ServiceContext()
    p = GoogleAdkWebBridgePlugin()
    await p.enable(ctx)

    web_bridge = ctx.require(GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY)
    nodes = [
        {"id": "planner", "label": "Planner Agent", "type": "supervisor"},
        {"id": "executor", "label": "Code Runner", "type": "worker"},
        {"id": "verifier", "label": "Adversarial Verifier", "type": "critic"},
    ]
    edges = [
        {"source": "planner", "target": "executor"},
        {"source": "executor", "target": "verifier"},
    ]

    a2ui_graph = web_bridge.export_graph(nodes, edges, format="a2ui")
    mermaid_graph = web_bridge.export_graph(nodes, edges, format="mermaid")

    print("Mermaid Syntax:\n", mermaid_graph["graph_data"])
```

---

## Recipe 3: Configure Tunix GRPO for Reasoning RL

**Goal**: Generate a verified JAX configuration for Group Relative Policy Optimization (GRPO).

```python
from plugins.machine_learning.google_tunix_posttraining.main import (
    GOOGLE_TUNIX_POSTTRAINING_SERVICE_KEY,
    GoogleTunixPosttrainingPlugin,
)

async def configure_grpo():
    ctx = ServiceContext()
    p = GoogleTunixPosttrainingPlugin()
    await p.enable(ctx)

    tunix = ctx.require(GOOGLE_TUNIX_POSTTRAINING_SERVICE_KEY)
    config = tunix.inspect_config(
        pipeline_type="grpo",
        model_name="gemma-2-9b",
        learning_rate=5e-5,
        batch_size=8,
    )

    step_res = tunix.launch_grpo(config["config"], dry_run=True, num_steps=10)
    print("Simulated Policy Loss:", step_res["metrics"]["final_policy_loss"])
```
