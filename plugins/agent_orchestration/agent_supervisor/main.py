"""Hierarchical multi-agent supervisor, token budget allocator, and consensus voting plugin."""

from __future__ import annotations

from typing import Any


def coordinate_swarm_tasks(
    objective: str,
    agents: list[dict[str, Any]],
    max_total_tokens: int = 50000,
) -> dict[str, Any]:
    """Divide a swarm objective across specialized worker agents with token allocations."""
    if not agents:
        return {"status": "error", "error": "No agents provided for swarm coordination"}

    per_agent_budget = max_total_tokens // len(agents)
    assignments: list[dict[str, Any]] = []

    for i, a in enumerate(agents, start=1):
        agent_id = a.get("id", f"agent_{i}")
        role = a.get("role", "worker")
        assignments.append({
            "agent_id": agent_id,
            "role": role,
            "allocated_tokens": per_agent_budget,
            "subtask": f"Execute phase {i} of '{objective}' specialized in {role}.",
        })

    return {
        "status": "ok",
        "objective": objective,
        "swarm_size": len(agents),
        "total_token_budget": max_total_tokens,
        "assignments": assignments,
    }


def tally_consensus_votes(
    votes: list[dict[str, Any]],
    threshold: float = 0.66,
) -> dict[str, Any]:
    """Tally agent votes to determine if supermajority consensus is reached."""
    if not votes:
        return {"status": "error", "error": "No votes recorded"}

    approvals = 0
    rejections = 0
    weighted_confidence = 0.0

    for v in votes:
        vote = str(v.get("vote", "")).lower()
        conf = float(v.get("confidence", 1.0))
        weighted_confidence += conf

        if vote in ("approve", "yes", "accept", "1", "true"):
            approvals += 1
        else:
            rejections += 1

    total = len(votes)
    approval_ratio = approvals / total
    consensus_reached = approval_ratio >= threshold
    avg_confidence = round(weighted_confidence / total, 2)

    return {
        "status": "ok",
        "total_votes": total,
        "approvals": approvals,
        "rejections": rejections,
        "approval_ratio": round(approval_ratio, 2),
        "required_threshold": threshold,
        "consensus_reached": consensus_reached,
        "avg_confidence": avg_confidence,
        "decision": "APPROVED" if consensus_reached else "REJECTED",
    }
