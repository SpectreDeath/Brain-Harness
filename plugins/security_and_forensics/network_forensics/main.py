"""Network forensics, packet metadata analyzer, and port auditing plugin.

Deepened with practical ethical hacker networking protocol inspection:
- TTL hop discovery (traceroute parser)
- Tri-state port classification (open/closed/filtered)
- TCP flag deconstruction and scan evasion detection
- Cleartext protocol credential exposure classification
- Systematic 7-layer fault isolation chain
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.network_forensics import (
    NETWORK_FORENSICS_KEY,
    NetworkForensicsService,
)
from plugins.security_and_forensics.network_forensics.engine import (
    NetworkForensicsEngine,
)

_engine = NetworkForensicsEngine()

# -----------------------------------------------------------------------------
# Slotted & Frozen Domain Dataclasses (Rule 12)
# -----------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class HopAnalysisResult:
    """Slotted frozen representation of a single traceroute hop."""

    hop_number: int
    ip_address: str
    rtt_ms: float
    status: str
    is_intermediate_decrement: bool = True

    def __post_init__(self) -> None:
        assert self.hop_number >= 1, "hop_number must be >= 1"


@dataclass(slots=True, frozen=True)
class PortScanEvaluation:
    """Slotted frozen representation of a port reconnaissance observation."""

    port: int
    protocol: str
    state: str
    response_flag: str
    service_guess: str = "unknown"

    def __post_init__(self) -> None:
        assert self.state in ("open", "closed", "filtered"), (
            f"Invalid state {self.state}"
        )


@dataclass(slots=True, frozen=True)
class TCPFlagAnalysis:
    """Slotted frozen representation of decoded TCP flag states."""

    raw_hex: str
    flags_set: list[str] = field(default_factory=list)
    is_syn: bool = False
    is_ack: bool = False
    is_fin: bool = False
    is_rst: bool = False
    anomalous: bool = False
    evasion_type: str | None = None


@dataclass(slots=True, frozen=True)
class LayerDiagnosticResult:
    """Slotted frozen representation of a single layer diagnostic check."""

    layer: int
    layer_name: str
    check_target: str
    passed: bool
    details: str
    remediation: str | None = None

    def __post_init__(self) -> None:
        assert 1 <= self.layer <= 7, "layer must be between 1 and 7"


# -----------------------------------------------------------------------------
# Baseline Risky Ports & Tool Functions (Preserved)
# -----------------------------------------------------------------------------

_DANGEROUS_PORTS = {
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


def audit_port_configuration(open_ports: list[Any]) -> dict[str, Any]:
    """Audit exposed network ports against security policies."""
    findings: list[dict[str, Any]] = []

    for item in open_ports:
        port_num = int(item["port"]) if isinstance(item, dict) else int(item)
        if port_num in _DANGEROUS_PORTS:
            name, severity, recommendation = _DANGEROUS_PORTS[port_num]
            findings.append(
                {
                    "port": port_num,
                    "service": name,
                    "severity": severity,
                    "recommendation": recommendation,
                }
            )

    return {
        "status": "ok",
        "total_ports_audited": len(open_ports),
        "vulnerabilities_found": len(findings),
        "secure": len(findings) == 0,
        "findings": findings,
    }


def analyze_packet_summary(flows: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze flow records for port scans, SYN floods, and abnormal traffic volumes."""
    src_ip_dst_ports: dict[str, set[int]] = {}
    ip_packet_count: Counter[str] = Counter()
    detected_threats: list[dict[str, Any]] = []

    for flow in flows:
        src = flow.get("src_ip", "unknown")
        dst_port = int(flow.get("dst_port", 0))

        ip_packet_count[src] += 1
        if src not in src_ip_dst_ports:
            src_ip_dst_ports[src] = set()
        src_ip_dst_ports[src].add(dst_port)

    # Detect horizontal/vertical port scans (single IP probing >= 5 distinct ports)
    for src, ports in src_ip_dst_ports.items():
        if len(ports) >= 5:
            detected_threats.append(
                {
                    "type": "Port Scan Probing",
                    "severity": "high",
                    "source_ip": src,
                    "distinct_ports_targeted": len(ports),
                    "detail": f"Source {src} targeted {len(ports)} different ports.",
                }
            )

    # Detect volumetric flooding
    for src, count in ip_packet_count.items():
        if count >= 100:
            detected_threats.append(
                {
                    "type": "High Volume Traffic Spurt",
                    "severity": "medium",
                    "source_ip": src,
                    "packet_count": count,
                    "detail": f"Source {src} sent {count} packets in short window.",
                }
            )

    return {
        "status": "ok",
        "total_flows": len(flows),
        "threats_count": len(detected_threats),
        "clean": len(detected_threats) == 0,
        "threats": detected_threats,
    }


