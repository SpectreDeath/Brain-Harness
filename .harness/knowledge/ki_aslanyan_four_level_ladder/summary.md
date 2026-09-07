# The Four-Level Ladder & Pre-Flight Agent Scoping Heuristics

**ID:** `ki_aslanyan_four_level_ladder`  
**Category:** `agent_orchestration`  
**Origin:** *The AI Agent Engineer's Guide: 60 Patterns for Building Autonomous Systems* (Vahe Aslanyan, LUNARTECH)  
**Provenance Lineage:** Chapter 0: "Should This Be an Agent at All?", freeCodeCamp, 2026.

## Executive Summary
Agent framing is intellectually fashionable but frequently misapplied to problems best solved by simpler architectures. Autonomous agents introduce nondeterminism, cascading failure modes, and quadratic cost scaling. Before building an agent, system architects must map the problem onto the Four-Level Ladder and strictly select the lowest level that solves the problem.

### The Four-Level Ladder
1. **Level 1 (Static Prompt)**: Single model invocation, static template, zero tools, zero persistent memory. Input in, output out.
   - *Selection Heuristic*: Input fits in one context call, output structure is fully specified, errors recoverable by simple re-prompting. (e.g., summarization, translation, schema extraction from known formats).
2. **Level 2 (Deterministic Workflow)**: Fixed sequence of steps (Step A $\rightarrow$ Step B $\rightarrow$ Step C). The model produces content, but software control flow is invariant.
   - *Selection Heuristic*: Decomposes into a fixed flowchart that fits on a napkin. Sequence does not branch based on intermediate model decisions. (e.g., ETL pipelines, research $\rightarrow$ draft $\rightarrow$ cite).
3. **Level 3 (Bounded Agent)**: Dynamic next-step tool selection within a restricted toolset ($< 15$ tools) and small step budget ($< 20$ steps).
   - *Selection Heuristic*: Right next step depends dynamically on prior tool output; actions are easily reversible. (e.g., ticket triage, SQL query answering against known schemas).
4. **Level 4 (Full Agent)**: Holds overarching goals across long horizons, manages multi-step memory, recovers autonomously from environmental errors.
   - *Selection Heuristic*: Multi-turn task execution where dynamic error recovery and planning are strictly necessary.

## The 5 Pre-Flight Scoping Questions
Before building a Level 3 or Level 4 agent, engineering teams must answer all five questions with quantitative metrics:
1. **Measurable Success**: Define a day-one quantitative metric (completion rate, accepted output rate, time-to-resolution).
2. **Worst-Case Blast Radius**: Identify the catastrophic production failure and enforce physical sandbox/permission boundaries.
3. **Cost Ceiling per Session**: Establish hard token and monetary budget ceilings per session and verify business value exceeds cost.
4. **Session Evaluation Harness**: Specify the labeled multi-turn trajectory replay dataset before writing policy prompts.
5. **Off-Switch & Rollback**: Implement sub-second human override mechanisms with state preservation and transactional rollback.

## Architectural Invariants & Rules
1. **Lowest Viable Level Rule**: Always default to the lowest level on the ladder. Escalation to Level 3 or 4 requires proving Level 1 and 2 cannot satisfy requirements.
2. **Pre-Flight Scoping Gate**: Never approve agent implementation if any of the 5 pre-flight questions lacks a quantifiable metric.
