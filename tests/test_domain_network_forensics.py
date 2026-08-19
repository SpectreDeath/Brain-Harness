"""Tests for Domain 1: Network Forensics plugin."""

from __future__ import annotations

import pytest

from plugins.security_and_forensics.network_forensics.main import (
    analyze_packet_summary,
    audit_port_configuration,
    inspect_tls_certificate,
)


@pytest.mark.unit
class TestNetworkForensicsPlugin:
    def test_audit_port_configuration(self) -> None:
        open_ports = [22, 23, 80, 443, 6379]
        res = audit_port_configuration(open_ports)
        assert res["status"] == "ok"
        assert res["secure"] is False
        assert res["vulnerabilities_found"] >= 3  # Telnet, HTTP, Redis

    def test_analyze_packet_flows_port_scan(self) -> None:
        flows = [
            {"src_ip": "10.0.0.99", "dst_port": 21},
            {"src_ip": "10.0.0.99", "dst_port": 22},
            {"src_ip": "10.0.0.99", "dst_port": 23},
            {"src_ip": "10.0.0.99", "dst_port": 80},
            {"src_ip": "10.0.0.99", "dst_port": 443},
            {"src_ip": "10.0.0.99", "dst_port": 3389},
        ]
        res = analyze_packet_summary(flows)
        assert res["status"] == "ok"
        assert res["clean"] is False
        assert res["threats_count"] >= 1
        assert res["threats"][0]["type"] == "Port Scan Probing"

    def test_inspect_tls_certificate(self) -> None:
        expired_cert = {"days_to_expiry": -5, "tls_version": "TLSv1.0"}
        res = inspect_tls_certificate(expired_cert)
        assert res["status"] == "ok"
        assert res["valid"] is False
        assert res["alerts_count"] == 2