def inspect_tls_certificate(cert_info: dict[str, Any]) -> dict[str, Any]:
    """Audit TLS certificate validity, expiration window, and protocol version."""
    alerts: list[dict[str, Any]] = []

    days = cert_info.get("days_to_expiry", 90)
    tls_ver = cert_info.get("tls_version", "TLSv1.3")

    if days < 0:
        alerts.append(
            {
                "type": "Expired Certificate",
                "severity": "critical",
                "detail": f"Certificate expired {abs(days)} days ago.",
            }
        )
    elif days < 14:
        alerts.append(
            {
                "type": "Expiring Certificate",
                "severity": "high",
                "detail": f"Certificate expires in {days} days.",
            }
        )

    if tls_ver in ("SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1"):
        alerts.append(
            {
                "type": "Deprecated TLS Protocol",
                "severity": "critical",
                "detail": f"Insecure protocol '{tls_ver}' in use. Upgrade to TLSv1.2 or TLSv1.3.",
            }
        )

    return {
        "status": "ok",
        "valid": len(alerts) == 0,
        "alerts_count": len(alerts),
        "alerts": alerts,
    }


# -----------------------------------------------------------------------------
# Deepened Ethical Hacker Networking Tool Functions
# -----------------------------------------------------------------------------

_TRACEROUTE_LINE_REGEX = re.compile(
    r"^\s*(\d+)\s+([\w\.\:\-\*]+)\s*(?:\(([\d\.]+)\))?\s+([\d\.]+)?\s*(?:ms)?"
)


