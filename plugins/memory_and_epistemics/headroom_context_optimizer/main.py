"""Headroom Context Optimizer Plugin.

Provides intelligent context routing, SmartCrusher JSON array compaction,
Cross-Context Retrieval (CCR) deduplication, cache alignment drift detection,
and prior-turn extended thinking compaction.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import uuid
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.headroom_optimizer import (
    HEADROOM_CONTEXT_OPTIMIZER_KEY,
    CacheDriftResult,
    ContentCompressResult,
    DedupTurnsResult,
    HeadroomContextOptimizerService,
    SavingsLedger,
    ThinkingCompactResult,
)
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

logger = structlog.get_logger(__name__)


def _estimate_tokens(text: str) -> int:
    """Fast deterministic token estimator (roughly 4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


class HeadroomContextOptimizerEngine(HeadroomContextOptimizerService):
    """Execution engine for Headroom context optimization algorithms."""

    def __init__(self) -> None:
        self._total_in_tokens: int = 0
        self._total_out_tokens: int = 0
        self._net_tokens_saved: int = 0
        self._strategy_counts: dict[str, int] = Counter()
        self._digest_cache: dict[str, str] = {}

    def compress_content(
        self,
        content: str,
        content_type: str | None = None,
        target_ratio: float = 0.6,
        preserve_keys: list[str] | None = None,
    ) -> ContentCompressResult:
        if not content or not content.strip():
            return ContentCompressResult(
                status="skipped",
                original_tokens=0,
                compressed_tokens=0,
                savings_ratio=0.0,
                strategy="passthrough",
                compressed_text=content,
            )

        orig_toks = _estimate_tokens(content)
        detected_type = content_type.lower() if content_type else self._detect_content_type(content)
        strategy = detected_type
        compressed = content

        if detected_type == "json":
            compressed, strategy = self._compress_json(content, preserve_keys or [])
        elif detected_type == "code":
            compressed, strategy = self._compress_code(content)
        elif detected_type == "log":
            compressed, strategy = self._compress_logs(content)
        elif detected_type == "search":
            compressed, strategy = self._compress_search_results(content)
        elif detected_type == "diff":
            compressed, strategy = self._compress_diff(content)
        else:
            compressed, strategy = self._compress_text(content)

        comp_toks = _estimate_tokens(compressed)
        if comp_toks > orig_toks:
            compressed = content
            comp_toks = orig_toks
            strategy = "passthrough"

        saved_toks = max(0, orig_toks - comp_toks)
        ratio = (saved_toks / orig_toks) if orig_toks > 0 else 0.0

        self._total_in_tokens += orig_toks
        self._total_out_tokens += comp_toks
        self._net_tokens_saved += saved_toks
        self._strategy_counts[strategy] = self._strategy_counts.get(strategy, 0) + 1

        return ContentCompressResult(
            status="ok",
            original_tokens=orig_toks,
            compressed_tokens=comp_toks,
            savings_ratio=round(min(1.0, max(0.0, ratio)), 4),
            strategy=strategy,
            compressed_text=compressed,
        )

    def dedup_turns(
        self,
        messages: list[dict[str, Any]],
        min_lines: int = 3,
        min_chars: int = 40,
    ) -> DedupTurnsResult:
        if not messages:
            return DedupTurnsResult(
                status="ok",
                compacted_messages=[],
                deduplicated_blocks=0,
                tokens_saved=0,
            )

        seen_blocks: dict[str, str] = {}  # hash -> first observation summary
        dedup_count = 0
        tokens_saved = 0
        new_messages: list[dict[str, Any]] = []

        for msg in messages:
            content = msg.get("content")
            role = msg.get("role", "user")

            if isinstance(content, str) and len(content) >= min_chars and content.count("\n") >= min_lines - 1:
                block_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:12]
                if block_hash in seen_blocks:
                    # Deduplicate with CCR digest marker
                    orig_tok = _estimate_tokens(content)
                    marker = f"[CCR tool digest: {block_hash} | original length: {len(content)} chars | matching turn {seen_blocks[block_hash]}]"
                    marker_tok = _estimate_tokens(marker)
                    saved = max(0, orig_tok - marker_tok)
                    tokens_saved += saved
                    dedup_count += 1
                    new_messages.append({"role": role, "content": marker})
                    continue
                else:
                    seen_blocks[block_hash] = f"role={role}"
                    new_messages.append(msg)
            else:
                new_messages.append(msg)

        self._net_tokens_saved += tokens_saved
        return DedupTurnsResult(
            status="ok",
            compacted_messages=new_messages,
            deduplicated_blocks=dedup_count,
            tokens_saved=tokens_saved,
        )

    def detect_cache_drift(
        self,
        system_prompt: str,
    ) -> CacheDriftResult:
        if not system_prompt:
            return CacheDriftResult(status="ok", is_cache_stable=True, volatile_items=[], recommendations=[])

        volatile: list[dict[str, Any]] = []
        recs: list[str] = []

        # 1. UUID Detection
        uuid_pattern = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
        for match in uuid_pattern.finditer(system_prompt):
            raw = match.group(0)
            try:
                val = uuid.UUID(raw)
                volatile.append({"type": "uuid", "value": raw, "position": match.start()})
            except ValueError:
                pass

        # 2. ISO 8601 Timestamps
        iso_pattern = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
        for match in iso_pattern.finditer(system_prompt):
            volatile.append({"type": "timestamp_iso8601", "value": match.group(0), "position": match.start()})

        # 3. Hex Hashes (32, 40, or 64 hex characters)
        hash_pattern = re.compile(r"\b([0-9a-fA-F]{32}|[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\b")
        for match in hash_pattern.finditer(system_prompt):
            volatile.append({"type": "hex_hash", "value": match.group(0), "position": match.start()})

        # 4. JWT Detection (3 base64url segments separated by dots)
        jwt_pattern = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
        for match in jwt_pattern.finditer(system_prompt):
            volatile.append({"type": "jwt_token", "value": match.group(0)[:15] + "...", "position": match.start()})

        is_stable = len(volatile) == 0
        if not is_stable:
            recs.append("Isolate dynamic timestamps and UUIDs into user context turns rather than the system prompt.")
            recs.append("Keep system prompt prefix 100% byte-identical across requests to maintain Anthropic/OpenAI prompt cache hits.")

        return CacheDriftResult(
            status="ok",
            is_cache_stable=is_stable,
            volatile_items=volatile,
            recommendations=recs,
        )

    def compact_thinking(
        self,
        messages: list[dict[str, Any]],
        keep_last_turns: int = 2,
    ) -> ThinkingCompactResult:
        if not messages:
            return ThinkingCompactResult(status="ok", messages=[], compacted_turns=0, tokens_saved=0)

        compacted_count = 0
        tokens_saved = 0
        new_msgs: list[dict[str, Any]] = []

        # Identify assistant turns from the end
        assistant_indices = [i for i, m in enumerate(messages) if m.get("role") == "assistant"]
        preserve_indices = set(assistant_indices[-keep_last_turns:]) if keep_last_turns > 0 else set()

        thinking_regex = re.compile(r"<thinking>([\s\S]*?)</thinking>", re.IGNORECASE)

        for i, msg in enumerate(messages):
            if i in preserve_indices or msg.get("role") != "assistant":
                new_msgs.append(msg)
                continue

            content = msg.get("content")
            if isinstance(content, str) and "<thinking>" in content.lower():
                def _replace_thinking(match: re.Match[str]) -> str:
                    nonlocal compacted_count, tokens_saved
                    raw_think = match.group(1).strip()
                    orig_tok = _estimate_tokens(raw_think)
                    th_hash = hashlib.sha256(raw_think.encode("utf-8")).hexdigest()[:8]
                    summary = f"[prior reasoning, compressed: {th_hash} ({orig_tok} toks)]"
                    saved = max(0, orig_tok - _estimate_tokens(summary))
                    tokens_saved += saved
                    compacted_count += 1
                    return summary

                new_content = thinking_regex.sub(_replace_thinking, content)
                new_msgs.append({**msg, "content": new_content})
            else:
                new_msgs.append(msg)

        self._net_tokens_saved += tokens_saved
        return ThinkingCompactResult(
            status="ok",
            messages=new_msgs,
            compacted_turns=compacted_count,
            tokens_saved=tokens_saved,
        )

    def get_savings_metrics(
        self,
        reset: bool = False,
    ) -> SavingsLedger:
        est_cost = (self._net_tokens_saved / 1_000_000) * 3.0  # Approx $3.00/MTok blend
        ledger = SavingsLedger(
            total_in_tokens=self._total_in_tokens,
            total_out_tokens=self._total_out_tokens,
            net_tokens_saved=self._net_tokens_saved,
            net_cost_saved_usd=round(est_cost, 4),
            strategy_counts=dict(self._strategy_counts),
        )
        if reset:
            self._total_in_tokens = 0
            self._total_out_tokens = 0
            self._net_tokens_saved = 0
            self._strategy_counts.clear()
        return ledger

    # -------------------------------------------------------------------------
    # Internal Format Compressors
    # -------------------------------------------------------------------------

    def _detect_content_type(self, text: str) -> str:
        s = text.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            return "json"
        if s.startswith("diff --git") or s.startswith("--- ") or "\n@@ " in s:
            return "diff"
        if re.search(r"^(?:def |class |import |from |function |const |let |var |fn |impl )", s, re.MULTILINE):
            return "code"
        if re.search(r"^\d+:\s", s, re.MULTILINE) or re.search(r"^.*:\d+:.*", s, re.MULTILINE):
            return "search"
        if any(marker in s.lower() for marker in ("error:", "warning:", "traceback", "exception:", "passed in", "failed")):
            return "log"
        return "text"

    def _compress_json(self, text: str, preserve_keys: list[str]) -> tuple[str, str]:
        try:
            data = json.loads(text)
        except Exception:
            return self._compress_text(text)

        if isinstance(data, list) and len(data) > 5:
            # SmartCrusher array compaction
            sample_size = 5
            total = len(data)
            keys = set()
            for item in data:
                if isinstance(item, dict):
                    keys.update(item.keys())
            compacted = {
                "_headroom_smart_crush": True,
                "total_rows": total,
                "schema_keys": sorted(keys),
                "head_sample": data[:3],
                "tail_sample": data[-2:],
            }
            return json.dumps(compacted, ensure_ascii=False, separators=(",", ":")), "smart_crusher_json"

        return json.dumps(data, ensure_ascii=False, separators=(",", ":")), "json_minified"

    def _compress_code(self, text: str) -> tuple[str, str]:
        # Strip consecutive blank lines and trailing line whitespace
        lines = [line.rstrip() for line in text.splitlines()]
        cleaned: list[str] = []
        blank = False
        for l in lines:
            if not l.strip():
                if not blank:
                    cleaned.append("")
                    blank = True
            else:
                cleaned.append(l)
                blank = False
        return "\n".join(cleaned), "code_whitespace_collapsed"

    def _compress_logs(self, text: str) -> tuple[str, str]:
        lines = text.splitlines()
        if len(lines) <= 20:
            return text, "log_passthrough"
        # Keep first 10 and last 10 lines, with summary in middle
        omitted = len(lines) - 20
        res = lines[:10] + [f"... [Headroom LogCompressor: {omitted} lines omitted] ..."] + lines[-10:]
        return "\n".join(res), "log_truncated"

    def _compress_search_results(self, text: str) -> tuple[str, str]:
        # Collapse repetitive paths in grep/ripgrep outputs
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:50]), "search_grouped"

    def _compress_diff(self, text: str) -> tuple[str, str]:
        lines = text.splitlines()
        # Keep diff headers and changed lines
        filtered = [l for l in lines if l.startswith(("+", "-", "@@", "diff", "index"))]
        return "\n".join(filtered), "diff_condensed"

    def _compress_text(self, text: str) -> tuple[str, str]:
        # Remove consecutive whitespaces and excessive newlines
        compacted = re.sub(r"\n{3,}", "\n\n", text.strip())
        return compacted, "text_normalized"


