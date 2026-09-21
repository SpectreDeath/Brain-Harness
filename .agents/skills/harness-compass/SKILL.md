---
name: harness-compass
description: Evolve, calibrate, and benchmark autonomous AI agent harnesses using constrained evolution, 4-stage proactive feedback, dual-track optimization, and R3 integration. Do not use for generic prompt writing, single-turn prompts, or unconstrained benchmark overfitting.
---

# HarnessCompass: Automatic Harness Evolution Engine

`harness-compass` is the production skill for autonomously discovering, calibrating, and optimizing agent harnesses (prompts, tools, middleware, memory, skills, and sub-agents) while strictly preventing benchmark overfitting and context bloat.

Synthesized from foundational research by Zhang et al. (*HarnessCompass: Guiding Automatic Harness Evolution toward Generalizable and Effective Agent Harnesses*, arXiv:2608.01918v1, 2026), this skill inverts the conventional trial-and-error approach to agent scaffolding into a mathematically bounded, closed-loop engineering optimization cycle.

Rather than allowing meta-agents to accumulate memorized, task-specific fixes or stack redundant advisory rules, `harness-compass` enforces three core principles:
1. **Constrained Evolution**: A Global Generalization Gate filtering every candidate edit across all 7 orthogonal surfaces against strict Content and Placement invariants.
2. **Proactive First-Person Feedback**: Eliciting Blind pre-verdict reflections and post-verdict failure attributions directly from the coding agent to capture genuine usability friction grounded in execution traces.
3. **Component-Wise Optimization & R3 Integration**: Parallelizing exploration into disjoint Structural and Guidance tracks and consolidating them via Revision, Recombination, and Occam's Razor Refinement.

See [CARD.md](CARD.md) for the companion summary card, quick-reference tables, and verification checklist.
See `config.default.yaml` for baseline operational budgets.
Consult [../agent-harness-architect/SKILL.md](../agent-harness-architect/SKILL.md) for harness architecture partitioning and [../adversarial-agent-verifier/SKILL.md](../adversarial-agent-verifier/SKILL.md) for adversarial runtime gates.

---

## 1. Seed Initialization & Bounded Protocol

Establish a minimal, unpolluted baseline harness $H_0$ and define the evaluation sample before initiating iterative optimization:

1. **Initialize Seed Harness $H_0$**:
   - Limit tools to a single isolated shell command execution wrapper.
   - Enforce a minimal system prompt defining task instructions with zero pre-loaded domain tricks.
   - Declare zero initial middleware, zero domain skills, and zero sub-agents.
   - *Rationale*: Minimal seeds ensure that every capability in later harnesses is attributable to verified loop progress rather than inherited unmeasured boilerplate.
2. **Partition Benchmark Splits**:
   - Select a representative sample $D$ of tasks (e.g. 50 tasks from SWE-Bench Verified).
   - Reserve the remaining tasks (e.g. 450 tasks) as a strictly held-out evaluation set never exposed to the meta-agent.
3. **Configure Rollout Budgets**:
   - Set rollout multiplier $k \ge 2$ per task to compute robust binary Pass@1 success rates.
   - Bound total evolution iterations to $N \le 5$ turns to prevent search-space drift.

> **Completion criterion**: Minimal seed $H_0$ verified operational, evaluation split isolated from held-out set, and baseline Pass@1 recorded.

---

## 2. Global Generalization Gate Enforcement

Every candidate modification to any of the 7 harness component surfaces must pass the two-part Generalization Gate before application:

