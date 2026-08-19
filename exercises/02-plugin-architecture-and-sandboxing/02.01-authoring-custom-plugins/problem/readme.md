# Problem: Create a Text Transformation Plugin

## Objective

Author a `TextTransformPlugin` subclassing `HarnessPlugin` that registers a string reversal tool into the `ToolRegistry`.

## Tasks

1. Define `TextTransformPlugin`.
2. Require `TOOL_REGISTRY_KEY`.
3. In `on_enable()`, register `"text.reverse"` with `ToolRegistry`.
