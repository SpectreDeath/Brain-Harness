# The Five Canonical Failure Modes & Verified Architectural Antidotes

Distilled from Chapter 1.6 and Chapter 15 of *The AI Agent Engineer's Guide* by Vahe Aslanyan (LUNARTECH).

---

## 1. Looped Reasoning

- **Symptom:** The agent thinks-acts-thinks-acts forever without making forward progress.
- **Root Cause:** Policy proposes actions that do not alter the environment's state in a way the policy can perceive.
- **Verified Antidote:**
  - **Pattern 17 (ReAct Loop):** Enforce strict step budget ceiling ($N_{max} \le 20$).
  - **Pattern 20 (Adaptive Replanner):** Compute state delta $\Delta S$ at each step. If $\Delta S = 0$ for 3 consecutive steps, abort or rebuild plan.
- **False Antidote:** Telling the model in the prompt to "not loop" (zero measurable effect).

---

## 2. Tool Spoofing (Prompt Injection / Exploitation)

- **Symptom:** Agent is manipulated into executing unauthorized tools or targeting wrong resources.
- **Root Cause:** Model treats external retrieved data as executable instructions.
- **Verified Antidote:**
  - **Pattern 53 (Constitution-Bound):** Pre-execution code interceptor validating tool arguments against invariant boundaries.
  - **Pattern 37 (Side-Effect Auditor):** Append-only audit log with transactional rollback.
  - **Structural Data/Instruction Separation:** Wrap untrusted inputs in XML delimiters (`<user_doc>`).
- **False Antidote:** Regex sanitization of inputs (easily bypassed).

---

## 3. Context Exhaustion

- **Symptom:** Agent forgets its original goal midway through a long trajectory.
- **Root Cause:** Context window treated as infinite memory; instructions scroll out of effective attention range.
- **Verified Antidote:**
  - **Pattern 25 (Working-Memory Manager):** Per-step prompt reconstruction with middle-out tool observation pruning.
  - **Pattern 16 (Hierarchical Decomposer):** Recursively execute bounded subgoals.
- **False Antidote:** Upgrading to a larger context window model (postpones failure, doesn't fix).

---

## 4. Goal Drift

- **Symptom:** Agent gradually pivots from the original goal to an adjacent, trivial task.
- **Root Cause:** Policy interprets intermediate tool results as the goal state.
- **Verified Antidote:**
  - **Pattern 19 (Plan-Then-Execute):** Upfront inspectable plan serving as an immutable anchor.
  - **Pattern 59 (Drift Detector):** Periodic invariant checks comparing current trajectory against root goal.
- **False Antidote:** Lowering model temperature (reduces noise, not drift).

---

## 5. Silent Success on the Wrong Task

- **Symptom:** Agent confidently claims success on a task adjacent to what was requested.
- **Root Cause:** Model "rounds" user intent to a familiar, easy problem it can easily solve.
- **Verified Antidote:**
  - **Pattern 8 (Chain-of-Thought Auditor):** Verifies each premise and transition in a reasoning trace.
  - **Pattern 47 (Reflection):** Dual-check reflection comparing final deliverable directly against initial intake request.
- **False Antidote:** Prompting "make sure you understand the question" (ignored).
