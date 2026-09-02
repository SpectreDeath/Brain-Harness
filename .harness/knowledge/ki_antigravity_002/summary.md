# 4-Stage Hook Lifecycle & Tri-State Policy Evaluation

**ID:** `ki_antigravity_002`  
**Category:** `security_and_forensics`  
**Origin:** `google-antigravity-sdk`  
**Provenance Lineage:** `google/antigravity/hooks/hook_runner.py`, `google/antigravity/hooks/policy.py`

## Executive Summary
Antigravity enforces a strict 4-stage hook lifecycle: SessionContext (start/end), TurnContext (pre/post), OperationContext (pre/post tool), and SubagentContext. HookRunner evaluates declarative security policies returning tri-state decisions: ALLOW (execute immediately), DENY (short-circuit with error payload), or ASK_USER (halt execution and prompt human in the loop for terminal confirmation).

## Architectural Invariants & Rules
1. Every tool invocation must pass through HookRunner.pre_tool before process execution.
2. Security policies must strictly resolve to ALLOW, DENY, or ASK_USER.
3. DENY decisions short-circuit immediately without invoking subprocess transports or models.
