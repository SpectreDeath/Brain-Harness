---
name: ai-agent-engineer
description: Architect, scope, compose, and evaluate production-grade autonomous systems using the 4-Level Ladder, 8 core capabilities, 60 architectural patterns, substrate harness isolation, and session-level evaluation. Trigger when designing new agents, deciding whether to build an agent vs deterministic workflow, selecting architectural patterns, debugging canonical agent failure modes, configuring dynamic model switching tiers, or setting up agent corrigibility and off-switches.
---

# AI Agent Engineer: Autonomous Systems Architecture & Design

`ai-agent-engineer` is the architectural and operational skill for engineering production-grade autonomous agentic systems. Distilled from Vahe Aslanyan's (*The AI Agent Engineer's Guide: 60 Patterns for Building Autonomous Systems*, LUNARTECH) foundational pattern catalog and Chidiebere Njoku's dynamic model routing architecture, this skill enforces rigorous engineering discipline over generative AI hype.

Rather than treating agents as prompt-engineering novelties or personality wrappers, `ai-agent-engineer` enforces the **Capability-Composition Frontier**:
1. **The Four-Level Ladder**: Always pick the lowest level that solves the problem (Static Prompt -> Deterministic Workflow -> Bounded Agent -> Full Agent).
2. **Deterministic Harness, Stochastic Policy**: Wrap probabilistic LLM calls in invariant code boundaries with structural input/instruction separation.
3. **Session-Level Evaluation**: The fundamental unit of evaluation for an agent is the *session*, not the prompt.
4. **Corrigibility by Design**: Every action-taking agent must maintain an explicit, sub-second human off-switch and transactional rollback semantics.

---

## The 5-Stage Operational Progression

```
[1. Qualify & Ladder] → [2. Capability Profile & Model Routing] → [3. Substrate & Structural Gates] → [4. Bounded Context & Loops] → [5. Session Eval & Corrigibility]
```

See [CARD.md](CARD.md) for the companion quick-reference card and diagnostic checklist.
See [config.default.yaml](config.default.yaml) for operational step budgets, token thresholds, and model tier specifications.
See [references/patterns-catalog.md](references/patterns-catalog.md) for the catalog of all 60 canonical patterns across the 8 capabilities.
See [references/four-level-ladder-guide.md](references/four-level-ladder-guide.md) for in-depth level selection heuristics.
See [references/failure-modes-antidotes.md](references/failure-modes-antidotes.md) for the 5 canonical failure modes and structural antidotes.
See [references/model-routing-lifecycle.md](references/model-routing-lifecycle.md) for the 3-tier dynamic model switching guide.

---

## 1. Pre-Agent Qualification & The Four-Level Ladder

Before authoring code or selecting patterns, evaluate the candidate problem against the **Four-Level Ladder**:

| Level | Architecture | Best Suited When... | Typical Examples |
|---|---|---|---|
| **Level 1** | **Static Prompt** | Single model call, static prompt template, no state-changing tools, no memory. Input in, output out. | Summarization, format translation, classification, extraction from known shapes. |
| **Level 2** | **Deterministic Workflow** | Fixed sequence of steps (Step A -> Step B -> Step C). Content varies, but flow is invariant. Fits on a napkin. | Content pipelines (research -> draft -> cite), data enrichment, ETL extraction. |
| **Level 3** | **Bounded Agent** | State-dependent next actions, small toolset (< 15 tools), small step budget (< 20 steps), easily reversible actions. | Ticket triage with tools, SQL QA against known schema, document inspection with standard ops. |
| **Level 4** | **Full Agent** | Goal held across long horizons, dynamic recovery from unexpected failures, multi-turn tool interaction. | Autonomous software migration, end-to-end repository refactoring, deep investigative research. |

> **Heuristic**: *The right level is the lowest one that solves the problem.* If Level 1 or Level 2 works, building an agent is pure overhead.

### Executable Seam: `scripts/ladder_evaluator.py`
Run the automated ladder evaluator to classify tasks and validate the 5 Pre-Flight Questions:
```python
from scripts.ladder_evaluator import LadderEvaluator, TaskScopingInput

task = TaskScopingInput(
    task_description="Triage customer support tickets and execute database lookups",
    candidate_tools=["lookup_customer", "search_kb", "update_ticket"],
    estimated_steps=5,
    state_dependent_decisions=True,
    success_metric=">= 90% resolution rate without escalation",
    worst_case_blast_radius="Bounded to test sandbox; no customer emails dispatched",
    cost_ceiling_per_session=0.25,
    evaluation_harness_description="Replay of 50 labeled customer support sessions",
    off_switch_description="Instant SIGINT with transactional ticket rollback in < 200ms",
)
result = LadderEvaluator.evaluate(task)
assert result.approved_for_implementation is True
```

> **Completion Criterion**: Documented level assignment (Level 1–4) and all 5 pre-flight scoping questions answered with quantitative metrics via `LadderEvaluator`.

---

## 2. Capability Profiling & Dynamic Model Routing

