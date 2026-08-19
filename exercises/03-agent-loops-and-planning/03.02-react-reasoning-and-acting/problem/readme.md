# Problem: Run a ReAct Agent Task with Mock LLM

## Objective

Configure a `ReActAgentService` with a mock LLM and a calculator tool, and verify that the agent parses thoughts, invokes the tool, and returns the final answer.

## Tasks

1. Register `"math.add"` in `ToolRegistry`.
2. Provide a mock LLM that generates an Action step followed by a Final Answer.
3. Run the task and verify the `AgentTaskResult`.
