"""Network forensics, packet metadata analyzer, and port auditing plugin."""

from __future__ import annotations

from collections import Counter
from typing import Any

# Risky default ports
_DANGEROUS_PORTS = {
    21: ("FTP", "critical", "Cleartext credentials; replace with SFTP."),
    23: ("Telnet", "critical", "Unencrypted remote shell; replace with SSH."),
    80: ("HTTP", "medium", "Unencrypted web traffic; enforce HTTPS on port 443."),
    3389: ("RDP", "high", "Exposed Windows Remote Desktop; restrict to VPN/bastion."),
    6379: ("Redis", "critical", "Exposed Redis key-value store; bind to localhost only."),
    27017: ("MongoDB", "critical", "Exposed MongoDB instance; bind to private subnet."),
}


def audit_port_configuration(open_ports: list[Any]) -> dict[str, Any]:
    """Audit exposed network ports against security policies."""
    findings: list[dict[str, Any]] = []

    for item in open_ports:
        port_num = int(item["port"]) if isinstance(item, dict) else int(item)
        if port_num in _DANGEROUS_PORTS:
            name, severity, recommendation = _DANGEROUS_PORTS[port_num]
            findings.append({
                "port": port_num,
                "service": name,
                "severity": severity,
                "recommendation": recommendation,
            })

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
            detected_threats.append({
                "type": "Port Scan Probing",
                "severity": "high",
                "source_ip": src,
                "distinct_ports_targeted": len(ports),
                "detail": f"Source {src} targeted {len(ports)} different ports.",
            })

    # Detect volumetric flooding
    for src, count in ip_packet_count.items():
        if count >= 100:
            detected_threats.append({
                "type": "High Volume Traffic Spurt",
                "severity": "medium",
                "source_ip": src,
                "packet_count": count,
                "detail": f"Source {src} sent {count} packets in short window.",
            })

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
        alerts.append({
            "type": "Expired Certificate",
            "severity": "critical",
            "detail": f"Certificate expired {abs(days)} days ago.",
        })
    elif days < 14:
        alerts.append({
            "type": "Expiring Certificate",
            "severity": "high",
            "detail": f"Certificate expires in {days} days.",
        })

    if tls_ver in ("SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1"):
        alerts.append({
            "type": "Deprecated TLS Protocol",
            "severity": "critical",
            "detail": f"Insecure protocol '{tls_ver}' in use. Upgrade to TLSv1.2 or TLSv1.3.",
        })

    return {
        "status": "ok",
        "valid": len(alerts) == 0,
        "alerts_count": len(alerts),
        "alerts": alerts,
    }