```
┌─────────────────────────────────────────────────────────────┐
│                 GLOBAL GENERALIZATION GATE                  │
├──────────────────────────────┬──────────────────────────────┤
│ Content Requirement          │ Placement Requirement        │
│ - Zero task/instance IDs     │ - Capability: Middleware,    │
│ - Zero test function names   │   tools, sub-agents (code)   │
│ - Zero private codebase symb │ - Guidance: System prompt,   │
│ - Zero keyword branching     │   memory, skills (advice)    │
│ - Reusable criteria only     │ - No advisory code leaks     │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Content Invariant (What an Edit May Express)**:
   - **Hard Ban**: Reject any edit mentioning specific benchmark instance IDs (e.g. `sympy-1234`), concrete test files (`tests/test_*.py`), private symbols of a task-under-test repository, or keyword branching (`if "token" in text:`).
   - **Mandatory Form**: Every rule must be formulated as a *cross-task reusable principle* paired with an *applicability criterion* that the agent can evaluate on an unseen codebase.
   - **Litmus Test**: *"Would this change still help a task from a library the agent has never seen?"* If not, discard it.
2. **Placement Invariant (Where an Edit Must Reside)**:
   - **Capability Edits**: Performing concrete actions triggered by execution events (running narrow tests, parsing exit codes, installing missing packages, verifying patch syntax) MUST reside in executable code (`middleware`, `tool_impl`, `sub_agent`).
   - **Guidance Edits**: Behavioral advice, heuristic judgment rules, and prioritization guidelines MUST reside in guidance text (`systemprompt`, `memory`, `skills`).
   - **Advisory Leak Ban**: Structural code surfaces must NEVER merely inject conversational suggestions into the model context.
3. **Memory Deduplication & Conflict Merging**:
   - Before committing lessons to memory, scan existing entries.
   - If a new observation contradicts an existing rule, merge them into a single deciding criterion stating *when* each applies based on consumer dependency scope.

> **Completion criterion**: 100% of candidate edits pass automated regex and structural placement checks; zero task-specific tokens present.

---

## 3. Proactive First-Person Feedback Pipeline

Supplement external execution traces with first-person usability reflections from the coding agent across 4 sequential stages:

1. **Stage 1: Blind Pre-Verdict Report**:
   - Provide the raw trajectory $\tau$ to the agent with the verifier verdict $r(\tau)$ strictly withheld.
   - Elicit usability friction with existing features (`kind: improve_existing`) and capabilities the agent wished existed (`kind: new_capability`).
   - *Defense*: Withholding the outcome eliminates hindsight rationalization bias.
2. **Stage 2: Hindsight Post-Verdict Attribution**:
   - Reveal the verifier verdict and prompt the agent to attribute the outcome to one of four mutually exclusive causes:
     - `harness`: Missing tools, misleading error messages, or restrictive execution environment. (Retained).
     - `agent_reasoning`: Flawed logic, syntax hallucination, or wrong hypothesis. (Discarded from harness evolution).
     - `task_ambiguity`: Contradictory requirements or incomplete problem description. (Discarded).
     - `environment`: Sandbox timeout, system crashes, or network failures. (Discarded).
3. **Stage 3: Pre/Post Reconciliation**:
   - Merge the blind and hindsight reports into an agreed candidate set, computing self-consistency (`pre_post_agree`, `partial`, `conflict`).
4. **Stage 4: Trajectory Grounding Gate**:
   - Analyzer verifies each claim against the raw trace:
     - `improve_existing` must reference specific turns with observable tool errors or friction.
     - `new_capability` must demonstrate a concrete gap that the proposed capability would have solved.
   - Route surviving grounded items to coarse tracks (`structural` vs `guidance`) and compute recurrence confidence scores.

> **Completion criterion**: Non-harness failures discarded, surviving feedback grounded with specific turn citations, and confidence scores assigned.

---

## 4. Component-Wise Dual-Track Optimization

Prevent cross-component interference by isolating structural mechanics from behavioral guidance during exploratory evolution:

1. **Parallel Track Partitioning**:
   - In each round, fork two independent harness variants from current best $H^*$:
     - **Track A (Structural Variant)**: Constrained strictly to `middleware`, `tool_impl`, and `sub_agent` code files.
     - **Track B (Guidance Variant)**: Constrained strictly to `systemprompt`, `skills`, `tool_desc`, and `memory` markdown/YAML files.
2. **Disjoint Surface Invariant**:
   - Ensure Track A cannot modify guidance files and Track B cannot modify executable code files.
3. **Independent Evaluation**:
   - Roll out both variants across the sample dataset $D$.
   - Compute Pass@1 for Track A ($T_{struct}$) and Track B ($T_{guidance}$).
   - Designate the higher-scoring variant as Winner ($H_w$) and the alternative as Loser ($H_\ell$).

> **Completion criterion**: Structural and guidance variants evaluated independently on disjoint surfaces; winner and loser determined.

---

## 5. R3 Integration & Occam's Razor Refinement

Consolidate complementary improvements from the losing track into the winning harness without inheriting regressions or bloat:

1. **Phase 1: Revision (Loser Triage)**:
   - Inspect every change in $H_\ell$ individually.
   - **KEEP**: Independent positive contributions that do not conflict with $H_w$ changes.
   - **DROP**: Regression sources, ungrounded modifications, or task-specific heuristics. When uncertain, DROP.
2. **Phase 2: Recombination (Additive Fusion)**:
   - Apply kept loser changes onto the $H_w$ base harness.
   - In any file-level collision, $H_w$ changes take absolute precedence.
3. **Phase 3: Refinement (Occam's Razor Redundancy Hunt)**:
   - Actively audit every advisory item (system prompt rules, memory entries, tool notes) against executable code mechanisms in the combined harness.
   - **The Duplication Purge**: If an advisory rule's behavior is already deterministically enforced by middleware or tools, **DELETE the advisory text**.
   - Preserves prompt token budgets and eliminates advisory degradation across rounds.
4. **Acceptance Gate**:
   - If $\text{Pass@1}(H_w) > \text{Pass@1}(H^*)$, accept consolidated $H_t$ as the new champion $H^*$. Otherwise, revert and retain previous $H^*$.

> **Completion criterion**: R3 integration manifest generated, redundant advisory prompt text purged, and updated champion harness committed.

---

## Diagnostic Coaching Rubrics

When evaluating an evolved harness or auditing an agent system, answer these five diagnostic questions:

```
┌─────────────────────────────────────────────────────────────┐
│             HARNESS DIAGNOSTIC AUDIT SCORECARD              │
├──────────────────────────────┬──────────────────────────────┤
│ 1. Content Generality Gate   │ 2. Placement Boundary Invar. │
│ [ ] Zero task/repo tokens    │ [ ] Code executes actions    │
│ [ ] Zero test function names │ [ ] Advice in prompt/memory  │
├──────────────────────────────┼──────────────────────────────┤
│ 3. Failure Attribution Purity│ 4. Trajectory Grounding Rigor│
│ [ ] Reasoning errors dropped │ [ ] Trace citations verified │
│ [ ] Env crashes filtered     │ [ ] Plausible gap for new tool│
├──────────────────────────────┼──────────────────────────────┤
│ 5. Occam's Redundancy Purge  │ Gate Threshold: 100% Pass on │
│ [ ] Advisory duplicates dead │ all 5 diagnostic dimensions  │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Content Generality**: Does any prompt line, memory entry, or tool check mention a specific repository name, task ID, test filename, or private symbol? *(If yes, fail).*
2. **Placement Boundary**: Does any middleware or tool component merely inject conversational advice into the context? *(If yes, fail; move to prompt or make code deterministic).*
3. **Failure Attribution**: Are feedback items filtered so that model hallucinations and sandbox crashes do not pollute the harness evolution evidence? *(If no, fail).*
4. **Trajectory Grounding**: Is every claimed tool friction grounded in raw trace turns with observable error codes or blocked progress? *(If no, fail).*
5. **Occam's Razor**: Does the harness contain prompt instructions telling the agent to do something that middleware already enforces automatically? *(If yes, fail; purge the prompt text).*

