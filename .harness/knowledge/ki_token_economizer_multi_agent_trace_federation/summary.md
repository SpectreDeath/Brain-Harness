# Standardized Multi-Harness Session Trajectory & Cost Ledger Federation

## Context & Theoretical Grounding
Different coding agents format their session logs differently: Claude Code uses JSONL events, Codex uses rollout trees, Copilot CLI uses transactional records, and Pi uses hierarchical session transcripts.

## Distilled Mental Models & Heuristics
1. **The DomainAdapter Abstraction**:
   - Standardizes `load_trajectory()`, `tool_usage()`, `parse_catalog()`, `protected_tools()`, and `spiral_snapshot()` across heterogeneous agents.
2. **The Stage Lifecycle**:
   - 4 lifecycle hooks: `before_task(task, injected)`, `build_tools(task)`, `run_kwargs(task)`, and `after_task(task, row, run_dir, srow)`.
   - Any mechanism can plug into any runner (live IDE plugin or offline benchmark harness) without altering core logic.
3. **The Single Cost Definition**:
   - Cost accounting lives strictly in `ledger.py` and `pricing.py`. All stages report token overhead against the same ledger to prevent drift between optimization claims and actual billing.

## Anti-Pattern Defenses
- **Vendor-Locked Pruning**: Hardcoding optimization logic directly into agent-specific CLI hooks.
- **Untracked Optimization Overhead**: Failing to account for judge or distillation token usage in net efficiency metrics.
