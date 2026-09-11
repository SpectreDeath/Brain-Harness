---
name: swarm-reflection-optimizer
description: Introspect agent session execution logs, apply textual backpropagation to repair failing multi-agent DAGs, and resolve game-theoretic payoffs through adversarial reflection. Do not use for simple deterministic script debugging or linear tasks.
---

# Swarm Reflection Optimizer: Multi-Agent Backpropagation & Deliberation

`swarm-reflection-optimizer` is an authoritative composite meta-skill that orchestrates recursive introspection, textual error backpropagation, game-theoretic deliberation, and Aquinas-style adversarial self-reflection across multi-agent execution graphs.

It coordinates five specialized capabilities:
1. **Endogenous History & Execution Log Introspection** ([`harness-reflector`](../harness-reflector/SKILL.md))
2. **Brain Bridge & Memory Introspection** ([`mind-reader`](../mind-reader/SKILL.md))
3. **Agentic Neural Network (ANN) Textual Backpropagation** ([`sme-ann-backprop`](../sme-ann-backprop/SKILL.md))
4. **Game-Theoretic Swarm Deliberation & Payoff Resolution** ([`game-theoretic-swarm-deliberator`](../game-theoretic-swarm-deliberator/SKILL.md))
5. **Aquinas Adversarial Self-Reflection Protocol** ([`questio-reflection`](../questio-reflection/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/sme-ann-backprop` for textual gradient dynamics, `/game-theoretic-swarm-deliberator` for voting rules, and [backprop-heuristics.md](references/backprop-heuristics.md) for backpropagation heuristics.

---

## The 5-Stage Swarm Optimization Progression

```
[1. Transcript Introspection] ──► [2. ANN Textual Backprop] ──► [3. Game-Theoretic Deliberation]
                                                                            │
                                                                            ▼
[5. Team Verification & Commit] ◄── [4. Aquinas Invariant Gate] ◄───────────┘
```

---

## 1. Transcript Introspection & Error Attribution

Audit multi-agent trajectory logs and identify precise failure localization along execution DAGs:

1. **Streaming JSONL Transcript Ingestion (Rule 22)**:
   - Query session transcripts via read-only SQLite URI modes (`file:...?mode=ro`) to eliminate lock contention.
2. **DAG Topology Reconstruction (Rule 17 & Rule 36)**:
   - Reconstruct spawn edges and thread lifecycle states using composite keying (`{run_id}_{node_id}`).
3. **Loss Function Formulation**:
   - Quantify trajectory error signals: tool call failures, hallucinated schemas, budget blowout, or goal deviations.

> **Completion criterion**: Trajectory loss computed and failure blamed to specific upstream node in execution DAG.

---

## 2. ANN Textual Backpropagation

Propagate error gradients backward through the multi-agent graph via structured textual backprop:

1. **Calculate Textual Error Gradients**:
   - Compute delta directives explaining *why* the node output deviated from expectations.
2. **Momentum-Smoothed Prompt Updates**:
   - Apply momentum smoothing to prevent destructive oscillation: update $= \beta \cdot \text{prior} + (1 - \beta) \cdot \text{gradient}$.
3. **Candidate Team Block Reconfiguration**:
   - Scaffolding candidate prompt and persona revisions for failing nodes in the DAG.

> **Completion criterion**: Textual gradient updates calculated and applied to target node system prompts.

---

## 3. Game-Theoretic Swarm Deliberation

Assemble multi-persona agent swarms to evaluate and deliberate competing remediation strategies:

1. **Ministerial Persona Allocation**:
   - Spawn distinct personas (Architect, Security Auditor, Reliability Engineer, Performance Specialist).
2. **Payoff Matrix Formulation**:
   - Construct a matrix evaluating payoff across Risk, Complexity, Maintainability, and Latency.
3. **Consensus Voting Rules**:
   - Apply Borda count ranking, weighted majority, or unanimous consensus to select winning repair strategy.

> **Completion criterion**: Payoff matrix evaluated and consensus repair strategy resolved via Borda count.

---

## 4. Aquinas Adversarial Self-Reflection (Questio)

Stress-test the consensus strategy through rigorous medieval disputation:

1. **The Question (*Utrum*)**:
   - Formulate the precise architectural proposal as a disputation question.
2. **The Objections (*Videtur Quod Non*)**:
   - Formulate the strongest possible counter-arguments, failure edge cases, and regression vectors.
3. **The Authority (*Sed Contra*)**:
   - Cite inviolable repository rules (Rule 1 to Rule 44) as binding constitutional guardrails.
4. **The Resolution (*Respondeo Dicendum*)**:
   - Defend the refined proposal, systematically dismantling each objection with mathematical or architectural proofs.

> **Completion criterion**: Questio disputation document completed with all counter-objections definitively answered.

---

## 5. Candidate Team Verification & Memory Commit

Validate candidate repair under test conditions and persist heuristics:

1. **4-Stage Candidate Team Execution**:
   - Re-run the optimized multi-agent workflow inside transactional isolation (`async with context.transaction()`).
2. **Regression Contract Pass**:
   - Confirm target task completes with zero errors and token budget stays within limits.
3. **Knowledge Vault Distillation (Rule 40)**:
   - Scaffolding canonical dual-file items (`metadata.json` + `summary.md`) capturing the repaired failure topology and prompt heuristics.

> **Completion criterion**: Repaired workflow passes 100% and optimization heuristics committed to Knowledge Vault.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every optimization run renders an interactive HTML visual brief in `%TEMP%` displaying the execution DAG loss topology, Borda count payoff matrices, and before-and-after token consumption.

### 2. The Mandatory Checkpoint Pillar
The agent must never deploy prompt adjustments or mutate agent DAG definitions without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent ungrounded prompt thrashing, voting collusion, and circular disputations.

---

## Anti-Patterns

- **Direct Prompt Overwriting** — Modifying agent prompts on a single failure without computing textual gradients or analyzing causal DAG roots.
- **Unbounded Disputation Loops** — Running philosophical self-reflection without an actionable resolution (*Respondeo*) and testable verification.
- **Single-File Vault Pollution** — Dumping single flat JSON files into `.harness/knowledge/` instead of the canonical dual-file directory (`metadata.json` + `summary.md`).
- **Collusive Swarm Homogeneity** — Populating deliberation swarms with identical personas that rubber-stamp proposals without genuine adversarial tension.
- **Lock Contention on Active Sessions** — Querying live session databases in write mode instead of read-only URI modes (`mode=ro`, Rule 22).
- **Missing Negative Boundaries** — Scaffolding skills without explicit `Do not use for...` constraints in frontmatter descriptions.
