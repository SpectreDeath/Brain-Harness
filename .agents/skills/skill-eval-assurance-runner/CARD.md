```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: skill-eval-assurance-runner                                   │
│ Category: agent_orchestration / eval_assurance                       │
│ Version: 1.0.0                                                       │
│ Invocation: /skill-eval-assurance-runner                             │
│ Triggers: "wilson ci", "pass hat k", "action sequence grader",       │
│           "tool constraint", "preflight boundary", "seal digest"     │
│ Requires: "self-evaluating-ai-pipeline"                              │
│ Target: Small-N stats, trajectory graders & sealed eval envelopes    │
└──────────────────────────────────────────────────────────────────────┘
```

# Skill Eval Assurance Runner — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Small-N Statistics** | `compute_wilson_ci()`, `compute_pass_hat_k()`, `compute_hake_normalized_gain()` | `ConfidenceIntervalResult` (`mean`, `lower`, `upper`) |
| **2. Trajectory Grading** | `grade_action_sequence()`, `grade_tool_constraints()` | `ActionSequenceGrade`, `ToolConstraintGrade` |
| **3. Honesty & Sealing** | `audit_preflight_boundary()`, `verify_sealed_envelope()` | `PreflightBoundaryFinding`, `SealedEnvelopeCheck` |

---

## Mandatory Invariants Checklist

- [ ] **Wilson Clamping**: Confidence interval bounds stay strictly within `[0.0, 1.0]` for all `0 <= successes <= trials`.
- [ ] **Exact Pass^k**: Return `0.0` whenever `k < 1`, `k > trials`, or `successes < k`.
- [ ] **Preflight Honesty**: Static tool allowlists and post-run boundary graders always emit `state="unresolved"`.
- [ ] **Constant-Time Digest Match**: Verify `"digest"` via `hmac.compare_digest` after stripping `"digest"` from canonical sorted JSON.
- [ ] **Slotted & Frozen Models**: All domain results use `slots=True, frozen=True` (Rule 12).
