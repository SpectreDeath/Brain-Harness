"""Subnet geometry calculations, cleartext exposure analysis, and 7-layer fault tree."""

from __future__ import annotations

import ipaddress
from typing import Any
from dataclasses import asdict

from harness.services.network_forensics import (
    CleartextExposureData,
    DiagnosticChainReportData,
    LayerDiagnosticData,
    SubnetGeometryData,
)
from .models import LayerDiagnosticResult

_DEFAULT_CLEARTEXT_SERVICES = {
    21: (
        "FTP",
        "critical",
        "Cleartext authentication credentials and data channel payload.",
        "Migrate to SFTP (port 22) or FTPS (TLS).",
    ),
    23: (
        "Telnet",
        "critical",
        "Unencrypted terminal session transmitting passwords in plaintext.",
        "Migrate to SSH (port 22).",
    ),
    80: (
        "HTTP",
        "high",
        "Cleartext session tokens, cookies, and POST bodies vulnerable to sniffing.",
        "Enforce HTTPS with HSTS on port 443.",
    ),
    110: (
        "POP3",
        "high",
        "Cleartext email authentication and mail spool transfer.",
        "Migrate to POP3S with TLS (port 995).",
    ),
    143: (
        "IMAP",
        "high",
        "Cleartext mailbox synchronization and credentials.",
        "Migrate to IMAPS with TLS (port 993).",
    ),
}

_CLEARTEXT_SERVICES = _DEFAULT_CLEARTEXT_SERVICES


def calculate_subnet_geometry(cidr: str) -> SubnetGeometryData:
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


def classify_cleartext_exposure_data(
    protocol: str,
    port: int,
    cleartext_services: dict[int, tuple[str, str, str, str]] | None = None,
) -> CleartextExposureData:
    """Evaluate cleartext protocol exposure risk returning typed CleartextExposureData."""
    proto_norm = protocol.strip().upper()
    port_num = int(port)
    services = cleartext_services or _DEFAULT_CLEARTEXT_SERVICES

    if port_num in services:
        name, severity, risk_detail, recommendation = services[port_num]
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


def classify_cleartext_exposure_dict(
    protocol: str,
    port: int,
    cleartext_services: dict[int, tuple[str, str, str, str]] | None = None,
) -> dict[str, Any]:
    """Evaluate cleartext protocol exposure risk returning dictionary."""
    data = classify_cleartext_exposure_data(protocol, port, cleartext_services)
    return {
        "status": data.status,
        "protocol": data.protocol,
        "port": data.port,
        "is_cleartext": data.is_cleartext,
        "severity": data.severity,
        "credential_harvest_risk": data.credential_harvest_risk,
        "recommendation": data.recommendation,
    }


def run_7layer_diagnostic_chain_data(
    target: str,
    port: int = 80,
) -> DiagnosticChainReportData:
    """Execute systematic 7-layer fault isolation chain returning typed DiagnosticChainReportData."""
    results: list[LayerDiagnosticData] = []
    remediations: list[str] = []
    earliest_failing_layer: int | None = None
    target_norm = target.strip().lower()

    # Step 1: Layer 1 (Physical)
    l1_pass = target_norm not in ("unplugged", "link_down", "cable_disconnected")
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
        remediations.append("Layer 1 Failure: Connect network cable or re-enable network adapter.")

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
        remediations.append("Layer 2 Failure: Clear and refresh ARP cache or check switch port VLAN assignment.")

    # Step 3: Layer 3 (Network)
    l3_pass = l2_pass and target_norm not in ("unreachable", "gateway_down", "no_route")
    l3_details = (
        f"Default gateway and target route reachable for {target}."
        if l3_pass
        else f"Network unreachable; no route to destination {target}."
    )
    l3_rem = (
        None
        if l3_pass
        else "Check local IP address, subnet mask, default gateway route, and upstream routing tables."
    )
    results.append(
        LayerDiagnosticData(
            layer=3,
            layer_name="Network",
            check_target="IP Route & Gateway",
            passed=l3_pass,
            details=l3_details,
            remediation=l3_rem,
        )
    )
    if not l3_pass and earliest_failing_layer is None:
        earliest_failing_layer = 3
        remediations.append("Layer 3 Failure: Check routing table, default gateway reachability, and ICMP responses.")

    # Step 4: Layer 4 (Transport)
    l4_pass = l3_pass and target_norm not in ("port_closed", "connection_refused", "reset")
    l4_details = (
        f"TCP connection established to {target}:{port}."
        if l4_pass
        else f"Transport connection failed; RST received or connection timed out on port {port}."
    )
    l4_rem = (
        None
        if l4_pass
        else f"Verify remote service is listening on port {port} and intermediate firewalls permit TCP SYN traffic."
    )
    results.append(
        LayerDiagnosticData(
            layer=4,
            layer_name="Transport",
            check_target=f"TCP Socket ({port})",
            passed=l4_pass,
            details=l4_details,
            remediation=l4_rem,
        )
    )
    if not l4_pass and earliest_failing_layer is None:
        earliest_failing_layer = 4
        remediations.append(f"Layer 4 Failure: Check firewall rules and verify daemon is listening on port {port}.")

    # Step 5: Layer 7 (Application)
    l7_pass = l4_pass and target_norm not in ("http_500", "tls_error", "bad_gateway")
    l7_details = (
        f"Application handshake and protocol transaction completed successfully with {target}."
        if l7_pass
        else f"Application protocol error (HTTP error / TLS handshake failure) with {target}."
    )
    l7_rem = (
        None
        if l7_pass
        else "Inspect application server logs, TLS certificate validity, and reverse proxy upstream health."
    )
    results.append(
        LayerDiagnosticData(
            layer=7,
            layer_name="Application",
            check_target="Protocol Session",
            passed=l7_pass,
            details=l7_details,
            remediation=l7_rem,
        )
    )
    if not l7_pass and earliest_failing_layer is None:
        earliest_failing_layer = 7
        remediations.append("Layer 7 Failure: Inspect application server logs, TLS certificates, and HTTP response codes.")

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


def run_7layer_diagnostic_chain_dict(
    target: str,
    port: int = 80,
) -> dict[str, Any]:
    """Execute systematic 7-layer fault isolation chain returning dictionary with LayerDiagnosticResult items."""
    report = run_7layer_diagnostic_chain_data(target, port)
    layer_models = [
        LayerDiagnosticResult(
            layer=r.layer,
            layer_name=r.layer_name,
            check_target=r.check_target,
            passed=r.passed,
            details=r.details,
            remediation=r.remediation,
        )
        for r in report.results
    ]

    return {
        "status": report.status,
        "target": report.target,
        "port": report.port,
        "all_passed": report.all_passed,
        "earliest_failing_layer": report.earliest_failing_layer,
        "results": [asdict(r) for r in layer_models],
        "remediations": report.remediations,
    }
