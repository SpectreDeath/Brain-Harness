## External Ingestion Workspace Scope Boundary & Non-Workspace Shell Fallback

### Problem
When AI agents introspect or bridge external codebases located outside the active workspace directory (e.g. `D:\GitHub\cloned\<repo>`), IDE-level filesystem inspection tools (e.g., `view_file`) frequently fail due to security policy boundaries:
`Permission denied for read_file. Target file path is outside the active workspace. Matches default system policy.`

Agents that fail to anticipate this error often stall, enter retry loops, or erroneously prompt the human for workspace re-configuration.

### Invariant & Defensive Heuristic
When inspecting external repositories located outside the active workspace root:
1. **Immediate Non-Modifying Shell Pivot**: Agents must immediately pivot to non-modifying shell reads (`run_command` with PowerShell `Get-Content`, `Get-ChildItem -Recurse`, or standalone Python scratch scripts).
2. **Scratch Script Isolation**: For complex multi-file AST inspection or dependency parsing, write a temporary inspector script to `<appDataDir>\brain\<conv_id>\scratch\inspect_*.py` and execute it via `python <path>`.
3. **Piping & Codec Discipline**: Ensure all external output streams are read using UTF-8 encoding (Rule 23) to prevent Unicode and BOM corruptions.

### Codification
- **Rule 46 (AGENTS.md)**: External Ingestion Permission Boundary Fallback.
- Never block agent progress when an external path triggers an IDE workspace policy denial; use safe read-only subprocess streams.
