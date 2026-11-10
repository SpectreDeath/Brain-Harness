# Evidence Isolation Guard Plugin

The `plugin.evidence_isolation_guard` plugin implements fail-closed tripwires and trial identity verification synthesized from Google Harness² (`google/harness2`, arXiv 2610.14224).

## Architecture & Responsibilities

1. **Answer-Key Filtering**: Rejects any path matching declared answer-key leak patterns before context enters model execution.
2. **Grader-Verdict Tripwire**: Enforces bounded-chunk scanning (1MB blocks with boundary overlap) across all evidence files for evaluator verdicts, scores, and grader markers (`deterministic_eval_summary`, `pass_rate`, etc.). Fails closed if traversal exceeds `max_depth`.
3. **Canonical Trial Identity**: Content-addresses harness directories and task prompt/files into stable SHA-1 digests using POSIX-normalized relative paths and atomic filesystem completion markers (`.refine_complete`).
4. **Environment Secret Scrubbing**: Strips provider API keys and tokens from runner child processes while retaining caller-specified authentication parameters.

## Seams

- **Service Key**: `EVIDENCE_ISOLATION_SERVICE_KEY` (`service.evidence_isolation`)
- **Protocol**: `EvidenceIsolationService`
- **Resolver**: `resolve_evidence_isolation(context)`
