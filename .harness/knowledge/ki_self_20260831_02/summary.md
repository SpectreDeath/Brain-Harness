# In-Flight Tool-Call Stream Normalization & AST Auto-Repair

## Metadata
- **KI ID**: `ki_self_20260831_02`
- **Source Target**: `openclaw/packages/tool-call-repair`
- **Format**: `typescript_monorepo`
- **Timestamp**: `2026-08-31T19:25:00Z`
- **Status**: `VERIFIED`
- **Tags**: `tool_calling, stream_parsing, ast_repair, json_normalization, endogenous_memory, self_reflection`

## Operational Summary & Context
Non-fine-tuned models frequently emit markdown code fences or unescaped XML tool calls in plain text streams. Strict JSON-RPC parsers crash unless streaming intercepts normalize payloads before dispatch.

## Distilled Learning & Invariant
Wrap all tool-calling streaming parsers with dynamic AST regex interceptors and syntax normalizers. Detect markdown ```json fences and XML <tool_call> blocks in-flight, strip trailing commas, auto-close unbalanced braces, and promote extracted objects into native tool invocation frames without aborting the step execution loop.

## Isnad Lineage & Grounding
- **Assertion**: Streaming tool execution engines must intercept plain-text model codeblocks (JSON fences, XML <tool_call> tags) and auto-repair syntax defects in-flight (trailing commas, unclosed brackets) before propagating to execution dispatch.
  - `primary_code`: `openclaw/packages/tool-call-repair` (Verified: True)
  - `rule_spec`: `AGENTS.md#L21` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/repo-reader-1788199910.html` (Verified: True)
