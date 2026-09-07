# Skill Summary Card: `ai-agent-engineer`

```
┌────────────────────────────────────────────────────────────┐
│                    SKILL SUMMARY CARD                      │
├────────────────────────────────────────────────────────────┤
│ SKILL:       ai-agent-engineer                             │
│ Category:    agent_orchestration / architecture-engineering│
│ Invocation:  /ai-agent-engineer                            │
│ Trigger:     "design an agent", "build autonomous agent",  │
│              "agent patterns", "evaluate agent",           │
│              "dynamic model routing", "agent failure modes"│
│ Version:     1.1.0                                         │
│ Provides:    "autonomous_systems_architecture"             │
├────────────────────────────────────────────────────────────┤
│ Target:      Scope, architect, compose, and evaluate       │
│              production-grade autonomous agents across the │
│              4-Level Ladder and 60 canonical patterns.     │
└────────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Engineering Workflow

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Qualify & Ladder** | Map problem to 4-Level Ladder via `ladder_evaluator.py`; validate 5 scoping questions | Scoping Worksheet & Level Decision | Level justified; 5 questions passed with metrics |
| **2. Capability Profile** | Select patterns; validate via `capability_profiler.py`; route models via `dynamic_model_router.py` | 1-Page Capability Contract & Model Matrix | Invariants verified; 3-tier routing & fallback active |
| **3. Substrate & Gates** | Wrap policy in 5 abstractions; wire Constitution and Side-Effect Auditor | Deterministic Harness & Rollback Hooks | Invariant action gating active; rollback declared |
| **4. Bounded Loops** | Bound context via Working Memory Manager; instrument ReAct step caps | Bounded ReAct Engine & Pruning Config | Prompt budget $\le$ 60% window; stagnation replanner active |
| **5. Session Eval** | Execute 4-surface eval; audit against 5 canonical failures; wire off-switch | Session Eval Report & Corrigibility Hook | Evals passing; sub-second kill-switch verified |

---

## The Three Pillars Cheat Sheet

### 1. The Four-Level Ladder & Heuristics
- **Level 1 (Static Prompt)**: One model call, no tools, no memory. Input $\rightarrow$ Output.
- **Level 2 (Deterministic Workflow)**: Fixed step sequence ($A \rightarrow B \rightarrow C$). Content varies, flow is static.
- **Level 3 (Bounded Agent)**: Dynamic tool decisions, small toolset ($< 15$ tools), small budget ($< 20$ steps).
- **Level 4 (Full Agent)**: Long-horizon goal, autonomous error recovery, multi-turn state management.
> *Invariant: Always pick the lowest level that solves the problem.*

### 2. The 5 Canonical Failures & Antidotes
- **Looped Reasoning**: ReAct step bounds (Pat 17) + Adaptive Replanner progress delta (Pat 20).
- **Tool Spoofing**: Constitution-Bound gating (Pat 53) + Side-Effect Auditor rollback (Pat 37).
- **Context Exhaustion**: Working-Memory Manager middle-out pruning (Pat 25) + per-step prompt assembly.
- **Goal Drift**: Plan-Then-Execute immutable anchor (Pat 19) + Drift Detector (Pat 59).
- **Silent Success (Wrong Task)**: CoT Auditor (Pat 8) + Reflection verification against input (Pat 47).

### 3. Dynamic Model Routing 3-Tier Lifecycle
- **Tier 1 (Complexity Analysis)**: Intent classification, token length, reasoning depth scoring.
- **Tier 2 (Routing Matrix)**: Low $\rightarrow$ Flash/Haiku, Medium $\rightarrow$ Balanced, High $\rightarrow$ Extended Thinking.
- **Tier 3 (Resilient Fallbacks)**: Automated provider failover, jittered retry, circuit breaker.

---

## Verification & Quality Checklist

- [ ] **Level Justified**: Programmatically verified via `LadderEvaluator.evaluate()` before selecting Level 3/4.
- [ ] **5 Scoping Questions Complete**: Success metric, blast radius, cost ceiling, eval suite, off-switch defined.
- [ ] **Capability Profile Validated**: Programmatically asserted via `CapabilityProfiler.validate_profile()`.
- [ ] **Dynamic Model Router Active**: Tier 1 complexity analysis and Tier 3 fallback chain simulated.
- [ ] **Context Budget Bounded**: Working memory manager enforces middle-out truncation on tool observations.
- [ ] **Off-Switch Verified**: Operator abort halts agent in $\le 500\text{ ms}$ with clean resource disposal.
