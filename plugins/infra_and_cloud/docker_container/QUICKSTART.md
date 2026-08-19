# Quick Start Guide: `domain.docker_container` (v1.0.0)

> Docker container linter, multi-stage Dockerfile generator, and container security auditor

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`lint_dockerfile`**: Lint Dockerfile for root user vulnerabilities, missing cache flags, latest tag usage, and security antipatterns
- **`generate_dockerfile`**: Generate an optimized, production-ready multi-stage Dockerfile for a given language/runtime
- **`audit_container_security`**: Audit container runtime configuration (privileged mode, read-only rootfs, capabilities, volume mounts)

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.docker_container.lint_dockerfile', {'dockerfile_content': '<dockerfile_content>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.docker_container
harness plugin enable domain.docker_container
```

## ⚡ Available Entrypoints & Skills
- **`lint_dockerfile(dockerfile_content: string)`**
  Lint Dockerfile for root user vulnerabilities, missing cache flags, latest tag usage, and security antipatterns
- **`generate_dockerfile(runtime: string, entrypoint_command: string, port: integer)`**
  Generate an optimized, production-ready multi-stage Dockerfile for a given language/runtime
- **`audit_container_security(container_config: object)`**
  Audit container runtime configuration (privileged mode, read-only rootfs, capabilities, volume mounts)