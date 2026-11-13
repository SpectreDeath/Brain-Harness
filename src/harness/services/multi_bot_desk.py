"""Multi-Bot Desk Orchestrator Service — hop-depth guards, in-band MCP approvals, and screen leases.

Distilled from bot-hq:
- Bounded bot-to-bot relay depth (max 3 hops) and group-chat fan-out limits
- In-band MCP tool approval classification (auto-allow read vs blocking write card)
- Primary-vs-managed bot home, gateway port, CDP port, and display lease allocation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

ApprovalDecision = Literal["auto_allow", "require_approval", "deny", "skipped"]
BotRoleKind = Literal["primary", "managed", "room"]


@dataclass(slots=True, frozen=True)
class BotHopDispatchRequest:
    """Immutable request to relay a message from one bot (or room) to another."""

    from_bot_id: str
    to_bot_id: str
    message_text: str
    current_depth: int = 0
    max_depth: int = 3
    is_room_broadcast: bool = False
    room_member_ids: tuple[str, ...] = ()
    mentioned_bot_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.from_bot_id.strip():
            raise ValueError("from_bot_id must be non-empty")
        if not self.to_bot_id.strip():
            raise ValueError("to_bot_id must be non-empty")
        if self.current_depth < 0:
            raise ValueError("current_depth must be >= 0")
        if self.max_depth < 1:
            raise ValueError("max_depth must be >= 1")


@dataclass(slots=True, frozen=True)
class BotHopDispatchOutcome:
    """Result of evaluating whether a bot-to-bot or room dispatch is permitted."""

    allowed: bool
    next_depth: int
    target_bot_ids: tuple[str, ...]
    reason: str


@dataclass(slots=True, frozen=True)
class McpApprovalRequest:
    """Immutable in-band MCP tool call approval evaluation request."""

    bot_id: str
    tool_name: str
    is_read_only: bool = False
    always_allowed_tools: tuple[str, ...] = ()
    user_interrupted: bool = False

    def __post_init__(self) -> None:
        if not self.bot_id.strip():
            raise ValueError("bot_id must be non-empty")
        if not self.tool_name.strip():
            raise ValueError("tool_name must be non-empty")


@dataclass(slots=True, frozen=True)
class McpApprovalOutcome:
    """Deterministic approval outcome for an in-band MCP tool call."""

    bot_id: str
    tool_name: str
    decision: ApprovalDecision
    blocks_turn: bool
    reason: str


@dataclass(slots=True, frozen=True)
class BotDeskLease:
    """Isolated runtime resource lease for a primary or managed bot."""

    bot_id: str
    role: BotRoleKind
    display_index: int
    gateway_port: int | None
    cdp_port: int | None
    mutates_primary_config: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.bot_id.strip():
            raise ValueError("bot_id must be non-empty")
        if self.display_index < 0:
            raise ValueError("display_index must be >= 0")


class MultiBotDeskEngine:
    """Pure, deterministic domain engine for multi-bot desk orchestration."""

    MAX_SCREENS_PER_COMPUTER = 4
    MAX_ROOM_FANOUT = 3
    BASE_GATEWAY_PORT = 8650
    BASE_CDP_PORT = 9200

    def evaluate_bot_hop_dispatch(
        self, request: BotHopDispatchRequest
    ) -> BotHopDispatchOutcome:
        """Enforce ping-pong hop-depth cap and room-chat fan-out bounds."""
        if request.current_depth >= request.max_depth:
            return BotHopDispatchOutcome(
                allowed=False,
                next_depth=request.current_depth,
                target_bot_ids=(),
                reason=f"hop_depth_limit_reached ({request.current_depth} >= {request.max_depth})",
            )

        if request.is_room_broadcast:
            if request.mentioned_bot_ids:
                targets = tuple(
                    b
                    for b in request.mentioned_bot_ids
                    if b in request.room_member_ids and b != request.from_bot_id
                )[: self.MAX_ROOM_FANOUT]
            else:
                targets = tuple(
                    b for b in request.room_member_ids if b != request.from_bot_id
                )[: self.MAX_ROOM_FANOUT]

            if not targets:
                return BotHopDispatchOutcome(
                    allowed=False,
                    next_depth=request.current_depth + 1,
                    target_bot_ids=(),
                    reason="no_eligible_room_members",
                )
            return BotHopDispatchOutcome(
                allowed=True,
                next_depth=request.current_depth + 1,
                target_bot_ids=targets,
                reason="room_fanout_bounded",
            )

        if request.to_bot_id == request.from_bot_id:
            return BotHopDispatchOutcome(
                allowed=False,
                next_depth=request.current_depth,
                target_bot_ids=(),
                reason="self_dispatch_blocked",
            )

        return BotHopDispatchOutcome(
            allowed=True,
            next_depth=request.current_depth + 1,
            target_bot_ids=(request.to_bot_id,),
            reason="bot_hop_permitted",
        )

    def evaluate_mcp_tool_approval(
        self, request: McpApprovalRequest
    ) -> McpApprovalOutcome:
        """Classify an in-band MCP tool call into auto_allow, require_approval, or skipped."""
        if request.user_interrupted:
            return McpApprovalOutcome(
                bot_id=request.bot_id,
                tool_name=request.tool_name,
                decision="skipped",
                blocks_turn=False,
                reason="superseded_by_user_interrupt",
            )

        if request.is_read_only:
            return McpApprovalOutcome(
                bot_id=request.bot_id,
                tool_name=request.tool_name,
                decision="auto_allow",
                blocks_turn=False,
                reason="read_only_tool_fast_path",
            )

        if request.tool_name in request.always_allowed_tools:
            return McpApprovalOutcome(
                bot_id=request.bot_id,
                tool_name=request.tool_name,
                decision="auto_allow",
                blocks_turn=False,
                reason="stored_always_allow_policy",
            )

        return McpApprovalOutcome(
            bot_id=request.bot_id,
            tool_name=request.tool_name,
            decision="require_approval",
            blocks_turn=True,
            reason="write_tool_awaits_card_approval",
        )

    def allocate_bot_desk_lease(
        self,
        bot_id: str,
        *,
        is_primary: bool = False,
        occupied_displays: tuple[int, ...] = (),
    ) -> BotDeskLease:
        """Allocate an isolated display, gateway port, and CDP port without mutating primary config."""
        if is_primary:
            return BotDeskLease(
                bot_id=bot_id,
                role="primary",
                display_index=0,
                gateway_port=None,
                cdp_port=None,
                mutates_primary_config=False,
                metadata={"isolation": "external_primary_gateway"},
            )

        used = set(occupied_displays) | {0}
        free_slot = next(
            (i for i in range(1, self.MAX_SCREENS_PER_COMPUTER) if i not in used),
            None,
        )
        if free_slot is None:
            raise ValueError(
                f"No free screen slots remaining (max {self.MAX_SCREENS_PER_COMPUTER})"
            )

        return BotDeskLease(
            bot_id=bot_id,
            role="managed",
            display_index=free_slot,
            gateway_port=self.BASE_GATEWAY_PORT + free_slot,
            cdp_port=self.BASE_CDP_PORT + free_slot,
            mutates_primary_config=False,
            metadata={"isolation": "managed_hermes_home"},
        )


@runtime_checkable
class MultiBotDeskProtocol(Protocol):
    """Typed IoC service protocol for multi-bot desk orchestration."""

    def evaluate_bot_hop_dispatch(
        self, request: BotHopDispatchRequest
    ) -> BotHopDispatchOutcome: ...

    def evaluate_mcp_tool_approval(
        self, request: McpApprovalRequest
    ) -> McpApprovalOutcome: ...

    def allocate_bot_desk_lease(
        self,
        bot_id: str,
        *,
        is_primary: bool = False,
        occupied_displays: tuple[int, ...] = (),
    ) -> BotDeskLease: ...


MULTI_BOT_DESK_SERVICE_KEY: ServiceKey[MultiBotDeskProtocol] = ServiceKey(
    "service.multi_bot_desk_orchestrator"
)

__all__ = [
    "ApprovalDecision",
    "BotDeskLease",
    "BotHopDispatchOutcome",
    "BotHopDispatchRequest",
    "BotRoleKind",
    "MULTI_BOT_DESK_SERVICE_KEY",
    "McpApprovalOutcome",
    "McpApprovalRequest",
    "MultiBotDeskEngine",
    "MultiBotDeskProtocol",
]
