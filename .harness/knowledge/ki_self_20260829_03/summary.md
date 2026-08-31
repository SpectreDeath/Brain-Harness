# KI: Transactional Git Checkpoints & In-Flight Syntax Diagnostic Self-Repair

## Operational Summary
Autonomous agent code modifications require two complementary runtime safety nets: transactional workspace rollbacks to prevent dirty state from failed executions, and immediate in-flight syntax verification to catch bracket mismatches and syntax errors before turn finalization.

## Architecture Invariants
1. **Transactional Context & Git Checkpoints**:
   - Tool execution executes inside `async with self.context.transaction() as tx:`.
   - On tool success: Invokes `FilesystemGitService.commit_transaction(...)` creating an atomic checkpoint commit.
   - On error or exception: Calls `await tx.dispose()` and `FilesystemGitService.rollback_transaction()`, restoring working tree files to their pre-step state.
2. **In-Flight Syntax Validation**:
   - File edits immediately invoke `ArchLinterService.lint_file(path)`.
   - Any syntax error (`ast.parse`), JSON parse failure, or bracket imbalance is injected directly into `observation["lint_diagnostics"]`.
   - The LLM receives the error immediately in the next step, enabling instantaneous self-repair before closing the task.

## Key Code References
- ReAct Loop: [`src/harness/agent/react.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/agent/react.py)
- Git Transaction Service: [`src/harness/services/filesystem_git.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/services/filesystem_git.py)
- Architecture Linter: [`src/harness/services/arch_linter.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/services/arch_linter.py)
- Unit Tests: [`tests/test_git_transactional.py`](file:///D:/GitHub/projects/Brain%20Harness/tests/test_git_transactional.py), [`tests/test_linter_loop.py`](file:///D:/GitHub/projects/Brain%20Harness/tests/test_linter_loop.py)
