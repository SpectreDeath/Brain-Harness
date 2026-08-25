# Context Type System Plugin — Quickstart

The **Context Type System** plugin enforces typed boundaries, origin ledger tracking, multi-hop Isnad lineage DAG traversal, token budgeting, and structured prompt assembly across LLM agent memory channels (`instruction`, `memory`, `evidence`, `tool_output`).

---

## Key Features

1. **Origin Ledger Invariant**: Content first observed in an unverified channel (e.g. `tool_output`) cannot be re-inserted directly into a protected channel (`instruction`) without an explicit, policy-permitted transformation.
2. **Multi-Hop Isnad Lineage**: Traces the complete ancestor chain of derivations (`tool_output -> evidence -> memory`) with cycle protection.
3. **Token-Aware Prompt Assembly**: Knapsack priority pruning and channel allocation quotas ensure prompts fit within LLM context windows without dropping critical high-priority instructions.
4. **Session Snapshot Serialization**: Export and restore context sessions as portable JSON snapshots for persistent checkpoints across multi-turn agent runs.

---

## Standalone Tool Usage Examples

### 1. Register Context Items & Promote Tool Output

```python
from plugins.memory_and_epistemics.context_type_system.main import (
    context_add,
    context_validate_tool_output,
    context_transform,
    context_get_lineage,
    context_assemble_prompt,
    context_export_session,
    context_import_session,
)

sid = "agent-run-201"

# Add instruction
res_inst = context_add(sid, "instruction", "Answer with factual data.", source="system", priority=100)

# Add raw tool output
res_tool = context_add(sid, "tool_output", "Sensor temp: 72.4F", source="tool:sensor")
tool_id = res_tool["item"]["request_id"]

# Elevate tool output to evidence
res_ev = context_validate_tool_output(sid, tool_id)
ev_id = res_ev["item"]["request_id"]

# Promote evidence to memory
res_mem = context_transform(sid, ev_id, "memory")
mem_id = res_mem["item"]["request_id"]
```

### 2. Trace Isnad Provenance Lineage

```python
lineage_res = context_get_lineage(sid, mem_id)
print(f"Hops: {lineage_res['hops']}")
for hop in lineage_res["lineage"]:
    print(f"-> [{hop['context_type']}] id={hop['request_id']} (derived_from={hop['derived_from']})")
```

### 3. Assemble Token-Budgeted Prompt

```python
prompt_res = context_assemble_prompt(
    sid,
    max_tokens=200,
    channel_quotas={"instruction": 0.4, "memory": 0.3, "evidence": 0.3},
)
print("Used Tokens:", prompt_res["used_tokens"])
print("Dropped Items:", prompt_res["dropped_items_count"])
print(prompt_res["prompt"])
```

### 4. Snapshot Export & Restore

```python
# Checkpoint session state
snapshot = context_export_session(sid)["data"]

# Restore to a new session
context_import_session("agent-run-201-restored", snapshot)
```
