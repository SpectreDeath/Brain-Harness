"""Port auditing and tri-state reachability evaluation (open, closed, filtered)."""

from __future__ import annotations

from typing import Any
from dataclasses import asdict

from harness.services.network_forensics import (
    PortEvaluationData,
    PortReconReportData,
)
from .models import PortScanEvaluation

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

_DANGEROUS_PORTS = _DEFAULT_DANGEROUS_PORTS


def audit_port_configuration(open_ports: list[int]) -> dict[str, Any]:
    """Audit listening ports against dangerous/unencrypted service database."""
    vulnerabilities: list[dict[str, Any]] = []

    for port in open_ports:
        if port in _DANGEROUS_PORTS:
            service, severity, remediation = _DANGEROUS_PORTS[port]
            vulnerabilities.append({
                "port": port,
                "service": service,
                "severity": severity,
                "remediation": remediation,
            })

    return {
        "status": "ok",
        "scanned_ports_count": len(open_ports),
        "vulnerabilities_found": len(vulnerabilities),
        "secure": len(vulnerabilities) == 0,
        "vulnerabilities": vulnerabilities,
    }


def evaluate_port_states_data(port_probes: list[dict[str, Any]]) -> PortReconReportData:
    """Evaluate tri-state port states returning typed PortReconReportData."""
    evaluations: list[PortEvaluationData] = []
    open_ports: list[int] = []
    closed_ports: list[int] = []
    filtered_ports: list[int] = []

    for probe in port_probes:
        port = probe.get("port", 0)
        protocol = probe.get("protocol", "TCP").upper()
        raw_resp = probe.get("response", "").strip().upper()
        service = probe.get("service", "unknown")

        if any(term in raw_resp for term in ("SYN/ACK", "OPEN")):
            state = "open"
            open_ports.append(port)
        elif any(term in raw_resp for term in ("RST", "CLOSED")):
            state = "closed"
            closed_ports.append(port)
        else:
            state = "filtered"
            filtered_ports.append(port)

        evaluations.append(
            PortEvaluationData(
                port=port,
                protocol=protocol,
                state=state,
                response_flag=raw_resp if raw_resp else "NO_RESPONSE",
                service_guess=service,
            )
        )

    return PortReconReportData(
        status="ok",
        total_ports=len(evaluations),
        open_ports=open_ports,
        closed_ports=closed_ports,
        filtered_ports=filtered_ports,
        evaluations=evaluations,
    )


def evaluate_port_states_dict(port_probes: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate tri-state port reachability returning dictionary with PortScanEvaluation items."""
    evaluations: list[PortScanEvaluation] = []
    open_ports: list[int] = []
    closed_ports: list[int] = []
    filtered_ports: list[int] = []

    for probe in port_probes:
        port = probe.get("port", 0)
        protocol = probe.get("protocol", "TCP").upper()
        raw_resp = probe.get("response", "").strip().upper()
        service = probe.get("service", "unknown")

        if any(term in raw_resp for term in ("SYN/ACK", "OPEN")):
            state = "open"
            open_ports.append(port)
        elif any(term in raw_resp for term in ("RST", "CLOSED")):
            state = "closed"
            closed_ports.append(port)
        else:
            state = "filtered"
            filtered_ports.append(port)

        evaluations.append(
            PortScanEvaluation(
                port=port,
                protocol=protocol,
                state=state,
                response_flag=raw_resp if raw_resp else "NO_RESPONSE",
                service_guess=service,
            )
        )

    return {
        "status": "ok",
        "total_ports": len(evaluations),
        "open_ports": open_ports,
        "closed_ports": closed_ports,
        "filtered_ports": filtered_ports,
        "evaluations": [asdict(e) for e in evaluations],
    }
