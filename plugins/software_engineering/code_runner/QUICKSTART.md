# Quick Start Guide: `plugin.code_runner` (v1.0.0)

> Sandboxed Python REPL and script execution engine with output capture and timeout protection

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`python_exec`**: Execute a Python code block in a sandboxed subprocess and capture stdout, stderr, and return code
- **`python_eval`**: Evaluate a Python expression and return the printed string representation of the result
- **`run_temp_script`**: Execute a standalone Python script file with arguments and return output

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.code_runner.python_exec', {'code': '<code>', 'timeout': '<timeout>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.code_runner
harness plugin enable plugin.code_runner
```

## ⚡ Available Entrypoints & Skills
- **`python_exec(code: string, timeout: number)`**
  Execute a Python code block in a sandboxed subprocess and capture stdout, stderr, and return code
- **`python_eval(expression: string, timeout: number)`**
  Evaluate a Python expression and return the printed string representation of the result
- **`run_temp_script(script_content: string, args: array, timeout: number)`**
  Execute a standalone Python script file with arguments and return output