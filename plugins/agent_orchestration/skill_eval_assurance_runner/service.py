"""Subprocess-isolated service implementation for Skill Eval Assurance Runner."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from harness.services.skill_eval_assurance import (
    ActionSequenceGrade,
    ConfidenceIntervalResult,
    MatchingMode,
    PreflightBoundaryFinding,
    SealedEnvelopeCheck,
    SkillEvalAssuranceEngine,
    SkillEvalAssuranceProtocol,
    ToolConstraintGrade,
)


class DefaultSkillEvalAssuranceService(SkillEvalAssuranceProtocol):
    """Service adapter delegating to SkillEvalAssuranceEngine with Rule 14 subprocess support."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = SkillEvalAssuranceEngine()

    def compute_wilson_ci(
        self,
        successes: int,
        trials: int,
        *,
        confidence_level: float | None = None,
    ) -> ConfidenceIntervalResult:
        return self._engine.compute_wilson_ci(
            successes, trials, confidence_level=confidence_level
        )

    def compute_pass_hat_k(self, successes: int, trials: int, k: int) -> float:
        return self._engine.compute_pass_hat_k(successes, trials, k)

    def compute_hake_normalized_gain(self, pre: float, post: float) -> float:
        return self._engine.compute_hake_normalized_gain(pre, post)

    def grade_action_sequence(
        self,
        actual_actions: tuple[str, ...],
        expected_actions: tuple[str, ...],
        *,
        matching_mode: MatchingMode | None = None,
    ) -> ActionSequenceGrade:
        return self._engine.grade_action_sequence(
            actual_actions, expected_actions, matching_mode=matching_mode
        )

    def grade_tool_constraints(
        self,
        observed_tools: tuple[str, ...],
        *,
        expect_tools: tuple[str, ...] = (),
        reject_tools: tuple[str, ...] = (),
        allow_only: bool = False,
    ) -> ToolConstraintGrade:
        return self._engine.grade_tool_constraints(
            observed_tools,
            expect_tools=expect_tools,
            reject_tools=reject_tools,
            allow_only=allow_only,
        )

    def audit_preflight_boundary(
        self,
        *,
        requested_tools: tuple[str, ...] | None = None,
        has_post_run_boundary_grader: bool = False,
    ) -> tuple[PreflightBoundaryFinding, ...]:
        return self._engine.audit_preflight_boundary(
            requested_tools=requested_tools,
            has_post_run_boundary_grader=has_post_run_boundary_grader,
        )

    def seal_json_envelope(self, payload: dict[str, Any]) -> str:
        return self._engine.seal_json_envelope(payload)

    def verify_sealed_envelope(self, payload: dict[str, Any]) -> SealedEnvelopeCheck:
        return self._engine.verify_sealed_envelope(payload)

    async def run_cli_subprocess(
        self, args: list[str], *, timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute the skill CLI script in an isolated subprocess with Rule 14 pipe cleanup."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "skill-eval-assurance-runner"
            / "scripts"
            / "skill_eval_assurance_engine.py"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                close_fn = getattr(pipe, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        pass
