"""TokenEconomizer service protocol, typed models, and ServiceKey.

Based on UC Berkeley & Microsoft Research (arXiv:2610.22732):
Experience-driven black-box cost control for coding agents through:
1. Micro-skills lifecycle & asymmetric contradiction eviction
2. Dynamic evidence-based tool pruning with protected work surfaces
3. 3-tier failure-loop turn guard with non-destructive mirroring
4. Unified multi-agent trajectory trace and pricing ledger federation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class MicroSkillFact:
    """Slotted immutable representation of a repository micro-skill fact."""

    key: str
    state: str  # CANDIDATE | ACTIVE | RETIRED
    confirms_count: int
    contradicts_count: int
    score: float
    firing_rate: float
    is_high_stakes: bool = False
    assertion: str = ""
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("MicroSkillFact.key cannot be empty")
        if self.state not in ("CANDIDATE", "ACTIVE", "RETIRED"):
            raise ValueError(f"Invalid micro-skill state: {self.state}")
        if self.confirms_count < 0 or self.contradicts_count < 0:
            raise ValueError("Confirmations and contradictions cannot be negative")
        if not (0.0 <= self.firing_rate <= 1.0):
            raise ValueError(f"firing_rate must be between 0.0 and 1.0, got {self.firing_rate}")


@dataclass(slots=True, frozen=True)
class ToolPrunePolicy:
    """Slotted immutable policy of pruned vs protected tools."""

    status: str
    pruned_tools: tuple[str, ...] = field(default_factory=tuple)
    protected_tools: tuple[str, ...] = field(default_factory=tuple)
    inapplicable_tools: tuple[str, ...] = field(default_factory=tuple)
    estimated_tokens_saved: int = 0
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("ok", "skipped", "error"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.estimated_tokens_saved < 0:
            raise ValueError("Tokens saved cannot be negative")


@dataclass(slots=True, frozen=True)
class TurnGuardDecision:
    """Slotted immutable decision from 3-tier failure-loop intervention."""

    is_stuck: bool
    tier: int  # 0: None, 1: Heuristic Conjunction, 2: Paid LLM Judge
    action: str  # "continue" | "nudge" | "abort"
    reason: str
    nudge_text: str | None = None
    edit_churn: int = 0
    error_outputs: int = 0
    stagnation_ratio: float = 0.0
    envelope_ratio: float = 0.0
    error: str | None = None

    def __post_init__(self) -> None:
        if self.action not in ("continue", "nudge", "abort"):
            raise ValueError(f"Invalid action: {self.action}")
        if not (0 <= self.tier <= 2):
            raise ValueError(f"tier must be 0, 1, or 2, got {self.tier}")
        if not (0.0 <= self.stagnation_ratio <= 1.0):
            raise ValueError(f"stagnation_ratio must be between 0.0 and 1.0, got {self.stagnation_ratio}")


@dataclass(slots=True, frozen=True)
class TrajectoryTrace:
    """Slotted immutable parsed trajectory of an agent session."""

    session_id: str
    agent_type: str
    turns_count: int
    tool_calls_count: int
    distinct_tools: tuple[str, ...] = field(default_factory=tuple)
    total_tokens_spent: int = 0
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not self.session_id.strip():
            raise ValueError("session_id cannot be empty")
        if self.turns_count < 0 or self.tool_calls_count < 0 or self.total_tokens_spent < 0:
            raise ValueError("Turn/call/token counts cannot be negative")


@dataclass(slots=True, frozen=True)
class TokenLedgerMetrics:
    """Slotted immutable token and pricing ledger metrics."""

    total_in_tokens: int
    total_out_tokens: int
    net_tokens_saved: int
    net_cost_saved_usd: float
    active_microskills_count: int
    pruned_tools_count: int
    loop_nudges_count: int
    loop_aborts_count: int

    def __post_init__(self) -> None:
        if self.total_in_tokens < 0 or self.total_out_tokens < 0 or self.net_tokens_saved < 0:
            raise ValueError("Token counts cannot be negative")
        if (
            self.active_microskills_count < 0
            or self.pruned_tools_count < 0
            or self.loop_nudges_count < 0
            or self.loop_aborts_count < 0
        ):
            raise ValueError("Counts cannot be negative")


@runtime_checkable
class TokenEconomizerService(Protocol):
    """Protocol for experience-driven cost control, micro-skills, tool pruning, and turn guard."""

    def record_micro_skill_observation(
        self,
        key: str,
        success: bool,
        edited_files: list[str] | None = None,
        is_high_stakes: bool = False,
        assertion: str = "",
    ) -> MicroSkillFact:
        """Record an observation of an environmental fact across agent sessions."""
        ...

    def get_active_micro_skills(self) -> tuple[MicroSkillFact, ...]:
        """Retrieve all currently ACTIVE micro-skills clearing the firing gate."""
        ...

    def evaluate_tool_pruning(
        self,
        loaded_tools: list[str],
        session_tool_history: list[dict[str, int]],
        protected_tools: list[str] | None = None,
        inapplicable_tools: list[str] | None = None,
        evidence_sessions_threshold: int = 2,
    ) -> ToolPrunePolicy:
        """Evaluate loaded tools against usage history and compute exclusion set."""
        ...

    def evaluate_turn_guard(
        self,
        turn_history: list[dict[str, Any]],
        envelope_turn_p90: int = 20,
        envelope_margin: float = 1.25,
        level: str = "default",
    ) -> TurnGuardDecision:
        """Evaluate ongoing turn trajectory against 3-tier failure-loop heuristics."""
        ...

    def parse_trajectory(
        self,
        raw_log: str | dict[str, Any],
        agent_format: str = "generic_jsonl",
    ) -> TrajectoryTrace:
        """Parse raw agent session log into standardized trajectory trace."""
        ...

    def get_token_ledger(self, reset: bool = False) -> TokenLedgerMetrics:
        """Retrieve cumulative session savings, tokens trimmed, and pricing metrics."""
        ...


TOKEN_ECONOMIZER_SERVICE_KEY: ServiceKey[TokenEconomizerService] = ServiceKey(
    "memory.token_economizer"
)

