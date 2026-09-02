"""Hermes Cognitive Engine — learning loop, verification stop hooks, and think scrubbing."""

from __future__ import annotations

import re
from typing import Any


def create_skill_from_trajectory(
    trajectory_id: str,
    skill_name: str,
    domain: str,
    tool_sequence: list[str],
) -> dict[str, Any]:
    """Synthesize an OpenSkills compliant skill from a successful tool execution trajectory."""
    clean_name = skill_name.strip().lower().replace(" ", "-")
    steps_md = "\n".join(f"{i+1}. Run `{tool}` to advance stage." for i, tool in enumerate(tool_sequence))

    skill_markdown = f"""---
name: {clean_name}
description: "Autonomously formed skill from trajectory {trajectory_id} in domain {domain}."
version: 1.0.0
category: {domain}
platforms: [linux, macos, windows]
metadata:
  origin: "hermes-agent closed learning loop"
  trajectory_id: "{trajectory_id}"
---

# {clean_name.replace('-', ' ').title()}

## Prescribed Workflow Sequence
{steps_md}
"""

    return {
        "status": "ok",
        "trajectory_id": trajectory_id,
        "skill_name": clean_name,
        "domain": domain,
        "step_count": len(tool_sequence),
        "skill_markdown": skill_markdown,
    }


def evaluate_verification_evidence(
    session_id: str,
    executed_commands: list[str],
    file_mutations: list[str],
) -> dict[str, Any]:
    """Inspect verification evidence to ensure edits were verified before turn completion."""
    has_mutations = len(file_mutations) > 0
    verification_patterns = ["pytest", "test", "check", "lint", "cargo test", "npm test", "vitest", "python -m unittest"]

    has_verification_run = False
    matching_cmds: list[str] = []
    for cmd in executed_commands:
        cmd_lower = cmd.lower()
        if any(pat in cmd_lower for pat in verification_patterns):
            has_verification_run = True
            matching_cmds.append(cmd)

    if has_mutations and not has_verification_run:
        return {
            "status": "warning",
            "session_id": session_id,
            "verification_passed": False,
            "mutations_detected": len(file_mutations),
            "mutated_files": file_mutations,
            "nudge_action": "STOP_BLOCKED_UNVERIFIED_MUTATION",
            "message": "Files were modified but no verification test command was executed. Please run test suite before finishing.",
        }

    return {
        "status": "ok",
        "session_id": session_id,
        "verification_passed": True,
        "mutations_detected": len(file_mutations),
        "verified_commands": matching_cmds,
        "nudge_action": "PROCEED",
        "message": "Verification evidence verified successfully.",
    }


def scrub_think_stream(
    raw_chunk: str,
    capture_telemetry: bool = True,
) -> dict[str, Any]:
    """Parse reasoning tokens and separate internal thoughts from user-facing text."""
    # Find complete think tags
    think_match = re.search(r"<think>(.*?)</think>", raw_chunk, flags=re.DOTALL)
    if think_match:
        thought_content = think_match.group(1).strip()
        cleaned_text = re.sub(r"<think>.*?</think>", "", raw_chunk, flags=re.DOTALL).strip()
        return {
            "status": "ok",
            "cleaned_text": cleaned_text,
            "thought_telemetry": thought_content if capture_telemetry else "",
            "is_thinking": False,
        }

    # Handle unclosed <think> tag
    if "<think>" in raw_chunk:
        parts = raw_chunk.split("<think>", 1)
        return {
            "status": "ok",
            "cleaned_text": parts[0].strip(),
            "thought_telemetry": parts[1].strip() if capture_telemetry else "",
            "is_thinking": True,
        }

    return {
        "status": "ok",
        "cleaned_text": raw_chunk,
        "thought_telemetry": "",
        "is_thinking": False,
    }


def nudge_learning_persistence(
    turn_count: int,
    complexity_score: float,
) -> dict[str, Any]:
    """Calculate whether the agent should trigger an autobiographical persistence nudge."""
    # Urgent if long conversation with high complexity
    urgency = (turn_count * 0.1) + (complexity_score * 0.5)
    should_nudge = urgency >= 0.8 or turn_count >= 8

    return {
        "status": "ok",
        "turn_count": turn_count,
        "complexity_score": complexity_score,
        "calculated_urgency": round(urgency, 3),
        "should_nudge": should_nudge,
        "recommended_action": "PERSIST_KNOWLEDGE_ITEM" if should_nudge else "CONTINUE_IN_MEMORY",
    }
