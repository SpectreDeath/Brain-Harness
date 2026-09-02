---
name: sme-ann-backprop
description: Formulate and execute Agentic Neural Network (ANN) textual backpropagation, momentum-smoothed gradient updates, and 4-stage candidate team block validation to autonomously optimize multi-agent DAGs and repair failing agent workflows.
---

# SME ANN Backprop & Self-Evolving Workflow Engine

`sme-ann-backprop` operationalizes Agentic Neural Network ($\mathcal{ANN}$) textual backpropagation and candidate pool governance for Brain Harness. Distilled from the **SME Forensic Gateway (Lawnmower Man v3.0.1)**, it treats multi-agent workflow DAGs as layered networks where execution errors are backpropagated as structured textual gradients ($\nabla_{\text{text}}$), smoothed via momentum velocity buffers, and gated through a 4-stage validation filter before persistent pool insertion.

Every ANN self-optimization cycle follows a strict five-stage progression:

```
[1. Trajectory Analysis & Global Loss] → [2. Layerwise Local Gradients] → [3. Momentum Velocity Smoothing] → [4. 4-Stage Candidate Validation] → [5. Candidate Pool Commit & Routing]
```

See [CARD.md](CARD.md) for the companion summary card, backpropagation formulas, and verification invariants.
Consult `/crafting-skills` for skill craft standards, `/data-topology-mapper` for DAG blast radius mapping, and `/deep-repo-auditor` for repository distillation.

---

## 1. Trajectory Analysis & Global Textual Loss ($G_{\text{global}}$)

Inspect the execution transcript of a multi-agent or multi-step workflow to compute the global loss signal:

1. **Loss Quantification**:
   - Compute bounded loss score:
     $$\text{Loss}_{\text{global}} = \frac{\text{Number of Failed Steps / Layers}}{\text{Total Trajectory Steps}} \in [0.0, 1.0]$$
2. **Layer Failure Localization**:
   - Extract the specific layer indices $\ell \in [0, N-1]$ that raised exceptions, returned error observation payloads, or failed schema validation.
3. **Inter-Layer Structural Suggestions**:
   - Generate high-level routing suggestions and input rewiring instructions to isolate failed dependencies.

> **Completion criterion**: `GlobalGradient` object emitted with verified loss score, failed layer indices, and structural recommendations.

---

## 2. Layerwise Local Textual Gradients ($G_{\text{local},\ell}$)

Formulate local layerwise gradients for each active agent team block $f_{\ell}$:

1. **Combined Loss Computation**:
   - Balance global trajectory feedback with local step outcome using mixing parameter $\beta = 0.5$:
     $$\text{Loss}_{\text{combined}} = \beta \cdot \text{Loss}_{\text{global}} + (1 - \beta) \cdot \text{Loss}_{\text{local}}$$
2. **Node Prompt Refinement**:
   - For failed nodes: Append explicit output schema constraints, parameter validation checks, and error-handling directives.
   - For successful nodes: Optimize for conciseness and logical consistency.
3. **Validator Node Insertion**:
   - If structural gaps caused execution failure, insert downstream validation nodes (e.g. `node_validator` with static analysis or schema check roles).

> **Completion criterion**: `LocalGradient` synthesized for each affected layer with prompt suggestions and node/edge updates.

---

## 3. Momentum Velocity Smoothing (`MomentumBuffer`)

Smooth prompt and topological updates across iterations to eliminate oscillation:

1. **Update Velocity Tracking**:
   - Maintain historical gradient velocity per layer index $\ell$:
     $$G'_{t,\ell} = \alpha \cdot G_{t,\ell} + (1 - \alpha) \cdot G_{t-1,\ell} \quad (\alpha = 0.7)$$
2. **Prompt Merge & Stabilization**:
   - Merge previous prompt improvements with incoming suggestions to prevent catastrophic forgetting of validated instructions.

> **Completion criterion**: Momentum-smoothed local gradient $G'_{t,\ell}$ produced.

---

## 4. 4-Stage Candidate Validation Filter

Gate candidate agent blocks ($f'_{\ell}$) through 4 rigorous verification stages before pool insertion:

1. **Stage 1 (Node Validation)**:
   - Ensure all nodes declare valid agent identifiers, non-empty role prompts, and required capabilities.
2. **Stage 2 (Edge Validation)**:
   - Ensure all directed edges connect valid existing vertices; reject dangling links.
3. **Stage 3 (Structural Acyclicity & Deduplication)**:
   - Run cycle detection to guarantee strictly acyclic DAG execution.
   - Verify candidate structure is unique and not already present in the existing pool.
4. **Stage 4 (Performance Baseline)**:
   - Confirm projected candidate loss is $\le$ baseline performance threshold.

> **Completion criterion**: 4-stage filter returns `is_valid: true`. If invalid, failure reason and rejected stage are reported.

---

## 5. Candidate Pool Commit & Dynamic Selection

Persist validated candidate team blocks into SQLite WAL candidate pools:

1. **Atomic Insertion**:
   - Insert validated block into `candidate_pools` table ($F_{\ell}$) with unique `block_id`, `layer_index`, `loss_score`, and JSON schema payload.
2. **Dynamic $O(1)$ Team Selection**:
   - Select candidate team block minimizing loss score or matching specific task context tags during runtime execution.

> **Completion criterion**: Candidate block saved to SQLite WAL storage and ready for dynamic routing.

---

## In-File Reference & Formulas

- **Global Loss**: $\text{Loss}_{\text{global}} = \frac{|\text{Failed Layers}|}{|\text{Total Steps}|}$
- **Combined Layer Loss**: $\text{Loss}_{\text{combined}} = \beta \cdot \text{Loss}_{\text{global}} + (1 - \beta) \cdot \text{Loss}_{\text{local}}$
- **Momentum Smoothing**: $G'_{t} = \alpha G_{t} + (1 - \alpha) G_{t-1}$ where $\alpha = 0.7$
- **Candidate Pool**: $F_{\ell} = \{ f_{1}, f_{2}, \dots, f_{k} \}$ persisted in SQLite WAL `laboratory.db`

---

## Anti-Patterns

- **Oscillatory Prompt Churn** — Applying raw gradient updates without momentum smoothing, causing prompts to thrash between conflicting instructions.
- **Ungated Pool Pollution** — Committing candidate agent blocks without running the 4-stage validation filter.
- **Circular Execution Deadlocks** — Allowing edge mutations that introduce cycles into agent execution DAGs.
- **Unbounded Loss Metrics** — Using non-normalized loss scales instead of strictly bounded $[0.0, 1.0]$ loss metrics.
