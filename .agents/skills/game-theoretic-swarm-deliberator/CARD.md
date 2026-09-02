# Skill Summary Card: `game-theoretic-swarm-deliberator`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        game-theoretic-swarm-deliberator          │
│ Category:    multi_agent / game_theory / simulation    │
│ Invocation:  /game-theoretic-swarm-deliberator         │
│ Trigger:     "deliberate swarm", "swarm voting",       │
│              "resolve payoff matrix", "wargame swarm"  │
│ Version:     1.0.0                                     │
│ Requires:    "compute-model-assessor"                  │
│ Provides:    "multi_persona_consensus_deliberation"    │
├────────────────────────────────────────────────────────┤
│ Target:      Synthesize domain minister proposals into │
│              game-theoretic consensus action vectors.  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Deliberation Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Snapshot & Fan-Out** | Ingest state & configure persona weights | Persona roster | Weights initialized |
| **2. Parallel Deliberation** | Harvest structured domain proposals | `AgentProposal` array | 100% persona coverage |
| **3. Payoff Formulation** | Build candidate payoff profile matrix | Candidate action set | Candidate set non-empty |
| **4. Voting Synthesis** | Apply Borda count / Majority / Unanimity | `SwarmDeliberationResult` | Winning action selected |
| **5. Action Dispatch** | Verify safety & dispatch action vector | Step execution payload | Zero unhandled errors |

---

## Invariants & Guardrails

- [ ] **Heuristic Fallback Invariant**: Maintain deterministic rule engine fallback for all personas if live LLM endpoints fail.
- [ ] **Weighted Priority Invariant**: Weight persona votes according to domain urgency (e.g. Defense 1.2x, Epidemiology 1.1x).
- [ ] **Structured Proposal Invariant**: Require explicit confidence scores and reasoning chains on every proposal.
- [ ] **Formal Voting Invariant**: Execute mathematical voting algorithms (Borda count / Majority) rather than subjective choice.
