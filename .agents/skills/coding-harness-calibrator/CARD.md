# Skill Summary Card: `coding-harness-calibrator`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       coding-harness-calibrator                 │
│ Category:    agent_orchestration / harness-calibration │
│ Invocation:  /coding-harness-calibrator                │
│ Trigger:     "calibrate harness",                      │
│              "coding harness design",                  │
│              "context staging", "planning scaffold",   │
│              "action space calibration",               │
│              "stuck detection", "bash vs tools"        │
│ Version:     1.0.0                                     │
│ Provides:    "empirical_harness_calibration"           │
├────────────────────────────────────────────────────────┤
│ Target:      Empirically calibrate and optimize        │
│              coding agent harnesses across context     │
│              staging, action spaces, and planning.     │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Harness Calibration Cycle

| Stage | Objective | Primary Mechanism | Completion Gate |
|---|---|---|---|
| **1. Capability & Workload Triage** | Match model scale and workload type to harness mode | 30B/120B/550B triage & CLI vs Codebase classification | Mode selected (Scaffold vs Efficiency; CLI vs Codebase) |
| **2. Action Space Calibration** | Optimize tool granularity and minimize re-patches | Predefined typed tools vs Bash-only shell interface | Action interface locked; re-patch throttling active |
| **3. Two-Tier Context Staging** | Prevent context overflow while bounding token cost | Soft $B_1$ (0.60) elision & Hard $B_2$ (0.85) summarization | Preamble pinned; stubs inserted; dead $M_2$ recall pruned |
| **4. In-Flight Substrate Safeguards** | Protect workspace integrity and prevent spin loops | Read-before-write hash, AST linting, streak detector | Path bounds verified; streak 5 warn / streak 8 kill set |
| **5. Trajectory Stopping** | Enforce termination discipline and suppress loops | Planning-driven verification tail truncation | Execution stops on plan milestone completion |

---

## The Three Pillars Cheat Sheet

### 1. Two-Tier Context Staging Engine (Core Principle 1)
```python
# Staging Invariant: Soft elision (M1) before expensive LLM summarization (M3)
if tokens(history) >= soft_threshold_b1:  # 0.60 usable window
    for bulky_obs in middle_region:
        replace_with_stub(bulky_obs)  # M1: free, instantaneous

if tokens(history) >= hard_threshold_b2:  # 0.85 usable window
    running_summary = summarize_oldest_events(middle_region, schema=SEVEN_HEADINGS)
    # Deprecation Invariant: Discard M2 recall_event (<0.1% usage, 0% gain)
```

### 2. Action Space & Granularity Specialization (Core Principle 2)
```python
# Weak Models (30B): Predefined typed tools prevent syntax collapse (+15% SWE-Bench SR)
# Strong Models (550B+) on CLI Tasks: Bash-only cuts re-patches (4.6 -> 1.5) and cost (-53%)
if model.capability == "weak" or workload == "codebase_repo":
    active_tools = [read_file, write_file, edit_file, list_files, grep_text, bash]
elif model.capability == "strong" and workload == "terminal_cli":
    active_tools = [bash, update_plan]  # Bash-only composite scripting
```

### 3. Trajectory Stopping & Stuck Detection (Core Principle 3)
```python
# Streak-based stuck detector prevents runaway token expenditure
if consecutive_identical_calls >= 5:
    inject_system_reminder("Repeating identical calls yields no progress. Stop and re-plan.")
if consecutive_failing_calls >= 8:
    hard_terminate(reason="stuck_threshold_exceeded")

# Planning acts as a stopping controller for strong models:
if plan.all_milestones_completed and last_tests_passed:
    terminate_trajectory(success=True)  # Suppress redundant post-edit verification loops
```

---

## Verification & Quality Checklist

- [ ] **Context Staging**: Rule-based elision ($M_1$) triggers at $B_1=0.60$ before LLM summarization ($M_3$) at $B_2=0.85$.
- [ ] **Dead Machinery Pruned**: Schema contains zero uninvoked `recall_event` machinery.
- [ ] **Action Interface Match**: Weak models receive typed schemas; capable models on CLI tasks use bash composition.
- [ ] **In-Flight AST Diagnostics**: File write and edit tool observations include syntax check feedback.
- [ ] **Stuck Detection**: Consecutive identical tool calls trigger a warning at streak 5 and terminate at streak 8.
- [ ] **Stopping Discipline**: Planning suppresses redundant post-edit verification cycles for capable models.
- [ ] **Pre-Flight Validation**: Passes `harness skills validate` with zero errors.
