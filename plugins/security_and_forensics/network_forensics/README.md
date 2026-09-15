# domain.network_forensics (v1.0.0)

Network traffic metadata analyzer, TLS cert inspector, and port security auditor

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/network_forensics` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `audit_port_configuration` | `(open_ports)` | Audit open ports and exposed network services against security best practices |
| `analyze_packet_summary` | `(flows)` | Analyze network flows (IP source/dest, protocol, packet sizes, flags) for port scans and DDoS signatures |
| `inspect_tls_certificate` | `(cert_info)` | Validate TLS/SSL certificate metadata (issuer, expiration, cipher suites) |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Network forensics, packet metadata analyzer, and port auditing plugin.

#### Functions

- `def audit_port_configuration(open_ports) -> dict[str, Any]` — Audit exposed network ports against security policies.
- `def analyze_packet_summary(flows) -> dict[str, Any]` — Analyze flow records for port scans, SYN floods, and abnormal traffic volumes.
- `def inspect_tls_certificate(cert_info) -> dict[str, Any]` — Audit TLS certificate validity, expiration window, and protocol version.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.network_forensics.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
