"""Network Forensics service protocol, typed models, and ServiceKey.

Elevates network forensics, protocol dissection, tri-state recon,
and 7-layer fault isolation into a first-class micro-kernel IoC service seam.
Synthesized from The Cyber Mentor (2026, ki_20260923_ethical_hacker_networking).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


# -----------------------------------------------------------------------------
# Typed Domain Models & Report Envelopes
# -----------------------------------------------------------------------------


class NetworkReportBase(BaseModel):
    """Base model with backward-compatible dictionary item access."""

    def __getitem__(self, key: str) -> Any:
        try:
            val = getattr(self, key)
            if isinstance(val, list):
                # If items in list are NetworkReportBase, allow dict-like behavior
                return val
            return val
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class HopAnalysisData(NetworkReportBase):
    """Data model for an individual traceroute hop observation."""

    hop_number: int = Field(..., ge=1, description="Hop index in sequence (1-indexed)")
    ip_address: str = Field(
        ..., description="IP address or hostname at hop (* if filtered)"
    )
    rtt_ms: float = Field(default=0.0, description="Round trip time in milliseconds")
    status: str = Field(
        default="active", description="Hop status: active, filtered, unreachable"
    )
    is_intermediate_decrement: bool = Field(
        default=True, description="Whether router decremented TTL"
    )


class TracerouteReportData(NetworkReportBase):
    """Data envelope for aggregated traceroute hop analysis results."""

    status: str = Field(default="ok", description="Status indicator")
    target: str = Field(default="unknown", description="Target destination")
    total_hops: int = Field(default=0, description="Total hops evaluated")
    reached_target: bool = Field(default=False, description="Whether target responded")
    hops: list[HopAnalysisData] = Field(default_factory=list, description="Parsed hops")
    anomalies: list[dict[str, Any]] = Field(
        default_factory=list, description="Routing loops, latency spikes, filters"
    )


class PortEvaluationData(NetworkReportBase):
    """Data model for an individual port reachability evaluation."""

    port: int = Field(..., ge=1, le=65535, description="Port number")
    protocol: str = Field(default="TCP", description="Transport protocol (TCP, UDP)")
    state: str = Field(..., description="Tri-state status: open, closed, filtered")
    response_flag: str = Field(
        default="NO_RESPONSE", description="Observed response signature"
    )
    service_guess: str = Field(default="unknown", description="Service name guess")


class PortReconReportData(NetworkReportBase):
    """Data envelope for multi-port tri-state reconnaissance results."""

    status: str = Field(default="ok", description="Status indicator")
    total_ports: int = Field(default=0, description="Total ports evaluated")
    open_ports: list[int] = Field(
        default_factory=list, description="Open ports (SYN/ACK)"
    )
    closed_ports: list[int] = Field(
        default_factory=list, description="Closed ports (RST)"
    )
    filtered_ports: list[int] = Field(
        default_factory=list, description="Filtered ports (drop/timeout)"
    )
    evaluations: list[PortEvaluationData] = Field(
        default_factory=list, description="Detailed evaluations"
    )


class TCPFlagAnalysisData(NetworkReportBase):
    """Data model for decoded TCP header flags and evasion signatures."""

    status: str = Field(default="ok", description="Status indicator")
    raw_hex: str = Field(
        ..., description="Raw hexadecimal flag string (e.g. 0x02, 0x29)"
    )
    flags_set: list[str] = Field(
        default_factory=list, description="Names of asserted flags"
    )
    is_syn: bool = Field(default=False, description="SYN flag asserted")
    is_ack: bool = Field(default=False, description="ACK flag asserted")
    is_fin: bool = Field(default=False, description="FIN flag asserted")
    is_rst: bool = Field(default=False, description="RST flag asserted")
    is_psh: bool = Field(default=False, description="PSH flag asserted")
    is_urg: bool = Field(default=False, description="URG flag asserted")
    anomalous: bool = Field(
        default=False, description="Whether flags represent an evasion scan"
    )
    evasion_type: str | None = Field(
        default=None, description="Evasion pattern description"
    )


class CleartextExposureData(NetworkReportBase):
    """Data model for cleartext protocol exposure and credential risk."""

    status: str = Field(default="ok", description="Status indicator")
    protocol: str = Field(..., description="Protocol name (HTTP, Telnet, FTP, etc.)")
    port: int = Field(..., description="Port number")
    is_cleartext: bool = Field(
        default=False, description="Whether traffic is unencrypted"
    )
    severity: str = Field(
        default="info", description="Severity: info, medium, high, critical"
    )
    credential_harvest_risk: str = Field(
        default="", description="Harvesting risk detail for packet sniffing"
    )
    recommendation: str = Field(
        default="", description="Mitigation or encryption recommendation"
    )


class LayerDiagnosticData(NetworkReportBase):
    """Data model for an individual OSI layer fault isolation check."""

    layer: int = Field(..., ge=1, le=7, description="OSI layer number (1 to 7)")
    layer_name: str = Field(
        ..., description="Layer name: Physical, Data Link, Network, etc."
    )
    check_target: str = Field(..., description="Specific target or component checked")
    passed: bool = Field(..., description="Whether layer check passed")
    details: str = Field(..., description="Diagnostic observation details")
    remediation: str | None = Field(
        default=None, description="Remediation instructions if failed"
    )


class DiagnosticChainReportData(NetworkReportBase):
    """Data envelope for systematic 7-layer network fault isolation."""

    status: str = Field(default="ok", description="Status indicator")
    target: str = Field(..., description="Diagnostic target destination")
    port: int = Field(default=80, description="Diagnostic port")
    all_passed: bool = Field(..., description="Whether all evaluated layers passed")
    earliest_failing_layer: int | None = Field(
        default=None, description="Lowest OSI layer with failure"
    )
    results: list[LayerDiagnosticData] = Field(
        default_factory=list, description="Per-layer observations"
    )
    remediations: list[str] = Field(
        default_factory=list, description="Ordered remediations"
    )


class SubnetGeometryData(NetworkReportBase):
    """Data model for bitwise IPv4 CIDR subnet geometry and host bounds."""

    status: str = Field(default="ok", description="Status indicator")
    cidr: str = Field(..., description="Input CIDR notation (e.g. 192.168.1.0/24)")
    network_address: str = Field(..., description="Network boundary address")
    broadcast_address: str = Field(..., description="Broadcast boundary address")
    netmask: str = Field(..., description="Dotted decimal subnet mask")
    prefix_length: int = Field(..., ge=0, le=32, description="Prefix length /n")
    total_addresses: int = Field(
        ..., description="Total address space in subnet (2^(32-n))"
    )
    usable_hosts: int = Field(..., description="Usable host count (total - 2)")
    usable_host_range: str = Field(..., description="First and last usable host IPs")


# -----------------------------------------------------------------------------
# Micro-Kernel Service Protocol
# -----------------------------------------------------------------------------


@runtime_checkable
class NetworkForensicsService(Protocol):
    """Protocol defining network forensics and diagnostic operations."""

    def audit_port_configuration(self, open_ports: list[Any]) -> dict[str, Any]:
        """Audit open ports and exposed network services against security best practices."""
        ...

    def analyze_packet_summary(self, flows: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze network flows for port scans, SYN floods, and volumetric flooding."""
        ...

    def inspect_tls_certificate(self, cert_info: dict[str, Any]) -> dict[str, Any]:
        """Audit TLS certificate validity, expiration window, and protocol version."""
        ...

    def analyze_traceroute_hops(
        self, raw_output: str
    ) -> TracerouteReportData | dict[str, Any]:
        """Parse traceroute output, identify intermediate TTL-decrementing hops, and detect latency anomalies."""
        ...

    def evaluate_port_states(
        self, scan_results: list[dict[str, Any]]
    ) -> PortReconReportData | dict[str, Any]:
        """Classify port scan findings into tri-state reachability: open, closed, or filtered."""
        ...

    def decode_tcp_flags(self, flags_hex: str) -> TCPFlagAnalysisData | dict[str, Any]:
        """Decode hexadecimal TCP flags, evaluate handshake semantics, and detect scan evasion signatures."""
        ...

    def classify_cleartext_exposure(
        self, protocol: str, port: int
    ) -> CleartextExposureData | dict[str, Any]:
        """Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities."""
        ...

    def run_7layer_diagnostic_chain(
        self, target: str, port: int = 80
    ) -> DiagnosticChainReportData | dict[str, Any]:
        """Execute systematic 7-layer network fault isolation chain from physical to application layer."""
        ...

    def calculate_subnet_geometry(
        self, cidr: str
    ) -> SubnetGeometryData | dict[str, Any]:
        """Calculate bitwise network address, broadcast address, and host capacity for a CIDR prefix."""
        ...

    def generate_visual_brief(self, output_path: str | None = None) -> str:
        """Generate interactive HTML visual brief with Mermaid network topology diagrams in %TEMP%."""
        ...


NETWORK_FORENSICS_KEY: ServiceKey[NetworkForensicsService] = ServiceKey(
    "service.network_forensics"
)
