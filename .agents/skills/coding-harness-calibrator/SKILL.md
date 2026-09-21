---
name: coding-harness-calibrator
description: Empirically calibrate and optimize autonomous coding agent harnesses across context management (T0-T4 staging), action spaces (tools vs bash), and planning scaffolds. Do not use for generic prompt writing, superficial linting, or ungrounded chat loops.
---

# Coding Harness Calibrator: Empirical Component-Level Optimization

`coding-harness-calibrator` is the empirical engineering engine for tuning, sizing, and configuring autonomous coding agent harnesses. Grounded in the foundational research of Fan et al. (*An Empirical Study of Harness Design for Coding Agents*, arXiv:2609.20804v1, September 2026), this skill replaces monolithic guesswork with validated empirical laws derived from 176 systematically matched experimental settings across SWE-Bench Verified and Terminal-Bench 2.1.

Rather than treating the agent harness as an indivisible black box, `coding-harness-calibrator` isolates and tunes the three load-bearing architectural levers: **Planning Scaffolds**, **Action Space Interfaces**, and **Staged Context Management**, backed by deterministic in-flight substrate safeguards.

Every harness calibration workflow executes this 5-stage progression:

```
[1. Capability & Workload Triage] → [2. Action Space Boundary Calibration] → [3. Two-Tier Context Staging Engine] → [4. In-Flight Substrate Safeguards] → [5. Trajectory Stopping & Convergence]
```

See [CARD.md](CARD.md) for the companion summary card, stage reference matrix, and verification checklist.
Consult [../agent-harness-architect/SKILL.md](../agent-harness-architect/SKILL.md) for macro runtime shell selection, [../harness-compass/SKILL.md](../harness-compass/SKILL.md) for automatic harness evolution, and [../crafting-skills/SKILL.md](../crafting-skills/SKILL.md) for skill authoring standards.

---

## 1. Capability & Workload Triage

Diagnose the model tier and workload characteristics to determine the optimal component configuration:

1. **Model Capability Tiering**:
   - **Weaker / Small Models (e.g. 30B parameters)**: Require **Scaffold Mode**. Must enable persistent planning (`update_plan`) to sustain execution trajectories beyond 10 turns and expose predefined typed tools to prevent out-of-interface syntax collapse.
   - **Intermediate Models (e.g. 120B parameters)**: Require **Balanced Mode**. Planning provides slight structural guidance; predefined tools yield moderate efficiency gains over bash.
   - **Strong / Frontier Models (e.g. 550B+, Claude 3.5/3.7, GPT-4o/5)**: Require **Efficiency Mode**. Planning acts primarily as a **stopping-point controller** to truncate redundant post-edit verification loops (saving 25%–48% cost).
2. **Workload Triage**:
   - **Terminal-Centric Workloads** (e.g. Terminal-Bench tasks, environment provisioning, multi-step CLI operations): Strongly favor a **bash-only** action interface for capable models, allowing composite command chaining.
   - **Repository Codebase Workloads** (e.g. SWE-Bench bug fixing across large multi-file projects): Require structured file tools (`read_file`, `edit_file`) to bound edit blast radiuses and eliminate file localization failures.

> **Completion criterion**: Model capability tier (Scaffold vs Efficiency) and workload profile (Terminal-Centric vs Codebase) mapped to target configuration flags.

---

## 2. Action Space Boundary Calibration

Configure the agent's interaction interface to minimize re-patch churn and action-selection overhead:

1. **Predefined Typed Tool Interface**:
   - Expose typed schemas: `read_file(path, offset, limit)`, `write_file(path, content, overwrite)`, `edit_file(path, old_text, new_text, replace_all)`, `list_files`, `glob_files`, `grep_text`.
   - Mandatory for weak models lacking robust shell bash composition (boosts SWE-Bench success by +15.0%).
   - Enforce read-before-write checks and cryptographic SHA-256 state tracking.
