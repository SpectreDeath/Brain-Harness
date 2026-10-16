# domain.network_forensics (v1.0.0)

Network traffic metadata analyzer, TLS cert inspector, tri-state port security auditor, and 7-layer fault isolation engine

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/network_forensics` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.network_forensics` |
| Dependencies Required | None |

---

## Architecture & Subpackage Decomposition

The Network Forensics plugin is partitioned into specialized domain submodules under `engine/`, unifying network reconnaissance and forensic diagnostics while eliminating code duplication:

- **[engine/models.py](engine/models.py)**: Slotted and frozen domain dataclasses (`HopAnalysisResult`, `PortScanEvaluation`, `TCPFlagAnalysis`, `LayerDiagnosticResult`) enforcing strict immutability (Rule 12).
- **[engine/ports.py](engine/ports.py)**: Dangerous port configuration auditing (`audit_port_configuration`) and tri-state port reachability evaluation (`evaluate_port_states_data`, `evaluate_port_states_dict`).
- **[engine/packets.py](engine/packets.py)**: Packet flow anomaly detection (`analyze_packet_summary`), TCP flag bitmask decoding (`decode_tcp_flags_data`, `decode_tcp_flags_dict`), and TLS certificate validation (`inspect_tls_certificate`).
- **[engine/traceroute.py](engine/traceroute.py)**: Traceroute hop parsing (`parse_traceroute_hops`, `analyze_traceroute_dict`) with TTL-decrementing discovery, filtered hop detection, and latency anomaly discovery.
- **[engine/diagnostics.py](engine/diagnostics.py)**: Bitwise IPv4 CIDR subnet geometry calculation (`calculate_subnet_geometry`), cleartext service risk analysis (`classify_cleartext_exposure_dict`), and systematic 7-layer fault isolation chain (`run_7layer_diagnostic_chain_dict`).
- **[engine/brief.py](engine/brief.py)**: Interactive HTML visual brief generator (`generate_visual_brief`) with stateDiagram and flowchart Mermaid visualizations.
- **[engine/core.py](engine/core.py)**: Coordinator `NetworkForensicsEngine` implementing the slotted engine interface.
- **[main.py](main.py)**: Lean coordinator facade (~190 lines) re-exporting public symbols, defining manifest tool functions, implementing `NetworkForensicsPlugin(HarnessPlugin, NetworkForensicsService)`, and exporting module singleton `plugin` (Rule 45).

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `audit_port_configuration` | `(open_ports)` | Audit open ports and exposed network services against security best practices |
| `analyze_packet_summary` | `(flows)` | Analyze network flows (IP source/dest, protocol, packet sizes, flags) for port scans and DDoS signatures |
| `inspect_tls_certificate` | `(cert_info)` | Validate TLS/SSL certificate metadata (issuer, expiration, cipher suites) |
| `analyze_traceroute_hops` | `(raw_output)` | Parse traceroute output, identify intermediate TTL-decrementing hops, and detect latency anomalies or routing loops |
| `evaluate_port_states` | `(scan_results, port_probes)` | Classify port scan findings into tri-state reachability: open (SYN/ACK), closed (RST), or filtered (drop/timeout) |
| `decode_tcp_flags` | `(flags_hex)` | Decode hexadecimal TCP flags, evaluate handshake semantics, and detect scan evasion signatures (Null, Xmas, SYN-FIN) |
| `classify_cleartext_exposure` | `(protocol, port)` | Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities for HTTP, Telnet, FTP, etc. |
| `run_7layer_diagnostic_chain` | `(target, port)` | Execute systematic 7-layer network fault isolation chain from physical to application layer |
| `calculate_subnet_geometry` | `(cidr)` | Calculate bitwise network address, broadcast address, and host capacity for an IPv4 CIDR prefix |
| `generate_visual_brief` | `(output_path)` | Generate interactive HTML visual brief with Mermaid diagrams in %TEMP% |
---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.network_forensics.main import plugin, NetworkForensicsEngine

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)

# Direct engine usage
engine = NetworkForensicsEngine()
res = engine.calculate_subnet_geometry("192.168.1.0/24")
print(res.usable_host_range)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), single-seam IoC resolution (Rule 49 & 58), single-source plugin exports (Rule 45), and bounded directory traversal (Rule 52).
