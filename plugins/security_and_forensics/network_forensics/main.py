"""Network Forensics & Ethical Hacker Networking Plugin for Brain Harness.

Provides automated protocol inspection, tri-state recon, TCP flag decoding,
7-layer fault isolation, subnet bitwise geometry, and packet anomaly detection.
Implements the NetworkForensicsService protocol for micro-kernel IoC integration.
"""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.network_forensics import (
    NETWORK_FORENSICS_KEY,
    NetworkForensicsService,
)

try:
    from . import engine as _mod
except (ImportError, ValueError):
    import engine as _mod  # type: ignore[no-redef]

HopAnalysisResult = _mod.HopAnalysisResult
LayerDiagnosticResult = _mod.LayerDiagnosticResult
NetworkForensicsEngine = _mod.NetworkForensicsEngine
PortScanEvaluation = _mod.PortScanEvaluation
TCPFlagAnalysis = _mod.TCPFlagAnalysis
_CLEARTEXT_SERVICES = _mod._CLEARTEXT_SERVICES
_DANGEROUS_PORTS = _mod._DANGEROUS_PORTS
_TRACEROUTE_LINE_REGEX = _mod._TRACEROUTE_LINE_REGEX
_engine_analyze_packet_summary = _mod.analyze_packet_summary
analyze_traceroute_dict = _mod.analyze_traceroute_dict
_engine_audit_port_configuration = _mod.audit_port_configuration
_calc_subnet_geom = _mod.calculate_subnet_geometry
classify_cleartext_exposure_dict = _mod.classify_cleartext_exposure_dict
decode_tcp_flags_dict = _mod.decode_tcp_flags_dict
evaluate_port_states_dict = _mod.evaluate_port_states_dict
_gen_visual_brief = _mod.generate_visual_brief
_engine_inspect_tls_certificate = _mod.inspect_tls_certificate
run_7layer_diagnostic_chain_dict = _mod.run_7layer_diagnostic_chain_dict

# Global default engine instance
_engine = NetworkForensicsEngine()


# -----------------------------------------------------------------------------
# Module Tool Functions (Callable by Agent, StepExecutionEngine, & Manifest)
# -----------------------------------------------------------------------------

def audit_port_configuration(open_ports: list[int | dict[str, Any]]) -> dict[str, Any]:
    """Audit open ports and exposed network services against security best practices."""
    clean = [int(p.get("port", 0)) if isinstance(p, dict) else int(p) for p in open_ports if isinstance(p, (dict, int, str))]
    return _engine_audit_port_configuration(clean)


def analyze_packet_summary(flows: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze network flows for port scans and DDoS signatures."""
    return _engine_analyze_packet_summary(flows)


def inspect_tls_certificate(cert_info: dict[str, Any]) -> dict[str, Any]:
    """Validate TLS/SSL certificate metadata (issuer, expiration, cipher suites)."""
    return _engine_inspect_tls_certificate(cert_info)


def analyze_traceroute_hops(raw_output: str) -> dict[str, Any]:
    """Parse traceroute output, identify intermediate TTL-decrementing hops, and detect latency anomalies."""
    return analyze_traceroute_dict(raw_output)


def evaluate_port_states(port_probes: list[dict[str, Any]] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Classify port scan findings into tri-state reachability: open, closed, or filtered."""
    probes = port_probes or kwargs.get("scan_results") or []
    return evaluate_port_states_dict(probes)


def decode_tcp_flags(flags_hex: str) -> dict[str, Any]:
    """Decode hexadecimal TCP flags, evaluate handshake semantics, and detect scan evasion signatures."""
    return decode_tcp_flags_dict(flags_hex)


def classify_cleartext_exposure(protocol: str, port: int) -> dict[str, Any]:
    """Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities."""
    return classify_cleartext_exposure_dict(protocol, port)


def run_7layer_diagnostic_chain(target: str, port: int = 80) -> dict[str, Any]:
    """Execute systematic 7-layer network fault isolation chain from physical to application layer."""
    return run_7layer_diagnostic_chain_dict(target, port)


def calculate_subnet_geometry(cidr: str) -> dict[str, Any]:
    """Calculate bitwise network address, broadcast address, and host capacity for an IPv4 CIDR prefix."""
    return _calc_subnet_geom(cidr).model_dump()


def generate_visual_brief(output_path: str | None = None) -> str:
    """Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%."""
    return _gen_visual_brief(output_path)


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Plugin Implementation (Rule 2, 45, 49)
# -----------------------------------------------------------------------------

class NetworkForensicsPlugin(HarnessPlugin, NetworkForensicsService):
    """Network Forensics Plugin exposing network inspection and diagnostic services."""

    def __init__(self, engine: NetworkForensicsEngine | None = None) -> None:
        super().__init__()
        self._engine = engine or _engine

    @property
    def engine(self) -> NetworkForensicsEngine:
        return self._engine

    @property
    def name(self) -> str:
        return "plugin.network_forensics"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Network forensics, tri-state recon, TCP flag decoding, and 7-layer fault isolation engine"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [NETWORK_FORENSICS_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(NETWORK_FORENSICS_KEY, self)

    def analyze_traceroute_hops(self, raw_output: str) -> dict[str, Any]:
        return analyze_traceroute_hops(raw_output)

    def evaluate_port_states(self, port_probes: list[dict[str, Any]]) -> dict[str, Any]:
        return evaluate_port_states(port_probes)

    def decode_tcp_flags(self, flags_hex: str) -> dict[str, Any]:
        return decode_tcp_flags(flags_hex)

    def classify_cleartext_exposure(self, protocol: str, port: int) -> dict[str, Any]:
        return classify_cleartext_exposure(protocol, port)

    def run_7layer_diagnostic_chain(self, target: str, port: int = 80) -> dict[str, Any]:
        return run_7layer_diagnostic_chain(target, port)

    def calculate_subnet_geometry(self, cidr: str) -> dict[str, Any]:
        return calculate_subnet_geometry(cidr)

    def generate_visual_brief(self, output_path: str | None = None) -> str:
        return generate_visual_brief(output_path)


# Module-level singleton (Rule 45)
plugin = NetworkForensicsPlugin()

__all__ = [
    "HopAnalysisResult", "LayerDiagnosticResult", "NetworkForensicsEngine",
    "NetworkForensicsPlugin", "PortScanEvaluation", "TCPFlagAnalysis",
    "_CLEARTEXT_SERVICES", "_DANGEROUS_PORTS", "_TRACEROUTE_LINE_REGEX",
    "_engine", "analyze_packet_summary", "analyze_traceroute_hops",
    "audit_port_configuration", "calculate_subnet_geometry",
    "classify_cleartext_exposure", "decode_tcp_flags",
    "evaluate_port_states", "generate_visual_brief",
    "inspect_tls_certificate", "plugin", "run_7layer_diagnostic_chain",
]
