"""Domain engine for TokenEconomizer.

Implements experience-driven micro-skills lifecycle, dynamic tool pruning,
3-tier turn guard failure-loop detection, and multi-agent trace federation.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from harness.services.token_economizer import (
    MicroSkillFact,
    TokenEconomizerService,
    TokenLedgerMetrics,
    ToolPrunePolicy,
    TrajectoryTrace,
    TurnGuardDecision,
)


@dataclass(slots=True)
class _InternalFactRecord:
    """Mutable internal state of a learned micro-skill fact."""

    key: str
    assertion: str
    state: str = "CANDIDATE"
    is_high_stakes: bool = False
    drift: bool = True
    confirms: list[tuple[int, set[str]]] = field(default_factory=list)
    contradicts: list[int] = field(default_factory=list)
    fire_num: int = 0
    fire_den: int = 0
    promoted_at: int | None = None
    retired_at: int | None = None

    def drifted_confirms_count(self) -> int:
        if not self.drift:
            return len(self.confirms)
        kept_files: list[set[str]] = []
        count = 0
        for _, files in self.confirms:
            if not files or all(len(files & k) == 0 for k in kept_files):
                kept_files.append(files)
                count += 1
        return count

    def calculate_score(self, current_task_idx: int, gamma: float = 0.8, lam: float = 5.0) -> float:
        score = sum(gamma ** (current_task_idx - idx) for idx, _ in self.confirms)
        score -= lam * sum(gamma ** (current_task_idx - idx) for idx in self.contradicts)
        return score

    def firing_rate(self) -> float:
        if self.fire_den == 0:
            return 1.0  # optimistic default before exercise
        return self.fire_num / self.fire_den


class TokenEconomizerEngine(TokenEconomizerService):
    """Core domain implementation of TokenEconomizer service protocol."""

    def __init__(
        self,
        k_promote: int = 3,
        gamma: float = 0.8,
        lam: float = 5.0,
        score_floor: float = 0.0,
        hard_kill: bool = True,
        fire_gate: float = 0.40,
        fire_min_n: int = 4,
        default_protected_tools: tuple[str, ...] = (
            "read_file",
            "edit_file",
            "run_command",
            "write_file",
            "view_file",
            "bash",
            "exec",
        ),
    ) -> None:
        self.k_promote = k_promote
        self.gamma = gamma
        self.lam = lam
        self.score_floor = score_floor
        self.hard_kill = hard_kill
        self.fire_gate = fire_gate
        self.fire_min_n = fire_min_n
        self.protected_tools_set = frozenset(default_protected_tools)

        self._task_counter: int = 0
        self._facts: dict[str, _InternalFactRecord] = {}

        # Cumulative ledger
        self._total_in_tokens: int = 0
        self._total_out_tokens: int = 0
        self._net_tokens_saved: int = 0
        self._loop_nudges: int = 0
        self._loop_aborts: int = 0

    def record_micro_skill_observation(
        self,
        key: str,
        success: bool,
        edited_files: list[str] | None = None,
        is_high_stakes: bool = False,
        assertion: str = "",
    ) -> MicroSkillFact:
        self._task_counter += 1
        now = self._task_counter
        files_set = set(edited_files or [])

        record = self._facts.get(key)
        if record is None:
            record = _InternalFactRecord(
                key=key,
                assertion=assertion or key,
                is_high_stakes=is_high_stakes,
                drift=True,
            )
            self._facts[key] = record

        record.fire_den += 1
        if success:
            record.fire_num += 1
            record.confirms.append((now, files_set))
        else:
            record.contradicts.append(now)

        # Compute state transitions
        score = record.calculate_score(now, self.gamma, self.lam)
        drifted_confirms = record.drifted_confirms_count()

        if record.state == "CANDIDATE":
            if success and drifted_confirms >= self.k_promote:
                record.state = "ACTIVE"
                record.promoted_at = now
        elif record.state == "ACTIVE":
            if not success:
                if self.hard_kill and record.is_high_stakes:
                    record.state = "RETIRED"
                    record.retired_at = now
                elif score < self.score_floor:
                    record.state = "RETIRED"
                    record.retired_at = now

        firing_rate = record.firing_rate()
        return MicroSkillFact(
            key=record.key,
            state=record.state,
            confirms_count=len(record.confirms),
            contradicts_count=len(record.contradicts),
            score=round(score, 3),
            firing_rate=round(firing_rate, 3),
            is_high_stakes=record.is_high_stakes,
            assertion=record.assertion,
        )

    def get_active_micro_skills(self) -> tuple[MicroSkillFact, ...]:
        active_list: list[MicroSkillFact] = []
        now = self._task_counter
        for record in self._facts.values():
            if record.state == "ACTIVE":
                score = record.calculate_score(now, self.gamma, self.lam)
                rate = record.firing_rate()
                # Apply firing gate
                if record.fire_den >= self.fire_min_n and rate < self.fire_gate:
                    continue
                active_list.append(
                    MicroSkillFact(
                        key=record.key,
                        state=record.state,
                        confirms_count=len(record.confirms),
                        contradicts_count=len(record.contradicts),
                        score=round(score, 3),
                        firing_rate=round(rate, 3),
                        is_high_stakes=record.is_high_stakes,
                        assertion=record.assertion,
                    )
                )
        return tuple(active_list)

    def evaluate_tool_pruning(
        self,
        loaded_tools: list[str],
        session_tool_history: list[dict[str, int]],
        protected_tools: list[str] | None = None,
        inapplicable_tools: list[str] | None = None,
        evidence_sessions_threshold: int = 2,
    ) -> ToolPrunePolicy:
        protected = set(self.protected_tools_set)
        if protected_tools:
            protected.update(protected_tools)

        inapplicable = set(inapplicable_tools or [])
        pruned: list[str] = []

        # Count total usage across session history
        usage_counts: Counter[str] = Counter()
        for sess in session_tool_history:
            for tool_name, count in sess.items():
                if count > 0:
                    usage_counts[tool_name] += count

        num_sessions = len(session_tool_history)

        for tool in loaded_tools:
            if tool in protected:
                continue
            if tool in inapplicable:
                pruned.append(tool)
                continue

            # If tool has zero usage across >= threshold sessions, prune it
            if num_sessions >= evidence_sessions_threshold and usage_counts[tool] == 0:
                pruned.append(tool)

        tokens_per_tool = 350
        saved_tokens = len(pruned) * tokens_per_tool
        self._net_tokens_saved += saved_tokens

        return ToolPrunePolicy(
            status="ok",
            pruned_tools=tuple(sorted(pruned)),
            protected_tools=tuple(sorted(protected)),
            inapplicable_tools=tuple(sorted(inapplicable)),
            estimated_tokens_saved=saved_tokens,
        )

    def evaluate_turn_guard(
        self,
        turn_history: list[dict[str, Any]],
        envelope_turn_p90: int = 20,
        envelope_margin: float = 1.25,
        level: str = "default",
    ) -> TurnGuardDecision:
        turn_count = len(turn_history)
        if turn_count == 0:
            return TurnGuardDecision(
                is_stuck=False,
                tier=0,
                action="continue",
                reason="No turns recorded",
                stagnation_ratio=0.0,
                envelope_ratio=0.0,
            )

        # Threshold calibrations
        gate_min_turns = 12 if level == "aggressive" else (24 if level == "conservative" else 18)
        gate_error_outputs = 4 if level == "aggressive" else (8 if level == "conservative" else 6)
        backstop_mult = 1.8 if level == "aggressive" else (3.5 if level == "conservative" else 2.5)

        # Count errors, churn, distinct files, and repeat failures
        error_count = 0
        file_edits: Counter[str] = Counter()
        error_signatures: list[str] = []

        for turn in turn_history:
            is_err = turn.get("is_error") or turn.get("status") == "error"
            if is_err:
                error_count += 1
                err_msg = str(turn.get("error_message") or turn.get("result") or "").strip()
                if err_msg:
                    error_signatures.append(err_msg[:120])

            target_file = turn.get("file_path") or turn.get("file") or ""
            if target_file and turn.get("tool") in ("edit_file", "edit", "write_file", "write"):
                file_edits[target_file] += 1

        edit_churn = max(file_edits.values()) if file_edits else 0
        distinct_files = len(file_edits)

        # Stagnation: ratio of repeated error signatures
        stagnation = 0.0
        if len(error_signatures) > 1:
            sig_counts = Counter(error_signatures)
            repeated = sum(c - 1 for c in sig_counts.values() if c > 1)
            stagnation = repeated / len(error_signatures)

        envelope_ratio = turn_count / max(1, envelope_turn_p90)

        # Check Hard Backstop first
        if envelope_ratio >= backstop_mult:
            self._loop_aborts += 1
            return TurnGuardDecision(
                is_stuck=True,
                tier=2,
                action="abort",
                reason=f"Turn count ({turn_count}) exceeded hard backstop ({backstop_mult}x envelope p90)",
                edit_churn=edit_churn,
                error_outputs=error_count,
                stagnation_ratio=round(stagnation, 3),
                envelope_ratio=round(envelope_ratio, 3),
            )

        # Tier 0 Free Gate
        if turn_count < gate_min_turns and error_count < gate_error_outputs:
            return TurnGuardDecision(
                is_stuck=False,
                tier=0,
                action="continue",
                reason="Tier-0 gate closed (turn activity within healthy bounds)",
                edit_churn=edit_churn,
                error_outputs=error_count,
                stagnation_ratio=round(stagnation, 3),
                envelope_ratio=round(envelope_ratio, 3),
            )

        # Tier 1 Heuristic Conjunction
        has_churn = edit_churn >= 4 or distinct_files >= 3
        has_errors = error_count >= 6
        has_stagnation = stagnation >= 0.20
        past_envelope = envelope_ratio >= envelope_margin

        if has_churn and has_errors and has_stagnation and past_envelope:
            self._loop_nudges += 1
            recent_err = error_signatures[-1] if error_signatures else "repeated failure"
            nudge = (
                f"[LoopGuard Intervention] Turn {turn_count} appears stuck in a repetitive failure spiral "
                f"(edit churn={edit_churn}, errors={error_count}, stagnation={round(stagnation * 100)}%). "
                f"Recent error: '{recent_err[:80]}'. "
                f"Please inspect assumptions and try an alternative approach rather than repeating identical steps."
            )
            return TurnGuardDecision(
                is_stuck=True,
                tier=1,
                action="nudge",
                reason="Heuristic conjunction met (churn, sustained errors, stagnation, envelope passed)",
                nudge_text=nudge,
                edit_churn=edit_churn,
                error_outputs=error_count,
                stagnation_ratio=round(stagnation, 3),
                envelope_ratio=round(envelope_ratio, 3),
            )

        return TurnGuardDecision(
            is_stuck=False,
            tier=0,
            action="continue",
            reason="Heuristic conjunction not met; continuing execution",
            edit_churn=edit_churn,
            error_outputs=error_count,
            stagnation_ratio=round(stagnation, 3),
            envelope_ratio=round(envelope_ratio, 3),
        )

    def parse_trajectory(
        self,
        raw_log: str | dict[str, Any],
        agent_format: str = "generic_jsonl",
    ) -> TrajectoryTrace:
        if isinstance(raw_log, str):
            try:
                data = json.loads(raw_log)
            except Exception:
                # Treat as JSONL
                lines = [json.loads(line) for line in raw_log.strip().splitlines() if line.strip()]
                data = {"session_id": "jsonl_session", "turns": lines}
        else:
            data = raw_log

        session_id = data.get("session_id") or data.get("id") or "sess_default"
        turns = data.get("turns") or data.get("steps") or []
        distinct_tools: set[str] = set()
        tool_calls_count = 0
        total_tokens = 0

        for turn in turns:
            tool = turn.get("tool") or turn.get("name")
            if tool:
                distinct_tools.add(tool)
                tool_calls_count += 1
            total_tokens += turn.get("tokens") or turn.get("total_tokens") or 0

        self._total_in_tokens += total_tokens
        return TrajectoryTrace(
            session_id=session_id,
            agent_type=agent_format,
            turns_count=len(turns),
            tool_calls_count=tool_calls_count,
            distinct_tools=tuple(sorted(distinct_tools)),
            total_tokens_spent=total_tokens,
        )

    def get_token_ledger(self, reset: bool = False) -> TokenLedgerMetrics:
        active_count = len(self.get_active_micro_skills())
        cost_saved_usd = (self._net_tokens_saved / 1_000_000.0) * 3.0  # $3/M standard input tokens

        metrics = TokenLedgerMetrics(
            total_in_tokens=self._total_in_tokens,
            total_out_tokens=self._total_out_tokens,
            net_tokens_saved=self._net_tokens_saved,
            net_cost_saved_usd=round(cost_saved_usd, 4),
            active_microskills_count=active_count,
            pruned_tools_count=0,
            loop_nudges_count=self._loop_nudges,
            loop_aborts_count=self._loop_aborts,
        )
        if reset:
            self._total_in_tokens = 0
            self._total_out_tokens = 0
            self._net_tokens_saved = 0
            self._loop_nudges = 0
            self._loop_aborts = 0

        return metrics