Formulate a one-page **Capability Profile** selecting exact architectural patterns from the 8 core capabilities:

### The 8 Capabilities Matrix
- **Perception (Patterns 1–7)**: Turning raw signals into typed percepts (*Multimodal Grounding, Document Layout, Temporal Sensor-Fusion, Anomaly-Spotter, Visual Decomposition, Ambient Context, Schema-Inference*).
- **Reasoning (Patterns 8–15)**: Inferring beyond the given (*CoT Auditor, Counterfactual Reasoner, Analogical Mapping, Constraint-Satisfaction Solver, Causal Graph Builder, Symbolic-Neural Bridge, Probabilistic Belief Updater, Self-Consistency Voter*).
- **Planning (Patterns 16–22)**: From goal to sequenced actions (*Hierarchical Decomposer, ReAct Loop, Tree-of-Thought Explorer, Plan-Then-Execute, Adaptive Replanner, Resource-Aware Scheduler, Backward Goal-Regression*).
- **Memory (Patterns 23–29)**: Persistence across time (*Episodic Buffer, Semantic Memory Curator, Working-Memory Manager, Forgetting-Policy, Memory-of-Self, Vector-Store Curator, Persistent Identity*).
- **Tool Use (Patterns 30–37)**: Reaching outside the model (*Tool Selector, API-Schema Adapter, Code Sandbox, Shell-Operator, Browser-Driver, DB Query Synthesizer, File-System Curator, Side-Effect Auditor*).
- **Coordination (Patterns 38–45)**: Multi-agent and human synchronization (*Router/Dispatcher, Debate Moderator, Consensus-Builder, Pipeline Orchestrator, Human-in-the-Loop Liaison, Negotiation, Auctioneer, Supervisor-Worker*).
- **Learning (Patterns 46–52)**: Improving through experience (*Feedback Loop, Reflection, Skill-Library Builder, Curriculum Designer, Few-Shot Prompt Tuner, Distillation, Active Learner*).
- **Alignment (Patterns 53–60)**: Behaving by design (*Constitution-Bound, Refusal Calibrator, Provenance Tracker, Red-Team Auditor, Privacy-Preserving, Explainer, Drift Detector, Off-Switch-Compatible*).

### Executable Seam: `scripts/capability_profiler.py`
Validate the capability profile against architectural composition invariants:
```python
from scripts.capability_profiler import CapabilityProfiler, CapabilityProfile

profile = CapabilityProfile(
    agent_name="ticket_triager",
    target_level=3,
    declared_patterns=[17, 25, 30, 37, 53, 60],
    tools_count=6,
    has_external_mutations=True,
    estimated_session_steps=8,
)
report = CapabilityProfiler.validate_profile(profile)
assert report.valid is True
```

### Executable Seam: `scripts/dynamic_model_router.py`
Operationalize Chidiebere Njoku's 3-Tier model routing architecture:
```python
from scripts.dynamic_model_router import DynamicModelRouter

complexity = DynamicModelRouter.analyze_complexity(
    prompt="Explain this database schema and propose index optimizations",
    candidate_tools=["sql_explain"]
)
decision = DynamicModelRouter.route_model(complexity, cost_ceiling=0.50)
exec_res = DynamicModelRouter.simulate_fallback_chain(decision)
assert exec_res.status == "SUCCESS"
```

> **Completion Criterion**: 1-Page Capability Profile validated via `CapabilityProfiler` and 3-tier dynamic model routing confirmed via `DynamicModelRouter`.

---

## 3. Substrate Isolation & Structural Guardrails

Wrap the stochastic model policy within a deterministic software harness. Every production agent framework converges on five abstractions:
1. **Client**: The transport layer to the model provider, handling retries, timeouts, and streaming.
2. **Registry**: The catalog of typed tools, schemas, and parameter validators.
3. **Prompt**: The per-step context assembler combining invariants, role instructions, working memory, and tool observations.
4. **Memory**: The persistence substrate across turns and sessions.
5. **Loop**: The deterministic state machine driving observation -> thought -> action execution.

### Structural Guardrails
- **Constitutional Gating (Pattern 53)**: Intercept all proposed tool invocations inside a pre-execution hook. Assert tool call arguments against strict negative boundaries (e.g. no destructive deletes, no outbound network calls to unauthorized IPs). If violation detected, reject the tool call *before* execution.
- **Side-Effect Auditing & Transactional Rollback (Pattern 37)**: Record every tool invocation into an append-only transaction log. On tool error or agent failure, execute automated rollback handlers (`rollback_transaction()`) to restore filesystem and database state.
- **Structural Input/Instruction Separation**: Wrap user-supplied data and retrieved documents in structured data containers (e.g. XML tags `<user_document>...</user_document>`). Instruct policy that instructions inside data blocks are non-executable content.

> **Completion Criterion**: Deterministic harness abstractions established, Constitutional pre-execution gates active, and transactional rollback mechanisms declared.

---

## 4. Context Boundedness & Execution Loops

