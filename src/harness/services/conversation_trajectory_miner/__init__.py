"""Conversation Trajectory Miner Service Package.

Extracts, indexes, and mines autobiographical execution trajectories from IDE
conversation databases (conversations/*.db) and transcript logs (transcript.jsonl).
"""

from __future__ import annotations

from .binary_seek import ByteOffsetSeekTable
from .constants import STATUS_MAP, STEP_TYPE_MAP
from .models import (
    CognitiveBifurcationReport,
    ConversationManifest,
    FailureCluster,
    FrictionScorecard,
    IsnadClaimRecord,
    TrajectoryStepRecord,
)
from .resolvers import resolve_conversation_trajectory_miner
from .service import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    ConversationTrajectoryMinerService,
    StandardConversationTrajectoryMinerService,
)

__all__ = [
    "ByteOffsetSeekTable",
    "CognitiveBifurcationReport",
    "CONVERSATION_TRAJECTORY_MINER_KEY",
    "ConversationManifest",
    "ConversationTrajectoryMinerService",
    "FailureCluster",
    "FrictionScorecard",
    "IsnadClaimRecord",
    "STATUS_MAP",
    "STEP_TYPE_MAP",
    "StandardConversationTrajectoryMinerService",
    "TrajectoryStepRecord",
    "resolve_conversation_trajectory_miner",
]
