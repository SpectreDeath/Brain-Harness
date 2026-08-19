# Quick Start Guide: `domain.k8s_manifest` (v1.0.0)

> Kubernetes manifest linter, resource request/limit validator, and pod security context checker

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`lint_k8s_manifest`**: Lint Kubernetes YAML manifests for missing labels, deprecations, and missing namespaces
- **`validate_resource_limits`**: Ensure CPU/memory requests and limits are explicitly declared on all container specs
- **`check_security_context`**: Audit securityContext (runAsNonRoot, allowPrivilegeEscalation, drop capabilities)

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.k8s_manifest.lint_k8s_manifest', {'manifest_yaml': '<manifest_yaml>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.k8s_manifest
harness plugin enable domain.k8s_manifest
```

## ⚡ Available Entrypoints & Skills
- **`lint_k8s_manifest(manifest_yaml: string)`**
  Lint Kubernetes YAML manifests for missing labels, deprecations, and missing namespaces
- **`validate_resource_limits(manifest_yaml: string)`**
  Ensure CPU/memory requests and limits are explicitly declared on all container specs
- **`check_security_context(manifest_yaml: string)`**
  Audit securityContext (runAsNonRoot, allowPrivilegeEscalation, drop capabilities)