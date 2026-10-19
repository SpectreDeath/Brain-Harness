"""Slotted domain models for PyRIT GenAI Red-Teaming Scanner (Rule 12)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

VALID_TARGET_TYPES = {"agent_loop", "system_prompt", "tool_interface", "mcp_endpoint"}
VALID_TECHNIQUES = {"crescendo", "roleplay_jailbreak", "encoding_fuzz", "tool_hijack", "prompt_injection"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


@dataclass(slots=True, frozen=True)
class RedTeamTarget:
    """Slotted immutable representation of a red-teaming scan target."""

    target_type: str = "agent_loop"
    endpoint: str = "local"
    max_turns: int = 10
    provider: str = "routed"

    def __post_init__(self) -> None:
        if self.target_type not in VALID_TARGET_TYPES:
            raise ValueError(f"target_type must be one of {sorted(VALID_TARGET_TYPES)}")
        if not self.endpoint:
            raise ValueError("endpoint must be non-empty")
        if self.max_turns <= 0:
            raise ValueError("max_turns must be positive")


@dataclass(slots=True, frozen=True)
class AttackVector:
    """Attack strategy configuration and intensity bounds."""

    technique: str = "crescendo"
    intensity: int = 3
    payload_count: int = 10

    def __post_init__(self) -> None:
        if self.technique not in VALID_TECHNIQUES:
            raise ValueError(f"technique must be one of {sorted(VALID_TECHNIQUES)}")
        if not (1 <= self.intensity <= 5):
            raise ValueError("intensity must be between 1 and 5")
        if self.payload_count <= 0:
            raise ValueError("payload_count must be positive")


@dataclass(slots=True, frozen=True)
class VulnerabilityScorecard:
    """Outcome report evaluating target resistance to adversarial probes."""

    attack_success_rate: float
    leaked_system_tokens: tuple[str, ...]
    bypassed_tool_boundaries: tuple[str, ...]
    risk_level: str
    recommendations: tuple[str, ...]
    elapsed_ms: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.attack_success_rate <= 1.0):
            raise ValueError("attack_success_rate must be in [0.0, 1.0]")
        if self.risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {sorted(VALID_RISK_LEVELS)}")
        if self.elapsed_ms < 0.0:
            raise ValueError("elapsed_ms must be non-negative")
