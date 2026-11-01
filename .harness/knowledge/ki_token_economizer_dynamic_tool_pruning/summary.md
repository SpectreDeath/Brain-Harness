# Empirical Evidence-Based Tool Pruning & Capability Masking

## Context & Theoretical Grounding
Every loaded tool's JSONSchema description is re-sent and billed on every single conversational turn. In multi-tool agents (e.g. Claude Code with 15+ tools, IDEs with 40+ tools), tool schemas consume thousands of prefix tokens per request.

## Distilled Mental Models & Heuristics
1. **The Dual Exclusion Policy**:
   - **Hardcoded Exclusions**: Inapplicable tools known a priori not to belong to the active domain (e.g. Jupyter notebook tools in CLI C++ tasks).
   - **Evidence-Based Pruning**: If a tool remains loaded but unused for $p=10$ prompts across at least $m=2$ sessions, or across $s=5$ sessions of any length, it is proposed for pruning.
2. **The Protected Work-Surface Invariant**:
   - Work-surface tools (`read_file`, `edit_file`, `run_command`, etc.) are declared in `protected_tools()` and are immune from pruning under all conditions.
3. **Periodic Re-Audit & Fast Restoration**:
   - Pruning states re-audit every `evidence_reaudit` sessions. A single user command or tool restoration signal immediately brings pruned tools back into scope.

## Anti-Pattern Defenses
- **Blind All-Tool Loading**: Sending 50+ tool schemas to the model when the current task only exercises 3 file-editing tools.
- **Unprotected Core Pruning**: Dropping critical read/write primitives due to temporary inactivity.
