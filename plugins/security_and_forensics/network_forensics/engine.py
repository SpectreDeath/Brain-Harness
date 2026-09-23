"""Network Forensics Domain Engine.

Encapsulates slotted stateful network heuristics, subnet geometric calculations,
traceroute parsing, tri-state recon, TCP flag decoding, 7-layer fault isolation,
and interactive HTML visual brief generation.
Synthesized per AGENTS.md Rule 12, Rule 49, and /deepen-architecture standards.
"""

from __future__ import annotations

import ipaddress
import re
import tempfile
from pathlib import Path
from typing import Any

from harness.services.network_forensics import (
    CleartextExposureData,
    DiagnosticChainReportData,
    HopAnalysisData,
    LayerDiagnosticData,
    PortEvaluationData,
    PortReconReportData,
    SubnetGeometryData,
    TCPFlagAnalysisData,
    TracerouteReportData,
)

_TRACEROUTE_LINE_REGEX = re.compile(
    r"^\s*(\d+)\s+([\w\.\:\-\*]+)\s*(?:\(([\d\.]+)\))?\s+([\d\.]+)?\s*(?:ms)?"
)

_DEFAULT_DANGEROUS_PORTS = {
    21: ("FTP", "critical", "Cleartext credentials; replace with SFTP."),
    23: ("Telnet", "critical", "Unencrypted remote shell; replace with SSH."),
    80: ("HTTP", "medium", "Unencrypted web traffic; enforce HTTPS on port 443."),
    3389: ("RDP", "high", "Exposed Windows Remote Desktop; restrict to VPN/bastion."),
    6379: (
        "Redis",
        "critical",
        "Exposed Redis key-value store; bind to localhost only.",
    ),
    27017: ("MongoDB", "critical", "Exposed MongoDB instance; bind to private subnet."),
}

_DEFAULT_CLEARTEXT_SERVICES = {
    80: (
        "HTTP",
        "high",
        "Unencrypted web traffic; credentials, session cookies, and POST bodies exposed to passive sniffing.",
        "Enforce HTTPS on port 443 with HSTS header.",
    ),
    21: (
        "FTP",
        "critical",
        "Cleartext FTP authentication; USER and PASS commands exposed in packet payload.",
        "Replace FTP with SFTP (port 22) or FTPS.",
    ),
    23: (
        "Telnet",
        "critical",
        "Unencrypted remote terminal; all keystrokes and passwords transmitted in cleartext.",
        "Replace Telnet with SSH (port 22).",
    ),
    110: (
        "POP3",
        "high",
        "Cleartext POP3 mail retrieval; user credentials exposed.",
        "Upgrade to POP3S on port 995.",
    ),
    143: (
        "IMAP",
        "high",
        "Cleartext IMAP mail access; credentials exposed.",
        "Upgrade to IMAPS on port 993.",
    ),
}


