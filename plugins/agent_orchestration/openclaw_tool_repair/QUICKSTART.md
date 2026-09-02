# OpenClaw Tool Repair Plugin Quickstart

The `plugin.openclaw_tool_repair` provides in-flight plain-text tool-call recovery and stream normalization to prevent LLM execution failures when models emit code blocks or malformed JSON instead of native tool calls.

## Key Capabilities

1. **`openclaw_parse_tool_blocks`**: Scans assistant text for JSON code fences, XML `<tool_call>` tags, and standalone tool signatures.
2. **`openclaw_repair_tool_call`**: Cleans up trailing commas, unescaped quotes, and unclosed braces/brackets.
3. **`openclaw_normalize_stream_chunk`**: Strips plain-text tool invocations from the streaming transcript while promoting them into structured tool events.

## Example Usage

```python
from harness.kernel.context import ServiceContext
from harness.services.openclaw_bridge import OPENCLAW_TOOL_REPAIR_KEY

repair_svc = context.resolve(OPENCLAW_TOOL_REPAIR_KEY)

# Handle plain text output from a model
raw_text = 'Let me run this for you:\n```json\n{"tool": "bash", "arguments": {"command": "ls -la",}}\n```'
blocks = repair_svc.parse_plain_text_tool_blocks(raw_text)

for block in blocks:
    print(f"Tool: {block.tool_name}, Arguments: {block.arguments}, Repaired: {block.is_repaired}")
```
