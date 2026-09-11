# Explanation: Architectural Principles & Sandboxing Invariants in Mantis

This document explains the design decisions, threat boundaries, and trade-offs behind the Google Mantis integration into Brain Harness.

---

## 1. Why Decoupled Sequential Skills Beat Monolithic System Prompts
Conventional coding agent frameworks attempt security reviews using large, complex prompts asking an LLM to "find all vulnerabilities, verify them, explain the attack, and write a fix" in a single generation step.

In practice, this architecture breaks down across four fronts:
1. **Confirmation Bias & Hallucination Cascades:** When a model asserts that an input is unvalidated on Line 42, subsequent turns assume the premise is true, compounding errors into fictional vulnerability reports.
2. **Context Window Starvation:** Supplying whole-codebase ASTs, execution logs, and patch diffs simultaneously exhausts the attention mechanism, causing the model to miss subtle off-by-one errors or memory safety violations.
3. **Assertion Traps:** Large language models routinely confuse runtime invariant assertions (`assert p != NULL`) with actionable security boundaries, generating "exploits" that only trigger when assertions are enabled in debug mode.

Mantis enforces a **decoupled sequential workflow** where each stage has a distinct, single responsibility and independent gatekeeping criteria. The researcher cannot verify findings; the reviewer cannot write fixes; the patch generator cannot certify safety without the independent reproducer.

---

## 2. Subprocess Sandbox Isolation & Rule 14 Invariant
Untrusted repositories and model-generated exploit scripts must never execute within the Harness kernel process:

1. **Process Boundary:** All dynamic execution occurs inside a dedicated child process with restricted environment variables, no sensitive token inheritance, and temporary shadow directory isolation.
2. **Rule 14 Pipe Drainage Guarantee:** Asynchronous process management on Windows proactor loops and POSIX event loops is prone to zombie process leaks and unclosed pipe handles if exceptions interrupt execution. The `MantisSandboxEngine` wraps all subprocess invocations in strict `try...finally` blocks that drain stdout/stderr, close `stdin`, and explicitly terminate runaway processes.

```
+-------------------------------------------------------------+
| Brain Harness Process (Trusted)                            |
|  - ServiceContext (IoC)                                     |
|  - StepExecutionEngine                                      |
+------------------------------+------------------------------+
                               | IPC (JSON-RPC / Subprocess)
                               v
+-------------------------------------------------------------+
| Mantis Sandbox Child Process (Untrusted Sandbox)           |
|  - Shadow Workspace Directory                               |
|  - ASAN / UBSAN Sanitizers Enabled                          |
|  - Timeout Guard (60s - 120s)                              |
+-------------------------------------------------------------+
```

---

## 3. Transactional Shadow Patch & Bypass Re-Attack
When fixing vulnerabilities, writing a patch that silences the specific crash input is insufficient. Fixes frequently introduce regressions or fail against basic boundary mutations (e.g., adding `strip()` but forgetting negative length prefixes).

Mantis implements a **transactional shadow patch lifecycle**:
1. The candidate diff is written to a temporary shadow directory without modifying the user's active Git working tree.
2. The original crash reproducer script is executed against the patched tree. If the crash recurs, the patch is rejected (`PATCH_FAILED_TO_FIX`).
3. If the baseline reproducer is blocked, an adversarial re-attack pass generates payload mutations. If any variant succeeds in bypassing the fix, the patch is rejected (`REATTACK_BYPASSED`).
4. Only if both passes succeed is the verdict set to `VERIFIED_SECURE`, allowing the transaction to commit to the repository checkpoint.

---

## 4. Open Knowledge Format (OKF v0.2) & Content-Addressed Signatures
Multi-turn agent sweeps frequently re-examine files touched by prior passes. Without persistent state deduplication, agents duplicate findings and waste inference compute.

Mantis utilizes:
- **Deterministic Stable Signatures:** `SHA256(filepath::CWE::target_symbol)[:16]`. Regardless of which subagent visits the file, the identity of the flaw remains constant across runs.
- **OKF v0.2 SQLite Schema:** Findings, execution logs, and architectural concepts are persisted in a relational store, allowing fast delta queries and cross-run lineage resolution.
