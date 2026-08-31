# Adversarial Red-Teaming Subprocess Isolation (`ki_self_20260827_02`)

## Summary
Red-teaming and adversarial security tooling (e.g. Microsoft PyRIT converters, multi-turn jailbreak orchestrators, and prompt scoring classifiers) must execute strictly inside sandboxed subprocesses with rigid timeout limits.

## Architectural Invariant
1. **Subprocess Sandboxing:** PyRIT and related security evaluation modules must never execute directly inside the kernel in-process runtime.
2. **Timeout Barriers:** Tool calls must have hard cancellation deadlines (`WaitMsBeforeAsync` / async asyncio wait envelopes) to prevent infinite loops during adversarial probe generations.
3. **Pure State Transitions:** Evaluation scores and converter outputs are emitted as structured immutable events onto the Event Bus without altering kernel state.

## Provenance
- Synthesized via `repo-to-plugin-forge` and verified in `plugins/security_and_forensics/pyrit_redteaming/`.