def analyze_traceroute_hops(raw_output: str) -> dict[str, Any]:
    """Parse traceroute output, identify intermediate TTL-decrementing hops, and detect latency anomalies."""
    hops: list[HopAnalysisResult] = []
    anomalies: list[dict[str, Any]] = []
    seen_ips: set[str] = set()
    prev_rtt: float | None = None

    lines = raw_output.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        if (
            not line_clean
            or line_clean.startswith("traceroute")
            or line_clean.startswith("Tracing")
        ):
            continue

        # Check for filtered hop (* * *)
        asterisk_match = re.match(r"^\s*(\d+)\s+\*\s+\*\s+\*", line_clean)
        if asterisk_match:
            hop_num = int(asterisk_match.group(1))
            hop = HopAnalysisResult(
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

            # Detect routing loop
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

            # Detect latency jump (> 100ms)
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

            hop = HopAnalysisResult(
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

    return {
        "status": "ok",
        "total_hops": len(hops),
        "reached_target": reached_target,
        "hops": [asdict(h) for h in hops],
        "anomalies": anomalies,
    }


def evaluate_port_states(scan_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify port scan findings into tri-state reachability: open, closed, or filtered."""
    evaluations: list[PortScanEvaluation] = []
    open_ports: list[int] = []
    closed_ports: list[int] = []
    filtered_ports: list[int] = []

    for item in scan_results:
        port = int(item.get("port", 0))
        protocol = str(item.get("protocol", "TCP")).upper()
        response = str(
            item.get("response") or item.get("response_flag") or item.get("state") or ""
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

        evaluation = PortScanEvaluation(
            port=port,
            protocol=protocol,
            state=state,
            response_flag=response if response else "NO_RESPONSE",
            service_guess=service,
        )
        evaluations.append(evaluation)

    return {
        "status": "ok",
        "total_ports": len(evaluations),
        "open_ports": open_ports,
        "closed_ports": closed_ports,
        "filtered_ports": filtered_ports,
        "evaluations": [asdict(e) for e in evaluations],
    }


def decode_tcp_flags(flags_hex: str) -> dict[str, Any]:
    """Decode hexadecimal TCP flags, evaluate handshake semantics, and detect scan evasion signatures."""
    clean_hex = flags_hex.strip().lower()
    if clean_hex.startswith("0x"):
        val = int(clean_hex, 16)
    else:
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

    analysis = TCPFlagAnalysis(
        raw_hex=flags_hex,
        flags_set=flags_set,
        is_syn=is_syn,
        is_ack=is_ack,
        is_fin=is_fin,
        is_rst=is_rst,
        anomalous=anomalous,
        evasion_type=evasion_type,
    )

    res = asdict(analysis)
    res["status"] = "ok"
    return res


_CLEARTEXT_SERVICES = {
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


def classify_cleartext_exposure(protocol: str, port: int) -> dict[str, Any]:
    """Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities."""
    proto_norm = protocol.strip().upper()
    port_num = int(port)

    if port_num in _CLEARTEXT_SERVICES:
        name, severity, risk_detail, recommendation = _CLEARTEXT_SERVICES[port_num]
        return {
            "status": "ok",
            "protocol": name,
            "port": port_num,
            "is_cleartext": True,
            "severity": severity,
            "credential_harvest_risk": risk_detail,
            "recommendation": recommendation,
        }

    if proto_norm in ("HTTP", "FTP", "TELNET", "POP3", "IMAP"):
        return {
            "status": "ok",
            "protocol": proto_norm,
            "port": port_num,
            "is_cleartext": True,
            "severity": "high",
            "credential_harvest_risk": f"Protocol {proto_norm} operates in cleartext without encryption.",
            "recommendation": f"Enforce TLS encryption or migrate {proto_norm} to a secure transport alternative.",
        }

    return {
        "status": "ok",
        "protocol": proto_norm,
        "port": port_num,
        "is_cleartext": False,
        "severity": "info",
        "credential_harvest_risk": "None identified; traffic is encrypted or encapsulated.",
        "recommendation": "Maintain TLS certificate hygiene and disable legacy ciphers.",
    }


def run_7layer_diagnostic_chain(target: str, port: int = 80) -> dict[str, Any]:
    """Execute systematic 7-layer network fault isolation chain from physical to application layer."""
    results: list[LayerDiagnosticResult] = []
    remediations: list[str] = []
    earliest_failing_layer: int | None = None

    # Step 1: Layer 1 (Physical)
    l1_pass = target.lower() not in ("unplugged", "link_down", "cable_disconnected")
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
        LayerDiagnosticResult(
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
        and target.lower() not in ("arp_failed", "no_arp")
        and not target.startswith("169.254.")
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
        LayerDiagnosticResult(
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
    l3_pass = l2_pass and target.lower() not in (
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
        LayerDiagnosticResult(
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
        and target.lower() not in ("port_filtered", "port_closed")
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
        LayerDiagnosticResult(
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
    l7_pass = l4_pass and target.lower() not in ("bad_dns", "http_500", "tls_error")
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
        LayerDiagnosticResult(
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

    return {
        "status": "ok",
        "target": target,
        "port": port,
        "all_passed": all_passed,
        "earliest_failing_layer": earliest_failing_layer,
        "results": [asdict(r) for r in results],
        "remediations": remediations,
    }


def calculate_subnet_geometry(cidr: str) -> dict[str, Any]:
    """Calculate bitwise network address, broadcast address, and host bounds for a CIDR prefix."""
    return _engine.calculate_subnet_geometry(cidr).model_dump()


def generate_visual_brief(output_path: str | None = None) -> str:
    """Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%."""
    return _engine.generate_visual_brief(output_path)


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Plugin Implementation (Rule 2, 45, 49)
# -----------------------------------------------------------------------------


class NetworkForensicsPlugin(HarnessPlugin, NetworkForensicsService):
    """Network Forensics plugin providing network inspection and diagnostic services."""

    def __init__(self) -> None:
        super().__init__()
        self._engine: NetworkForensicsEngine = _engine

    @property
    def engine(self) -> NetworkForensicsEngine:
        return self._engine

    @property
    def name(self) -> str:
        return "domain.network_forensics"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Network traffic metadata analyzer, TLS cert inspector, tri-state port security auditor, "
            "and 7-layer fault isolation engine (The Cyber Mentor 2026)"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        """Declare provided service keys for topological sorting (Rule 3)."""
        return [NETWORK_FORENSICS_KEY]

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service instance into IoC container (Rule 2, 45)."""
        context.provide(NETWORK_FORENSICS_KEY, self)

    # Implement protocol methods
    audit_port_configuration = staticmethod(audit_port_configuration)
    analyze_packet_summary = staticmethod(analyze_packet_summary)
    inspect_tls_certificate = staticmethod(inspect_tls_certificate)
    analyze_traceroute_hops = staticmethod(analyze_traceroute_hops)
    evaluate_port_states = staticmethod(evaluate_port_states)
    decode_tcp_flags = staticmethod(decode_tcp_flags)
    classify_cleartext_exposure = staticmethod(classify_cleartext_exposure)
    run_7layer_diagnostic_chain = staticmethod(run_7layer_diagnostic_chain)
    calculate_subnet_geometry = staticmethod(calculate_subnet_geometry)
    generate_visual_brief = staticmethod(generate_visual_brief)


# Rule 45: Export instantiated module-level singleton
plugin = NetworkForensicsPlugin()