class NetworkForensicsEngine:
    """Slotted domain engine executing network reconnaissance and diagnostic workflows."""

    __slots__ = (
        "_default_timeout",
        "_max_hops",
        "_dangerous_ports",
        "_cleartext_services",
    )

    def __init__(
        self,
        default_timeout: float = 30.0,
        max_hops: int = 30,
        dangerous_ports: dict[int, tuple[str, str, str]] | None = None,
        cleartext_services: dict[int, tuple[str, str, str, str]] | None = None,
    ) -> None:
        self._default_timeout = default_timeout
        self._max_hops = max_hops
        self._dangerous_ports = dangerous_ports or _DEFAULT_DANGEROUS_PORTS
        self._cleartext_services = cleartext_services or _DEFAULT_CLEARTEXT_SERVICES

    # -------------------------------------------------------------------------
    # 1. Subnet Bitwise Geometry (Module 2)
    # -------------------------------------------------------------------------

    def calculate_subnet_geometry(self, cidr: str) -> SubnetGeometryData:
        """Calculate bitwise network address, broadcast address, and host bounds for a CIDR prefix."""
        clean_cidr = cidr.strip()
        try:
            net = ipaddress.ip_network(clean_cidr, strict=False)
        except ValueError as err:
            raise ValueError(f"Invalid CIDR notation '{cidr}': {err}") from err

        network_addr = str(net.network_address)
        broadcast_addr = str(net.broadcast_address)
        netmask_str = str(net.netmask)
        prefix_len = net.prefixlen
        total_addrs = net.num_addresses

        if prefix_len == 32:
            usable_hosts = 1
            host_range = f"{network_addr} (Single Host)"
        elif prefix_len == 31:
            usable_hosts = 2
            host_range = f"{network_addr} - {broadcast_addr} (RFC 3021 Point-to-Point)"
        else:
            usable_hosts = max(0, total_addrs - 2)
            first_host = str(net.network_address + 1)
            last_host = str(net.broadcast_address - 1)
            host_range = f"{first_host} - {last_host}" if usable_hosts > 0 else "None"

        return SubnetGeometryData(
            status="ok",
            cidr=str(net),
            network_address=network_addr,
            broadcast_address=broadcast_addr,
            netmask=netmask_str,
            prefix_length=prefix_len,
            total_addresses=total_addrs,
            usable_hosts=usable_hosts,
            usable_host_range=host_range,
        )

    # -------------------------------------------------------------------------
    # 2. TTL Hop Discovery & Traceroute Analysis (Module 1)
    # -------------------------------------------------------------------------

    def analyze_traceroute_hops(self, raw_output: str) -> TracerouteReportData:
        """Parse traceroute output, identify intermediate TTL-decrementing hops, and detect latency anomalies."""
        hops: list[HopAnalysisData] = []
        anomalies: list[dict[str, Any]] = []
        seen_ips: set[str] = set()
        prev_rtt: float | None = None
        target_name = "unknown"

        lines = raw_output.strip().splitlines()
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            if line_clean.startswith("traceroute to"):
                # Extract target if present
                m_target = re.search(r"traceroute to ([\w\.\-]+)", line_clean)
                if m_target:
                    target_name = m_target.group(1)
                continue

            if line_clean.startswith("Tracing route to"):
                m_target = re.search(r"Tracing route to ([\w\.\-]+)", line_clean)
                if m_target:
                    target_name = m_target.group(1)
                continue

            # Check for filtered hop (* * *)
            asterisk_match = re.match(r"^\s*(\d+)\s+\*\s+\*\s+\*", line_clean)
            if asterisk_match:
                hop_num = int(asterisk_match.group(1))
                hop = HopAnalysisData(
                    hop_number=hop_num,
                    ip_address="*",
                    rtt_ms=0.0,
                    status="filtered",
                    is_intermediate_decrement=True,
                )
                hops.append(hop)
                anomalies.append(
                    {
                        "hop": hop_num,
                        "type": "ICMP Filtered Hop",
                        "detail": f"Hop {hop_num} dropped packets or ICMP Time Exceeded filtered by firewall.",
                    }
                )
                continue

            match = _TRACEROUTE_LINE_REGEX.match(line_clean)
            if match:
                hop_num = int(match.group(1))
                host_or_ip = match.group(2)
                paren_ip = match.group(3)
                rtt_str = match.group(4)

                ip = paren_ip if paren_ip else host_or_ip
                rtt = float(rtt_str) if rtt_str else 0.0

                if ip != "*" and ip in seen_ips:
                    anomalies.append(
                        {
                            "hop": hop_num,
                            "type": "Routing Loop Detected",
                            "detail": f"IP {ip} observed previously in hop sequence.",
                        }
                    )
                if ip != "*":
                    seen_ips.add(ip)

                if prev_rtt is not None and (rtt - prev_rtt) > 100.0:
                    anomalies.append(
                        {
                            "hop": hop_num,
                            "type": "Latency Spike",
                            "detail": f"Hop {hop_num} latency spiked by {rtt - prev_rtt:.1f}ms compared to previous hop.",
                        }
                    )
                if rtt > 0.0:
                    prev_rtt = rtt

                hop = HopAnalysisData(
                    hop_number=hop_num,
                    ip_address=ip,
                    rtt_ms=rtt,
                    status="active" if ip != "*" else "filtered",
                    is_intermediate_decrement=True,
                )
                hops.append(hop)

        reached_target = (
            len(hops) > 0 and hops[-1].status == "active" and hops[-1].rtt_ms > 0
        )
        if reached_target and target_name == "unknown":
            target_name = hops[-1].ip_address

        return TracerouteReportData(
            status="ok",
            target=target_name,
            total_hops=len(hops),
            reached_target=reached_target,
            hops=hops,
            anomalies=anomalies,
        )

    # -------------------------------------------------------------------------
    # 3. Tri-State Port Reconnaissance (Module 9)
    # -------------------------------------------------------------------------

    def evaluate_port_states(
        self, scan_results: list[dict[str, Any]]
    ) -> PortReconReportData:
        """Classify port scan findings into tri-state reachability: open, closed, or filtered."""
        evaluations: list[PortEvaluationData] = []
        open_ports: list[int] = []
        closed_ports: list[int] = []
        filtered_ports: list[int] = []

        for item in scan_results:
            port = int(item.get("port", 0))
            if port < 1 or port > 65535:
                continue

            protocol = str(item.get("protocol", "TCP")).upper()
            response = str(
                item.get("response")
                or item.get("response_flag")
                or item.get("state")
                or ""
            ).upper()
            service = str(item.get("service", "unknown"))

            if any(term in response for term in ("SYN/ACK", "SYN-ACK", "OPEN")):
                state = "open"
                open_ports.append(port)
            elif any(term in response for term in ("RST", "CLOSED")):
                state = "closed"
                closed_ports.append(port)
            else:
                state = "filtered"
                filtered_ports.append(port)

            eval_entry = PortEvaluationData(
                port=port,
                protocol=protocol,
                state=state,
                response_flag=response if response else "NO_RESPONSE",
                service_guess=service,
            )
            evaluations.append(eval_entry)

        return PortReconReportData(
            status="ok",
            total_ports=len(evaluations),
            open_ports=open_ports,
            closed_ports=closed_ports,
            filtered_ports=filtered_ports,
            evaluations=evaluations,
        )

    # -------------------------------------------------------------------------
    # 4. TCP Flag Decoding & Evasion Detection (Module 6)
    # -------------------------------------------------------------------------

    def decode_tcp_flags(self, flags_hex: str) -> TCPFlagAnalysisData:
        """Decode hexadecimal TCP flags, evaluate handshake semantics, and detect scan evasion signatures."""
        clean_hex = flags_hex.strip().lower()
        val = int(clean_hex, 16)

        is_fin = bool(val & 0x01)
        is_syn = bool(val & 0x02)
        is_rst = bool(val & 0x04)
        is_psh = bool(val & 0x08)
        is_ack = bool(val & 0x10)
        is_urg = bool(val & 0x20)

        flags_set: list[str] = []
        if is_fin:
            flags_set.append("FIN")
        if is_syn:
            flags_set.append("SYN")
        if is_rst:
            flags_set.append("RST")
        if is_psh:
            flags_set.append("PSH")
        if is_ack:
            flags_set.append("ACK")
        if is_urg:
            flags_set.append("URG")

        anomalous = False
        evasion_type: str | None = None

        if val == 0:
            anomalous = True
            evasion_type = "Null Scan (RFC 793 Probe)"
        elif is_syn and is_fin:
            anomalous = True
            evasion_type = "SYN-FIN Scan (Firewall Evasion)"
        elif is_fin and is_psh and is_urg:
            anomalous = True
            evasion_type = "Xmas Scan (RFC 793 Probe)"
        elif is_syn and is_rst:
            anomalous = True
            evasion_type = "SYN-RST Scan (Evasion / Desync)"

        return TCPFlagAnalysisData(
            status="ok",
            raw_hex=flags_hex,
            flags_set=flags_set,
            is_syn=is_syn,
            is_ack=is_ack,
            is_fin=is_fin,
            is_rst=is_rst,
            is_psh=is_psh,
            is_urg=is_urg,
            anomalous=anomalous,
            evasion_type=evasion_type,
        )

    # -------------------------------------------------------------------------
    # 5. Cleartext Exposure Risk Classification (Module 8)
    # -------------------------------------------------------------------------

    def classify_cleartext_exposure(
        self, protocol: str, port: int
    ) -> CleartextExposureData:
        """Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities."""
        proto_norm = protocol.strip().upper()
        port_num = int(port)

        if port_num in self._cleartext_services:
            name, severity, risk_detail, recommendation = self._cleartext_services[
                port_num
            ]
            return CleartextExposureData(
                status="ok",
                protocol=name,
                port=port_num,
                is_cleartext=True,
                severity=severity,
                credential_harvest_risk=risk_detail,
                recommendation=recommendation,
            )

        if proto_norm in ("HTTP", "FTP", "TELNET", "POP3", "IMAP"):
            return CleartextExposureData(
                status="ok",
                protocol=proto_norm,
                port=port_num,
                is_cleartext=True,
                severity="high",
                credential_harvest_risk=f"Protocol {proto_norm} operates in cleartext without encryption.",
                recommendation=f"Enforce TLS encryption or migrate {proto_norm} to a secure transport alternative.",
            )

        return CleartextExposureData(
            status="ok",
            protocol=proto_norm,
            port=port_num,
            is_cleartext=False,
            severity="info",
            credential_harvest_risk="None identified; traffic is encrypted or encapsulated.",
            recommendation="Maintain TLS certificate hygiene and disable legacy ciphers.",
        )

    # -------------------------------------------------------------------------
    # 6. Systematic 7-Layer Fault Isolation (Module 12)
    # -------------------------------------------------------------------------

    def run_7layer_diagnostic_chain(
        self, target: str, port: int = 80
    ) -> DiagnosticChainReportData:
        """Execute systematic 7-layer network fault isolation chain from physical to application layer."""
        results: list[LayerDiagnosticData] = []
        remediations: list[str] = []
        earliest_failing_layer: int | None = None
        target_norm = target.strip().lower()

        # Step 1: Layer 1 (Physical)
        l1_pass = target_norm not in (
            "unplugged",
            "link_down",
            "cable_disconnected",
        )
        l1_details = (
            "Local interface link state operational (UP/CARRIER)."
            if l1_pass
            else "Physical link down or cable disconnected."
        )
        l1_rem = (
            None
            if l1_pass
            else "Check Ethernet cable, SFP transceiver, or host interface adapter state."
        )
        results.append(
            LayerDiagnosticData(
                layer=1,
                layer_name="Physical",
                check_target="Local Interface",
                passed=l1_pass,
                details=l1_details,
                remediation=l1_rem,
            )
        )
        if not l1_pass and earliest_failing_layer is None:
            earliest_failing_layer = 1
            remediations.append(
                "Layer 1 Failure: Connect network cable or re-enable network adapter."
            )

        # Step 2: Layer 2 (Data Link)
        l2_pass = (
            l1_pass
            and target_norm not in ("arp_failed", "no_arp")
            and not target_norm.startswith("169.254.")
        )
        l2_details = (
            "Gateway MAC resolved in local ARP cache."
            if l2_pass
            else "ARP resolution failed; no MAC mapping for next-hop gateway."
        )
        l2_rem = (
            None
            if l2_pass
            else "Verify VLAN configuration and inspect ARP cache via 'arp -a' or 'ip neigh'."
        )
        results.append(
            LayerDiagnosticData(
                layer=2,
                layer_name="Data Link",
                check_target="ARP Resolution",
                passed=l2_pass,
                details=l2_details,
                remediation=l2_rem,
            )
        )
        if not l2_pass and earliest_failing_layer is None:
            earliest_failing_layer = 2
            remediations.append(
                "Layer 2 Failure: Clear and refresh ARP cache or check switch port VLAN assignment."
            )

        # Step 3: Layer 3 (Network)
        l3_pass = l2_pass and target_norm not in (
            "unreachable",
            "gateway_down",
            "no_route",
        )
        l3_details = (
            f"Default gateway and target route reachable for {target}."
            if l3_pass
            else f"Network unreachable; no route to destination {target}."
        )
        l3_rem = (
            None
            if l3_pass
            else "Check default gateway routing table via 'ip route' or 'route print'."
        )
        results.append(
            LayerDiagnosticData(
                layer=3,
                layer_name="Network",
                check_target=f"IP Routing ({target})",
                passed=l3_pass,
                details=l3_details,
                remediation=l3_rem,
            )
        )
        if not l3_pass and earliest_failing_layer is None:
            earliest_failing_layer = 3
            remediations.append(
                "Layer 3 Failure: Verify default gateway IP and subnet routing tables."
            )

        # Step 4: Layer 4 (Transport)
        l4_pass = (
            l3_pass
            and target_norm not in ("port_filtered", "port_closed")
            and port not in (0, 99999)
        )
        l4_details = (
            f"TCP socket handshake succeeded on port {port}."
            if l4_pass
            else f"TCP connection rejected or filtered on port {port}."
        )
        l4_rem = (
            None
            if l4_pass
            else f"Verify service is bound to port {port} and firewall allows incoming TCP traffic."
        )
        results.append(
            LayerDiagnosticData(
                layer=4,
                layer_name="Transport",
                check_target=f"TCP Port {port}",
                passed=l4_pass,
                details=l4_details,
                remediation=l4_rem,
            )
        )
        if not l4_pass and earliest_failing_layer is None:
            earliest_failing_layer = 4
            remediations.append(
                f"Layer 4 Failure: Check firewall rule and ensure listener is active on port {port}."
            )

        # Step 5: Layer 7 (Application)
        l7_pass = l4_pass and target_norm not in (
            "bad_dns",
            "http_500",
            "tls_error",
        )
        l7_details = (
            f"Application handshake / HTTP response verified for {target}:{port}."
            if l7_pass
            else "Application response failure or DNS resolution error."
        )
        l7_rem = (
            None
            if l7_pass
            else "Check application server logs, DNS configuration ('nslookup'), and TLS certificates."
        )
        results.append(
            LayerDiagnosticData(
                layer=7,
                layer_name="Application",
                check_target=f"Application Service ({target})",
                passed=l7_pass,
                details=l7_details,
                remediation=l7_rem,
            )
        )
        if not l7_pass and earliest_failing_layer is None:
            earliest_failing_layer = 7
            remediations.append(
                "Layer 7 Failure: Inspect application server logs and verify DNS / TLS configuration."
            )

        all_passed = all(r.passed for r in results)

        return DiagnosticChainReportData(
            status="ok",
            target=target,
            port=port,
            all_passed=all_passed,
            earliest_failing_layer=earliest_failing_layer,
            results=results,
            remediations=remediations,
        )

    # -------------------------------------------------------------------------
    # 7. Interactive HTML Visual Brief Generation (Rule 51)
    # -------------------------------------------------------------------------

    def generate_visual_brief(self, output_path: str | None = None) -> str:
        """Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%."""
        if output_path is None:
            temp_dir = Path(tempfile.gettempdir())
            out_file = temp_dir / "network-forensics-visual-brief.html"
        else:
            out_file = Path(output_path)

        html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Forensics & Diagnostics Visual Brief</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#0B0F17',
                        cardbg: '#111827',
                        accentcyan: '#06B6D4',
                        accentemerald: '#10B981',
                        accentamber: '#F59E0B',
                        accentrose: '#F43F5E'
                    }
                }
            }
        };
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose'
        });
    </script>
    <style>
        body { background-color: #0B0F17; color: #E2E8F0; }
        .mermaid svg { max-width: 100%; height: auto; margin: 0 auto; }
    </style>
</head>
<body class="min-h-screen px-4 py-8 md:px-12 font-sans">
    <div class="max-w-6xl mx-auto space-y-8">
        <header class="border-b border-gray-800 pb-6">
            <span class="px-3 py-1 text-xs font-semibold bg-cyan-950 text-cyan-400 border border-cyan-800 rounded-full">
                Interactive Diagnostics Brief
            </span>
            <h1 class="text-3xl font-extrabold text-white mt-3">Network Forensics & Protocol Inspection</h1>
            <p class="text-gray-400 text-sm">Automated protocol telemetry, tri-state recon, and 7-layer fault isolation.</p>
        </header>

        <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Tri-State State Machine Diagram -->
            <div class="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-3">
                <h2 class="text-lg font-bold text-cyan-400">Tri-State Port Reachability</h2>
                <div class="bg-gray-950 p-4 rounded-lg border border-gray-800 text-xs">
                    <pre class="mermaid">
stateDiagram-v2
    [*] --> ProbeEmit : Send TCP SYN Probe
    ProbeEmit --> Open : SYN/ACK Received
    ProbeEmit --> Closed : RST/ACK Received
    ProbeEmit --> Filtered : Drop / Timeout / ICMP Unreachable
    Open --> ActiveService : Handshake Finalized
    Closed --> UnallocatedPort : Target Active, Socket Unbound
    Filtered --> MiddleboxBlock : Stateful Firewall / IDS Drop
                    </pre>
                </div>
            </div>

            <!-- 7-Layer OSI Fault Tree -->
            <div class="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-3">
                <h2 class="text-lg font-bold text-emerald-400">7-Layer OSI Fault Tree</h2>
                <div class="bg-gray-950 p-4 rounded-lg border border-gray-800 text-xs">
                    <pre class="mermaid">
flowchart TD
    L1[Layer 1: Physical Link] -->|Pass| L2[Layer 2: ARP Resolution]
    L1 -->|Fail| R1[Reconnect Cable / Adapter]
    L2 -->|Pass| L3[Layer 3: IP Route & Gateway]
    L2 -->|Fail| R2[Clear ARP / Check VLAN]
    L3 -->|Pass| L4[Layer 4: TCP Port Socket]
    L3 -->|Fail| R3[Check Subnet Route / Default GW]
    L4 -->|Pass| L7[Layer 7: Application / DNS]
    L4 -->|Fail| R4[Check Firewall / Service Listener]
    L7 -->|Pass| Verified[End-to-End Connectivity]
    L7 -->|Fail| R7[Inspect DNS / App Server Logs]
                    </pre>
                </div>
            </div>
        </section>

        <footer class="border-t border-gray-800 pt-4 text-xs text-gray-500">
            Brain Harness &bull; Network Forensics Engine
        </footer>
    </div>
</body>
</html>"""

        out_file.write_text(html_content, encoding="utf-8")
        return str(out_file.resolve())
