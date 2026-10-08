"""Tests for Network Forensics Plugin decomposition (plugins/security_and_forensics/network_forensics).

Verifies:
- Isolated importability of submodules under engine/:
  - engine.models (Slotted & frozen dataclasses per Rule 12)
  - engine.ports (Port configuration auditing and tri-state evaluation)
  - engine.packets (Packet flow anomaly detection, TCP flag decoding, and TLS inspection)
  - engine.traceroute (Traceroute parsing and latency spike detection)
  - engine.diagnostics (Subnet geometry, cleartext risk classification, 7-layer fault tree)
  - engine.brief (Interactive HTML visual brief generator)
  - engine.core (Unified NetworkForensicsEngine)
- Backward compatibility of main.py facade exports, tool wrappers, and plugin singleton (Rule 45)
- Line-count bound on main.py coordinator facade (Rule 11 context budget)
"""

from __future__ import annotations

import pytest
from pathlib import Path

from plugins.security_and_forensics.network_forensics.engine.models import (
    HopAnalysisResult,
    LayerDiagnosticResult,
    PortScanEvaluation,
    TCPFlagAnalysis,
)
from plugins.security_and_forensics.network_forensics.engine.ports import (
    audit_port_configuration,
    evaluate_port_states_data,
    evaluate_port_states_dict,
)
from plugins.security_and_forensics.network_forensics.engine.packets import (
    analyze_packet_summary,
    decode_tcp_flags_data,
    decode_tcp_flags_dict,
    inspect_tls_certificate,
)
from plugins.security_and_forensics.network_forensics.engine.traceroute import (
    analyze_traceroute_dict,
    parse_traceroute_hops,
)
from plugins.security_and_forensics.network_forensics.engine.diagnostics import (
    calculate_subnet_geometry,
    classify_cleartext_exposure_data,
    classify_cleartext_exposure_dict,
    run_7layer_diagnostic_chain_data,
    run_7layer_diagnostic_chain_dict,
)
from plugins.security_and_forensics.network_forensics.engine.brief import generate_visual_brief
from plugins.security_and_forensics.network_forensics.engine.core import NetworkForensicsEngine
from plugins.security_and_forensics.network_forensics.main import (
    HopAnalysisResult as FacadeHopAnalysisResult,
    LayerDiagnosticResult as FacadeLayerDiagnosticResult,
    PortScanEvaluation as FacadePortScanEvaluation,
    TCPFlagAnalysis as FacadeTCPFlagAnalysis,
    NetworkForensicsPlugin,
    analyze_packet_summary as facade_analyze_packet_summary,
    analyze_traceroute_hops as facade_analyze_traceroute_hops,
    audit_port_configuration as facade_audit_port_configuration,
    calculate_subnet_geometry as facade_calculate_subnet_geometry,
    classify_cleartext_exposure as facade_classify_cleartext_exposure,
    decode_tcp_flags as facade_decode_tcp_flags,
    evaluate_port_states as facade_evaluate_port_states,
    generate_visual_brief as facade_generate_visual_brief,
    inspect_tls_certificate as facade_inspect_tls_certificate,
    plugin,
    run_7layer_diagnostic_chain as facade_run_7layer_diagnostic_chain,
)
from harness.services.network_forensics import NETWORK_FORENSICS_KEY, NetworkForensicsService


def test_models_immutability_and_slots():
    """Verify engine.models slotted and frozen behavior."""
    hop = HopAnalysisResult(
        hop_number=1,
        ip_address="192.168.1.1",
        rtt_ms=1.5,
        status="active",
    )
    assert hasattr(hop, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        hop.rtt_ms = 3.0  # type: ignore[misc]

    port_eval = PortScanEvaluation(
        port=443,
        protocol="TCP",
        state="open",
        response_flag="SYN/ACK",
    )
    assert hasattr(port_eval, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        port_eval.state = "closed"  # type: ignore[misc]


def test_isolated_ports_submodule():
    """Verify engine.ports audit and tri-state evaluation."""
    audit = audit_port_configuration([22, 23, 80])
    assert audit["status"] == "ok"
    assert audit["secure"] is False

    evals = evaluate_port_states_dict([
        {"port": 80, "response": "SYN/ACK"},
        {"port": 22, "response": "RST"},
        {"port": 443, "response": "none"},
    ])
    assert evals["status"] == "ok"
    assert evals["open_ports"] == [80]
    assert evals["closed_ports"] == [22]
    assert evals["filtered_ports"] == [443]


def test_isolated_packets_submodule():
    """Verify engine.packets flow analysis, TCP flag decoding, and TLS inspection."""
    flows = [
        {"src_ip": "10.0.0.1", "dst_port": 22},
        {"src_ip": "10.0.0.1", "dst_port": 23},
        {"src_ip": "10.0.0.1", "dst_port": 80},
        {"src_ip": "10.0.0.1", "dst_port": 443},
        {"src_ip": "10.0.0.1", "dst_port": 8080},
    ]
    summary = analyze_packet_summary(flows)
    assert summary["status"] == "ok"
    assert summary["clean"] is False
    assert len(summary["threats"]) >= 1

    flags = decode_tcp_flags_dict("0x02")
    assert flags["is_syn"] is True
    assert flags["anomalous"] is False

    tls = inspect_tls_certificate({"days_to_expiry": 100, "tls_version": "TLSv1.3"})
    assert tls["status"] == "ok"
    assert tls["valid"] is True


def test_isolated_traceroute_submodule():
    """Verify engine.traceroute parsing and latency detection."""
    sample = """
    traceroute to 1.1.1.1, 30 hops max
     1  192.168.1.1 (192.168.1.1)  1.2 ms
     2  10.0.0.1 (10.0.0.1)  2.5 ms
    """
    res = analyze_traceroute_dict(sample)
    assert res["status"] == "ok"
    assert res["total_hops"] == 2
    assert res["reached_target"] is True


def test_isolated_diagnostics_submodule():
    """Verify engine.diagnostics subnet geometry, cleartext risk, and 7-layer chain."""
    geom = calculate_subnet_geometry("192.168.0.0/24")
    assert geom.total_addresses == 256
    assert geom.usable_hosts == 254

    cleartext = classify_cleartext_exposure_dict("HTTP", 80)
    assert cleartext["is_cleartext"] is True

    chain = run_7layer_diagnostic_chain_dict("localhost", port=80)
    assert chain["status"] == "ok"
    assert chain["all_passed"] is True


def test_facade_backward_compatibility():
    """Verify main.py re-exports, tool wrappers, and plugin singleton."""
    assert FacadeHopAnalysisResult is HopAnalysisResult
    assert FacadePortScanEvaluation is PortScanEvaluation
    assert FacadeTCPFlagAnalysis is TCPFlagAnalysis
    assert FacadeLayerDiagnosticResult is LayerDiagnosticResult

    # Facade tools callable
    res = facade_decode_tcp_flags("0x02")
    assert res["is_syn"] is True

    # Plugin singleton (Rule 45)
    assert isinstance(plugin, NetworkForensicsPlugin)
    assert plugin.name == "plugin.network_forensics"
    assert NETWORK_FORENSICS_KEY in plugin.provides
    assert isinstance(plugin.engine, NetworkForensicsEngine)


def test_main_facade_line_count():
    """Verify main.py coordinator facade stays under 200 lines (Rule 11 context budget)."""
    main_file = Path("plugins/security_and_forensics/network_forensics/main.py")
    lines = main_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) < 200, f"main.py should be under 200 lines, but was {len(lines)}"
