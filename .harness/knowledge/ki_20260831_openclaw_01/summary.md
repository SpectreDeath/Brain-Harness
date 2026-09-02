# In-Flight Plain-Text Tool-Call Stream Normalization & Repair

## Context
When interacting with diverse LLM providers, models occasionally drift from provider-native tool call schemas and emit tool calls as plain-text JSON blocks, Markdown code fences, or XML-wrapped calls directly in the assistant's content stream. If unhandled, the ReAct step execution engine interprets this as a final text response rather than a tool invocation, halting execution or producing agent hallucinations.

## Distilled Learning
Implement an isomorphic stream repair and promotion pipeline:
1. **Pre-Execution Stream Interception**: Inspect incoming delta chunks or final assistant messages for plain-text tool invocation signatures (e.g. ````json {"tool": ...}```` or `{"name": "...", "parameters": {...}}`).
2. **Deterministic Payload Extraction**:
   - Extract tool names and argument payloads with protected range resolvers to prevent greedy extraction over user-intended markdown.
   - Clean up trailing commas, unescaped characters, and unbalanced brackets.
3. **Event Promotion**: Synthesize standard `tool_call` frame events containing structured `tool_name` and `arguments`, stripping the raw plain-text representation from the visible chat transcript.
4. **Zero-Overhead Fallback**: If no valid tool signature is parsed, pass the message through untouched as regular model text.

## Triggers & Seam Choices
- **Trigger**: Pre-LLM response normalization inside `StepExecutionEngine` or during tool call parsing.
- **Seam Choice**: Encapsulate as a pluggable stream filter (`service.openclaw.tool_repair`) registered in the Harness IoC container.
