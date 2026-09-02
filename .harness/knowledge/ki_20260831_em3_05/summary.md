# Autonomous Self-Healing Feedback Loop with AST Patch Synthesis & Rollback

## Context
Autonomous agents synthesizing new tools, plugins, or workflows encounter sporadic runtime errors (e.g. missing standard library imports, uncoerced input dictionaries, unhandled edge-case exceptions). Without an automated self-healing loop, each minor error terminates the agent loop.

## Distilled Learning
Implement closed-loop autonomous repair:
1. **Failure Signature Interception**:
   - Capture error type and message: `NameError`, `ImportError`, `TypeError`, `ValueError`.
2. **Contextual Patch Synthesis**:
   - For `NameError` / `ImportError`: Inject missing module imports or required aliases.
   - For `TypeError` / `ValueError`: Inject input sanitization and schema coercion guards.
   - For unhandled crashes: Wrap execution body in defensive exception boundaries.
3. **Atomic Rollback Guarantee**:
   - Snapshot the original file content before applying the patch.
   - Execute validator tests; if validation fails, restore the snapshot immediately and record diagnostic telemetry.

## Triggers & Seam Choices
- **Trigger**: Tool execution error inside ReAct loop or plugin compilation failure in `plugin_creator`.
- **Seam Choice**: Integrate inside `harness.creator.remediation` and `StepExecutionEngine` as an automatic retry interceptor before reporting error status.
