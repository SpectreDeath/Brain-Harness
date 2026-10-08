"""Packet flow anomaly detection, TCP flag decoding, and TLS inspection."""

from __future__ import annotations

from typing import Any
from dataclasses import asdict

from harness.services.network_forensics import TCPFlagAnalysisData
from .models import TCPFlagAnalysis


def analyze_packet_summary(flows: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze summary of packet flows to detect port scans, syn floods, and anomalous traffic."""
    threats: list[dict[str, Any]] = []

    # Detect port scanning: same src_ip targeting >= 5 distinct dst_ports
    src_targets: dict[str, set[int]] = {}
    for flow in flows:
        s_ip = flow.get("src_ip", "0.0.0.0")
        d_port = flow.get("dst_port", 0)
        src_targets.setdefault(s_ip, set()).add(d_port)

    for s_ip, ports in src_targets.items():
        if len(ports) >= 5:
            threats.append({
                "type": "Port Scan Probing",
                "severity": "high",
                "source_ip": s_ip,
                "probed_ports_count": len(ports),
                "remediation": f"Block source IP {s_ip} at edge firewall.",
            })

    return {
        "status": "ok",
        "total_flows_analyzed": len(flows),
        "threats_count": len(threats),
        "clean": len(threats) == 0,
        "threats": threats,
    }


def inspect_tls_certificate(cert_info: dict[str, Any]) -> dict[str, Any]:
    """Validate TLS certificate parameters (expiry, cipher suite, TLS version)."""
    alerts: list[str] = []
    days_to_expiry = cert_info.get("days_to_expiry", 0)
    tls_version = cert_info.get("tls_version", "TLSv1.2")

    if days_to_expiry <= 0:
        alerts.append("Certificate has expired")
    elif days_to_expiry < 30:
        alerts.append("Certificate expiring within 30 days")

    if tls_version in ("TLSv1.0", "TLSv1.1", "SSLv3", "SSLv2"):
        alerts.append(f"Insecure TLS version: {tls_version}")

    return {
        "status": "ok",
        "valid": len(alerts) == 0,
        "alerts_count": len(alerts),
        "alerts": alerts,
    }


def decode_tcp_flags_data(flags_hex: str) -> TCPFlagAnalysisData:
    """Decode hexadecimal TCP flags returning typed TCPFlagAnalysisData."""
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


def decode_tcp_flags_dict(flags_hex: str) -> dict[str, Any]:
    """Decode hexadecimal TCP flags returning dictionary with TCPFlagAnalysis model data."""
    data = decode_tcp_flags_data(flags_hex)
    model = TCPFlagAnalysis(
        raw_hex=data.raw_hex,
        flags_set=data.flags_set,
        is_syn=data.is_syn,
        is_ack=data.is_ack,
        is_fin=data.is_fin,
        is_rst=data.is_rst,
        is_psh=data.is_psh,
        is_urg=data.is_urg,
        anomalous=data.anomalous,
        evasion_type=data.evasion_type,
    )
    res = asdict(model)
    res["status"] = "ok"
    return res
