# Quick Start Guide: `domain.ci_pipeline` (v1.0.0)

> CI/CD pipeline workflow linter, circular job dependency detector, and action security auditor

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`validate_github_actions_workflow`**: Validate GitHub Actions YAML workflow structure (name, on trigger, jobs, permissions)
- **`find_circular_job_dependencies`**: Detect cyclic or broken 'needs:' dependencies across pipeline jobs
- **`audit_action_pins`**: Audit third-party GitHub Actions for mutable tags (e.g. @v3) vs immutable commit SHA pins

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.ci_pipeline.validate_github_actions_workflow', {'workflow_yaml': '<workflow_yaml>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.ci_pipeline
harness plugin enable domain.ci_pipeline
```

## ⚡ Available Entrypoints & Skills
- **`validate_github_actions_workflow(workflow_yaml: string)`**
  Validate GitHub Actions YAML workflow structure (name, on trigger, jobs, permissions)
- **`find_circular_job_dependencies(jobs: object)`**
  Detect cyclic or broken 'needs:' dependencies across pipeline jobs
- **`audit_action_pins(workflow_yaml: string)`**
  Audit third-party GitHub Actions for mutable tags (e.g. @v3) vs immutable commit SHA pins