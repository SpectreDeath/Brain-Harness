"""Dialectical debate orchestration and arbiter verdict synthesis."""

from __future__ import annotations

import sys
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def conduct_dialectical_debate(
    topic: str,
    pro_arguments: list[str],
    con_arguments: list[str],
) -> dict[str, Any]:
    """Orchestrate dialectical argument rounds between Proposer and Challenger."""
    rounds: list[dict[str, Any]] = []
    max_rounds = max(len(pro_arguments), len(con_arguments))

    for i in range(max_rounds):
        pro_claim = pro_arguments[i] if i < len(pro_arguments) else "No further supporting arguments."
        con_claim = con_arguments[i] if i < len(con_arguments) else "No further counter-arguments."

        rounds.append({
            "round_number": i + 1,
            "proposer_claim": pro_claim,
            "challenger_counter": con_claim,
        })

    return {
        "status": "ok",
        "topic": topic,
        "total_rounds": len(rounds),
        "pro_points_count": len(pro_arguments),
        "con_points_count": len(con_arguments),
        "rounds": rounds,
    }


def synthesize_debate_verdict(debate_summary: dict[str, Any]) -> dict[str, Any]:
    """Synthesize an impartial arbiter decision based on debate rounds."""
    topic = debate_summary.get("topic", "General Proposal")
    rounds = debate_summary.get("rounds", [])
    pro_count = debate_summary.get("pro_points_count", 0)
    con_count = debate_summary.get("con_points_count", 0)

    verdict_lines = [
        f"### ⚖️ Arbiter Verdict on '{topic}'",
        f"- **Rounds Evaluated:** {len(rounds)}",
        f"- **Thesis Arguments:** {pro_count}",
        f"- **Antithesis Counter-Points:** {con_count}",
    ]

    recommendation = "PROCEED_WITH_MITIGATIONS" if con_count > 0 else "PROCEED_DIRECTLY"
    if con_count > pro_count * 2:
        recommendation = "REJECT_OR_RETHINK"

    verdict_lines.append(f"- **Final Recommendation:** **{recommendation}**")

    return {
        "status": "ok",
        "topic": topic,
        "recommendation": recommendation,
        "verdict_markdown": "\n".join(verdict_lines),
    }


__all__ = [
    "conduct_dialectical_debate",
    "synthesize_debate_verdict",
]
