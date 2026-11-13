"""Skill Eval Assurance Runner Service — statistical CI, trajectory graders, and sealed release checks.

Distilled from microsoft/waza (v0.41.0):
- Small-N Wilson score confidence intervals and unbiased tau-bench pass^k
- Hake normalized gain controlling for ceiling effects
- Deterministic action_sequence and tool_constraint graders (exact/in_order/any_order + F1)
- Preflight boundary honesty separating static declarations from runtime enforcement
- Content-addressed canonical JSON digest sealing and verification
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any, Literal, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

MatchingMode = Literal["exact_match", "in_order_match", "any_order_match"]
BoundaryState = Literal["unresolved", "valid", "invalid"]

_STD_NORMAL = NormalDist()


@dataclass(slots=True, frozen=True)
class ConfidenceIntervalResult:
    """Bounded confidence interval and point estimate for binary or continuous eval scores."""

    mean: float
    lower: float
    upper: float
    confidence_level: float
    sample_count: int
    method: str = "wilson"

    def __post_init__(self) -> None:
        if not (0.0 < self.confidence_level < 1.0):
            raise ValueError("confidence_level must be strictly between 0 and 1")
        if self.sample_count < 0:
            raise ValueError("sample_count must be >= 0")


@dataclass(slots=True, frozen=True)
class ActionSequenceGrade:
    """Deterministic grading outcome for an ordered or unordered agent tool trajectory."""

    passed: bool
    matching_mode: MatchingMode
    precision: float
    recall: float
    f1: float
    expected_actions: tuple[str, ...]
    actual_actions: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ToolConstraintGrade:
    """Deterministic evaluation of expected/rejected tool usage and allow-only bounds."""

    passed: bool
    score: float
    violations: tuple[str, ...] = ()
    matched_expected: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class PreflightBoundaryFinding:
    """Static preflight diagnostic explicitly refusing to conflate intent with runtime enforcement."""

    rule_id: str
    state: BoundaryState
    mode: str
    summary: str
    remediation: str


@dataclass(slots=True, frozen=True)
class SealedEnvelopeCheck:
    """Verification outcome for a content-addressed release envelope."""

    valid: bool
    computed_digest: str
    declared_digest: str | None
    reason: str


def _is_subsequence(expected: tuple[str, ...], actual: tuple[str, ...]) -> bool:
    idx = 0
    for item in actual:
        if idx < len(expected) and item == expected[idx]:
            idx += 1
    return idx == len(expected)


class SkillEvalAssuranceEngine:
    """Pure, deterministic domain engine for skill evaluation assurance."""

    def __init__(
        self,
        *,
        default_confidence_level: float = 0.95,
        default_matching_mode: MatchingMode = "in_order_match",
    ) -> None:
        if not (0.0 < default_confidence_level < 1.0):
            raise ValueError("default_confidence_level must be strictly between 0 and 1")
        self._default_confidence_level = default_confidence_level
        self._default_matching_mode = default_matching_mode

    def compute_wilson_ci(
        self,
        successes: int,
        trials: int,
        *,
        confidence_level: float | None = None,
    ) -> ConfidenceIntervalResult:
        """Compute a Wilson score interval clamped to [0, 1] for small-N (3-10) agent evals."""
        level = self._default_confidence_level if confidence_level is None else confidence_level
        if not (0.0 < level < 1.0):
            raise ValueError("confidence_level must be strictly between 0 and 1")
        if trials < 1:
            return ConfidenceIntervalResult(
                mean=0.0,
                lower=0.0,
                upper=0.0,
                confidence_level=level,
                sample_count=0,
                method="wilson",
            )
        if successes < 0 or successes > trials:
            raise ValueError("successes must satisfy 0 <= successes <= trials")

        n = float(trials)
        p = float(successes) / n
        z = _STD_NORMAL.inv_cdf(0.5 + level / 2.0)
        z2 = z * z
        denom = 1.0 + z2 / n
        center = (p + z2 / (2.0 * n)) / denom
        half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))

        return ConfidenceIntervalResult(
            mean=p,
            lower=max(0.0, center - half),
            upper=min(1.0, center + half),
            confidence_level=level,
            sample_count=trials,
            method="wilson",
        )

    def compute_pass_hat_k(self, successes: int, trials: int, k: int) -> float:
        """Compute unbiased tau-bench pass^k = C(successes, k) / C(trials, k)."""
        if k < 1 or k > trials or successes < k or trials < 1 or successes < 0:
            return 0.0
        prob = 1.0
        for i in range(k):
            prob *= float(successes - i) / float(trials - i)
        return prob

    def compute_hake_normalized_gain(self, pre: float, post: float) -> float:
        """Compute Hake normalized gain g = (post - pre) / (1 - pre) for ceiling adjustment."""
        if pre >= 1.0:
            return 0.0
        if post >= 1.0:
            return 1.0
        if abs(post - pre) < 1e-12:
            return 0.0
        return (post - pre) / (1.0 - pre)

    def grade_action_sequence(
        self,
        actual_actions: tuple[str, ...],
        expected_actions: tuple[str, ...],
        *,
        matching_mode: MatchingMode | None = None,
    ) -> ActionSequenceGrade:
        """Grade actual tool sequence against expected trajectory using F1 + sequence rules."""
        if not expected_actions:
            raise ValueError("expected_actions must contain at least one action")
        mode: MatchingMode = self._default_matching_mode if matching_mode is None else matching_mode
        if mode not in ("exact_match", "in_order_match", "any_order_match"):
            raise ValueError(f"Unsupported matching_mode: {mode}")

        exp_counts = Counter(expected_actions)
        act_counts = Counter(actual_actions)
        overlap = sum((exp_counts & act_counts).values())

        precision = overlap / len(actual_actions) if actual_actions else 0.0
        recall = overlap / len(expected_actions)
        f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0.0 else 0.0

        if mode == "exact_match":
            passed = actual_actions == expected_actions
        elif mode == "in_order_match":
            passed = _is_subsequence(expected_actions, actual_actions)
        else:
            passed = all(act_counts[k] >= v for k, v in exp_counts.items())

        return ActionSequenceGrade(
            passed=passed,
            matching_mode=mode,
            precision=precision,
            recall=recall,
            f1=f1,
            expected_actions=expected_actions,
            actual_actions=actual_actions,
        )

    def grade_tool_constraints(
        self,
        observed_tools: tuple[str, ...],
        *,
        expect_tools: tuple[str, ...] = (),
        reject_tools: tuple[str, ...] = (),
        allow_only: bool = False,
    ) -> ToolConstraintGrade:
        """Evaluate tool call observations against expected/rejected case-insensitive regex patterns."""
        if not expect_tools and not reject_tools and not allow_only:
            raise ValueError("At least one of expect_tools, reject_tools, or allow_only must be configured")

        compiled_expect = [(pat, re.compile(pat, re.IGNORECASE)) for pat in expect_tools]
        compiled_reject = [(pat, re.compile(pat, re.IGNORECASE)) for pat in reject_tools]

        matched_expected: list[str] = []
        violations: list[str] = []

        for pat, rx in compiled_expect:
            if any(rx.search(tool) for tool in observed_tools):
                matched_expected.append(pat)
            else:
                violations.append(f"missing_expected:{pat}")

        for pat, rx in compiled_reject:
            for tool in observed_tools:
                if rx.search(tool):
                    violations.append(f"rejected_tool:{tool}:{pat}")

        if allow_only and compiled_expect:
            for tool in observed_tools:
                if not any(rx.search(tool) for _, rx in compiled_expect):
                    violations.append(f"disallowed_tool:{tool}")

        total_checks = max(1, len(compiled_expect) + len(compiled_reject))
        score = max(0.0, 1.0 - (len(violations) / total_checks))
        return ToolConstraintGrade(
            passed=len(violations) == 0,
            score=score,
            violations=tuple(violations),
            matched_expected=tuple(matched_expected),
        )

    def audit_preflight_boundary(
        self,
        *,
        requested_tools: tuple[str, ...] | None = None,
        has_post_run_boundary_grader: bool = False,
    ) -> tuple[PreflightBoundaryFinding, ...]:
        """Classify static boundary configuration and post-run graders honestly as unresolved."""
        findings: list[PreflightBoundaryFinding] = []
        if has_post_run_boundary_grader:
            findings.append(
                PreflightBoundaryFinding(
                    rule_id="boundary.post_run",
                    state="unresolved",
                    mode="post-run-grader",
                    summary="Referenced boundary graders observe recorded evidence after execution; they are not preventive runtime controls.",
                    remediation="Inspect runtime policy denials and side-effect evidence separately.",
                )
            )
        if requested_tools is not None:
            mode = "requested-deny-all" if len(requested_tools) == 0 else "requested-allowlist"
            findings.append(
                PreflightBoundaryFinding(
                    rule_id="boundary.requested_policy",
                    state="unresolved",
                    mode=mode,
                    summary="Selected agent tools declaration expresses boundary intent, not verified runtime enforcement.",
                    remediation="Inspect runtime denial events and resulting workspace state.",
                )
            )
        return tuple(findings)

    def seal_json_envelope(self, payload: dict[str, Any]) -> str:
        """Compute canonical SHA-256 digest over payload with any 'digest' member stripped."""
        canonical_obj = {k: v for k, v in payload.items() if k != "digest"}
        encoded = json.dumps(canonical_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def verify_sealed_envelope(self, payload: dict[str, Any]) -> SealedEnvelopeCheck:
        """Verify that payload carries a matching canonical SHA-256 'digest' field."""
        computed = self.seal_json_envelope(payload)
        declared = payload.get("digest")
        if not isinstance(declared, str) or not declared.strip():
            return SealedEnvelopeCheck(
                valid=False,
                computed_digest=computed,
                declared_digest=None,
                reason="missing_declared_digest",
            )
        matched = hmac.compare_digest(computed, declared.strip())
        return SealedEnvelopeCheck(
            valid=matched,
            computed_digest=computed,
            declared_digest=declared.strip(),
            reason="digest_verified" if matched else "digest_mismatch",
        )


@runtime_checkable
class SkillEvalAssuranceProtocol(Protocol):
    """Typed IoC service protocol for skill evaluation assurance."""

    def compute_wilson_ci(
        self,
        successes: int,
        trials: int,
        *,
        confidence_level: float | None = None,
    ) -> ConfidenceIntervalResult: ...

    def compute_pass_hat_k(self, successes: int, trials: int, k: int) -> float: ...

    def compute_hake_normalized_gain(self, pre: float, post: float) -> float: ...

    def grade_action_sequence(
        self,
        actual_actions: tuple[str, ...],
        expected_actions: tuple[str, ...],
        *,
        matching_mode: MatchingMode | None = None,
    ) -> ActionSequenceGrade: ...

    def grade_tool_constraints(
        self,
        observed_tools: tuple[str, ...],
        *,
        expect_tools: tuple[str, ...] = (),
        reject_tools: tuple[str, ...] = (),
        allow_only: bool = False,
    ) -> ToolConstraintGrade: ...

    def audit_preflight_boundary(
        self,
        *,
        requested_tools: tuple[str, ...] | None = None,
        has_post_run_boundary_grader: bool = False,
    ) -> tuple[PreflightBoundaryFinding, ...]: ...

    def seal_json_envelope(self, payload: dict[str, Any]) -> str: ...

    def verify_sealed_envelope(self, payload: dict[str, Any]) -> SealedEnvelopeCheck: ...


SKILL_EVAL_ASSURANCE_SERVICE_KEY: ServiceKey[SkillEvalAssuranceProtocol] = ServiceKey(
    "service.skill_eval_assurance_runner"
)

__all__ = [
    "ActionSequenceGrade",
    "BoundaryState",
    "ConfidenceIntervalResult",
    "MatchingMode",
    "PreflightBoundaryFinding",
    "SKILL_EVAL_ASSURANCE_SERVICE_KEY",
    "SealedEnvelopeCheck",
    "SkillEvalAssuranceEngine",
    "SkillEvalAssuranceProtocol",
    "ToolConstraintGrade",
]
