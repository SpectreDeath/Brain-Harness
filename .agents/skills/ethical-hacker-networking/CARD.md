# Skill Summary Card: `ethical-hacker-networking`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       ethical-hacker-networking                 │
│ Category:    security_and_forensics                    │
│ Invocation:  /ethical-hacker-networking                │
│ Trigger:     "analyze network traffic",                │
│              "audit open ports",                       │
│              "diagnose 7 layer network fault",         │
│              "decode tcp flags",                       │
│              "inspect cleartext exposure"              │
│ Version:     1.0.0                                     │
│ Provides:    "network_forensics_service"               │
│ Requires:    "python-dataclass-architect"              │
├────────────────────────────────────────────────────────┤
│ Target:      Protocol reconnaissance, tri-state recon, │
│              packet capture inspection, and 7-layer    │
│              fault isolation for ethical hacking.      │
└────────────────────────────────────────────────────────┘
```

---

## 5-Stage Operational Progression

| Stage | Focus Area | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Protocol Encapsulation** | Subnet masking, TTL decrementing | Hop traversal list & subnet plan | Valid broadcast boundaries; hop latency mapped |
| **2. Tri-State Recon** | SYN vs Connect vs UDP scans | Tri-state port catalog | Explicit open/closed/filtered categorization |
| **3. Packet Dissection** | Frame & stream reconstruction | Flow anomaly & cleartext report | Identify unencrypted L7 credentials & anomalous flags |
| **4. Firewall & Tunneling** | Stateful conntrack vs stateless ACLs | Perimeter & tunnel evaluation | Distinguish L7 proxy forwarding vs L3 VPN tunnels |
| **5. 7-Layer Isolation** | Systematic bottom-up diagnostic chain | 7-layer diagnostic report | Isolate earliest failing OSI layer with remediation |

---

## Quick Reference Commands

| Objective | Command / Tool Call |
|---|---|
| **Hop Discovery** | `analyze_traceroute_hops(raw_output)` |
| **Port Recon** | `evaluate_port_states(scan_results)` |
| **TCP Flag Decode** | `decode_tcp_flags(flags_hex)` |
| **Cleartext Exposure** | `classify_cleartext_exposure(protocol, port)` |
| **7-Layer Diagnostic** | `run_7layer_diagnostic_chain(target, port)` |
| **Subnet Geometry** | `calculate_subnet_geometry(cidr)` |
| **Visual Brief** | `generate_visual_brief(output_path)` |
| **Headless CLI** | `harness network [traceroute|scan-ports|decode-flags|subnet]` |
| **Skill Dispatcher** | `python scripts/network_diagnostics.py --help` |

---

## Mandatory Invariants Checklist

- [ ] **Tri-State Categorization Invariant**: Never conflate dropped packets with closed ports; dropped probes must be classified as `filtered`.
- [ ] **7-Layer Diagnostic Order**: Always evaluate network faults sequentially from Layer 1 through Layer 7; never skip lower-layer connectivity checks.
- [ ] **Cleartext Defense Invariant**: Administrative credentials must never traverse unencrypted protocols (HTTP, Telnet) in production networks.
- [ ] **Slotted Data Structure Standard**: All packet inspection, traceroute hop, and subnet records must use slotted and frozen dataclass schemas.
- [ ] **Subnet Boundary Integrity**: Subnet geometry calculations must explicitly assert valid host bit allocations and broadcast boundaries.

