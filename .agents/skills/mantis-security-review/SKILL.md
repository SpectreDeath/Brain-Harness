---
name: mantis-security-review
description: "Execute Google Mantis autonomous security reviews across VCS commit history, AST taint analysis, finding deduplication ladders, critic filters, and multi-stage exploit chaining. Do not use for unauthorized external penetration testing or live exploit delivery."
category: security_and_forensics
version: "1.0.0"
---

# Google Mantis Autonomous Security Review & Triage Skill

Provides operational procedures, staged triage protocols, and invariant verification rules for the Google Mantis (`plugin.mantis_security_review`, `harness mantis`) security review pipeline.

## The 10-Stage Autonomous Review Lifecycle

1. **VCS History & Churn Scanning** (`harness mantis history-scan`):
   - Mines git history for bug-fix commits, vulnerability advisories, and high-churn code hotspots.
2. **Directory Attack Surface Mapping** (`harness mantis dir-summary`):
   - Maps total entrypoints, API endpoints, and configuration interfaces.
3. **Plan Feasibility & Threat Review** (`harness mantis plan-review`):
   - Binds threat model assumptions against target source paths and focus CWEs.
4. **AST Taint & Static Analysis** (`harness mantis audit`):
   - Analyzes source ASTs for SQL injection, command execution, path traversal, and memory unsafety.
5. **Deduplication Ladder** (`harness mantis dedupe`):
   - Collapses identical findings across syntactic hashing, AST normalization, and call-site clustering.
6. **Critic Filter & False Positive Screening** (`harness mantis critic-filter`):
   - Evaluates reachability, input sanitization, and release assertions to eliminate false positives.
7. **Security Gate Enforcement** (`harness mantis gate`):
   - Evaluates findings against enterprise policy (e.g. fail on `HIGH` or `CRITICAL`); exits non-zero on breach.
8. **Exploit Chaining & Tactic Synthesis** (`harness mantis chain-exploits`):
   - Composes individual primitives (e.g., SSRF + weak auth + deserialization) into end-to-end exploit graphs.
9. **Risk Calibration & Blast Radius** (`harness mantis calibrate-risk`):
   - Adjusts scores based on asset criticality, internet exposure, and defense-in-depth mitigations.
10. **Executive Report & Remediation Dossier** (`harness mantis report`):
    - Synthesizes structured markdown and JSON audit reports.

## Visual Brief

When executing full repository reviews or presenting exploit chains, Mantis can render self-contained HTML reports:
- **Brief Delivery**: Exported to `%TEMP%/mantis-review-<report_id>.html` containing interactive exploit chain DAGs and severity breakdown charts.
- **Visual Verification**: Inspect candidate exploit paths and risk calibration bands before committing remediation tickets.

## Mandatory Checkpoints

- **RequestFeedback**: Before finalizing exploit chaining or reporting findings with severity `CRITICAL`, pause and request feedback with discovered evidence paths.
- **Gate Enforcement Check**: Verify that `harness mantis gate` runs in non-interactive CI/CD pipelines with `--fail-on HIGH` to shift vulnerability blocking left.

## Anti-Patterns

- **Isolated Static Analysis** — Auditing files without mining commit histories or surveying directory entrypoint topologies.
- **Unfiltered Raw Finding Dumps** — Passing raw AST matches directly to developers without running deduplication ladders and critic filters.
- **False Absence Assumptions** — Treating a passing security review gate as formal proof that zero vulnerabilities exist.
- **Uncalibrated Severity Inflation** — Rating findings as Critical without considering network exposure or asset criticality.
- **Uncoordinated Chaining** — Generating disconnected exploit step lists without establishing verifiable data flow between stages.

## Related Resources

- [Summary Card](CARD.md) — Quick reference card and invariants checklist.
- [REA Reverse Engineering](../rea-reverse-engineering/SKILL.md) — Binary and managed runtime artifact dissection.
- [Pre-Commit Security Guard](../pre-commit-security-guard/SKILL.md) — Left-shifted pre-commit security interception.
- [Differential Facet Verifier](../differential-facet-verifier/SKILL.md) — Multi-provider observation comparison.
- [Reconstruction Obligation Ledger](../reconstruction-obligation-ledger/SKILL.md) — Cryptographic evidence sealing.

