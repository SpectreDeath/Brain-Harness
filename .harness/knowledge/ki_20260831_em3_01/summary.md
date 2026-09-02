# Pre-Execution AST Security Visitor for Dynamic Code Sandboxing

## Context
When an AI agent or skill engine generates and executes arbitrary Python code, relying solely on post-execution exception handling or runtime wrappers allows malicious or hallucinated code to escape container boundaries, invoke unmetered OS processes, or inspect private file systems.

## Distilled Learning
Implement a two-stage defense-in-depth static gating pattern:
1. **Pre-Execution AST Inspection**:
   - Parse source code with `ast.parse()`.
   - Traverse the Abstract Syntax Tree using `ast.NodeVisitor` subclass (`ASTSecurityScanner`).
   - Intercept `ast.Import` and `ast.ImportFrom` against a configurable `BLOCKED_MODULES` set (`os`, `sys`, `subprocess`, `shutil`, `socket`, `ctypes`, `builtins`, `importlib`, `pickle`, `shelve`, `tempfile`).
   - Intercept `ast.Call` nodes against `BLOCKED_FUNCTIONS` (`eval`, `exec`, `compile`, `__import__`, `open`, `getattr`, `setattr`, `delattr`) and attributes (`system`, `popen`, `spawn`, `execve`).
2. **Granular Violation Reporting**:
   - Yield structured `SecurityViolation(line, column, rule, message, severity)` items with explicit line coordinates for automated agent self-correction.
3. **Execution Gating**:
   - Abort execution immediately if `is_safe == False` before passing code to `asteval` or process executors.

## Triggers & Seam Choices
- **Trigger**: Prior to executing any dynamic Python skill, tool invocation, or user-supplied script.
- **Seam Choice**: Integrate inside `ArchLinterService` or `StepExecutionEngine` as a mandatory pre-flight validator before executing shell or Python processes.
