# Quick Start Guide: `domain.arch_linter` (v1.0.0)

> Codebase coupling/cohesion analyzer, circular import detector, and clean architecture boundary verifier

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`detect_circular_imports`**: Scan a Python directory, build the internal module import graph, and detect circular import cycles
- **`compute_module_coupling`**: Compute afferent (Ca) and efferent (Ce) coupling and instability metrics for package modules
- **`verify_clean_boundaries`**: Verify that inner architectural layers (e.g. kernel, domain) do not import from outer layers (e.g. ui, cli)

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.arch_linter.detect_circular_imports', {'root_path': '<root_path>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.arch_linter
harness plugin enable domain.arch_linter
```

## ⚡ Available Entrypoints & Skills
- **`detect_circular_imports(root_path: string)`**
  Scan a Python directory, build the internal module import graph, and detect circular import cycles
- **`compute_module_coupling(root_path: string)`**
  Compute afferent (Ca) and efferent (Ce) coupling and instability metrics for package modules
- **`verify_clean_boundaries(root_path: string, layer_hierarchy: array)`**
  Verify that inner architectural layers (e.g. kernel, domain) do not import from outer layers (e.g. ui, cli)