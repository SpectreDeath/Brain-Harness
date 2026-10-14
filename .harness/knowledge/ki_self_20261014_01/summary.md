# Skill CLI Script Single-File Self-Containment and Language Server Isolation

## Epistemic Introspection & Root Cause Analysis

When factoring complex Python scripts inside agent skill packages (`.agents/skills/<name>/scripts/`), developers and agents often attempt to decompose files into sibling modules (e.g. `deepen_cycle.py` importing `deepen_ops.py`). 

In modern IDE environments (VS Code, Cursor, Antigravity) governed by project-level type checkers (Pyright, Mypy), the project source root is conventionally configured to `src/` (via `pyproject.toml`). Because `.agents/skills/` sits outside `src/`, language servers cannot resolve relative or bare sibling imports without explicit `sys.path` tampering or workspace-wide package restructuring. This manifests as persistent `Cannot find module` or `F821 Undefined name` diagnostics.

## Actionable Invariant & Architectural Standard

1. **Single-File Self-Containment**: CLI orchestration scripts authored under `.agents/skills/<name>/scripts/` should remain self-contained single-file programs.
2. **Compact Command Dispatch**: Utilize concise argument subparser structures and dispatch dictionaries (`dispatch[args.subcommand](args)`) to stay strictly within the $\le 200$ LOC limit (Rule 11).
3. **Streamlined Subprocess Execution**: Keep subprocess runners compact (`subprocess.run(["git", "add"] + args.files)`) and avoid redundant abstraction layers for simple sequential CLI steps.
4. **Zero Sibling Drift**: Eliminating detached helper files prevents import path fragility across heterogeneous working directories and test proactors.

## Grounded Evidence & Isnād Lineage

- **Primary Commit**: `6e43ba7` (`fix(skills): consolidate deepen_cycle.py to single-file <=190 LOC and standardize CONTEXT-MAP.md markdown`).
- **Empirical Result**: Removed `deepen_ops.py`, reducing `deepen_cycle.py` to 189 lines with 0 Pyright errors and 100% test contract pass rate.
