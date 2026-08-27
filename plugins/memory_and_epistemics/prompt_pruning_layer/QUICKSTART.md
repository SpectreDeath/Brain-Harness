# Prompt Pruning Layer Plugin — Quickstart Guide

The `domain.prompt_pruning_layer` plugin provides deterministic, 3-pass compiler-style prompt optimization to eliminate redundant tokens before model inference.

## 🔄 The 3 Optimization Passes
1. **Pass 1 — Expired Context Elimination**: Superseded tool outputs sharing the same `tool_call_key` are evicted, keeping only the latest version.
2. **Pass 2 — Duplicate Context Elimination**: Redundant retrieved doc passages (normalized whitespace/casing) are collapsed to the first occurrence.
3. **Pass 3 — Dependency Restoration**: Any message defining a key (`DEFINE:<key>`) required by a surviving message (`REF:<key>`) is automatically restored.

## 🚀 Quick Usage

```python
from plugins.memory_and_epistemics.prompt_pruning_layer.main import (
    prune_messages, benchmark_pruning_workloads
)

messages = [
    {"id": "t1", "role": "tool_output", "content": "Database schema DEFINE:schema_v1", "turn": 1, "tool_call_key": "get_schema"},
    {"id": "t2", "role": "tool_output", "content": "Updated database schema", "turn": 2, "tool_call_key": "get_schema"},
    {"id": "d1", "role": "retrieved_doc", "content": "Installation guide excerpt.", "turn": 3},
    {"id": "d2", "role": "retrieved_doc", "content": "installation GUIDE excerpt.", "turn": 4},
    {"id": "u1", "role": "user", "content": "Export DDL matching REF:schema_v1", "turn": 5},
]

# Prune
result = prune_messages(messages, assemble_prompt=True)
print(f"Token reduction: {result['report']['token_reduction_pct']}%")
print(result["prompt_text"])
```