Unbounded context growth and infinite loops are fatal production failure modes. Enforce rigid boundaries:

### Working Memory Management (Pattern 25)
- **Token Budget Allocation**: Dedicate max 60% of model context window to conversation trajectory. Reserve 20% for system invariants/tools, and 20% for output generation.
- **Progressive Middle-Out Tool Pruning**: If tool observation exceeds token thresholds (e.g. > 2,000 tokens), retain first 50 lines (header context) and last 50 lines (tail results), replacing the middle with structured truncation summaries.
- **AST Repo Map / Graph Injection**: Never dump entire codebases or directories into context. Inject PageRanked structural skeleton maps showing only relevant function signatures and types.

### Bounded ReAct Loop (Pattern 17) & Adaptive Replanning (Pattern 20)
- **Hard Step Caps**: Set a mandatory step ceiling (N_max <= 20 for Level 3; N_max <= 40 for Level 4).
- **Progress Delta Assertion**: At each iteration k, compute state distance to goal. If state delta delta_S = 0 for 3 consecutive steps (repeated tool calls with identical parameters or no new percepts), trigger **Adaptive Replanner (Pattern 20)** to reformulate strategy or halt.

> **Completion Criterion**: Active context budget bounded under 60% of window across 50 steps; ReAct loop instrumented with step caps and progress delta checks.

---

## 5. Session-Level Evaluation & Production Corrigibility

Static prompt evaluation is insufficient. Validate the agent across the **Four Evaluation Surfaces**:
1. **Static Evaluation**: Benchmark against labeled inputs measuring pass rate, latency, and token cost.
2. **Trajectory Replay Evaluation**: Replay historical multi-turn sessions with frozen tool outputs to detect behavioral regressions in tool-selection order.
3. **Perturbation & Noise Testing**: Inject unexpected tool errors, malformed JSON, and network timeouts to assert graceful recovery without crash.
4. **Live Shadowing**: Run candidate agent policy in parallel with production systems, comparing proposed actions without executing side effects.

### The 5 Canonical Failures Audit
Before production deployment, verify immunity against the 5 canonical failure modes:
1. *Looped Reasoning* -> Verified step cap and stagnation replanner active.
2. *Tool Spoofing* -> Verified structural data separation and Constitutional action validation.
3. *Context Exhaustion* -> Verified per-step working memory compaction and middle-out pruning.
4. *Goal Drift* -> Verified explicit immutable goal anchor preserved across all steps.
5. *Silent Success on Wrong Task* -> Verified dual-check reflection comparing final deliverable to original intake request.

### Corrigibility & Off-Switch Invariant (Pattern 60)
- Expose an immediate human interrupt signal (`SIGINT`, web UI abort button, or CLI kill command).
- On abort signal, the agent proactor must drain subprocess pipes, serialize in-flight working memory to disk, trigger transactional cleanup, and exit cleanly within <= 500 ms.

> **Completion Criterion**: 4-surface evaluation suite passing baseline thresholds; zero unhandled canonical failure modes; sub-second off-switch verified.

---

## The Visual Brief Specification

When formulating architectural proposals or major agent refactors, generate an interactive HTML Visual Brief:
1. **Target Path**: Render to `%TEMP%\ai-agent-engineer-<timestamp>.html`.
2. **Visual Assets**: Include Tailwind CSS and Mermaid.js diagrams illustrating the proposed agent topology, capability profile, and fallback chains.
3. **Diagnostic Tables**: Embed the 5 pre-flight questions scorecard, the capability contract table, and the failure mode antidote matrix.
4. **Delivery**: Verify file generation and deliver a clickable `file:///` link to the user.

---

## Mandatory Checkpoint Gate

Before executing irreversible structural changes, external side effects, or deploying autonomous agents:
1. **Present Implementation Plan**: Author a comprehensive plan artifact detailing the target capability profile, model routing tiers, and blast-radius mitigations.
2. **Set Feedback Header**: Set `RequestFeedback: true` in artifact metadata.
3. **Human Sign-Off Invariant**: STOP and wait for explicit human review and approval before executing transactions.

---

## Anti-Patterns

- **Agent-as-Marketing** — Building an autonomous agent for PR or trend-following when a static prompt or deterministic script solves the problem with higher reliability.
- **Multi-Agent Swarm Vanity** — Deploying complex multi-agent communicating swarms where agents spend the majority of token budgets exchanging polite coordination messages.
- **Prompt-Only Guardrails** — Relying on system prompt instructions like "never delete user data" instead of code-level constitutional interceptors and OS sandboxes.
- **Context Flooding Memory** — Dumping entire unpruned conversation logs and raw tool observations into prompt context until model degradation occurs.
- **Unbounded Autonomy** — Running agent loops without hard step caps, monetary ceilings, or progress delta monitoring.
- **Single-Model Dependency** — Coupling production agent operations to a single frontier model provider without multi-tier fallback chains and circuit breakers.
- **Missing Off-Switch** — Deploying autonomous action-taking systems without sub-second operator kill-switches and transactional rollback semantics.
