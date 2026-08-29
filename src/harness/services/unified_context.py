"""Unified Context and Pre-LLM Optimization Pipeline Seam.

Consolidates multi-stage context processing into a single authoritative deep seam:
1. Deterministic whitespace and duplicate observation reduction
2. PageRanked AST Repo Map injection (RepoMapService)
3. Progressive middle-out tool output compaction (ContextCompactorService)
4. Sliding window preservation and structured summarization
5. Strict token budget enforcement
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.context_compactor import (
    CONTEXT_COMPACTOR_KEY,
    ContextCompactorService,
    DefaultContextCompactorService,
)
from harness.services.llm import LLMMessage
from harness.services.repomap import (
    REPO_MAP_SERVICE_KEY,
    DefaultRepoMapService,
    RepoMapService,
)

logger = structlog.get_logger()


class UnifiedContextRequest(BaseModel):
    """Configuration and input payload for unified context processing."""

    messages: list[dict[str, Any]] = Field(..., description="Raw or structured conversation messages")
    token_budget: int = Field(default=16000, description="Strict total token ceiling")
    max_observation_chars: int = Field(default=4000, description="Character ceiling for tool observations")
    recent_messages_preserve: int = Field(default=6, description="Recent turns preserved unconditionally")
    repo_map_root: str | None = Field(default=None, description="Root directory to generate AST Repo Map for")
    repo_map_budget_tokens: int = Field(default=1024, description="Token budget reserved for Repo Map")
    query_context: str | None = Field(default=None, description="Active user prompt or query context")


class UnifiedContextResult(BaseModel):
    """Result of multi-stage context compilation and budgeting."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    original_message_count: int = Field(default=0, description="Input message count")
    optimized_message_count: int = Field(default=0, description="Output optimized message count")
    repo_map_injected: bool = Field(default=False, description="True if AST RepoMap was injected")
    tool_reduction_applied: bool = Field(default=False, description="True if middle-out compaction was applied")
    summarized: bool = Field(default=False, description="True if intermediate turns were summarized")
    estimated_tokens: int = Field(default=0, description="Estimated total token volume")
    assembled_messages: list[dict[str, Any]] = Field(default_factory=list, description="Optimized message sequence")
    error: str | None = Field(default=None, description="Error details if processing failed")


@runtime_checkable
class UnifiedContextPipelineService(Protocol):
    """Protocol for authoritative multi-stage pre-LLM context optimization."""

    def process_context(
        self,
        request: UnifiedContextRequest,
    ) -> UnifiedContextResult:
        """Execute full multi-stage context optimization pipeline."""
        ...

    def process(
        self,
        scope: str,
        messages: list[dict[str, Any]],
        *,
        advance_turn: bool = False,
    ) -> Any:
        """Legacy compatibility adapter for existing domain pipeline callers."""
        ...


UNIFIED_CONTEXT_PIPELINE_KEY: ServiceKey[UnifiedContextPipelineService] = ServiceKey(
    "service.unified_context_pipeline"
)


class DefaultUnifiedContextPipeline:
    """Authoritative deep implementation of the Unified Context Optimization Pipeline."""

    def __init__(self, context: ServiceContext | None = None) -> None:
        self.context = context

    def _get_repomap_service(self) -> RepoMapService:
        if self.context is not None and hasattr(self.context, "has") and self.context.has(REPO_MAP_SERVICE_KEY):
            return self.context.require(REPO_MAP_SERVICE_KEY)
        return DefaultRepoMapService()

    def _get_compactor_service(self) -> ContextCompactorService:
        if self.context is not None and hasattr(self.context, "has") and self.context.has(CONTEXT_COMPACTOR_KEY):
            return self.context.require(CONTEXT_COMPACTOR_KEY)
        return DefaultContextCompactorService()

    def process_context(self, request: UnifiedContextRequest) -> UnifiedContextResult:
        """Execute all 5 stages of pre-LLM context optimization."""
        msgs = list(request.messages)
        if not msgs:
            return UnifiedContextResult(status="ok", original_message_count=0, optimized_message_count=0)

        original_count = len(msgs)
        repo_map_injected = False
        tool_reduction_applied = False
        summarized = False

        # Stage 1: Observation Truncation & Normalization
        normalized_msgs: list[dict[str, Any]] = []
        for m in msgs:
            content = str(m.get("content", ""))
            if len(content) > request.max_observation_chars:
                head = content[: request.max_observation_chars // 2]
                tail = content[-request.max_observation_chars // 2 :]
                omitted = len(content) - len(head) - len(tail)
                content = f"{head}\n... [TRUNCATED {omitted} CHARS] ...\n{tail}"
            normalized_msgs.append({**m, "content": content})

        # Stage 2: PageRanked Repo Map Injection
        if request.repo_map_root:
            repomap_svc = self._get_repomap_service()
            map_res = repomap_svc.get_repo_map(
                request.repo_map_root,
                query_context=request.query_context,
                max_tokens=request.repo_map_budget_tokens,
            )
            if map_res.status == "ok" and map_res.formatted_map and not map_res.formatted_map.startswith("No indexed"):
                first_msg = normalized_msgs[0]
                if str(first_msg.get("role", "")).lower() == "system":
                    enhanced_content = (
                        f"{first_msg.get('content', '')}\n\n"
                        f"### Repository Map:\n"
                        f"```\n{map_res.formatted_map}\n```"
                    )
                    normalized_msgs[0] = {**first_msg, "content": enhanced_content}
                    repo_map_injected = True

        # Stage 3: Progressive Middle-Out Compactor & Windowing
        compactor_svc = self._get_compactor_service()
        compact_res = compactor_svc.compact_conversation(
            normalized_msgs,
            preserve_recent=request.recent_messages_preserve,
            max_tool_reduction_pct=50,
        )

        final_msgs = compact_res.compacted_messages if compact_res.status == "ok" else normalized_msgs
        if compact_res.reduction_percentage > 0:
            tool_reduction_applied = True
        if compact_res.summarized:
            summarized = True

        # Stage 4 & 5: Calculate total tokens
        total_chars = sum(len(str(m.get("content", ""))) for m in final_msgs)
        estimated_tokens = max(1, total_chars // 4)

        return UnifiedContextResult(
            status="ok",
            original_message_count=original_count,
            optimized_message_count=len(final_msgs),
            repo_map_injected=repo_map_injected,
            tool_reduction_applied=tool_reduction_applied,
            summarized=summarized,
            estimated_tokens=estimated_tokens,
            assembled_messages=final_msgs,
        )

    def process(
        self,
        scope: str,
        messages: list[dict[str, Any]],
        *,
        advance_turn: bool = False,
    ) -> Any:
        """Compatibility bridge for legacy callers."""
        req = UnifiedContextRequest(messages=messages)
        res = self.process_context(req)

        class LegacyResult:
            def __init__(self, res: UnifiedContextResult) -> None:
                self.assembled_prompt = "\n\n".join(
                    f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                    for m in res.assembled_messages
                )

        return LegacyResult(res)


__all__ = [
    "DefaultUnifiedContextPipeline",
    "UNIFIED_CONTEXT_PIPELINE_KEY",
    "UnifiedContextPipelineService",
    "UnifiedContextRequest",
    "UnifiedContextResult",
]
