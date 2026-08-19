# Quick Start Guide: `domain.network_forensics` (v1.0.0)

> Network traffic metadata analyzer, TLS cert inspector, and port security auditor

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`audit_port_configuration`**: Audit open ports and exposed network services against security best practices
- **`analyze_packet_summary`**: Analyze network flows (IP source/dest, protocol, packet sizes, flags) for port scans and DDoS signatures
- **`inspect_tls_certificate`**: Validate TLS/SSL certificate metadata (issuer, expiration, cipher suites)

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.network_forensics.audit_port_configuration', {'open_ports': '<open_ports>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.network_forensics
harness plugin enable domain.network_forensics
```

## ⚡ Available Entrypoints & Skills
- **`audit_port_configuration(open_ports: array)`**
  Audit open ports and exposed network services against security best practices
- **`analyze_packet_summary(flows: array)`**
  Analyze network flows (IP source/dest, protocol, packet sizes, flags) for port scans and DDoS signatures
- **`inspect_tls_certificate(cert_info: object)`**
  Validate TLS/SSL certificate metadata (issuer, expiration, cipher suites)