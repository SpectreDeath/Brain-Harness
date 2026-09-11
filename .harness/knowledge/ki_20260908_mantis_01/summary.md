# Knowledge Item: Google Mantis Decoupled Security Review Pipeline & Sandboxed Crash Verification

- **ID:** `ki_20260908_mantis_01`
- **Source Target:** `D:\GitHub\cloned\Google\mantis`
- **Origin Authors:** Nick Galloway, Yulong Zhang (Google Research / Security)
- **Commits Traced:** 70 commits (June 15, 2026 – September 2, 2026)
- **Status:** `VERIFIED`

---

## 1. Architectural Philosophy: The Decoupled Sequential Pipeline
Single-prompt or monolithic agent sweeps routinely fail in real-world security audits due to three distinct failure modes:
1. **Hallucination Cascades:** An early false-positive assumption causes downstream agents to draft fictional exploit payloads or redundant patches.
2. **Context Window Blowout:** Injecting thousands of lines of code alongside test scripts, logs, and remediation guidelines rapidly exceeds model attention budgets.
3. **Assertion Traps:** LLMs identify "crashes" that rely entirely on debug-only `assert` statements which are eliminated in production release builds.

Mantis solves this through a strictly decoupled, sequential stage progression:
```
[History / Summary / Structural Index] ──► [Threat Model & Plan] ──► [Targeted Static Audit]
                                                                              │
                                                                              ▼
[Exploit Chaining & Reporting] ◄── [Patch Verification] ◄── [Sandboxed Reproduce] ◄── [Dedupe & Critic]
```

---

## 2. Core Bridged Invariants

### Invariant A: Empirical Proof-of-Concept Reproduction
A vulnerability finding is never finalized based on static analysis alone. The agent must write an executable Python or shell script and run it within an isolated sandbox environment. The finding is marked `CRASH_REPRODUCED` only if:
- Non-zero exit code indicates an unhandled exception or crash.
- AddressSanitizer (`ASAN`) triggers memory corruption violations (buffer overflow, use-after-free, double free).
- UndefinedBehaviorSanitizer (`UBSAN`) flags integer overflows or invalid pointer dereferences.

### Invariant B: Transactional Shadow Patch & Bypass Re-Attack
Patches are applied strictly inside temporary shadow directory sandboxes. The candidate fix is evaluated through a dual gate:
1. **Regression Gate:** The original crash reproducer MUST now fail to crash the application (`exit_code == 0`).
2. **Re-Attack Gate:** The reproducer is mutated with boundary and payload variants. If any variant succeeds in bypassing the fix, the status is set to `bypass_succeeded` and the patch is rejected.

### Invariant C: Multi-Pass Deduplication Ladder
Raw findings pass through three successive deduplication rungs:
1. **Syntactic Rung:** Normalized path, line number, and CWE tuple comparison.
2. **AST Symbol Rung:** AST node hierarchy and target symbol function/class identity.
3. **Deterministic Stable Signature:** `SHA256(filepath::CWE::target_symbol)[:16]`.

### Invariant D: Production Viability Critic
Filters out findings that cannot trigger in production:
- Drops assertion traps (`assert x == y`).
- Drops issues isolated to unit test directories (`test_*.py`) or debug wrappers.

---

## 3. Brain Harness Integration Seams
The Google Mantis capabilities are bridged into Brain Harness across three domain-partitioned plugins:
1. `plugins/security_and_forensics/mantis_security_review` (`service.mantis_security_review`): In-process review pipeline, VCS history mining, deduplication ladder, and risk calibration.
2. `plugins/security_and_forensics/mantis_sandbox_verifier` (`service.mantis_sandbox_verifier`): Subprocess-isolated crash reproduction and transactional patch verification adhering to Rule 14 pipe disposal invariants.
3. `plugins/software_engineering/mantis_structural_index` (`service.mantis_structural_index`): Content-addressed semantic unit index and SQLite symbol cache.
