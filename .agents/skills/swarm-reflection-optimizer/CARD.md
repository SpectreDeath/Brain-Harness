```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: swarm-reflection-optimizer                                    │
│ SKILL: swarm-reflection-optimizer                                     │
│ Category: agent_orchestration / meta-skills                          │
│ Version: 1.0.0                                                       │
│ Invocation: /swarm-reflection-optimizer                              │
│ Triggers: "swarm reflection optimizer", "optimize agent swarm",      │
│           "textual backprop", "game theoretic deliberation",         │
│           "questio reflection"                                       │
│ Requires: "harness-reflector", "mind-reader", "sme-ann-backprop",    │
│           "game-theoretic-swarm-deliberator", "questio-reflection"   │
│ Target: Multi-agent execution graph optimization & prompt backprop   │
└──────────────────────────────────────────────────────────────────────┘
```

# Swarm Reflection Optimizer — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Trajectory Audit** | Reconstruct execution DAG & localize error | Trajectory Loss Profile | Upstream failure root node identified |
| **Stage 2: ANN Backprop** | Calculate textual gradients & smooth updates | Textual Gradient Delta | Momentum-smoothed prompt updates computed |
| **Stage 3: Deliberation** | Formulate payoff matrix & run Borda count | Deliberation Matrix | Winning remediation strategy selected |
| **Stage 4: Questio Reflection** | Stress-test proposal against Aquinas objections | Questio Document | All counter-objections definitively answered |
| **Stage 5: Team Verify** | Execute candidate team & commit dual-file KI | Verified Graph & KI | Workflow passes green & dual-file KI saved |

---

## Vocabulary & Levers

- **Agentic Neural Network (ANN) Backprop**: Textual propagation of goal error signals backward through upstream agent prompts.
- **Momentum Smoothing**: Dampening prompt revisions across iterations to avoid erratic behavioral oscillations ($\beta = 0.7$).
- **Borda Count Voting**: Consensus voting algorithm ranking candidate actions across multiple ministerial agent personas.
- **Questio Protocol**: Four-part medieval disputation (*Utrum*, *Videtur Quod Non*, *Sed Contra*, *Respondeo*) stress-testing decisions.
- **Read-Only Session URI**: Querying active session databases via `file:...?mode=ro` to eliminate lock contention (Rule 22).
- **Composite Swarm Keying**: Keying multi-agent execution nodes as `{run_id}_{node_id}` to prevent cross-run collisions (Rule 36).

---

## Mandatory Invariants Checklist

- [ ] **Read-Only Session Ingestion**: Always connect to active session stores via read-only SQLite URI modes (Rule 22).
- [ ] **Composite Swarm Keying**: Node identifiers must use `{run_id}_{node_id}` composite keys (Rule 36).
- [ ] **Momentum-Smoothed Gradients**: Never overwrite agent prompts directly without applying momentum smoothing.
- [ ] **Aquinas Constitutional Check**: Every disputation must cite inviolable repository rules as *Sed Contra* authorities.
- [ ] **Canonical Dual-File Vault Format**: Knowledge items must be written as directory with `metadata.json` and `summary.md` (Rule 40).
