# Solution: Create a Text Transformation Plugin

## Explanation

The solution subclasses `HarnessPlugin`, requires `TOOL_REGISTRY_KEY`, and mounts the `"text.reverse"` tool during the `on_enable()` lifecycle hook.
