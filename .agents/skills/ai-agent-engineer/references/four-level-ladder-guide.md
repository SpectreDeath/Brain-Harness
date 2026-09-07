# The Four-Level Ladder Architectural Guide

Distilled from Chapter 0 of *The AI Agent Engineer's Guide* by Vahe Aslanyan (LUNARTECH).

---

## The Core Philosophy: Lowest Viable Level

Agent framing is fashionable, but for a large fraction of engineering problems, it is the wrong architecture. Autonomous agents introduce nondeterminism, cascading failure states, and cost expansion.

**The Golden Rule:** *The right level for any problem is the lowest one that solves it.*

```
┌─────────────────────────────────────────────────────────────┐
│                   THE FOUR-LEVEL LADDER                     │
├─────────────────────────────────────────────────────────────┤
│ Level 1: Static Prompt        (Single call, static flow)    │
│ Level 2: Deterministic Flow   (Fixed sequence of calls/ops) │
│ Level 3: Bounded Agent        (Dynamic tool loops < 15 tools)│
│ Level 4: Full Agent           (Long-horizon open autonomy)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Level 1: The Static Prompt

- **Architecture:** One model call, one prompt template, zero tools, zero persistent memory.
- **When to Choose:**
  - Input fits comfortably in a single model context window.
  - Output structure is fully specified by prompt/schema.
  - No need for state-changing side effects.
  - A bad output is easily recoverable by re-prompting.
- **Canonical Examples:** Summarization, translation, format conversion, code explanation, classification.

---

## 2. Level 2: The Deterministic Workflow

- **Architecture:** Multiple model calls or model+tool steps, but the *sequence* is invariant: Step A $\rightarrow$ Step B $\rightarrow$ Step C.
- **When to Choose:**
  - Problem decomposes into a fixed sequence of steps.
  - Each step has strict input/output contracts.
  - The flow fits on a napkin flowchart.
  - Content varies, but control flow does not.
- **Canonical Examples:** Content generation pipelines (Research $\rightarrow$ Draft $\rightarrow$ Fact-check $\rightarrow$ Format), ETL data enrichment (Parse $\rightarrow$ Normalize $\rightarrow$ Enrich $\rightarrow$ Store).

---

## 3. Level 3: The Bounded Agent

- **Architecture:** Model decides which tool to call next, but within a small fixed toolset ($< 15$ tools) and a small step budget ($< 20$ steps).
- **When to Choose:**
  - Next step depends dynamically on what previous step returned.
  - Large number of possible execution paths, but small toolset.
  - Actions are reversible.
- **Canonical Examples:** Customer support ticket triage, SQL QA over known schemas, document inspection with standard operations.

---

## 4. Level 4: The Full Agent

- **Architecture:** Model holds an overarching goal across long horizons, manages working and episodic memory, recovers dynamically from environmental failures.
- **When to Choose:**
  - Dynamic discovery and autonomous error recovery are strictly necessary.
  - System operates in an open or partially observed environment.
- **Mandatory Requirement:** Level 4 agents strictly require Pattern 60 (Off-Switch-Compatible) and Pattern 53 (Constitution-Bound).

---

## The 5 Pre-Flight Scoping Questions Checklist

Before approving any Level 3 or Level 4 agent:
1. **Measurable Success:** Day-one numeric target (e.g. completion rate $\ge 85\%$).
2. **Worst-Case Blast Radius:** Concrete worst-case failure mode bounded by permissions/sandboxing.
3. **Cost Ceiling:** Hard per-session budget ceiling with automated circuit breaker.
4. **Session Eval Harness:** Labeled dataset and trajectory replay test suite.
5. **Off-Switch & Rollback:** Sub-second human interrupt signal and transactional rollback.
