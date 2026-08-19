# Quick Start Guide: `domain.refactor_engine` (v1.0.0)

> Python AST refactoring engine, dead/unused code identifier, and function extraction tool

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`find_unused_functions`**: Find declared functions in Python source code that are never called internally within the module
- **`extract_function_preview`**: Preview extracting a block of lines into a new helper function with parameter discovery

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.refactor_engine.find_unused_functions', {'code': '<code>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.refactor_engine
harness plugin enable domain.refactor_engine
```

## ⚡ Available Entrypoints & Skills
- **`find_unused_functions(code: string)`**
  Find declared functions in Python source code that are never called internally within the module
- **`extract_function_preview(code: string, start_line: integer, end_line: integer, new_func_name: string)`**
  Preview extracting a block of lines into a new helper function with parameter discovery