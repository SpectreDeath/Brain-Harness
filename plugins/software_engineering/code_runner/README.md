# plugin.code_runner (v1.0.0)

Sandboxed Python REPL and script execution engine with output capture and timeout protection

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/code_runner` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.code_runner` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `python_exec` | `(code, timeout)` | Execute a Python code block in a sandboxed subprocess and capture stdout, stderr, and return code |
| `python_eval` | `(expression, timeout)` | Evaluate a Python expression and return the printed string representation of the result |
| `run_temp_script` | `(script_content, args, timeout)` | Execute a standalone Python script file with arguments and return output |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Sandboxed Python code runner and REPL plugin for Brain Harness.

#### Classes

- `class CodeRunnerPlugin` — Harness Plugin providing sandboxed Python code execution and expression evaluation.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def exec_python(code, timeout) -> PythonExecResult`
  - `def exec_python_async(code, timeout) -> PythonExecResult`
  - `def eval_python(expression, timeout) -> PythonEvalResult`
  - `def eval_python_async(expression, timeout) -> PythonEvalResult`
  - `def run_temp_script(script_content, args, timeout) -> ScriptRunResult`
  - `def run_temp_script_async(script_content, args, timeout) -> ScriptRunResult`


#### Functions

- `def python_exec(code, timeout) -> dict[str, Any]` — Execute a block of Python code in an isolated subprocess.
- `def python_eval(expression, timeout) -> dict[str, Any]` — Evaluate a single Python expression and capture the output.
- `def run_temp_script(script_content, args, timeout) -> dict[str, Any]` — Write script to a temp file, execute it with arguments, and clean up.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.code_runner.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