---

## Visual Brief Synthesis

Before committing an evolved harness to production, synthesize the round's progress into an interactive HTML Visual Brief:
- **Location**: Write to `%TEMP%\harness-compass-<timestamp>.html` (or artifact directory).
- **Visualization**: Include a Mermaid DAG mapping the 5-stage closed-loop progression, component surfaces, and track routing.
- **Scorecards**: Render the 6-dimension Diagnostic Evaluation Scorecard Table detailing Passing Gate thresholds.
- **Occam's Diff**: Highlight advisory prompt rules purged due to deterministic middleware enforcement.

---

## Mandatory Checkpoint Gates

Prevent uncurated or regressive harnesses from contaminating production agent runners:
1. **The Pre-Commit Checkpoint**: Present an `implementation_plan.md` artifact detailing candidate changes, predicted fixes, and risk tasks.
2. **Feedback Gate**: Set `RequestFeedback: true` in artifact metadata whenever an evolved harness requires human verification.
3. **Acceptance Threshold**: The champion harness is updated if and only if $\text{Pass@1}(H_w) > \text{Pass@1}(H^*)$; otherwise the transaction is disposed and rolled back.

---

## Anti-Patterns

- **Overfitted Answer Injection** — Hardcoding task-specific branches or memorized solutions instead of transferable decision criteria.
- **Advisory Middleware Leaks** — Implementing middleware or tools that merely inject conversational advice into the prompt based on coarse activity signals.
- **Hindsight Rationalization Bias** — Eliciting agent feedback only after showing the outcome, prompting the agent to invent retrospective justifications.
- **Joint Monolithic Evolution** — Modifying prompts, tools, middleware, and memory simultaneously in a single pass, triggering destructive interference.
- **Advisory Prompt Bloat** — Accumulating endless prompt rules and memory entries across iterations while implementing code tools that do the same job.
- **Spurious Feedback Hallucination** — Blindly accepting agent complaints without verifying against raw execution traces.
