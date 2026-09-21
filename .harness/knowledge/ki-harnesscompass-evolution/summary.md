# Knowledge Item: HarnessCompass — Generalizable Automatic Harness Evolution

## Epistemic Distillation & Core Insights

### 1. The Harness Overfitting Trilemma
Recent advances in autonomous software engineering demonstrate that an agent's harness (the configuration of system prompts, tools, middleware, skills, memory, and sub-agents) dominates performance as much as or more than the underlying LLM weights. However, unconstrained **Automatic Harness Evolution (AHE)** suffers from three critical pathologies:
1. **Search Task Overfitting**: When the meta-agent optimizes for a training set of tasks, it memorizes task-specific bug fixes (e.g. hardcoded branching on dataset keywords, library-specific helper functions, or memorized patch fragments). Performance on the training set climbs while held-out generalization degrades sharply.
2. **External Trace Observability Gap**: Standard evolution loops observe only raw execution traces (messages, tool calls, exit codes). An external observer can see *that* an agent failed, but cannot determine *why* the agent struggled to use a tool or what missing harness capability would have prevented the failure.
3. **Cross-Component Interference**: Stacking prompt modifications, tool adjustments, middleware guards, and memory updates in a single joint iteration introduces destructive interference, where guidance contradicts tool mechanics and prompt bloat exhausts context windows.

**HarnessCompass** resolves this trilemma through three interlocking architectural principles: **Constrained Evolution**, **Proactive Feedback**, and **Component-Wise Optimization**.

---

### 2. Principle 1: Constrained Evolution & The Global Generalization Gate
Every candidate edit proposed by the meta-agent must pass a two-part **Global Generalization Gate** across all 7 orthogonal surfaces:

#### The Content Invariant
- **Hard Ban**: Rejects any edit mentioning a specific task instance ID (e.g. `sympy-1234`), a test function/file path (`test_*.py`), a private symbol or class of a task-under-test codebase, or keyword matching (`if "token" in text:`).
- **Mandatory Criterion**: Only admissions of **cross-task reusable principles** paired with an **applicability criterion** that the agent can evaluate on unseen tasks.
- **The Litmus Test**: *"Would this still help a task from a library I have never seen?"* If it cannot be formulated as an applicability condition, it is discarded.

#### The Placement Invariant (Capability vs. Advice)
- **Capability Edits** (deterministic code actions such as running narrow tests, parsing exit codes, installing missing packages, or verifying patch integrity) must reside in executable code: `middleware`, `tools`, or `sub_agents`.
- **Guidance Edits** (behavioral heuristics, prioritization rules, reasoning principles) must reside in behavioral guidance surfaces: `systemprompt` or `memory`.
- **The Advisory Leak Ban**: Structural surfaces must NEVER merely inject conversational advice into the prompt based on coarse triggers (e.g. shell command counters). If a change's only effect is advice, it is guidance and must be placed in the system prompt.

#### Memory Deduplication Invariant
- Before adding new memory entries, existing items must be scanned for contradictions.
- If a new lesson contradicts an existing entry (e.g. "fix at producer" vs "keep fix local"), they must not be stacked; they must be merged into a single criterion defining *when* each applies based on consumer counts and global invariant scope.

---

### 3. Principle 2: Proactive First-Person Feedback
To close the observability gap, the coding agent itself reflects on harness usability before and after knowing the outcome:
1. **Blind Report (Pre-Verdict)**: The agent reflects on the trajectory with the verifier verdict withheld ($r(\tau)$ hidden). It reports friction with existing features (`improve_existing`) and capabilities it wished existed (`new_capability`). This prevents hindsight rationalization bias.
2. **Hindsight Report (Post-Verdict)**: The verifier verdict is revealed. The agent attributes the failure to one of four mutually exclusive causes:
   - `harness`: The harness lacked tools, gave misleading feedback, or blocked execution. (Retained for evolution).
   - `agent_reasoning`: The agent hallucinated or reasoned incorrectly despite adequate tools. (Discarded from harness evolution).
   - `task_ambiguity`: The task specification was contradictory or missing details. (Discarded).
   - `environment`: The sandbox crashed or had network/system failures. (Discarded).
3. **Reconciliation**: The pre- and post-verdict reports are reconciled into an agreed item set, labeled `pre_post_agree`, `partial`, or `conflict`.
4. **Trajectory Grounding**: An external analyzer verifies claims against the raw trace:
   - `improve_existing` requires direct evidence of tool friction in the trace.
   - `new_capability` requires observable trace evidence of a gap that the proposed capability would address.
   - Surviving items are routed to coarse tracks (`structural` vs `guidance`) and assigned confidence scores based on multi-task recurrence.

---

### 4. Principle 3: Component-Wise Optimization & The R3 Integrator
To prevent cross-component interference, evolution is decoupled into two disjoint tracks:
- **Track A (Structural)**: `middleware`, `tool_impl`, `sub_agent`
- **Track B (Guidance)**: `systemprompt`, `skills`, `tool_desc`, `memory`

Both variants are evolved in parallel and evaluated on the task sample. The higher-scoring variant becomes the **Winner** ($H_w$), while the other becomes the **Loser** ($H_\ell$).

Rather than discarding the loser, the **R3 Integrator** executes a three-stage synthesis on top of the $H_w$ base:
1. **Revision**: Scans every change in the loser manifest. Keeps only independent positive contributions that do not conflict with or duplicate winner changes. Drops regressions, task-specific hacking, and uncertain edits.
2. **Recombination**: Applies the kept loser edits onto the $H_w$ base. In any file-level collision, $H_w$ takes precedence.
3. **Refinement (Occam's Razor)**: Actively hunts for advisory prompt rules or memory entries whose behavior is now deterministically enforced by middleware or tool code in the combined harness. **Deletes the advisory prompt rule** while retaining the deterministic code mechanism. This actively eliminates prompt bloat.

---

### 5. Empirical Results on SWE-Bench Verified (500 Tasks)
- **Sample Pass@1**: Climbs from 54.0% (seed $H_0$) to 66.0% in 5 iterations (vs AHE's 63.0% in 20 iterations).
- **Held-Out Generalization**: 60.4% on 450 unseen tasks (vs AHE's 54.7%, a +5.7% margin), proving that the Generalization Gate and R3 Refinement prevent overfitting.
- **Cross-Model Transfer**: An evolved harness frozen under GPT-5.4 transferred directly to Claude-Sonnet-4.6, delivering an immediate +4.2% Pass@1 gain over the baseline, confirming that the evolved harness encodes foundational software engineering capabilities rather than model-specific quirks.
