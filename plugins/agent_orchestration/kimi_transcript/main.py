"""Kimi Transcript Plugin — Isomorphic 4-layer transcript data engine and 4-tier DI scope inspector."""

from __future__ import annotations

import time
import uuid
from typing import Any
import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.kimi_bridge import (
    KIMI_TRANSCRIPT_KEY,
    KimiTranscriptService,
    ScopeAnnotation,
    TranscriptFrame,
)

logger = structlog.get_logger(__name__)

# Events that are considered turn-level boundaries
TURN_EVENT_TYPES: set[str] = {
    "turn_start",
    "turn_complete",
    "user_input",
    "agent_response",
    "session_start",
    "session_end",
}

# Events that are considered tool block boundaries
BLOCK_EVENT_TYPES: set[str] = {
    "tool_call",
    "tool_result",
    "tool_error",
    "artifact_created",
    "checkpoint_saved",
}.union(TURN_EVENT_TYPES)


class TranscriptProjectionEngine:
    """Isomorphic 4-layer projection engine filtering agent streams by client granularity."""

    def normalize_frame(self, raw: dict[str, Any] | TranscriptFrame, default_turn: int = 0) -> TranscriptFrame:
        """Coerce dict or frame into a normalized TranscriptFrame."""
        if isinstance(raw, TranscriptFrame):
            return raw

        frame_id = str(raw.get("frame_id") or f"frm_{uuid.uuid4().hex[:8]}")
        turn_index = int(raw.get("turn_index", default_turn))
        granularity = str(raw.get("granularity", "delta")).lower()
        event_type = str(raw.get("event_type") or raw.get("type", "unknown"))
        payload = raw.get("payload", {})
        if not isinstance(payload, dict):
            payload = {"raw_payload": payload}
        ts = float(raw.get("timestamp", time.time()))

        return TranscriptFrame(
            frame_id=frame_id,
            turn_index=turn_index,
            granularity=granularity,
            event_type=event_type,
            payload=payload,
            timestamp=ts,
        )

    def filter_by_granularity(
        self,
        frames: list[TranscriptFrame],
        granularity: str = "delta",
    ) -> list[TranscriptFrame]:
        """Filter frames based on requested granularity: off, turn, block, delta."""
        g = granularity.lower()

        if g == "off":
            return []

        if g == "turn":
            return [f for f in frames if f.event_type in TURN_EVENT_TYPES]

        if g == "block":
            return [f for f in frames if f.event_type in BLOCK_EVENT_TYPES]

        # "delta" or any fallback returns all frames
        return list(frames)

    def project(
        self,
        raw_frames: list[dict[str, Any]] | list[TranscriptFrame],
        granularity: str = "delta",
        cursor: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Project and paginate transcript frames."""
        normalized = [self.normalize_frame(f, default_turn=i) for i, f in enumerate(raw_frames)]
        filtered = self.filter_by_granularity(normalized, granularity=granularity)

        total_count = len(filtered)
        start_idx = max(0, cursor)
        end_idx = min(total_count, start_idx + limit)
        page = filtered[start_idx:end_idx]
        has_more = end_idx < total_count
        next_cursor = end_idx if has_more else None

        return {
            "status": "ok",
            "granularity": granularity,
            "total_count": total_count,
            "cursor": start_idx,
            "limit": limit,
            "returned_count": len(page),
            "has_more": has_more,
            "next_cursor": next_cursor,
            "frames": [f.to_dict() for f in page],
        }


class ScopeInspector:
    """Inspects ServiceContext hierarchy and infers 4-tier DI scope annotations."""

    SCOPE_DEPTH_ROLES: dict[int, str] = {
        0: "app",
        1: "workspace",
        2: "session",
    }

    def inspect_context(
        self,
        context: ServiceContext,
        depth_limit: int = 10,
        include_services: bool = True,
    ) -> list[ScopeAnnotation]:
        """Walk up or down the context tree and generate ScopeAnnotation models."""
        # 1. Collect chain from current node up to root
        chain: list[ServiceContext] = []
        curr: ServiceContext | None = context
        while curr is not None and len(chain) < depth_limit:
            chain.append(curr)
            curr = curr.parent

        # 2. Reverse so root is index 0
        ordered_contexts = list(reversed(chain))
        annotations: list[ScopeAnnotation] = []

        for depth, ctx in enumerate(ordered_contexts):
            role = self.SCOPE_DEPTH_ROLES.get(depth, "agent")
            ctx_id = f"ctx_scope_{role}_{id(ctx)}"
            parent_id = f"ctx_scope_{self.SCOPE_DEPTH_ROLES.get(depth - 1, 'agent')}_{id(ctx.parent)}" if ctx.parent else None

            # Collect registered keys
            service_keys: list[str] = []
            if include_services and hasattr(ctx, "_entries"):
                service_keys = sorted(list(ctx._entries.keys()))

            annotations.append(
                ScopeAnnotation(
                    context_id=ctx_id,
                    scope_type=role,
                    parent_id=parent_id,
                    depth=depth,
                    service_keys=tuple(service_keys),
                    active_count=len(service_keys),
                )
            )

        return annotations


class KimiTranscriptServiceImpl(KimiTranscriptService):
    """Implementation of KimiTranscriptService providing projection and scope inspection."""

    def __init__(self) -> None:
        self._projection_engine = TranscriptProjectionEngine()
        self._scope_inspector = ScopeInspector()

    def project_transcript(
        self,
        frames: list[dict[str, Any]] | list[TranscriptFrame],
        granularity: str = "delta",
        cursor: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        return self._projection_engine.project(
            raw_frames=frames,
            granularity=granularity,
            cursor=cursor,
            limit=limit,
        )

    def inspect_context_hierarchy(self, context: Any) -> list[ScopeAnnotation]:
        if not isinstance(context, ServiceContext):
            return []
        return self._scope_inspector.inspect_context(context)


# Global service instance
_service_instance = KimiTranscriptServiceImpl()


async def kimi_transcript_project(
    frames: list[dict[str, Any]],
    granularity: str = "delta",
    cursor: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    """Projects raw event frames at client-requested granularity (off, turn, block, delta)."""
    return _service_instance.project_transcript(
        frames=frames,
        granularity=granularity,
        cursor=cursor,
        limit=limit,
    )


async def kimi_scope_inspect(
    context: ServiceContext | None = None,
    depth_limit: int = 10,
    include_services: bool = True,
) -> dict[str, Any]:
    """Introspects the active ServiceContext parent-child hierarchy with 4-tier scope roles."""
    ctx = context or ServiceContext()
    annotations = _service_instance.inspect_context_hierarchy(ctx)
    return {
        "status": "ok",
        "total_depth": len(annotations),
        "scopes": [a.to_dict() for a in annotations],
    }


class KimiTranscriptPlugin(HarnessPlugin):
    """Plugin providing isomorphic transcript streaming and 4-tier DI scope inspection."""

    name = "plugin.kimi_transcript"
    version = "1.0.0"

    def __init__(self, service: KimiTranscriptService | None = None) -> None:
        super().__init__()
        self._service = service or _service_instance

    async def on_enable(self, context: ServiceContext) -> None:
        """Register KimiTranscriptService into context."""
        context.provide(KIMI_TRANSCRIPT_KEY, self._service, provider=self.name)
        logger.info("KimiTranscriptPlugin enabled and service registered")

    async def on_disable(self, context: ServiceContext) -> None:
        """Unregister service on disable."""
        logger.info("KimiTranscriptPlugin disabled")
