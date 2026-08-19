"""Agent trajectory step auditor, stuck loop detector, and recovery prompt synthesizer plugin."""

from __future__ import annotations

from typing import Any


def audit_trajectory_steps(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit agent step history for failures, token usage, and inefficiencies."""
    failed_steps: list[int] = []
    actions_taken: list[str] = []

    for s in steps:
        step_num = s.get("step_number", len(actions_taken) + 1)
        action = s.get("action")
        if action:
            actions_taken.append(action)

        obs = str(s.get("observation", ""))
        if "error" in obs.lower() or "exception" in obs.lower() or "failed" in obs.lower():
            failed_steps.append(step_num)

    total_steps = len(steps)
    failure_rate = round(len(failed_steps) / total_steps, 2) if total_steps > 0 else 0.0

    loop_check = detect_repetitive_loop(actions_taken)

    return {
        "status": "ok",
        "total_steps": total_steps,
        "failed_steps_count": len(failed_steps),
        "failed_step_numbers": failed_steps,
        "failure_rate": failure_rate,
        "is_looping": loop_check["has_loop"],
        "loop_detail": loop_check.get("pattern"),
        "healthy": len(failed_steps) == 0 and not loop_check["has_loop"],
    }


def detect_repetitive_loop(actions: list[str], window_size: int = 2) -> dict[str, Any]:
    """Detect repeating cycles in action sequences (e.g. A -> B -> A -> B)."""
    if len(actions) < window_size * 2:
        return {"has_loop": False, "pattern": None}

    # Check for immediate consecutive repeats (A -> A -> A)
    if len(actions) >= 3 and actions[-1] == actions[-2] == actions[-3]:
        return {
            "has_loop": True,
            "pattern": f"Immediate repeat of '{actions[-1]}' (3x)",
            "action": actions[-1],
        }

    # Check 2-step cycle (A -> B -> A -> B)
    if len(actions) >= 4 and actions[-4:-2] == actions[-2:]:
        pattern_str = " -> ".join(actions[-2:])
        return {
            "has_loop": True,
            "pattern": f"Oscillating loop detected: [{pattern_str}] (2x)",
            "cycle": actions[-2:],
        }

    return {"has_loop": False, "pattern": None}


def synthesize_recovery_prompt(
    stuck_reason: str,
    last_failed_action: str | None = None,
) -> dict[str, Any]:
    """Generate an intervention prompt to break an agent out of a loop or error cycle."""
    prompt_lines = [
        "SYSTEM INTERVENTION / RECOVERY DIRECTIVE:",
        f"- Reason: {stuck_reason}",
    ]
    if last_failed_action:
        prompt_lines.append(f"- Note: Stop repeating '{last_failed_action}'. This approach is not working.")

    prompt_lines.extend([
        "- Instruction: Step back and re-evaluate your plan.",
        "- Explore alternative tools or ask a clarifying question if stuck.",
    ])

    return {
        "status": "ok",
        "recovery_prompt": "\n".join(prompt_lines),
    }
