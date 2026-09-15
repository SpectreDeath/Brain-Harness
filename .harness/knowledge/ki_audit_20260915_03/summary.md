## Bounded Directory Traversal & Noise-Root Pruning Invariant

### Discovery
Unpruned recursive directory walks (`Path.rglob("*")` or bare `os.walk`) on complex codebases containing deeply nested directories (`.git`, `node_modules`, `.venv`, `__pycache__`, `target`, `dist`, `.gemini`) trigger severe performance degradation, proactor pipe exhaustion, and background task timeouts on Windows environments.

### Architectural Invariant
All multi-project scanners, repository auditors, and background workers must adhere to **Rule 52**:
1. **Active Noise Root Pruning**: Mutate `dirs[:]` in-place during `os.walk` to prevent recursing into noise roots:
   ```python
   PRUNE = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache", "target", "dist", ".gemini"}
   for root_dir, dirs, files in os.walk(path):
       dirs[:] = [d for d in dirs if d not in PRUNE and not d.startswith(".")]
   ```
2. **Scan Depth Bounding**: Enforce a maximum traversal depth constraint ($\le 4$) relative to the search root.
3. **Subprocess Timeout Guard**: Declare bounded async subprocess timeouts to prevent background task CPU spin.

### Source References
- `AGENTS.md#L54`
- `src/harness/plugins/loader.py`

### Rule Reference
Governed by AGENTS.md Rule 52.
