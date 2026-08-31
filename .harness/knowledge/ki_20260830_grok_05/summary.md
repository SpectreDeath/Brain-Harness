# Preemptive Interjection Buffer & Prompt Queue

## Context
During long-running agent reasoning, large token generations, or multi-step execution loops, users may submit steering prompts or background diagnostic hooks may detect critical errors. Forcing the user to wait for generation completion wastes tokens and time, while naive process cancellation drops in-flight execution context.

## Distilled Learning
Implement an asynchronous interjection core and prompt queue:
- **Streaming Preemption Barrier**: An atomic interjection buffer monitors inbound channels while the LLM is actively streaming response tokens or executing tool steps.
- **Structured Interjection Events**: Interjections are formatted into structured event variants (`UserInterjection`, `SystemInterjection`, `CancelPending`), preserving the partial transcript up to the preemption point.
- **Graceful Context Splice**: When an interjection triggers, the engine cleanly halts the active token stream, flushes partial tool outputs to the event journal, and splices the interjection prompt into the message queue as the next high-priority turn.
- **Zero Event Loss**: Buffered interjections ensure that rapid subsequent keystrokes or queued prompts are ordered deterministically rather than dropped during transition states.

## Triggers & Seam Choices
- **Trigger**: Mid-generation user interruptions, real-time steering, or asynchronous rewake events.
- **Seam Choice**: Integrate at the agent streaming coordinator (`harness.agent` or `xai-interjection-core`) wrapping LLM token generation iterators.
