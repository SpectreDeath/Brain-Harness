# Quick Start Guide: `domain.security_scanner` (v1.0.0)

> Static code vulnerability scanner, secret detection, and dependency audit plugin

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`scan_secrets`**: Scan text or code content for leaked API keys, tokens, private keys, and passwords
- **`scan_code_vulnerabilities`**: Perform static AST and pattern analysis for security vulnerabilities (injection, eval, deserialization)
- **`audit_dependencies`**: Audit a requirements.txt or dependency list against known vulnerability patterns and unpinned packages

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.security_scanner.scan_secrets', {'content': '<content>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.security_scanner
harness plugin enable domain.security_scanner
```

## ⚡ Available Entrypoints & Skills
- **`scan_secrets(content: string)`**
  Scan text or code content for leaked API keys, tokens, private keys, and passwords
- **`scan_code_vulnerabilities(code: string)`**
  Perform static AST and pattern analysis for security vulnerabilities (injection, eval, deserialization)
- **`audit_dependencies(requirements_content: string)`**
  Audit a requirements.txt or dependency list against known vulnerability patterns and unpinned packages