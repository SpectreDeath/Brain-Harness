# Agent Orchestration Context

The Agent Orchestration context governs multi-agent coordination, hierarchical task decomposition, adversarial debate, quality evaluation, and human governance.

## Language

**Supervisor**:
A coordination node that decomposes high-level goals into DAG waves and delegates them to specialized workers.
_Avoid_: Manager, master, boss

**Debater**:
A dual-agent dialectical loop where a Generator node and a Critic node challenge each other's assertions until consensus or timeout.
_Avoid_: Arguer, combatant, discussion loop

**Critic**:
An evaluation agent that scores proposals against explicit criteria and searches for edge-case vulnerabilities.
_Avoid_: Reviewer, judge, grader

**Task Plan**:
A directed acyclic graph (DAG) of discrete execution steps with explicit dependencies and completion gates.
_Avoid_: Todo list, checklist, schedule

**Checkpoint**:
A blocking pause in execution that mandates explicit human review before proceeding with irreversible actions.
_Avoid_: Breakpoint, pause, stop sign
