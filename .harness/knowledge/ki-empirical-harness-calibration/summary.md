# Knowledge Item: Empirical Harness Calibration for Coding Agents

## Epistemic Distillation & Core Insights

### 1. The Monolithic Harness Fallacy
Prior agent benchmarks evaluated coding harnesses as monolithic end-to-end black boxes (e.g. OpenHands vs SWE-agent). Because multiple mechanisms were varied simultaneously, practitioners could not determine whether performance shifts stemmed from planning prompts, tool selection, context compaction policies, or sandbox infrastructure.

**Fan et al. (arXiv:2609.20804v1, September 2026)** isolate individual harness components while holding the core ReAct execution loop fixed across 176 systematically matched experimental settings. Evaluating 4 model scales (**Nemotron-3 30B/120B/550B** and **Mistral-Medium-3.5 128B**) on **SWE-Bench Verified** (500 real GitHub issues) and **Terminal-Bench 2.1** (89 end-to-end terminal tasks) establishes the first component-level empirical laws governing autonomous coding harnesses.

---

### 2. Context Management: The Staged Two-Threshold Law (T4 Architecture)

#### The Catastrophic Overflow Dynamic
Context management value scales inversely with window budget:
- At a **32k context-window budget** without management (**Tier 0**), agents catastrophically collapse: task success rate plummets to **6.4%–12.6%**, median trajectories terminate in **20–30 turns**, and agents die during file localization before ever reaching the verification phase.
- Enabling rule-based elision (**Tier 1**) rescues success rates to **20.6%–64.4%** across models by sustaining trajectories to **50–180 turns**, allowing agents to reach the edit and verification phases.
- At **128k context windows**, differences across management tiers diminish (median runs reach 40–74 turns regardless of tier), demonstrating that context management primarily serves as a **survival mechanism** preventing overflow crashes rather than fundamentally altering problem-solving strategy.

#### The Two-Threshold Staged Compression Pipeline
The optimal context management architecture combines rule-based elision ($M_1$) and structured LLM summarization ($M_3$) under two token thresholds:
1. **Preamble & Recent Window**: System prompt, initial task prompt, and a recent window of at least two turns (budgeted at 0.30 of the usable window) remain strictly **verbatim**.
2. **Soft Threshold $B_1$ (0.60 Usable Context)**: Stale bulky tool outputs in the middle region are replaced with compact deterministic stubs:
   `[tool output elided: {N_LINES} lines / {N_CHARS} chars. Re-read or re-run to get it again.]`
   Rule-based elision costs 0 LLM tokens, executes in sub-millisecond time, and immediately reclaims massive context headroom.
3. **Hard Threshold $B_2$ (0.85 Usable Context)**: If context continues expanding past $B_2$, the oldest middle-region events are folded into a structured natural-language summary by invoking the model without tools under 7 mandatory headings:
   - `## Goal`: User intent preserved verbatim.
   - `## Files touched`: Paths examined/modified with rationale.
   - `## Done`: Concrete milestones accomplished (tests passing, bug localized).
   - `## Pending`: Outstanding tasks.
   - `## Errors & fixes`: Failures encountered and remediations.
   - `## Current state`: Variables, branch, active test state.
   - `## Next step`: Immediate sequential operation.

#### The Recoverable Elision Myth ($M_2$ Recall Deprecation)
A critical negative finding: making elided tool outputs recoverable via external file storage and exposing a `recall_event(id)` tool (**Tier 2 & Tier 4**) adds significant operational machinery that models **almost never invoke** (<0.1% of trajectory turns) and yields **zero statistically significant accuracy gain** ($p > 0.05$ across all models). irreversible rule-based elision ($M_1$) captures all the empirical gains without the storage or schema complexity of retrieval caches.

---

### 3. Planning Duality: Accuracy Scaffold vs. Cost Optimizer

Planning interventions (injected `update_plan` tool, first-turn plan requirement, and per-turn plan reinjection) operate through two completely different behavioral mechanisms depending on model capability:

