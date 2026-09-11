# Mantis Sandbox Verifier Plugin (`plugin.mantis_sandbox_verifier`)

## Overview
`plugin.mantis_sandbox_verifier` encapsulates dynamic crash reproduction, Proof-of-Concept (PoC) payload execution, and transactional security patch verification. Untrusted payloads are executed strictly in isolated subprocess sandboxes with lazy staging (Rule 5 & 7).

## Service Key
- **Key**: `service.mantis_sandbox_verifier`
- **Type**: `ServiceKey[MantisSandboxVerifierService]`
- **Isolation**: `subprocess` (Untrusted execution boundary)

## Exported Tools
- `mantis_sandbox_exec`: Execute shell or binary commands with strict async pipe draining and process disposal (Rule 14).
- `mantis_reproduce_crash`: Run PoC crash reproducers with AddressSanitizer (`ASAN`) and UndefinedBehaviorSanitizer (`UBSAN`) instrumentation.
- `mantis_patch_verify`: Apply candidate diffs in shadow directory sandboxes, re-execute the reproducer, and run fresh bypass re-attack variants (`VERIFIED_SECURE` gate).

## Pipe Disposal Invariant (Rule 14)
All asynchronous child processes explicitly close and drain `stdin`, `stdout`, and `stderr` streams inside `finally` blocks, preventing resource leakages across Windows proactor loops and Unix event loops.
