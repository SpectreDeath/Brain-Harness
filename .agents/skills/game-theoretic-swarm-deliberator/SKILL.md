---
name: game-theoretic-swarm-deliberator
description: Orchestrate multi-persona LLM agent swarms to deliberate multi-domain strategic actions and resolve game-theoretic payoff matrices using Borda count, weighted majority, and unanimous consensus voting rules. Trigger when coordinating domain ministers (Defense, Epidemiology, Finance, Diplomacy), resolving payoff matrices, running multi-agent wargames, or aggregating strategic proposals.
---

# Game-Theoretic Swarm Deliberator: Multi-Persona Action & Payoff Voting Engine

`game-theoretic-swarm-deliberator` is the multi-agent consensus and game-theoretic voting engine distilled from the Strategify simulation harness. It orchestrates parallel domain personas (e.g. Defense, Epidemiology, Finance, Diplomacy, Legal) to deliberate strategic options and evaluate candidate payoff matrices using formal social choice voting rules.

Every deliberation session follows a deterministic 5-stage progression:

```
[1. Snapshot & Persona Fan-Out] → [2. Parallel Deliberation] → [3. Payoff Matrix Formulation] → [4. Voting & Consensus Synthesis] → [5. Verification & Action Dispatch]
```

See [CARD.md](CARD.md) for the companion summary card, voting rule cheat sheet, and invariant checklist.

---

## The 5-Stage Deliberation Progression

### Stage 1: Snapshot & Persona Fan-Out
Ingest the multi-domain simulation state snapshot and configure persona priority weights:
1. **Domain Minister Personas**:
   - `Defense` (Priority Weight: 1.2x) — Focuses on readiness, spectrum allocation, EW jamming, and deterrent force posture.
   - `Epidemiology` (Priority Weight: 1.1x) — Focuses on transmission rates ($R_0$), NPI lockdowns, and vaccine R&D.
   - `Finance` (Priority Weight: 1.0x) — Focuses on GDP growth, trade tariffs, supply chain chokepoint resilience, and inflation.
   - `Diplomacy` (Priority Weight: 1.0x) — Focuses on bilateral tensions, treaty compliance, multilateral summits, and alliance pacts.
2. **Provider Routing**: Query live providers (Ollama, OpenAI, Anthropic) or engage deterministic rule-based heuristic fallbacks.

> **Completion criterion**: Persona roster initialized with domain priority weights and state snapshot summary.

---

### Stage 2: Parallel Deliberation & Proposal Generation
Each persona independently reviews the domain snapshot and emits a structured proposal:
- `persona_name`: Name and role identifier.
- `domain`: Functional portfolio.
- `recommended_action`: Proposed tactical or policy action.
- `confidence_score`: Float between $0.0$ and $1.0$.
- `reasoning_chain`: Step-by-step rationale citing snapshot metrics.

> **Completion criterion**: Structured `AgentProposal` objects harvested from 100% of participating personas.

---

### Stage 3: Payoff Matrix & Action Candidate Formulation
Formulate the normal-form game or strategic candidate vector:
- Construct candidate action profiles $A = (a_1, a_2, \dots, a_k)$ or payoff candidate matrices.
- Align candidate choices against current adversary threat models and environmental stress factors.

> **Completion criterion**: Candidate action profile set or payoff candidate matrix array populated.

---

### Stage 4: Voting & Consensus Synthesis
Evaluate candidate options using the designated social choice aggregation rule:
1. **Borda Count Voting (`voting_rule="borda"`)**:
   - Each persona ranks candidates from best to worst.
   - Scores are assigned: $(N - 	ext{rank}) 	imes 	ext{priority\_weight}$.
   - The candidate with the maximum cumulative Borda score is selected as the winning action.
2. **Weighted Majority Voting (`voting_rule="majority"`)**:
   - Each persona casts its top preference weighted by its priority multiplier.
   - The candidate receiving the plurality of weighted votes wins.
3. **Unanimous Consensus (`voting_rule="unanimous"`)**:
   - Requires top-choice unanimity across all personas; defaults to safest defensive candidate upon deadlock.

> **Completion criterion**: Winning strategic payload synthesized and composite consensus score calculated ($\in [0, 1]$).

---

### Stage 5: Verification & Action Dispatch
1. Validate consensus action vector against structural safety invariants and treaty compliance checks.
2. Dispatch action vector to simulation stepping engine or external execution environment.
3. Record deliberation transcript and consensus score to execution session history.

> **Completion criterion**: Deliberation result validated and dispatched with zero unhandled exceptions.

---

## Voting Rule Matrix Reference

| Voting Rule | Mathematical Formulation | Best Used For | Deadlock Behavior |
|---|---|---|---|
| **Borda Count** | $	ext{Score}(c) = \sum_{p} (N - 	ext{rank}_p(c)) \cdot w_p$ | Multi-criteria trade-offs with conflicting priorities | Max score tie-breaker |
| **Weighted Majority** | $	ext{Votes}(c) = \sum_{p: 	ext{top}(p)=c} w_p$ | High-tempo tactical decision-making | Highest weight persona |
| **Unanimous** | $orall p_i, p_j: 	ext{top}(p_i) = 	ext{top}(p_j)$ | High-stakes nuclear/escalation thresholds | Conservative fallback |

---

## Anti-Patterns

- **Monolithic Persona Blending** — Collapsing distinct domain perspectives into a single generic prompt, eroding domain tension and realistic trade-off modeling.
- **Unweighted Aggregation** — Treating critical life-safety domains (Epidemiology, Defense) identically to soft diplomacy during existential crises.
- **Silent API Failure** — Crashing the swarm when an external LLM endpoint times out instead of engaging deterministic rule-based heuristic fallbacks.
- **Unranked Payoff Guessing** — Choosing payoff candidates without structured social choice aggregation.
