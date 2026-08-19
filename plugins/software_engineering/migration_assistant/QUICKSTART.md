# Quick Start Guide: `domain.migration_assistant` (v1.0.0)

> Python framework migration checker (Pydantic v1 to v2, Python 3.10+ union syntax, unittest to pytest)

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`check_pydantic_v2_readiness`**: Scan Python code for deprecated Pydantic v1 patterns (class Config, regex field parameter, validator decorator)
- **`check_python_version_compat`**: Scan for deprecated legacy Python patterns (typing.Union instead of |, typing.Optional, distutils)

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.migration_assistant.check_pydantic_v2_readiness', {'code': '<code>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.migration_assistant
harness plugin enable domain.migration_assistant
```

## ⚡ Available Entrypoints & Skills
- **`check_pydantic_v2_readiness(code: string)`**
  Scan Python code for deprecated Pydantic v1 patterns (class Config, regex field parameter, validator decorator)
- **`check_python_version_compat(code: string)`**
  Scan for deprecated legacy Python patterns (typing.Union instead of |, typing.Optional, distutils)