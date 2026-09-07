# The Five Canonical Agent Failure Modes & Architectural Antidotes

**ID:** `ki_aslanyan_canonical_failures_antidotes`  
**Category:** `agent_orchestration`  
**Origin:** *The AI Agent Engineer's Guide: 60 Patterns for Building Autonomous Systems* (Vahe Aslanyan, LUNARTECH)  
**Provenance Lineage:** Chapter 1.6 & Chapter 15, freeCodeCamp, 2026.

## Executive Summary
Across autonomous agent architectures, failures converge on five recurring canonical failure modes. Attempting to fix these failure modes through prompt adjustments (e.g. telling the model "do not loop" or "be safe") fails in production. Reliable mitigation requires structural, code-level architectural antidotes.

### The 5 Canonical Failure Modes
1. **Looped Reasoning**:
   - *Symptom*: Agent thinks-acts-thinks-acts indefinitely without making forward progress.
   - *Root Cause*: Proposed actions do not alter the environmental state in a way the policy can perceive.
   - *Verified Antidote*: Bounded ReAct Loop (Pattern 17) with hard step budget; Adaptive Replanner (Pattern 20) with explicit progress delta metrics.
   - *False Antidote*: Prompting the model "do not loop" (zero effect).
2. **Tool Spoofing (Prompt Injection / Exploitation)**:
   - *Symptom*: Agent is manipulated into executing dangerous tools or targeting incorrect resources.
   - *Root Cause*: Model treats external untrusted data as executable instructions.
   - *Verified Antidote*: Constitution-Bound Agent (Pattern 53) intercepting tool arguments; Side-Effect Auditor (Pattern 37) with rollback; structural data/instruction separation.
   - *False Antidote*: Regex sanitization of inputs (easily bypassed).
3. **Context Exhaustion (Attention Degradation)**:
   - *Symptom*: Agent forgets its original goal midway through a long trajectory.
   - *Root Cause*: Context window treated as infinite memory; load-bearing instructions scroll out of effective attention range.
   - *Verified Antidote*: Working-Memory Manager (Pattern 25) with middle-out tool observation pruning; Hierarchical Decomposer (Pattern 16) with per-step prompt rebuilding.
   - *False Antidote*: Upgrading to a model with a larger context window (merely delays failure).
4. **Goal Drift**:
   - *Symptom*: Agent pivots from the original goal to an adjacent or trivial objective based on intermediate discoveries.
   - *Root Cause*: Policy interprets intermediate tool results as the goal state.
   - *Verified Antidote*: Plan-Then-Execute (Pattern 19) maintaining an immutable goal anchor; Drift Detector (Pattern 59).
   - *False Antidote*: Lowering model temperature (reduces stochastic variance, not drift).
5. **Silent Success on the Wrong Task**:
   - *Symptom*: Agent confidently declares victory on a task different from what the user requested.
   - *Root Cause*: Policy "rounds" user intent to a familiar, easily solved neighboring problem.
   - *Verified Antidote*: Chain-of-Thought Auditor (Pattern 8); Reflection Agent (Pattern 47) explicitly comparing final output against initial intake specifications.
   - *False Antidote*: Prompting "make sure you understand the question" (ignored).

## Architectural Invariants & Rules
1. **Structural Antidote Invariant**: Never attempt to cure a canonical failure mode via prompt phrasing. Always implement the corresponding structural pattern.
2. **Pre-Execution Constitutional Interception**: Tool actions with external mutations must be validated against negative invariants before invoking the tool runner.
