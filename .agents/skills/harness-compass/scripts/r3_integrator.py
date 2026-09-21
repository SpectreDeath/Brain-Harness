"""HarnessCompass R3 Integrator & Generalization Gate Engine.

Backward-compatible facade delegating directly to the slotted
harness_compass_engine.py implementation.
"""

from __future__ import annotations

import sys

# Rule 23/50: Ensure UTF-8 standard stream handling on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from harness_compass_engine import (
    ComponentSurface,
    EvolutionRound,
    FailureAttribution,
    FeedbackItem,
    GateResult,
    GateViolation,
    GeneralizationGate,
    GroundedEvidence,
    GUIDANCE_SURFACES,
    HarnessCompassEngine,
    HarnessEdit,
    IntegrationManifest,
    ProactiveFeedbackGrounder,
    R3IntegratorEngine,
    STRUCTURAL_SURFACES,
    Track,
)

__all__ = [
    "ComponentSurface",
    "EvolutionRound",
    "FailureAttribution",
    "FeedbackItem",
    "GateResult",
    "GateViolation",
    "GeneralizationGate",
    "GroundedEvidence",
    "GUIDANCE_SURFACES",
    "HarnessCompassEngine",
    "HarnessEdit",
    "IntegrationManifest",
    "ProactiveFeedbackGrounder",
    "R3IntegratorEngine",
    "STRUCTURAL_SURFACES",
    "Track",
]


def main() -> None:
    print("HarnessCompass R3 Integrator initialized.")


if __name__ == "__main__":
    main()
