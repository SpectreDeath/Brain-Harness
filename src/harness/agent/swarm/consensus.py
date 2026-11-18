"""Supermajority voting and confidence-weighted consensus engine with pluggable strategies."""

from __future__ import annotations

import collections
from collections.abc import Mapping
import math
from typing import Any, Protocol, runtime_checkable


def _validate_provenance_multipliers(
    multipliers: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Validate (verified, unverified, none) provenance multipliers."""
    if len(multipliers) != 3:
        raise ValueError("provenance_multipliers must contain exactly 3 elements")
    verified_m, unverified_m, none_m = (float(x) for x in multipliers)
    for val in (verified_m, unverified_m, none_m):
        if not math.isfinite(val) or val < 0.0:
            raise ValueError("provenance_multipliers must be finite and non-negative")
    return (verified_m, unverified_m, none_m)


def _resolve_ki_multiplier(
    vote: Mapping[str, Any],
    ki_verification_map: Mapping[str, bool | None],
    multipliers: tuple[float, float, float],
) -> float:
    """Resolve confidence multiplier for a vote based on its linked KI verification status."""
    verified_mult, unverified_mult, none_mult = multipliers
    raw_ki = vote.get("ki_id")
    if not raw_ki:
        return none_mult
    ki_key = str(raw_ki).strip()
    if not ki_key:
        return none_mult
    if ki_key in ki_verification_map:
        status = ki_verification_map[ki_key]
    else:
        status = ki_verification_map.get(ki_key.replace("-", "_"))
    if status is True:
        return verified_mult
    if status is False:
        return unverified_mult
    return none_mult


@runtime_checkable
class SwarmConsensusProtocol(Protocol):
    """Protocol for pluggable swarm consensus evaluation strategies."""

    def evaluate(
        self,
        votes: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Evaluate agent votes and return structured decision outcome."""
        ...


class BinaryThresholdStrategy:
    """Supermajority threshold evaluation on boolean approval votes."""

    def evaluate(
        self,
        votes: list[dict[str, Any]],
        threshold: float = 0.66,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Evaluate approval ratio against required supermajority threshold."""
        if not votes:
            return {
                "status": "error",
                "error": "No votes provided",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        approvals = 0
        rejections = 0
        weighted_conf = 0.0

        for v in votes:
            vote_val = str(v.get("vote", "")).lower().strip()
            conf = float(v.get("confidence", 1.0))
            weighted_conf += conf

            if vote_val in ("approve", "yes", "accept", "1", "true", "pass"):
                approvals += 1
            else:
                rejections += 1

        total = len(votes)
        approval_ratio = approvals / total
        consensus_reached = approval_ratio >= threshold
        avg_conf = round(weighted_conf / total, 2)

        return {
            "status": "ok",
            "total_votes": total,
            "approvals": approvals,
            "rejections": rejections,
            "approval_ratio": round(approval_ratio, 2),
            "required_threshold": threshold,
            "consensus_reached": consensus_reached,
            "avg_confidence": avg_conf,
            "decision": "APPROVED" if consensus_reached else "REJECTED",
        }


class BordaConsensusStrategy:
    """Borda count rank-order point accumulation strategy."""

    def evaluate(
        self,
        votes: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Accumulate points from ranked choice ballots (top choice gets N-1, next N-2, ...)."""
        if not votes:
            return {
                "status": "error",
                "error": "No votes provided",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        scores: dict[str, float] = collections.defaultdict(float)

        for v in votes:
            ranking = v.get("ranking") or v.get("ranked_choices") or v.get("vote") or []
            if isinstance(ranking, str):
                ranking = [ranking]
            weight = float(v.get("weight", 1.0)) * float(v.get("confidence", 1.0))
            n = len(ranking)
            for idx, candidate in enumerate(ranking):
                points = (n - 1 - idx) * weight
                scores[candidate] += points

        if not scores:
            return {
                "status": "error",
                "error": "No ranked candidates extracted",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cand, top_score = sorted_candidates[0]

        # Check for tie
        if len(sorted_candidates) > 1 and sorted_candidates[1][1] == top_score:
            return {
                "status": "ok",
                "total_votes": len(votes),
                "scores": dict(scores),
                "winner": None,
                "consensus_reached": False,
                "decision": "NO_CONSENSUS",
                "is_tie": True,
            }

        return {
            "status": "ok",
            "total_votes": len(votes),
            "scores": dict(scores),
            "winner": top_cand,
            "top_score": top_score,
            "consensus_reached": True,
            "decision": top_cand,
            "is_tie": False,
        }


class WeightedMajorityStrategy:
    """Confidence-weighted majority choice voting strategy (with optional CISC normalization)."""

    def evaluate(
        self,
        votes: list[dict[str, Any]],
        normalization: str | None = None,
        temperature: float = 1.0,
        only_tie_break: bool = False,
        uncertainty_service: Any | None = None,
        ki_verification_map: Mapping[str, bool | None] | None = None,
        provenance_multipliers: tuple[float, float, float] = (1.0, 0.6, 0.4),
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Sum confidence-weighted votes, or apply CISC normalization / UncertaintyGuard delegation."""
        if not votes:
            return {
                "status": "error",
                "error": "No votes provided",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        if uncertainty_service is not None or normalization is not None:
            return self._evaluate_cisc(
                votes,
                normalization=normalization or "softmax",
                temperature=temperature,
                only_tie_break=only_tie_break,
                uncertainty_service=uncertainty_service,
                ki_verification_map=ki_verification_map,
                provenance_multipliers=provenance_multipliers,
            )

        validated_mults = (
            _validate_provenance_multipliers(provenance_multipliers)
            if ki_verification_map is not None
            else None
        )
        scores: dict[str, float] = collections.defaultdict(float)
        for v in votes:
            choice = str(v.get("choice") or v.get("vote") or "").strip()
            if not choice:
                continue
            weight = float(v.get("weight", 1.0)) * float(v.get("confidence", 1.0))
            if validated_mults is not None and ki_verification_map is not None:
                weight *= _resolve_ki_multiplier(v, ki_verification_map, validated_mults)
            scores[choice] += weight

        if not scores:
            return {
                "status": "error",
                "error": "No valid choices extracted from votes",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        sorted_choices = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_choice, top_weight = sorted_choices[0]

        if len(sorted_choices) > 1 and sorted_choices[1][1] == top_weight:
            return {
                "status": "ok",
                "total_votes": len(votes),
                "weights": dict(scores),
                "winner": None,
                "consensus_reached": False,
                "decision": "NO_CONSENSUS",
                "is_tie": True,
            }

        return {
            "status": "ok",
            "total_votes": len(votes),
            "weights": dict(scores),
            "winner": top_choice,
            "top_weight": round(top_weight, 4),
            "consensus_reached": True,
            "decision": top_choice,
            "is_tie": False,
        }

    def _evaluate_cisc(
        self,
        votes: list[dict[str, Any]],
        *,
        normalization: str,
        temperature: float,
        only_tie_break: bool,
        uncertainty_service: Any | None,
        ki_verification_map: Mapping[str, bool | None] | None = None,
        provenance_multipliers: tuple[float, float, float] = (1.0, 0.6, 0.4),
    ) -> dict[str, Any]:
        validated_mults = (
            _validate_provenance_multipliers(provenance_multipliers)
            if ki_verification_map is not None
            else None
        )
        answers: list[str] = []
        confs: list[float] = []
        for v in votes:
            choice = str(v.get("choice") or v.get("vote") or "").strip()
            if not choice:
                continue
            try:
                c_val = float(v.get("weight", 1.0)) * float(v.get("confidence", 1.0))
            except (TypeError, ValueError):
                continue
            if not math.isfinite(c_val):
                continue
            if validated_mults is not None and ki_verification_map is not None:
                c_val *= _resolve_ki_multiplier(v, ki_verification_map, validated_mults)
            answers.append(choice)
            confs.append(c_val)

        if not answers:
            return {
                "status": "error",
                "error": "No valid choices extracted from votes",
                "consensus_reached": False,
                "decision": "NO_VOTES",
            }

        if uncertainty_service is not None and hasattr(
            uncertainty_service, "aggregate_confidence_votes"
        ):
            report = uncertainty_service.aggregate_confidence_votes(
                answers,
                confs,
                normalization=normalization,
                temperature=temperature,
                only_tie_break=only_tie_break,
            )
            winner = report.chosen_answer
            return {
                "status": "ok",
                "total_votes": len(votes),
                "valid_trace_count": report.valid_trace_count,
                "weights": dict(report.answer_weights),
                "winner": winner,
                "confidence": report.confidence,
                "normalization": report.normalization,
                "consensus_reached": winner is not None,
                "decision": winner or "NO_CONSENSUS",
                "is_tie": False,
                "source": "service.uncertainty_guard",
                "provenance_grounded": ki_verification_map is not None,
            }

        if normalization == "softmax":
            max_c = max(confs)
            exps = [math.exp((c - max_c) * temperature) for c in confs]
            denom = sum(exps) or 1.0
            norm_weights = [w / denom for w in exps]
        elif normalization == "linear":
            min_c = min(confs)
            norm_weights = [temperature * (c - min_c) + 1.0 for c in confs]
        else:
            norm_weights = [max(c, 0.0) for c in confs]

        totals: dict[str, float] = {}
        counts: collections.Counter[str] = collections.Counter()
        for ans, w in zip(answers, norm_weights):
            counts[ans] += 1
            totals[ans] = totals.get(ans, 0.0) + w
        total_w = sum(totals.values())
        if only_tie_break:
            max_cnt = max(counts.values())
            tied = [a for a, cnt in counts.items() if cnt == max_cnt]
            winner = max(tied, key=lambda a: totals[a])
        else:
            winner = max(totals, key=lambda a: totals[a])
        conf_ratio = round(totals[winner] / total_w, 6) if total_w > 0.0 else 0.0
        return {
            "status": "ok",
            "total_votes": len(votes),
            "valid_trace_count": len(answers),
            "weights": {k: round(v, 6) for k, v in totals.items()},
            "winner": winner,
            "confidence": conf_ratio,
            "normalization": normalization,
            "consensus_reached": True,
            "decision": winner,
            "is_tie": False,
            "source": "builtin_cisc",
            "provenance_grounded": ki_verification_map is not None,
        }


class ConsensusEngine:
    """Unified consensus engine dispatching to pluggable strategies."""

    _binary_strategy = BinaryThresholdStrategy()
    _borda_strategy = BordaConsensusStrategy()
    _weighted_strategy = WeightedMajorityStrategy()

    @classmethod
    def tally(
        cls,
        votes: list[dict[str, Any]],
        threshold: float = 0.66,
    ) -> dict[str, Any]:
        """Tally multi-agent votes to determine consensus outcome."""
        return cls._binary_strategy.evaluate(votes, threshold=threshold)

    @classmethod
    def evaluate_borda(cls, votes: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate ranked votes using Borda count point accumulation."""
        return cls._borda_strategy.evaluate(votes)

    @classmethod
    def evaluate_weighted_majority(
        cls,
        votes: list[dict[str, Any]],
        *,
        normalization: str | None = None,
        temperature: float = 1.0,
        only_tie_break: bool = False,
        uncertainty_service: Any | None = None,
        ki_verification_map: Mapping[str, bool | None] | None = None,
        provenance_multipliers: tuple[float, float, float] = (1.0, 0.6, 0.4),
    ) -> dict[str, Any]:
        """Evaluate votes using confidence-weighted choice aggregation."""
        return cls._weighted_strategy.evaluate(
            votes,
            normalization=normalization,
            temperature=temperature,
            only_tie_break=only_tie_break,
            uncertainty_service=uncertainty_service,
            ki_verification_map=ki_verification_map,
            provenance_multipliers=provenance_multipliers,
        )

    @classmethod
    def evaluate_cisc_consensus(
        cls,
        votes: list[dict[str, Any]],
        *,
        normalization: str = "softmax",
        temperature: float = 2.5,
        only_tie_break: bool = False,
        uncertainty_service: Any | None = None,
        ki_verification_map: Mapping[str, bool | None] | None = None,
        provenance_multipliers: tuple[float, float, float] = (1.0, 0.6, 0.4),
    ) -> dict[str, Any]:
        """Evaluate multi-trace choices using CISC normalized confidence voting."""
        return cls._weighted_strategy.evaluate(
            votes,
            normalization=normalization,
            temperature=temperature,
            only_tie_break=only_tie_break,
            uncertainty_service=uncertainty_service,
            ki_verification_map=ki_verification_map,
            provenance_multipliers=provenance_multipliers,
        )


DefaultConsensusEngine = ConsensusEngine

__all__ = [
    "BinaryThresholdStrategy",
    "BordaConsensusStrategy",
    "ConsensusEngine",
    "DefaultConsensusEngine",
    "SwarmConsensusProtocol",
    "WeightedMajorityStrategy",
]
