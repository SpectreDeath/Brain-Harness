"""Core Prompt-Pruning Layer: Message models, 3-pass deterministic optimizer, and prompt builder."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Any

# Supported message roles
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_TOOL_OUTPUT = "tool_output"
ROLE_RETRIEVED_DOC = "retrieved_doc"

VALID_ROLES = {
    ROLE_SYSTEM,
    ROLE_USER,
    ROLE_ASSISTANT,
    ROLE_TOOL_OUTPUT,
    ROLE_RETRIEVED_DOC,
}

REF_PATTERN = re.compile(r"REF:([A-Za-z0-9_\-]+)")
DEFINE_PATTERN = re.compile(r"DEFINE:([A-Za-z0-9_\-]+)")


@dataclass
class Message:
    """A single unit of prompt state."""

    id: str
    role: str
    content: str
    turn: int
    tool_call_key: str | None = None
    expires_after_turn: int | None = None
    defines_keys: list[str] = field(default_factory=list)
    _dropped_by: str | None = None

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {self.role}. Expected one of {sorted(VALID_ROLES)}")
        if not self.defines_keys:
            self.defines_keys = DEFINE_PATTERN.findall(self.content)

    def references(self) -> list[str]:
        return REF_PATTERN.findall(self.content)

    def approx_token_count(self) -> int:
        if not self.content:
            return 0
        words = self.content.split()
        token_count = 0
        for w in words:
            pieces = re.findall(r"[A-Za-z0-9]+|[^\sA-Za-z0-9]", w)
            token_count += max(1, len(pieces))
        return token_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "turn": self.turn,
            "tool_call_key": self.tool_call_key,
            "expires_after_turn": self.expires_after_turn,
            "defines_keys": list(self.defines_keys),
            "approx_tokens": self.approx_token_count(),
        }


@dataclass
class PruneReport:
    input_count: int
    expired_removed: int
    duplicates_removed: int
    restored_for_dependency: int
    output_count: int
    removed_ids: list[str] = field(default_factory=list)
    tokens_before: int = 0
    tokens_after: int = 0

    @property
    def token_reduction_pct(self) -> float:
        if self.tokens_before == 0:
            return 0.0
        return round(100.0 * (1.0 - (self.tokens_after / self.tokens_before)), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_count": self.input_count,
            "output_count": self.output_count,
            "expired_removed": self.expired_removed,
            "duplicates_removed": self.duplicates_removed,
            "restored_for_dependency": self.restored_for_dependency,
            "removed_ids": list(self.removed_ids),
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "token_reduction_pct": self.token_reduction_pct,
        }


class PromptPruner:
    """Three deterministic compiler passes over prompt messages before assembly."""

    def _pass1_expired_context_elimination(self, messages: list[Message]) -> tuple[list[Message], list[Message]]:
        """Pass 1: Keep only the latest message for each tool_call_key."""
        last_occurrence = {}
        for m in messages:
            if m.tool_call_key:
                last_occurrence[m.tool_call_key] = m.id

        kept: list[Message] = []
        removed: list[Message] = []
        for m in messages:
            if m.tool_call_key and last_occurrence[m.tool_call_key] != m.id:
                m._dropped_by = "pass1_expired"
                removed.append(m)
            else:
                kept.append(m)
        return kept, removed

    def _pass2_duplicate_context_elimination(self, messages: list[Message]) -> tuple[list[Message], list[Message]]:
        """Pass 2: Collapse near-identical retrieved doc passages down to first occurrence."""
        seen = {}
        kept: list[Message] = []
        removed: list[Message] = []
        for m in messages:
            if m.role == ROLE_RETRIEVED_DOC:
                norm = " ".join(m.content.lower().split())
                if norm in seen:
                    m._dropped_by = "pass2_duplicate"
                    removed.append(m)
                    continue
                seen[norm] = m.id
            kept.append(m)
        return kept, removed

    def _pass3_dependency_restoration(
        self,
        all_messages: list[Message],
        kept_messages: list[Message],
        removed_messages: list[Message],
    ) -> tuple[list[Message], list[Message]]:
        """Pass 3: Restore any removed message carrying DEFINE:<key> needed by surviving REF:<key>."""
        kept_ids = {m.id for m in kept_messages}
        by_id = {m.id: m for m in all_messages}

        key_definer = {}
        for m in all_messages:
            for key in m.defines_keys:
                key_definer[key] = m.id

        referenced_keys = set()
        for m in kept_messages:
            referenced_keys.update(m.references())

        restored: list[Message] = []
        for key in referenced_keys:
            definer_id = key_definer.get(key)
            if definer_id and definer_id not in kept_ids:
                restored_msg = by_id[definer_id]
                restored_msg._dropped_by = None
                kept_messages.append(restored_msg)
                kept_ids.add(definer_id)
                restored.append(restored_msg)

        kept_messages.sort(key=lambda m: (m.turn, m.id))
        return kept_messages, restored

    def prune(self, messages: list[Message]) -> tuple[list[Message], PruneReport]:
        input_count = len(messages)
        tokens_before = sum(m.approx_token_count() for m in messages)

        after_p1, removed_p1 = self._pass1_expired_context_elimination(messages)
        after_p2, removed_p2 = self._pass2_duplicate_context_elimination(after_p1)

        all_removed = removed_p1 + removed_p2
        after_p3, restored = self._pass3_dependency_restoration(messages, after_p2, all_removed)

        restored_ids = {r.id for r in restored}
        removed_ids = [m.id for m in all_removed if m.id not in restored_ids]
        tokens_after = sum(m.approx_token_count() for m in after_p3)

        report = PruneReport(
            input_count=input_count,
            expired_removed=len(removed_p1),
            duplicates_removed=len(removed_p2),
            restored_for_dependency=len(restored),
            output_count=len(after_p3),
            removed_ids=removed_ids,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
        )
        return after_p3, report


class PromptBuilder:
    """Assembles a final prompt string from a list of Messages in chronological order."""

    def build(self, messages: list[Message]) -> str:
        ordered = sorted(messages, key=lambda m: (m.turn, m.id))
        lines = []
        for m in ordered:
            lines.append(f"[{m.role.upper()}] {m.content}")
        return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Synthetic Workload Generator & Benchmarking
# ---------------------------------------------------------------------------
@dataclass
class WorkloadConfig:
    name: str
    tool_reuse_prob: float
    doc_repeat_prob: float
    dependency_prob: float


WORKLOAD_CHAT = WorkloadConfig("chat", 0.05, 0.05, 0.02)
WORKLOAD_RAG = WorkloadConfig("rag", 0.15, 0.40, 0.05)
WORKLOAD_TOOL_AGENT = WorkloadConfig("tool_agent", 0.45, 0.20, 0.15)


@dataclass
class CorpusResult:
    messages: list[Message]
    required_ids: set[str]


def generate_corpus(num_turns: int = 100, workload: WorkloadConfig = WORKLOAD_TOOL_AGENT, seed: int = 42) -> CorpusResult:
    rng = random.Random(seed)
    messages: list[Message] = []
    required_ids: set[str] = set()

    messages.append(
        Message(
            id="sys_0",
            role=ROLE_SYSTEM,
            content="You are a helpful AI assistant operating in a tool-augmented environment.",
            turn=0,
        )
    )
    required_ids.add("sys_0")

    known_tool_keys = [f"tool_search_q{i}" for i in range(5)]
    known_passages = [
        f"Standard documentation excerpt {i} regarding system configuration and runtime parameters."
        for i in range(8)
    ]
    defined_keys_pool = []

    for t in range(1, num_turns + 1):
        # 1. User message
        use_ref = defined_keys_pool and (rng.random() < workload.dependency_prob)
        if use_ref:
            target_key, definer_id = rng.choice(defined_keys_pool)
            u_content = f"Please proceed based on prior output. REF:{target_key}"
            required_ids.add(definer_id)
        else:
            u_content = f"User query for turn {t}: what is the status of task {t}?"

        u_msg = Message(id=f"u_{t}", role=ROLE_USER, content=u_content, turn=t)
        messages.append(u_msg)
        required_ids.add(u_msg.id)

        # 2. Retrieved Docs
        if rng.random() < 0.6:
            if rng.random() < workload.doc_repeat_prob:
                p_text = rng.choice(known_passages)
            else:
                p_text = f"Unique retrieved passage for turn {t} with detailed context."
            d_msg = Message(id=f"d_{t}", role=ROLE_RETRIEVED_DOC, content=p_text, turn=t)
            messages.append(d_msg)

        # 3. Tool Output
        if rng.random() < 0.5:
            if rng.random() < workload.tool_reuse_prob:
                t_key = rng.choice(known_tool_keys)
            else:
                t_key = f"tool_op_{t}"

            # Maybe define a key
            if rng.random() < 0.3:
                d_key = f"key_t{t}"
                t_content = f"Tool result for {t_key}: status=ok DEFINE:{d_key}"
                t_msg = Message(id=f"t_{t}", role=ROLE_TOOL_OUTPUT, content=t_content, turn=t, tool_call_key=t_key)
                defined_keys_pool.append((d_key, t_msg.id))
            else:
                t_content = f"Tool result for {t_key}: status=success, records_found={rng.randint(1, 10)}"
                t_msg = Message(id=f"t_{t}", role=ROLE_TOOL_OUTPUT, content=t_content, turn=t, tool_call_key=t_key)
            messages.append(t_msg)

        # 4. Assistant message
        a_msg = Message(id=f"a_{t}", role=ROLE_ASSISTANT, content=f"Assistant response for turn {t}.", turn=t)
        messages.append(a_msg)
        required_ids.add(a_msg.id)

    return CorpusResult(messages=messages, required_ids=required_ids)
