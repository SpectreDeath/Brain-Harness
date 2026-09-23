---
name: ethical-hacker-networking
description: Execute protocol-level network reconnaissance, packet capture dissection, tri-state port evaluation, TCP flag analysis, and systematic 7-layer fault isolation. Do not use for generic web browsing, unauthorized penetration attacks, or unauthenticated Wi-Fi cracking.
version: 1.0.0
category: security_and_forensics
---

# Ethical Hacker Networking

A production-grade agent skill for protocol-level network reconnaissance, packet capture inspection, tri-state port evaluation, TCP flag state machine analysis, and systematic 7-layer fault isolation.

---

## Workflow: 5-Stage Protocol Operations

### Stage 1: Protocol Encapsulation & Subnet Geometry (Shu)
1. **Analyze Subnet Mask**:
   - Determine network prefix $/n$, host capacity ($2^{32-n} - 2$), broadcast address, and default gateway.
   - Assert host addresses reside within the valid broadcast domain before initiating probes.
2. **Hop Discovery via TTL Decrementing**:
   - Parse traceroute hop sequences (`analyze_traceroute_hops`).
   - Identify intermediate routers decrementing TTL to zero and generating ICMP Time Exceeded (Type 11, Code 0).
   - Flag anomalous high-latency hops, routing loops (repeating IPs), or filtering middleboxes (asterisks).

### Stage 2: Tri-State Port Reconnaissance & Flag State Analysis (Shu)
1. **Evaluate Tri-State Port Reachability**:
   - Classify scan responses into strict tri-state categories (`evaluate_port_states`):
     - `open`: SYN/ACK received; service actively listening.
     - `closed`: RST received; host active, port unallocated.
     - `filtered`: No response or ICMP Type 3 Unreachable; dropped by stateful firewall.
2. **Decode TCP Control Flags**:
   - Deconstruct TCP header bitmasks (`decode_tcp_flags`).
   - Detect scanning probes or firewall evasion maneuvers:
     - `SYN-FIN` (0x03): Illegal flag combination used for evasion.
     - `Null Scan` (0x00): All flags cleared; probes RFC 793 compliance.
     - `Xmas Scan` (0x29): FIN, PSH, URG flags asserted.

### Stage 3: Packet Capture Dissection & Cleartext Exposure (Ha)
1. **Dissect Protocol Streams**:
   - Inspect frame sequences and protocol headers from flow summaries (`analyze_packet_summary`).
   - Correlate bidirectional TCP stream sequences ($seq$, $ack$) to verify proper handshake completion.
2. **Classify Cleartext Protocol Exposures**:
   - Evaluate protocol and port combinations (`classify_cleartext_exposure`):
     - Port 80 (HTTP), Port 21 (FTP), Port 23 (Telnet), Port 110 (POP3), Port 143 (IMAP).
   - Flag exposure of credentials, session cookies, and sensitive payloads to passive Layer 2 sniffers.

### Stage 4: Firewall & Tunnel Traversal Architecture (Ha)
1. **Distinguish Middlebox Architecture**:
   - Contrast stateful firewall connection tracking (`conntrack`) vs stateless Access Control Lists (ACLs).
   - Differentiate Layer 7 proxies (terminating application streams, injecting `X-Forwarded-For`) from Layer 3 VPN tunnels (encapsulating IP datagrams into virtual TUN/TAP interfaces).
2. **Audit IPv6 Dual-Stack Exposure**:
   - Check if IPv6 Neighbor Discovery Protocol (NDP) or link-local scopes (`fe80::/10`) bypass IPv4 firewall rules.

### Stage 5: Systematic 7-Layer Fault Isolation (Ri)
1. **Execute Layer-by-Layer Verification**:
   - Execute deterministic diagnostic chain across the OSI stack (`run_7layer_diagnostic_chain`):
     - **Layer 1 (Physical)**: Interface link status and PHY negotiation.
     - **Layer 2 (Data Link)**: ARP/NDP table resolution and MAC address mapping.
     - **Layer 3 (Network)**: Local IP assignment and default gateway ICMP reachability.
     - **Layer 4 (Transport)**: TCP socket handshake on target service port.
     - **Layer 7 (Application/DNS)**: DNS resolution query, TLS handshake, and HTTP endpoint status.
2. **Emit Remediations**:
   - Provide concrete command strings and mitigation guidance for the earliest failing layer.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every network audit or recon session compiles an interactive HTML visual brief in `%TEMP%` displaying hop topologies, tri-state port matrices, TCP flag status, and 7-layer diagnostic trees.

### 2. The Mandatory Checkpoint Pillar
The agent must never execute active network scans or mutate firewall configurations without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent ungrounded scan assumptions, cleartext exposure in transit, and unordered troubleshooting chaos.

---

## Anti-Patterns

- **False Closed Assumption on Packet Drops** — Misinterpreting a dropped probe or timeout as a closed port rather than a filtered port protected by a firewall.
- **Unencrypted Administrative Protocols** — Transmitting management credentials over cleartext protocols (HTTP, Telnet) susceptible to passive packet sniffing.
- **IPv6 Dual-Stack Security Blindspot** — Enforcing stringent IPv4 perimeter firewalls while leaving IPv6 interfaces unmonitored and unfiltered.
- **Unordered Random Troubleshooting** — Diagnosing application-layer HTTP errors before verifying Layer 3 routing or Layer 4 transport connectivity.
- **Stateless Firewall Rule Asymmetry** — Configuring inbound stateless rules without corresponding return-path outbound rules for ephemeral ports.

---

## Diagnostic Scorecard

| Assessment Dimension | Score 1 (Deficient) | Score 3 (Competent) | Score 5 (Exemplary) |
|---|---|---|---|
| **Recon Precision** | Binary open/closed assumption; misses firewall presence | Accurately identifies filtered ports but relies on noisy scans | Tri-state classification with stealth SYN and evasion flag detection |
| **Protocol Forensics** | Unable to interpret raw packet headers or Wireshark streams | Filters TCP flows; identifies common cleartext passwords | Full stream reconstruction, TCP flag decoding, and timing analysis |
| **Troubleshooting Methodology** | Randomly tries application restart or reboot | Tests ping and curl without structured isolation | Sequential 7-layer root cause identification with isolated step reports |
| **Architecture Defense** | No awareness of state tables or proxy vs VPN seams | Knows basic firewall port blocking | Evaluates stateful conntrack tables, dual-stack IPv6, and TLS posture |
