"""Traceroute output parsing and TTL decrement analysis."""

from __future__ import annotations

import re
from typing import Any
from dataclasses import asdict

from harness.services.network_forensics import (
    HopAnalysisData,
    TracerouteReportData,
)
from .models import HopAnalysisResult

_TRACEROUTE_LINE_REGEX = re.compile(
    r"^\s*(\d+)\s+([\w\.\:\-\*]+)\s*(?:\(([\d\.]+)\))?\s+([\d\.]+)?\s*(?:ms)?"
)


def parse_traceroute_hops(raw_output: str, max_hops: int = 30) -> TracerouteReportData:
    """Parse traceroute output returning typed TracerouteReportData."""
    hops: list[HopAnalysisData] = []
    anomalies: list[dict[str, Any]] = []
    seen_ips: set[str] = set()
    prev_rtt: float | None = None
    target = "unknown"

    lines = raw_output.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if line_clean.startswith("traceroute to") or line_clean.startswith("Tracing route to"):
            m = re.search(r"to\s+([\w\.\-]+)", line_clean)
            if m:
                target = m.group(1)
            continue

        asterisk_match = re.match(r"^\s*(\d+)\s+\*\s+\*\s+\*", line_clean)
        if asterisk_match:
            hop_num = int(asterisk_match.group(1))
            hops.append(
                HopAnalysisData(
                    hop_number=hop_num,
                    ip_address="*",
                    rtt_ms=0.0,
                    status="filtered",
                    is_intermediate_decrement=True,
                )
            )
            anomalies.append({
                "hop": hop_num,
                "type": "ICMP Filtered Hop",
                "severity": "medium",
                "detail": f"Hop {hop_num} dropped ICMP time-exceeded probes (* * *).",
            })
            continue

        match = _TRACEROUTE_LINE_REGEX.match(line_clean)
        if match:
            hop_num = int(match.group(1))
            host_or_ip = match.group(2)
            ip_in_parens = match.group(3)
            rtt_val = float(match.group(4)) if match.group(4) else 0.0

            ip_addr = ip_in_parens or host_or_ip
            if ip_addr in seen_ips and ip_addr != "*":
                anomalies.append({
                    "hop": hop_num,
                    "type": "Routing Loop Detected",
                    "severity": "high",
                    "detail": f"IP {ip_addr} appeared at hop {hop_num} after prior visit.",
                })
            seen_ips.add(ip_addr)

            if prev_rtt is not None and (rtt_val - prev_rtt) > 100.0:
                anomalies.append({
                    "hop": hop_num,
                    "type": "Latency Spike",
                    "severity": "medium",
                    "delta_ms": round(rtt_val - prev_rtt, 2),
                    "detail": f"Latency jumped {round(rtt_val - prev_rtt, 2)}ms at hop {hop_num}.",
                })
            prev_rtt = rtt_val

            hops.append(
                HopAnalysisData(
                    hop_number=hop_num,
                    ip_address=ip_addr,
                    rtt_ms=rtt_val,
                    status="active",
                    is_intermediate_decrement=True,
                )
            )

    reached = False
    if hops:
        last_hop = hops[-1]
        if last_hop.status == "active" and last_hop.ip_address != "*":
            reached = True

    return TracerouteReportData(
        status="ok",
        target=target,
        total_hops=len(hops),
        reached_target=reached,
        hops=hops,
        anomalies=anomalies,
    )


def analyze_traceroute_dict(raw_output: str) -> dict[str, Any]:
    """Parse traceroute output returning dictionary with HopAnalysisResult items."""
    report = parse_traceroute_hops(raw_output)
    hop_results = [
        HopAnalysisResult(
            hop_number=h.hop_number,
            ip_address=h.ip_address,
            rtt_ms=h.rtt_ms,
            status=h.status,
            is_intermediate_decrement=h.is_intermediate_decrement,
        )
        for h in report.hops
    ]

    return {
        "status": report.status,
        "target": report.target,
        "total_hops": report.total_hops,
        "reached_target": report.reached_target,
        "hops": [asdict(h) for h in hop_results],
        "anomalies": report.anomalies,
    }
