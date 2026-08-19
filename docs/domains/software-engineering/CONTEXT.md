# Software Engineering Context

The Software Engineering context governs AST-aware code refactoring, architectural boundary linting, sandbox script execution, version control operations, and visual artifact reporting.

## Language

**Refactor Engine**:
An AST-manipulation pipeline that performs structural code transformations, seam consolidations, and import cleanup.
_Avoid_: Code editor, rewriter, mutator

**Architecture Linter**:
A static analysis tool that enforces module depth, detects cyclic dependencies, and verifies public seam invariants.
_Avoid_: Style checker, code reviewer, syntax linter

**Visual Brief**:
A self-contained, interactive HTML document rendered in temporary storage showing before-and-after topology diagrams and metrics.
_Avoid_: Diff report, summary page, HTML preview

**Runner**:
An isolated execution wrapper that runs test scripts and evaluates return codes without mutating host process state.
_Avoid_: Script launcher, terminal runner
