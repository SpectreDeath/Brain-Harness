# Subagent Thread Forking & Safety Auditing with guardian-v2

## Problem
Auditing user inputs and tool outputs for safety risks, malicious instructions, or prompt injections within the main model thread consumes valuable context window budget and risks poisoning the agent's working memory if adversarial instructions are parsed as legitimate context.

## Solution
Structure safety systems as decoupled extensions that leverage subagent thread forking:
1. **Thread Lifecycle Hook**: Capture thread start context (`GuardianThreadContext`) storing `forked_from_thread_id`.
2. **Subagent Delegation**: Delegate deep auditing tasks to isolated child threads (`spawn_subagent`) that run synchronous reviewer prompts or asynchronous scoring workers (`async_scorer.rs`).
3. **Structured Verdicts**: Return strict review verdicts (`StrictReviewReason`) back to the host runtime to block or proceed with execution without contaminating the primary conversation history.

## Operational Guideline
- Always isolate metacognitive or adversarial audits in ephemeral forked subagents.
- Never write intermediate safety deliberations directly to long-term memory or main turn context.

## Provenance
- Source repository: `D:/GitHub/cloned/codex-main/codex-main`
- Primary files: `codex-rs/ext/guardian-v2/src/lib.rs#L22-L79`, `codex-rs/ext/guardian-v2/src/sync_reviewer.rs`