| Model Scale | SWE-Bench SR (Off &rarr; On) | Cost Impact | Trajectory Length (Off &rarr; On) | Behavioral Mechanism |
|---|---|---|---|---|
| **Weak Model**<br>*(Nemotron-3 30B)* | **14.0% &rarr; 25.0%**<br>(+11.0% SR) | +$0.07 / task<br>(+$0.02 &rarr; $0.09) | **5 turns &rarr; 40 turns**<br>(+293% turns) | **Accuracy Scaffold**: Prevents premature collapse; drops runs terminating without edit from 68.6% to 27.8%. |
| **Intermediate**<br>*(Nemotron-3 120B)* | **47.0% &rarr; 44.0%**<br>(&sim;neutral) | +$0.09 / task<br>($0.25 &rarr; $0.34) | **27 turns &rarr; 33 turns**<br>(+20% turns) | Neutral accuracy; slight exploratory extension. |
| **Dense / Strong**<br>*(Nemotron-3 550B)* | **68.0% &rarr; 66.0%**<br>(&sim;neutral) | **-$0.98 / task**<br>($3.31 &rarr; $2.33, **-30%**) | **108 turns &rarr; 74 turns**<br>(**-31% turns**) | **Cost Saver / Stopping Controller**: Truncates redundant post-edit verification loops and stops execution when plan completes. |
| **Frontier Scale**<br>*(Mistral-3.5 128B)* | **69.0% &rarr; 69.0%**<br>(neutral) | **-$1.51 / task**<br>($4.65 &rarr; $3.14, **-32%**) | **68 turns &rarr; 53 turns**<br>(**-22% turns**) | **Cost Saver**: Suppresses exploratory tail and redundant tool verification. |

**Key Takeaway**: Planning does not make strong models "smarter" (accuracy is unchanged); it makes them **cheaper and faster** by establishing crisp termination criteria that prevent them from endlessly cycling in post-edit verification.

---

### 4. Action Space Boundary: Predefined Tools vs. Bash-Only

The action space interface governs the granularity and syntax overhead of agent operations:

#### Weak Models & Bash Illiteracy
For weaker models (30B), predefined structured tools (`read_file`, `write_file`, `edit_file`, `list_files`, `grep_text`) are **vital scaffolds**:
- Without predefined tools, 66% of bash-only trajectories terminate after out-of-interface call emissions (hallucinating missing tool schemas).
- Predefined tools raise SWE-Bench success by **+15.0%** (10% &rarr; 25%) and Terminal-Bench by **+10.1%** (3% &rarr; 13%).

#### Strong Models & Action Granularity Crossover
For strong, bash-fluent models (550B):
- **Bash-only outperforms predefined tools**: SWE-Bench success increases by **+3.6%** (66% &rarr; 69%) and Terminal-Bench success increases by **+5.6%** (45% &rarr; 51%), while cutting task cost by **53%** ($2.33 &rarr; $1.11) and **30%** ($2.43 &rarr; $1.70).
- **Action Granularity Shift**: Predefined tools force models into many fine-grained micro-interactions and repeated edits to the same file. Switching to bash-only drops repeated re-patches from **4.6 to 1.5** per task and raises coarse create-or-replace file operations from **51% to 76%**. Strong models bundle reading, parsing, editing, and testing into single composite shell scripts.

#### Workload Specificity Boundary
- **Terminal-Centric Workloads** (Terminal-Bench): Bash-only interface dominates because the tasks demand native CLI composition.
- **Repository-Scale Bug Fixing** (SWE-Bench): For models like Mistral-Medium, predefined tools remain essential on SWE-Bench (+24% SR advantage over bash-only) because line-numbered `read_file` and exact-string `edit_file` prevent file localization and patching syntax failures.

---

### 5. In-Flight Substrate Diagnostics & Stuck Detection

To prevent turn-based agent spin and wasted token budgets, harnesses must enforce three fixed substrate guards:
1. **Workspace Safety Gate & Read-Before-Write Hashing**: Resolves all relative paths against workspace root, rejects traversal escapes, and enforces read-before-write checks using cryptographic SHA-256 hashes to detect external file mutations.
2. **Post-Edit In-Flight Diagnostics**: File modifications immediately invoke fast AST linters (`ruff`, `pyflakes`, or Python syntax checks) and append diagnostic errors directly into the tool observation so the model can self-repair in-flight before executing test suites.
3. **Streak-Based Stuck Detection**:
   - Monitors streaks of consecutive calls with identical tool names and byte-identical arguments.
   - At **streak length 5**: Injects a one-time mandatory system reminder to stop repeating and re-evaluate strategy.
   - At **streak length 8 of identical failing calls**: Hard-terminates execution early to conserve token budget.
