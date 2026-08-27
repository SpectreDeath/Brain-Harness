"""Unified Context Optimization Pipeline: Integrated Seam for Type Channels, Decay, Pruning, and AST Skeletonization."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceKey
from plugins.memory_and_epistemics.context_compiler.compiler_core import (
    ContextCompiler,
    ModuleIndex,
)
from plugins.memory_and_epistemics.memory_decay_engine.decay_core import (
    DecaySessionStore,
    EbbinghausMemoryEngine,
)
from plugins.memory_and_epistemics.prompt_pruning_layer.pruner_core import (
    Message,
    PromptBuilder,
    PromptPruner,
)

logger = structlog.get_logger()


@dataclass
class PipelineMessage:
    id: str
    role: str
    content: str
    turn: int = 0
    channel: str = "memory"
    tool_call_key: str | None = None
    is_foundational: bool = False
    stability: float = 5.0

    def to_message(self) -> Message:
        return Message(
            id=self.id,
            role=self.role,
            content=self.content,
            turn=self.turn,
            tool_call_key=self.tool_call_key,
        )


@dataclass
class UnifiedPipelineResult:
    session_id: str
    input_messages_count: int
    decay_evicted_count: int
    pruner_removed_count: int
    final_messages_count: int
    tokens_raw: int
    tokens_optimized: int
    token_savings_pct: float
    elapsed_ms: float
    assembled_prompt: str
    code_context: str = ""
    decay_evicted_ids: list[str] = field(default_factory=list)
    pruner_removed_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "input_messages_count": self.input_messages_count,
            "decay_evicted_count": self.decay_evicted_count,
            "pruner_removed_count": self.pruner_removed_count,
            "final_messages_count": self.final_messages_count,
            "tokens_raw": self.tokens_raw,
            "tokens_optimized": self.tokens_optimized,
            "token_savings_pct": round(self.token_savings_pct, 2),
            "elapsed_ms": round(self.elapsed_ms, 3),
            "assembled_prompt": self.assembled_prompt,
            "code_context": self.code_context,
            "decay_evicted_ids": list(self.decay_evicted_ids),
            "pruner_removed_ids": list(self.pruner_removed_ids),
        }


class UnifiedContextPipeline:
    """End-to-end context optimizer seam uniting channel decay, 3-pass pruning, and AST compilation."""

    def __init__(self, decay_store: DecaySessionStore | None = None):
        self.decay_store = decay_store or DecaySessionStore()
        self.pruner = PromptPruner()
        self.builder = PromptBuilder()

    def process(
        self,
        session_id: str,
        messages: list[dict[str, Any] | PipelineMessage],
        target_repo_path: str | None = None,
        target_file_path: str | None = None,
        code_tier_limit: int = 3,
        advance_turn: bool = True,
    ) -> UnifiedPipelineResult:
        """Run full context optimization pipeline.

        1. Ingest into Ebbinghaus decay session with channel weighting.
        2. Advance turn and evict sub-threshold items.
        3. Convert surviving items to Messages and execute 3-pass deterministic pruning.
        4. Optionally compile AST code context if target repo/file is supplied.
        5. Assemble final prompt string and compute multi-stage token savings.
        """
        start = time.perf_counter()
        engine = self.decay_store.get_or_create(session_id)

        raw_messages: list[PipelineMessage] = []
        for i, m in enumerate(messages):
            if isinstance(m, PipelineMessage):
                raw_messages.append(m)
            elif isinstance(m, dict):
                raw_messages.append(
                    PipelineMessage(
                        id=str(m.get("id", f"msg_{i}")),
                        role=m.get("role", "user"),
                        content=m.get("content", ""),
                        turn=int(m.get("turn", engine.current_turn)),
                        channel=m.get("channel", "memory"),
                        tool_call_key=m.get("tool_call_key"),
                        is_foundational=bool(m.get("is_foundational", False)),
                        stability=float(m.get("stability", 5.0)),
                    )
                )

        # Stage 1: Register into Decay Engine
        for pm in raw_messages:
            if pm.id not in engine.items:
                engine.register(
                    key=pm.id,
                    content=pm.content,
                    stability=pm.stability,
                    is_foundational=pm.is_foundational,
                    channel=pm.channel,
                )
            else:
                engine.recall(pm.id)

        # Stage 2: Time Advancement & Decay Eviction
        decay_evicted: list[str] = []
        if advance_turn:
            decay_evicted = engine.step_turn()

        # Filter active messages
        active_ids = {item.key for item in engine.working_set()}
        surviving_messages = [pm.to_message() for pm in raw_messages if pm.id in active_ids]

        tokens_raw = sum(pm.to_message().approx_token_count() for pm in raw_messages)

        # Stage 3: 3-Pass Prompt Pruning
        pruned_messages, prune_report = self.pruner.prune(surviving_messages)

        # Stage 4: Optional AST Code Compilation
        code_context_str = ""
        if target_repo_path and target_file_path and Path(target_repo_path).exists():
            try:
                compiler = ContextCompiler(Path(target_repo_path), max_hops=code_tier_limit)
                compiled = compiler.compile(Path(target_file_path))
                code_context_str = compiled.to_prompt_string()
            except Exception as e:
                logger.warning("ast_code_compilation_skipped", error=str(e))

        # Stage 5: Final Assembly
        assembled_prompt = self.builder.build(pruned_messages)
        tokens_optimized = sum(m.approx_token_count() for m in pruned_messages)
        savings_pct = 100.0 * (1.0 - (tokens_optimized / tokens_raw)) if tokens_raw > 0 else 0.0

        elapsed_ms = (time.perf_counter() - start) * 1000

        return UnifiedPipelineResult(
            session_id=session_id,
            input_messages_count=len(raw_messages),
            decay_evicted_count=len(decay_evicted),
            pruner_removed_count=len(prune_report.removed_ids),
            final_messages_count=len(pruned_messages),
            tokens_raw=tokens_raw,
            tokens_optimized=tokens_optimized,
            token_savings_pct=savings_pct,
            elapsed_ms=elapsed_ms,
            assembled_prompt=assembled_prompt,
            code_context=code_context_str,
            decay_evicted_ids=decay_evicted,
            pruner_removed_ids=prune_report.removed_ids,
        )


UNIFIED_CONTEXT_PIPELINE_SERVICE_KEY = ServiceKey[UnifiedContextPipeline]("domain.unified_context_pipeline")
