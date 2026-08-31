# Async Rewake in Agent Lifecycle Hooks

## Context
When implementing deep code analysis or LLM-based security checks during agent tool invocations (such as git commit or git push), executing full reviews synchronously blocks the agent loop and introduces noticeable latency into user interactions.

## Distilled Learning
Implement an asynchronous lifecycle hook pattern with `asyncRewake: true`. The hook runs heavy checks in the background and only interrupts the session when actionable issues are discovered:
- The hook triggers upon matching tool invocations (e.g. `matcher: "Bash"`, `if: "Bash(git commit:*)"`).
- A background worker analyzes the diff or ast changes.
- Upon detecting vulnerabilities or failures, the engine dispatches a high-priority rewake message (`rewakeMessage`) to re-engage the agent with precise diagnostic context.

## Triggers & Seam Choices
- **Trigger**: Long-running linters, AST security scans, or second-pass LLM verifiers attached to tool executions.
- **Seam Choice**: Register in the event/hook registry (`hooks.json`) as a non-blocking post-tool interceptor with a priority rewake channel.
