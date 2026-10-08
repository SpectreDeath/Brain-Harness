"""NetworkForensicsEngine coordinator unifying network reconnaissance and diagnostic workflows."""

from __future__ import annotations

from typing import Any

from harness.services.network_forensics import (
    CleartextExposureData,
    DiagnosticChainReportData,
    PortReconReportData,
    SubnetGeometryData,
    TCPFlagAnalysisData,
    TracerouteReportData,
)
from .brief import generate_visual_brief
from .diagnostics import (
    _DEFAULT_CLEARTEXT_SERVICES,
    calculate_subnet_geometry,
    classify_cleartext_exposure_data,
    run_7layer_diagnostic_chain_data,
)
from .packets import decode_tcp_flags_data
from .ports import _DEFAULT_DANGEROUS_PORTS, evaluate_port_states_data
from .traceroute import parse_traceroute_hops


class NetworkForensicsEngine:
    """Slotted domain engine executing network reconnaissance and diagnostic workflows."""

    __slots__ = (
        "_default_timeout",
        "_max_hops",
        "_dangerous_ports",
        "_cleartext_services",
    )

    def __init__(
        self,
        default_timeout: float = 30.0,
        max_hops: int = 30,
        dangerous_ports: dict[int, tuple[str, str, str]] | None = None,
        cleartext_services: dict[int, tuple[str, str, str, str]] | None = None,
    ) -> None:
        self._default_timeout = default_timeout
        self._max_hops = max_hops
        self._dangerous_ports = dangerous_ports or _DEFAULT_DANGEROUS_PORTS
        self._cleartext_services = cleartext_services or _DEFAULT_CLEARTEXT_SERVICES

    def calculate_subnet_geometry(self, cidr: str) -> SubnetGeometryData:
        """Calculate bitwise network address, broadcast address, and host bounds for a CIDR prefix."""
        return calculate_subnet_geometry(cidr)

    def analyze_traceroute_hops(self, raw_output: str) -> TracerouteReportData:
        """Parse traceroute output, identify intermediate TTL-decrementing hops, and detect latency anomalies."""
        return parse_traceroute_hops(raw_output, max_hops=self._max_hops)

    def evaluate_port_states(self, port_probes: list[dict[str, Any]]) -> PortReconReportData:
        """Evaluate tri-state reachability of scanned ports across open, closed, and filtered states."""
        return evaluate_port_states_data(port_probes)

    def decode_tcp_flags(self, flags_hex: str) -> TCPFlagAnalysisData:
        """Decode hexadecimal TCP flags, evaluate handshake semantics, and detect scan evasion signatures."""
        return decode_tcp_flags_data(flags_hex)

    def classify_cleartext_exposure(self, protocol: str, port: int) -> CleartextExposureData:
        """Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities."""
        return classify_cleartext_exposure_data(protocol, port, self._cleartext_services)

    def run_7layer_diagnostic_chain(self, target: str, port: int = 80) -> DiagnosticChainReportData:
        """Execute systematic 7-layer network fault isolation chain from physical to application layer."""
        return run_7layer_diagnostic_chain_data(target, port)

    def generate_visual_brief(self, output_path: str | None = None) -> str:
        """Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%."""
        return generate_visual_brief(output_path)
