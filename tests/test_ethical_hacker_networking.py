"""Contract tests for ethical-hacker-networking skill, deepened plugin, and IoC service seam."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.network_forensics import (
    NETWORK_FORENSICS_KEY,
    DiagnosticChainReportData,
    NetworkForensicsService,
    PortReconReportData,
    SubnetGeometryData,
    TCPFlagAnalysisData,
    TracerouteReportData,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    index_skill_catalog,
    query_skill_router,
)
from plugins.security_and_forensics.network_forensics.engine import (
    NetworkForensicsEngine,
)
from plugins.security_and_forensics.network_forensics.main import (
    HopAnalysisResult,
    LayerDiagnosticResult,
    PortScanEvaluation,
    TCPFlagAnalysis,
    analyze_traceroute_hops,
    classify_cleartext_exposure,
    decode_tcp_flags,
    evaluate_port_states,
    plugin,
    run_7layer_diagnostic_chain,
)

_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
_SKILL_DIR = _WORKSPACE_ROOT / ".agents" / "skills" / "ethical-hacker-networking"
_PLUGIN_DIR = (
    _WORKSPACE_ROOT / "plugins" / "security_and_forensics" / "network_forensics"
)


@pytest.mark.unit
def test_dataclass_immutability_and_slots() -> None:
    """Verify Rule 12 and Rule 43: slotted, frozen dataclasses with validation assertions."""
    # 1. HopAnalysisResult
    hop = HopAnalysisResult(
        hop_number=1,
        ip_address="192.168.1.1",
        rtt_ms=1.2,
        status="active",
        is_intermediate_decrement=True,
    )
    assert hasattr(hop, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        hop.rtt_ms = 5.0  # type: ignore[misc]

    with pytest.raises(AssertionError):
        HopAnalysisResult(
            hop_number=0,  # Invalid hop number (< 1)
            ip_address="10.0.0.1",
            rtt_ms=2.0,
            status="active",
        )

    # 2. PortScanEvaluation
    port_eval = PortScanEvaluation(
        port=80,
        protocol="TCP",
        state="open",
        response_flag="SYN/ACK",
        service_guess="http",
    )
    assert hasattr(port_eval, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        port_eval.state = "closed"  # type: ignore[misc]

    with pytest.raises(AssertionError):
        PortScanEvaluation(
            port=80,
            protocol="TCP",
            state="unrecognized_state",  # Invalid state
            response_flag="SYN/ACK",
        )

    # 3. TCPFlagAnalysis
    flags = TCPFlagAnalysis(
        raw_hex="0x02",
        flags_set=["SYN"],
        is_syn=True,
        anomalous=False,
    )
    assert hasattr(flags, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        flags.is_syn = False  # type: ignore[misc]

    # 4. LayerDiagnosticResult
    layer = LayerDiagnosticResult(
        layer=3,
        layer_name="Network",
        check_target="Gateway IP",
        passed=True,
        details="Reachable",
    )
    assert hasattr(layer, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        layer.passed = False  # type: ignore[misc]

    with pytest.raises(AssertionError):
        LayerDiagnosticResult(
            layer=9,  # Invalid OSI layer (> 7)
            layer_name="Invalid",
            check_target="None",
            passed=False,
            details="Fail",
        )


@pytest.mark.unit
def test_traceroute_hop_parsing() -> None:
    """Verify traceroute hop parsing, TTL decrement discovery, filtered hops, and latency spikes."""
    sample_output = """
    traceroute to 8.8.8.8 (8.8.8.8), 30 hops max, 60 byte packets
     1  192.168.1.1 (192.168.1.1)  1.234 ms
     2  10.0.0.1 (10.0.0.1)  5.432 ms
     3  * * *
     4  142.250.64.1 (142.250.64.1)  135.800 ms
     5  8.8.8.8 (8.8.8.8)  138.200 ms
    """
    res = analyze_traceroute_hops(sample_output)
    assert res["status"] == "ok"
    assert res["total_hops"] == 5
    assert res["reached_target"] is True

    # Hop 3 is filtered (* * *)
    filtered_hops = [h for h in res["hops"] if h["status"] == "filtered"]
    assert len(filtered_hops) == 1
    assert filtered_hops[0]["hop_number"] == 3

    # Anomaly checks: should detect the filtered hop and latency spike at hop 4 (> 100ms delta)
    anomaly_types = [a["type"] for a in res["anomalies"]]
    assert "ICMP Filtered Hop" in anomaly_types
    assert "Latency Spike" in anomaly_types


@pytest.mark.unit
def test_tristate_port_evaluation() -> None:
    """Verify tri-state port evaluation (open, closed, filtered) per Claim 2."""
    scan_input = [
        {"port": 80, "response": "SYN/ACK", "service": "http"},
        {"port": 22, "response": "RST", "service": "ssh"},
        {"port": 443, "response": "none", "service": "https"},
        {"port": 8080, "response": "ICMP_UNREACHABLE", "service": "http-alt"},
    ]
    res = evaluate_port_states(scan_input)
    assert res["status"] == "ok"
    assert res["total_ports"] == 4
    assert res["open_ports"] == [80]
    assert res["closed_ports"] == [22]
    assert set(res["filtered_ports"]) == {443, 8080}

    evals = res["evaluations"]
    assert evals[0]["state"] == "open"
    assert evals[1]["state"] == "closed"
    assert evals[2]["state"] == "filtered"
    assert evals[3]["state"] == "filtered"


@pytest.mark.unit
def test_tcp_flag_decoding_and_evasion() -> None:
    """Verify TCP flag bitmask deconstruction and scan evasion signature detection."""
    # Normal SYN probe
    syn_res = decode_tcp_flags("0x02")
    assert syn_res["is_syn"] is True
    assert syn_res["is_ack"] is False
    assert syn_res["anomalous"] is False
    assert syn_res["evasion_type"] is None

    # Normal SYN/ACK response
    synack_res = decode_tcp_flags("0x12")
    assert synack_res["is_syn"] is True
    assert synack_res["is_ack"] is True
    assert synack_res["anomalous"] is False

    # Null Scan evasion (val = 0)
    null_res = decode_tcp_flags("0x00")
    assert null_res["anomalous"] is True
    assert "Null Scan" in (null_res["evasion_type"] or "")

    # SYN-FIN Scan evasion (0x01 | 0x02 = 0x03)
    synfin_res = decode_tcp_flags("0x03")
    assert synfin_res["anomalous"] is True
    assert "SYN-FIN" in (synfin_res["evasion_type"] or "")

    # Xmas Scan evasion (0x01 | 0x08 | 0x20 = 0x29)
    xmas_res = decode_tcp_flags("0x29")
    assert xmas_res["anomalous"] is True
    assert "Xmas Scan" in (xmas_res["evasion_type"] or "")


@pytest.mark.unit
def test_cleartext_exposure_classification() -> None:
    """Verify cleartext protocol vulnerability classification per Claim 3."""
    # HTTP
    http_res = classify_cleartext_exposure("HTTP", 80)
    assert http_res["is_cleartext"] is True
    assert http_res["severity"] in ("high", "critical")
    assert "HTTPS" in http_res["recommendation"]

    # Telnet
    telnet_res = classify_cleartext_exposure("Telnet", 23)
    assert telnet_res["is_cleartext"] is True
    assert telnet_res["severity"] == "critical"
    assert "SSH" in telnet_res["recommendation"]

    # FTP
    ftp_res = classify_cleartext_exposure("FTP", 21)
    assert ftp_res["is_cleartext"] is True
    assert ftp_res["severity"] == "critical"

    # HTTPS (Encrypted)
    https_res = classify_cleartext_exposure("HTTPS", 443)
    assert https_res["is_cleartext"] is False
    assert https_res["severity"] == "info"


@pytest.mark.unit
def test_7layer_fault_isolation_chain() -> None:
    """Verify systematic 7-layer network fault isolation per Claim 5."""
    # 1. Healthy target
    healthy_res = run_7layer_diagnostic_chain("192.168.1.10", port=80)
    assert healthy_res["status"] == "ok"
    assert healthy_res["all_passed"] is True
    assert healthy_res["earliest_failing_layer"] is None
    assert len(healthy_res["results"]) == 5

    # 2. Layer 3 failure (Network unreachable)
    l3_res = run_7layer_diagnostic_chain("unreachable", port=80)
    assert l3_res["status"] == "ok"
    assert l3_res["all_passed"] is False
    assert l3_res["earliest_failing_layer"] == 3
    # Layer 1 and 2 passed, Layer 3 failed, Layers 4 and 7 blocked
    assert l3_res["results"][0]["passed"] is True  # L1
    assert l3_res["results"][1]["passed"] is True  # L2
    assert l3_res["results"][2]["passed"] is False  # L3
    assert l3_res["results"][3]["passed"] is False  # L4
    assert l3_res["results"][4]["passed"] is False  # L7
    assert len(l3_res["remediations"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ioc_service_registration_and_resolution() -> None:
    """Verify Rule 2, 45, and 49: IoC container service provision and protocol conformance."""
    context = ServiceContext()
    await plugin.on_load(context)

    assert context.has(NETWORK_FORENSICS_KEY)
    svc = context.require(NETWORK_FORENSICS_KEY)
    assert isinstance(svc, NetworkForensicsService)

    # Invoke service methods through IoC interface
    flag_res = svc.decode_tcp_flags("0x02")
    assert flag_res["status"] == "ok"
    assert flag_res["is_syn"] is True

    cleartext_res = svc.classify_cleartext_exposure("HTTP", 80)
    assert cleartext_res["is_cleartext"] is True


@pytest.mark.integration
def test_plugin_validator_report() -> None:
    """Verify Rule 34 and Rule 38: PluginValidator confirms valid plugin manifest and layout."""
    report = PluginValidator.validate_sync(_PLUGIN_DIR)
    assert report.valid is True, f"PluginValidator errors: {report.errors}"
    assert len(report.checks) > 0


@pytest.mark.integration
def test_skill_validator_and_router_query() -> None:
    """Verify Rule 34, 35, 37, 44: SkillValidator passes and router indexes ethical-hacker-networking."""
    # 1. SkillValidator check
    report = SkillValidator.validate_sync(_SKILL_DIR)
    assert report.valid is True, f"SkillValidator errors: {report.errors}"
    assert len(report.warnings) == 0, (
        f"Unexpected SkillValidator warnings: {report.warnings}"
    )

    # 2. Skill Catalog Indexing & Router Query
    index_skill_catalog(str(_WORKSPACE_ROOT))
    res = query_skill_router(
        "analyze network traffic, decode tcp flags and traceroute hops", top_k=5
    )
    assert res["status"] == "ok"
    assert len(res["matches"]) > 0

    match_names = [m["skill_name"] for m in res["matches"]]
    assert "ethical-hacker-networking" in match_names, (
        f"'ethical-hacker-networking' not found in top router matches: {match_names}"
    )


@pytest.mark.unit
def test_subnet_geometry_bitwise_calculations() -> None:
    """Verify bitwise IPv4 CIDR subnet geometry and host bounds calculations."""
    engine = NetworkForensicsEngine()

    # /24 prefix: 256 addresses, 254 usable
    sub24 = engine.calculate_subnet_geometry("192.168.1.0/24")
    assert isinstance(sub24, SubnetGeometryData)
    assert sub24.network_address == "192.168.1.0"
    assert sub24.broadcast_address == "192.168.1.255"
    assert sub24.netmask == "255.255.255.0"
    assert sub24.total_addresses == 256
    assert sub24.usable_hosts == 254
    assert "192.168.1.1 - 192.168.1.254" in sub24.usable_host_range

    # /28 prefix: 16 addresses, 14 usable
    sub28 = engine.calculate_subnet_geometry("10.0.0.0/28")
    assert sub28.total_addresses == 16
    assert sub28.usable_hosts == 14
    assert sub28.netmask == "255.255.255.240"

    # /30 prefix: 4 addresses, 2 usable
    sub30 = engine.calculate_subnet_geometry("172.16.0.0/30")
    assert sub30.total_addresses == 4
    assert sub30.usable_hosts == 2

    # /32 single host
    sub32 = engine.calculate_subnet_geometry("10.1.1.5/32")
    assert sub32.usable_hosts == 1

    # Invalid CIDR raises ValueError
    with pytest.raises(ValueError):
        engine.calculate_subnet_geometry("invalid_cidr/99")


@pytest.mark.unit
def test_network_forensics_engine_direct() -> None:
    """Verify NetworkForensicsEngine direct execution and typed model returns."""
    engine = NetworkForensicsEngine()

    # 1. Traceroute typed report
    sample_trace = """
    traceroute to target.local (10.0.0.50), 30 hops max
     1  10.0.0.1 (10.0.0.1)  1.5 ms
     2  10.0.0.50 (10.0.0.50)  3.2 ms
    """
    tr_report = engine.analyze_traceroute_hops(sample_trace)
    assert isinstance(tr_report, TracerouteReportData)
    assert tr_report.total_hops == 2
    assert tr_report.reached_target is True
    assert tr_report.target == "target.local"
    # Backward-compatible subscriptable item access
    assert tr_report["total_hops"] == 2
    assert tr_report["reached_target"] is True

    # 2. Port recon typed report
    port_report = engine.evaluate_port_states(
        [{"port": 80, "response": "SYN/ACK"}, {"port": 22, "response": "RST"}]
    )
    assert isinstance(port_report, PortReconReportData)
    assert port_report.open_ports == [80]
    assert port_report.closed_ports == [22]
    assert port_report["open_ports"] == [80]

    # 3. Flag decode typed report
    flag_report = engine.decode_tcp_flags("0x29")
    assert isinstance(flag_report, TCPFlagAnalysisData)
    assert flag_report.anomalous is True
    assert "Xmas Scan" in (flag_report.evasion_type or "")
    assert flag_report["is_fin"] is True

    # 4. 7-layer diagnostic typed report
    diag_report = engine.run_7layer_diagnostic_chain("127.0.0.1", port=80)
    assert isinstance(diag_report, DiagnosticChainReportData)
    assert diag_report.all_passed is True
    assert diag_report.earliest_failing_layer is None


@pytest.mark.unit
def test_visual_brief_generation() -> None:
    """Verify NetworkForensicsEngine renders an interactive HTML visual brief in %TEMP%."""
    engine = NetworkForensicsEngine()
    out_path = engine.generate_visual_brief()
    assert out_path is not None
    p = Path(out_path)
    assert p.exists()
    assert p.suffix == ".html"
    content = p.read_text(encoding="utf-8")
    assert "mermaid" in content
    assert "Tri-State Port Reachability" in content
    assert "7-Layer OSI Fault Tree" in content
    assert len(content) > 1000


@pytest.mark.integration
def test_headless_click_cli_seams() -> None:
    """Verify Rule 10 & Rule 26: headless Click CLI inspection and JSON export seams."""
    import json
    from click.testing import CliRunner
    from harness.commands.network_forensics import network_forensics_group

    runner = CliRunner()

    # 1. decode-flags with JSON output
    res_flags = runner.invoke(
        network_forensics_group, ["decode-flags", "0x29", "--json-output"]
    )
    assert res_flags.exit_code == 0
    data_flags = json.loads(res_flags.output)
    assert data_flags["anomalous"] is True
    assert "Xmas Scan" in data_flags["evasion_type"]

    # 2. subnet with JSON output
    res_sub = runner.invoke(
        network_forensics_group, ["subnet", "192.168.1.0/24", "--json-output"]
    )
    assert res_sub.exit_code == 0
    data_sub = json.loads(res_sub.output)
    assert data_sub["usable_hosts"] == 254
    assert data_sub["netmask"] == "255.255.255.0"

    # 3. cleartext with JSON output
    res_clear = runner.invoke(
        network_forensics_group,
        ["cleartext", "--proto", "HTTP", "--port", "80", "--json-output"],
    )
    assert res_clear.exit_code == 0
    data_clear = json.loads(res_clear.output)
    assert data_clear["is_cleartext"] is True

    # 4. diagnose-7layer with JSON output
    res_diag = runner.invoke(
        network_forensics_group,
        ["diagnose-7layer", "10.0.0.1", "--port", "80", "--json-output"],
    )
    assert res_diag.exit_code == 0
    data_diag = json.loads(res_diag.output)
    assert data_diag["all_passed"] is True


@pytest.mark.integration
def test_standalone_skill_script_dispatch() -> None:
    """Verify Rule 49: standalone skill runner script syntax and headless execution."""
    import ast
    import json
    import subprocess

    script_path = _SKILL_DIR / "scripts" / "network_diagnostics.py"
    assert script_path.exists(), f"Skill runner script missing: {script_path}"

    # Syntax and AST check
    code = script_path.read_text(encoding="utf-8")
    tree = ast.parse(code)
    func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "main" in func_names
    assert "build_parser" in func_names

    # Subprocess execution with .venv python
    venv_py = _WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        proc = subprocess.run(
            [str(venv_py), str(script_path), "--subnet", "10.0.0.0/28", "--json"],
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["usable_hosts"] == 14
