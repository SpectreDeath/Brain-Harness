# Minimal ReAct Autonomous Loops, Safe-Path Sandboxing & Bounded Error Self-Repair

**ID:** `ki_hf_nano_harness_react_sandboxing`  
**Category:** `software_engineering`  
**Origin:** *The Context Course: Unit 6 (Nano Harness)* (Hugging Face)  
**Provenance Lineage:** Units 6.1-6.4, Hugging Face, 2026.

## Executive Summary

Understanding how enterprise coding agents function under the hood requires stripping away framework boilerplate and implementing a pure, minimal ReAct loop from first principles. Unit 6 introduces "Nano Harness" — a complete, fully functional coding agent in under 200 lines of standard Python.

### The Nano ReAct Architecture
```
User Goal ──► [Prompt + Tools Definition]
                     │
                     ▼
             ┌──► [LLM Call (OpenAI / HF Router API)]
             │       │
             │       ▼
             │   [Parse Action Codeblock / Tool Call]
             │       │
             │       ▼
             │   [Path Confinement & Command Whitelist Check]
             │       │
             │       ▼
             │   [Execute Tool in Subprocess / File System]
             │       │
             │       ▼
             └── [Append Observation to History] ──(Repeat until final_answer or Max Steps)
```

### Essential Safety & Sandboxing Mechanisms
1. **Filesystem Path Confinement (`safe_path`)**: Resolves requested paths and verifies they reside strictly inside the active project workspace:
   ```python
   def safe_path(target_path, workspace_root):
       resolved = Path(workspace_root, target_path).resolve()
       if not str(resolved).startswith(str(Path(workspace_root).resolve())):
           raise PermissionError(f"Access denied outside workspace: {target_path}")
       return resolved
   ```
2. **Command Whitelisting & Timeout Gating**: Shell execution tools enforce strict command whitelists (`git`, `pytest`, `python`) with mandatory subprocess timeouts to prevent hanging processes.
3. **Bounded In-Flight Self-Repair**: When tool execution fails (syntax errors, failed tests), the error traceback is appended as a standard observation, allowing the model to inspect its mistake and generate a corrective action on the next turn.

## Operational Deployment Invariants

1. **Step Limit Safety**: Every autonomous loop must enforce an explicit maximum step counter (default 30-50) to prevent infinite loops and runaway API billing.
2. **Error Recovery Isolation**: Exceptions raised during tool execution must never crash the Python proactor; catch `Exception`, format a clean diagnostic error string, and return it to the model.
3. **Deterministic Final Settlement**: Require a dedicated `final_answer(...)` tool call or sentinel token to formally conclude the task and emit deliverables.