class HeadroomContextOptimizerPlugin(HarnessPlugin):
    """Brain Harness plugin for Headroom context optimization."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = HeadroomContextOptimizerEngine()
        self._context: ServiceContext | None = None

    @property
    def name(self) -> str:
        return "plugin.headroom_context_optimizer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [HEADROOM_CONTEXT_OPTIMIZER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    @property
    def engine(self) -> HeadroomContextOptimizerEngine:
        return self._engine

    async def on_load(self, ctx: ServiceContext) -> None:
        self._context = ctx
        ctx.provide(HEADROOM_CONTEXT_OPTIMIZER_KEY, self._engine, provider=self.name)
        logger.info("headroom_context_optimizer_loaded", service_key=HEADROOM_CONTEXT_OPTIMIZER_KEY.name)

    async def on_enable(self) -> None:
        if self._context and self._context.has(TOOL_REGISTRY_KEY):
            registry: ToolRegistry = self._context.require(TOOL_REGISTRY_KEY)

            registry.register(
                name="headroom_compress_content",
                description="Compress arbitrary content (code, JSON, logs, diffs, text) using Headroom format-aware compressors",
                executor=lambda content, content_type=None, target_ratio=0.6, preserve_keys=None: (
                    asdict(self._engine.compress_content(content, content_type, target_ratio, preserve_keys))
                ),
                provider=self.name,
            )

            registry.register(
                name="headroom_dedup_turns",
                description="Cross-Context Retrieval (CCR): Deduplicate repeating tool returns and observations across conversation turns",
                executor=lambda messages, min_lines=3, min_chars=40: (
                    asdict(self._engine.dedup_turns(messages, min_lines, min_chars))
                ),
                provider=self.name,
            )

            registry.register(
                name="headroom_detect_cache_drift",
                description="Inspect system prompt for volatile elements (UUIDs, timestamps, hashes) that bust prompt cache prefixes",
                executor=lambda system_prompt: (
                    asdict(self._engine.detect_cache_drift(system_prompt))
                ),
                provider=self.name,
            )

            registry.register(
                name="headroom_compact_thinking",
                description="Compact prior-turn extended thinking reasoning blocks into deterministic summarized markers",
                executor=lambda messages, keep_last_turns=2: (
                    asdict(self._engine.compact_thinking(messages, keep_last_turns))
                ),
                provider=self.name,
            )

            registry.register(
                name="headroom_savings_metrics",
                description="Inspect session context savings, trimmed tokens, and compression ledger",
                executor=lambda reset=False: (
                    asdict(self._engine.get_savings_metrics(reset))
                ),
                provider=self.name,
            )

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass


# Module-level singleton (Rule 45)
plugin = HeadroomContextOptimizerPlugin()