2. **Bash-Only Action Interface**:
   - Strip predefined file, search, and web tools from the tool registry, leaving only `bash` alongside auxiliary planning tools.
   - Deploy for bash-fluent models on command-line tasks: cuts mean re-patches per task from 4.6 down to 1.5, shifts file-writing toward coarse create-or-replace actions (from 51% to 76%), and slashes execution costs by 30%–53%.
3. **Action Granularity Invariant**:
   - Ensure the interface prevents micro-patch thrashing: if an agent re-patches the same file more than 3 times, inject guidance to bundle modifications into composite scripts or whole-function replacements.

> **Completion criterion**: Tool schemas registered in accordance with model capability, and re-patch throttling active.

---

## 3. Two-Tier Context Staging Engine

Implement the empirical Two-Threshold Context Staging Pipeline ($T_4$ Architecture) to eliminate catastrophic context overflow:

1. **Preamble & Recent Window Isolation**:
   - System prompt, environment instructions, and initial task description are strictly pinned.
   - Verbatim recent window must be budgeted at 0.30 of the usable window and floored at a minimum of **two complete turns**.
2. **Soft Threshold $B_1$ (0.60 Usable Context) — Rule-Based Elision ($M_1$)**:
   - Once total tokens exceed $B_1$, immediately elide bulky tool observation bodies in the middle region.
   - Replace observation bodies with deterministic stubs:
     `[tool output elided: {N_LINES} lines / {N_CHARS} chars. Re-read or re-run to get it again.]`
   - Executes in sub-millisecond time with zero LLM API cost.
3. **Hard Threshold $B_2$ (0.85 Usable Context) — Structured Summarization ($M_3$)**:
   - If history still exceeds $B_2$ after elision, invoke a dedicated, tool-free call to the model to fold the oldest middle events into a structured running summary under 7 mandatory headings:
     `## Goal`, `## Files touched`, `## Done`, `## Pending`, `## Errors & fixes`, `## Current state`, `## Next step`.
   - Insert the summary block directly following the preamble.
4. **Deprecate Dead Machinery ($M_2$ Recall)**:
   - Do NOT implement complex external storage indices for reversible `recall_event(id)`. Empirical ablations prove models invoke recall in $<0.1\%$ of turns with zero accuracy gain ($p > 0.05$).

> **Completion criterion**: Two-threshold triggers ($B_1=0.60, B_2=0.85$) configured, 7-heading summary schema active, and dead recall machinery pruned.

---

## 4. In-Flight Substrate Safeguards

Deploy three deterministic substrate safeguards to protect the sandbox and prevent loop spinning:

1. **Workspace Safety Gate**:
   - Resolve every path against project root; reject any symlink or relative path escaping the workspace.
   - Classify commands into allow (read-only queries: `git status`, `git diff`, `ls`, `grep`), ask (destructive operations: `rm -rf`, `sudo`, `git reset --hard`), or deny.
2. **Post-Edit In-Flight Diagnostics**:
   - Immediately following any `edit_file`, `write_file`, or shell file modification, run fast read-only syntax checking (`ruff check`, `pyflakes`, or AST parse).
   - Append detected syntax errors, bracket mismatches, or undefined symbols directly into the tool observation for instant self-repair.
3. **Streak-Based Stuck Detection**:
   - Maintain a sliding log of consecutive tool calls with identical tool names and byte-identical arguments.
   - **Streak 5 (Warning)**: Inject a one-time `<system-reminder>` notifying the agent that repeating identical calls yields no progress and mandating strategy re-evaluation.
   - **Streak 8 (Hard Termination)**: If an identical failing call repeats 8 times, terminate execution immediately with a dedicated stuck stop reason to protect the token budget.

> **Completion criterion**: Path bounds enforced, in-flight AST diagnostics attached to edits, and streak thresholds (5 warn / 8 kill) verified.

---

## 5. Trajectory Stopping & Post-Edit Convergence

Calibrate planning scaffolds to govern trajectory termination and suppress redundant verification:

