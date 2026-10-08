"""Slotted and frozen domain models for network forensics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class HopAnalysisResult:
    """Slotted and frozen model representing a parsed traceroute hop."""

    hop_number: int
    ip_address: str
    rtt_ms: float
    status: str = "active"
    is_intermediate_decrement: bool = False

    def __post_init__(self) -> None:
        assert self.hop_number >= 1, "Hop number must be positive integer"
        assert self.rtt_ms >= 0.0, "RTT must be non-negative"


@dataclass(slots=True, frozen=True)
class PortScanEvaluation:
    """Slotted model representing tri-state port evaluation."""

    port: int
    protocol: str
    state: str
    response_flag: str
    service_guess: str = "unknown"

    def __post_init__(self) -> None:
        assert 1 <= self.port <= 65535, "Port must be in valid range [1, 65535]"
        assert self.state in ("open", "closed", "filtered"), "State must be open, closed, or filtered"


@dataclass(slots=True, frozen=True)
class TCPFlagAnalysis:
    """Slotted model representing TCP flag bitmask deconstruction."""

    raw_hex: str
    flags_set: list[str] = field(default_factory=list)
    is_syn: bool = False
    is_ack: bool = False
    is_fin: bool = False
    is_rst: bool = False
    is_psh: bool = False
    is_urg: bool = False
    anomalous: bool = False
    evasion_type: str | None = None


@dataclass(slots=True, frozen=True)
class LayerDiagnosticResult:
    """Slotted model representing an OSI 7-layer diagnostic check result."""

    layer: int
    layer_name: str
    check_target: str
    passed: bool
    details: str
    remediation: str | None = None

    def __post_init__(self) -> None:
        assert 1 <= self.layer <= 7, "Layer must be an OSI layer between 1 and 7"
