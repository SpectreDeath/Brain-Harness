# Spider Decision Experiments — Results Log

<!--
Template for per-phase entries:

## Phase N — <title> (<ISO timestamp>)
- Outcome: PASS | FAIL | PARTIAL
- Key metric(s): ...
- Finding(s): ...
- Follow-ups: ...
-->

## Phase 0 — Scaffolding, Shared Helpers & Frozen Snapshots (2026-11-18T14:56:40+00:00)
- Outcome: PASS
- Key metric(s): 7/7 snapshots cached & round-trip verified (vault=630/959, google_portfolio_root=57/81, grm=1275/4499, gvisor=47/83, airllm=44/60, airllm_plus=33/38, brain_harness_src=49/129); ruff check/format clean; 15/15 baseline pytest passed.
- Finding(s): Live-vs-cached entity, assertion, and triple sets matched 100% across all 7 models.
- Follow-ups: Proceed to Phase 1 false-bridge audit (1.1-1.3 checkpoint).