1. **Persistent Task Plan Protocol**:
   - Require the agent to initialize an explicit task plan via `update_plan` on turn 1 for non-trivial tasks.
   - Reinject the active plan before every turn without appending duplicate plan copies to the persistent context history.
   - Maintain the invariant: exactly ONE task `in_progress` at any time; mark tasks `completed` immediately upon verification.
2. **Verification Loop Suppression**:
   - For capable models, the primary benefit of planning is stopping-point discipline: once the final plan milestone is marked completed and tests pass, enforce trajectory termination.
   - Prevent open-ended exploratory verification spinning, which accounts for 40%–50% of wasted turns in uncalibrated harnesses.

> **Completion criterion**: Plan reinjection active per turn, and termination logic triggered upon final plan milestone completion.

---

## Diagnostic Coaching Rubrics

Evaluate whether a target coding harness satisfies empirical calibration standards using this 5-dimensional rubric:

| Dimension | Evaluation Criteria | Passing Threshold |
|---|---|---|
| **1. Overflow Resilience** | Harness sustains $\ge 50$ turns under a tight 32k window budget without memory overflow crashes. | Pass: Zero unhandled context overflow terminations. |
| **2. Staging Efficiency** | Rule-based elision ($M_1$) executes at $B_1=0.60$; structured LLM summarization ($M_3$) is deferred until $B_2=0.85$. | Pass: Elision precedes summarization; zero unmanaged middle tokens. |
| **3. Dead Machinery Pruning** | No unused recoverable event caches or uninvoked retrieval tools cluttering schemas. | Pass: Zero dead `recall_event` machinery in active schemas. |
| **4. Action Granularity** | Mean re-patches per task bounded $\le 2.0$ for capable models; coarse scripting enabled on CLI tasks. | Pass: Re-patch rate $\le 2.0$; interface matches model capability. |
| **5. Trajectory Stopping** | Stuck detector terminates identical failing streaks at turn 8; planning suppresses verification tails. | Pass: Zero runaway loops beyond 8 identical calls; verified stopping. |

---

## Visual Brief Synthesis

Before deploying or migrating an autonomous coding agent harness, synthesize the proposed configuration into an interactive HTML Visual Brief:
- **Location**: Write to `%TEMP%\book-to-skill-forge-<timestamp>.html` (or artifact directory).
- **Visualization**: Include a Mermaid DAG mapping the 5-stage closed-loop progression, component surfaces, and track routing.
- **Scorecards**: Render the 5-dimension Diagnostic Evaluation Scorecard Table detailing Passing Gate thresholds.
- **Ablation Comparison**: Present empirical trade-offs comparing unmanaged context, staged elision, and tool vs bash interfaces.

---

## Mandatory Checkpoint Gates

Prevent uncalibrated or regressive harnesses from contaminating production agent runners:
1. **The Pre-Commit Checkpoint**: Present an `implementation_plan.md` artifact detailing candidate component settings, predicted re-patch rates, and budget allocations.
2. **Feedback Gate**: Set `RequestFeedback: true` in artifact metadata whenever harness calibration parameters undergo structural modification.
3. **Acceptance Threshold**: The calibrated harness configuration is accepted if and only if context overflow is eliminated under test budgets and mean re-patches per task $\le 2.0$.

---

## Anti-Patterns

- **Monolithic Harness Conflation** — Evaluating coding agents solely as end-to-end black boxes, blinding engineers to which component drives success.
- **Dead Machinery Bloat** — Implementing complex external storage engines for recoverable elision (`recall_event`) that agents virtually never call.
- **Unstaged LLM Summarization** — Triggering expensive LLM summarization on all stale context without prior rule-based elision, burning token budgets and introducing summarization drift.
- **Uniform Planning Dogma** — Assuming planning always aids reasoning uniformly, failing to realize it functions as a cost-cutter for strong models and an edit scaffold for weak models.
- **Fixed Action Space Dogma** — Forcing structured tools onto bash-proficient models on CLI tasks (multiplying micro-edits) or forcing bash on weak models (causing interface collapse).
- **Unchecked Tool Spinning** — Allowing turn-based agents to execute repeated identical failing commands until exhausting step budgets without automated streak termination.
