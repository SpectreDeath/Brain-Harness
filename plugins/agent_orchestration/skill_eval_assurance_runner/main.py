"""Skill Eval Assurance Runner Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.skill_eval_assurance import (  # noqa: E402
    SKILL_EVAL_ASSURANCE_SERVICE_KEY,
    ActionSequenceGrade,
    ConfidenceIntervalResult,
    MatchingMode,
    PreflightBoundaryFinding,
    SealedEnvelopeCheck,
    SkillEvalAssuranceProtocol,
    ToolConstraintGrade,
)

try:
    from .service import DefaultSkillEvalAssuranceService
except ImportError:
    from service import DefaultSkillEvalAssuranceService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class SkillEvalAssuranceRunnerPlugin(HarnessPlugin, SkillEvalAssuranceProtocol):
    """HarnessPlugin providing SkillEvalAssuranceProtocol in the IoC container (Rule 45)."""

    name = "plugin.skill_eval_assurance_runner"
    version = "1.0.0"
    description = (
        "Skill evaluation assurance runner with Wilson confidence intervals, "
        "unbiased pass^k reliability, deterministic trajectory graders, and sealed digest verification"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultSkillEvalAssuranceService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SKILL_EVAL_ASSURANCE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(SKILL_EVAL_ASSURANCE_SERVICE_KEY, self, provider=self.name)
        logger.info("SkillEvalAssuranceRunnerPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def compute_wilson_ci(
        self,
        successes: int,
        trials: int,
        *,
        confidence_level: float | None = None,
    ) -> ConfidenceIntervalResult:
        return self._service.compute_wilson_ci(
            successes, trials, confidence_level=confidence_level
        )

    def compute_pass_hat_k(self, successes: int, trials: int, k: int) -> float:
        return self._service.compute_pass_hat_k(successes, trials, k)

    def compute_hake_normalized_gain(self, pre: float, post: float) -> float:
        return self._service.compute_hake_normalized_gain(pre, post)

    def grade_action_sequence(
        self,
        actual_actions: tuple[str, ...],
        expected_actions: tuple[str, ...],
        *,
        matching_mode: MatchingMode | None = None,
    ) -> ActionSequenceGrade:
        return self._service.grade_action_sequence(
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
        return self._service.grade_tool_constraints(
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
        return self._service.audit_preflight_boundary(
            requested_tools=requested_tools,
            has_post_run_boundary_grader=has_post_run_boundary_grader,
        )

    def seal_json_envelope(self, payload: dict[str, Any]) -> str:
        return self._service.seal_json_envelope(payload)

    def verify_sealed_envelope(self, payload: dict[str, Any]) -> SealedEnvelopeCheck:
        return self._service.verify_sealed_envelope(payload)


plugin = SkillEvalAssuranceRunnerPlugin()


def assurance_wilson_ci(
    successes: int, trials: int, confidence_level: float = 0.95
) -> dict[str, Any]:
    """Compute Wilson score CI for small-N evaluation trials."""
    return asdict(
        plugin.compute_wilson_ci(
            successes, trials, confidence_level=confidence_level
        )
    )


def assurance_pass_hat_k(successes: int, trials: int, k: int) -> dict[str, Any]:
    """Compute unbiased tau-bench pass^k estimate."""
    return {"pass_hat_k": plugin.compute_pass_hat_k(successes, trials, k)}


def assurance_grade_action_sequence(
    actual_actions: list[str],
    expected_actions: list[str],
    matching_mode: MatchingMode = "in_order_match",
) -> dict[str, Any]:
    """Grade action trajectory sequence."""
    return asdict(
        plugin.grade_action_sequence(
            tuple(actual_actions), tuple(expected_actions), matching_mode=matching_mode
        )
    )


def assurance_grade_tool_constraints(
    observed_tools: list[str],
    expect_tools: list[str] | None = None,
    reject_tools: list[str] | None = None,
    allow_only: bool = False,
) -> dict[str, Any]:
    """Evaluate observed tool invocations against expect/reject/allow_only rules."""
    return asdict(
        plugin.grade_tool_constraints(
            tuple(observed_tools),
            expect_tools=tuple(expect_tools or ()),
            reject_tools=tuple(reject_tools or ()),
            allow_only=allow_only,
        )
    )


def assurance_verify_sealed_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Verify canonical SHA-256 digest of a sealed evaluation envelope."""
    return asdict(plugin.verify_sealed_envelope(payload))
