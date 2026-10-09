"""Single-seam resolver factory for ConversationTrajectoryMinerService per Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext

from .service import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    ConversationTrajectoryMinerService,
    StandardConversationTrajectoryMinerService,
)


def resolve_conversation_trajectory_miner(
    ctx: ServiceContext | None = None,
) -> ConversationTrajectoryMinerService:
    """Resolve ConversationTrajectoryMinerService from IoC context or fall back to standard implementation (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(CONVERSATION_TRAJECTORY_MINER_KEY)
        if svc is not None and isinstance(svc, ConversationTrajectoryMinerService):
            return svc
    return StandardConversationTrajectoryMinerService()


__all__ = [
    "resolve_conversation_trajectory_miner",
]
