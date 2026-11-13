---
name: skill-eval-assurance-runner
description: Evaluate and assure agent skills using small-N Wilson confidence intervals, unbiased pass^k reliability, deterministic trajectory graders, preflight boundary honesty, and sealed digest verification. Do not use for subjective prose review or unconstrained production deployment.
---

# Skill Eval Assurance Runner

`skill-eval-assurance-runner` codifies the small-sample statistical rigor, deterministic trajectory grading, static boundary honesty, and content-addressed release verification distilled from `microsoft/waza` (`v0.41.0`).

See [CARD.md](CARD.md) for the companion summary card and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline statistical/grader defaults and [../self-evaluating-ai-pipeline/SKILL.md](../self-evaluating-ai-pipeline/SKILL.md) for golden regression workflows.

---

## 1. Small-Sample Statistics & Reliability

Measure 3-to-10-trial agent evaluations without normal-approximation collapse:

1. **Wilson Score Confidence Intervals (`compute_wilson_ci`)**: Bound binary pass rates strictly inside `[0.0, 1.0]` with reliable coverage at small N (`3-10` trials).
2. **Unbiased $\tau$-bench `pass^k` (`compute_pass_hat_k`)**: Compute $\binom{s}{k} / \binom{n}{k}$ sequentially instead of biased $p^k$ exponentiation.
3. **Hake Normalized Gain (`compute_hake_normalized_gain`)**: Scale improvements relative to headroom $(1 - \text{pre})$ so gains from `0.90 -> 0.95` register properly.

> **Completion criterion**: `ConfidenceIntervalResult` and scalar reliability metrics returned in `[0.0, 1.0]`.

---

## 2. Deterministic Trajectory & Constraint Graders

Grade recorded tool call sequences deterministically prior to expensive LLM judges:

1. **Action Sequence Grader (`grade_action_sequence`)**: Evaluate `actual_actions` against `expected_actions` using `exact_match`, `in_order_match`, or `any_order_match`, returning multiset Precision, Recall, and F1.
2. **Tool Constraint Grader (`grade_tool_constraints`)**: Enforce `expect_tools`, `reject_tools`, and `allow_only` regex rules (case-insensitive) over observed tool invocations.

> **Completion criterion**: `ActionSequenceGrade` and `ToolConstraintGrade` produced with explicit violation diagnostics.

---

## 3. Preflight Boundary Honesty & Sealed Digests

Separate declared intent from runtime proof and detect tampered artifacts:

1. **Boundary Honesty (`audit_preflight_boundary`)**: Mark static `.agent.md` tool allowlists (`requested-allowlist` / `requested-deny-all`) and post-run boundary graders explicitly as `unresolved` until runtime denial/side-effect evidence is verified.
2. **Canonical Digest Verification (`seal_json_envelope`, `verify_sealed_envelope`)**: Compute SHA-256 over compact sorted JSON after stripping `"digest"`, and compare in constant time before admitting evaluation receipts.

> **Completion criterion**: `PreflightBoundaryFinding` never overclaims runtime enforcement; `SealedEnvelopeCheck` validates integrity.

---

## The Three Foundational Pillars

### 1. Small-N Statistical Honesty
Use Wilson intervals and exact combinatorial `pass^k` estimators instead of fragile normal approximations on 3-to-10-trial agent evals.

### 2. Static Intent Is Not Runtime Enforcement
Treat preflight boundary declarations and post-run graders as `unresolved` pointers requiring runtime evidence, never as preventive security proofs.

### 3. Tamper-Evident Canonical Envelopes
Strip `"digest"` cleanly and hash sorted canonical JSON before admitting release or eval envelopes.

---

## Anti-Patterns

- **Normal-Approximation Intervals at N <= 10** — Using `p +/- z * sqrt(p(1-p)/n)` at small sample sizes produces bounds outside `[0, 1]` and collapses at `p = 0` or `p = 1`; always use `compute_wilson_ci()`.
- **Biased Power Exponentiation for Pass^k** — Computing `(s/n)^k` overestimates multi-run consistency; use combinatorial `C(s, k) / C(n, k)` via `compute_pass_hat_k()`.
- **Equating Frontmatter Allowlists with Sandboxing** — Treating a static `tools:` allowlist or post-run grader as preventive security proof masks uninspected runtime side effects.
- **Accepting Unsealed or Unverified Receipts** — Admitting JSON release bundles without recomputing canonical SHA-256 over keys excluding `"digest"` breaks lineage integrity.
