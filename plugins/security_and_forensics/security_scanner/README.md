# domain.security_scanner (v1.0.0)

Static code vulnerability scanner, secret detection, and dependency audit plugin

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/security_scanner` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `scan_secrets` | `(content)` | Scan text or code content for leaked API keys, tokens, private keys, and passwords |
| `scan_code_vulnerabilities` | `(code)` | Perform static AST and pattern analysis for security vulnerabilities (injection, eval, deserialization) |
| `audit_dependencies` | `(requirements_content)` | Audit a requirements.txt or dependency list against known vulnerability patterns and unpinned packages |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Security Scanner plugin — secrets detection, AST vulnerability scan, and dependency audit.

#### Functions

- `def scan_secrets(content) -> dict[str, Any]` — Scan string content for exposed secrets, tokens, and credentials.
- `def scan_code_vulnerabilities(code) -> dict[str, Any]` — Analyze Python code for dangerous AST constructs (eval, exec, subprocess, yaml, pickle).
- `def audit_dependencies(requirements_content) -> dict[str, Any]` — Audit requirements.txt for unpinned versions or vulnerable packages.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.security_scanner.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
