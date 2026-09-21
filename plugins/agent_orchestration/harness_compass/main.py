"""HarnessCompass Plugin — Automatic Harness Discovery, Calibration & R3 Integration.

Synthesized from foundational research by Zhang et al.
(HarnessCompass: Guiding Automatic Harness Evolution toward Generalizable and Effective Agent Harnesses,
arXiv:2608.01918v1, 2026) and grounded in Knowledge Item ki-harnesscompass-evolution.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import sys
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts and harness src directories are on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "harness-compass" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from harness_compass_engine import (  # type: ignore
    ComponentSurface,
    EvolutionRound,
    FailureAttribution,
    FeedbackItem,
    GateResult,
    GateViolation,
    GroundedEvidence,
    HarnessCompassEngine,
    HarnessEdit,
    IntegrationManifest,
    Track,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.harness_compass import (
    HARNESS_COMPASS_SERVICE_KEY,
    EvolutionRoundData,
    FeedbackItemData,
    GateResultData,
    GateViolationData,
    GroundedEvidenceData,
    HarnessCompassService,
    HarnessEditData,
    IntegrationManifestData,
)

logger = structlog.get_logger(__name__)


class HarnessCompassPlugin(HarnessPlugin, HarnessCompassService):
    """Plugin providing automatic harness evolution, generalization gating, and R3 integration."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        config_path = _PLUGIN_DIR / "config.default.yaml"
        self._engine = HarnessCompassEngine(
            config_path=config_path if config_path.exists() else None
        )

    @property
    def name(self) -> str:
        return "plugin.harness_compass"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Automatic harness discovery, calibration & R3 integration engine "
            "(Zhang et al. 2026)"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [HARNESS_COMPASS_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container."""
        context.provide(HARNESS_COMPASS_SERVICE_KEY, self)
        logger.info(
            "harness_compass_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Cleanup upon unload."""
        logger.info("harness_compass_plugin_unloaded")

    # --- HarnessCompassService Protocol Implementation ---

    def validate_edit(self, edit: HarnessEditData) -> GateResultData:
        """Evaluate a candidate harness edit against Content and Placement invariants."""
        try:
            surface = ComponentSurface(edit.surface.lower())
        except ValueError:
            surface = ComponentSurface.SYSTEMPROMPT

        domain_edit = HarnessEdit(
            id=edit.id,
            surface=surface,
            description=edit.description,
            target_file=edit.target_file,
            content=edit.content,
            action_type=edit.action_type,
            is_advisory=edit.is_advisory,
            is_code_executable=edit.is_code_executable,
        )

        res: GateResult = self._engine.evaluate_edit(domain_edit)
        return GateResultData(
            passed=res.passed,
            violations=[
                GateViolationData(
                    surface=v.surface,
                    rule=v.rule,
                    detail=v.detail,
                )
                for v in res.violations
            ],
        )

    def ground_feedback(
        self, item: FeedbackItemData, trajectory_turns: Sequence[dict[str, Any]]
    ) -> GroundedEvidenceData:
        """Ground first-person agent feedback against raw trajectory turns."""
        try:
            component = ComponentSurface(item.component.lower())
        except ValueError:
            component = ComponentSurface.TOOL_IMPL

        try:
            attr = FailureAttribution(item.attribution.lower())
        except ValueError:
            attr = FailureAttribution.HARNESS

        domain_item = FeedbackItem(
            kind=item.kind,
            component=component,
            friction=item.friction,
            desired_change=item.desired_change,
            trace_refs=tuple(item.trace_refs),
            severity=item.severity,
            attribution=attr,
            self_consistency=item.self_consistency,
        )

        res: GroundedEvidence = self._engine.ground_feedback(
            domain_item, list(trajectory_turns)
        )
        return GroundedEvidenceData(
            item=item,
            grounded=res.grounded,
            assigned_track=res.assigned_track.value,
            confidence=res.confidence,
            rejection_reason=res.rejection_reason,
        )

    def execute_r3_merge(
        self,
        winner_name: str,
        winner_score: float,
        winner_edits: Sequence[HarnessEditData],
        loser_name: str,
        loser_score: float,
        loser_edits: Sequence[HarnessEditData],
    ) -> IntegrationManifestData:
        """Execute R3 integration: Revision, Recombination, and Occam's Razor Refinement."""
        def _to_domain(e: HarnessEditData) -> HarnessEdit:
            try:
                s = ComponentSurface(e.surface.lower())
            except ValueError:
                s = ComponentSurface.SYSTEMPROMPT
            return HarnessEdit(
                id=e.id,
                surface=s,
                description=e.description,
                target_file=e.target_file,
                content=e.content,
                action_type=e.action_type,
                is_advisory=e.is_advisory,
                is_code_executable=e.is_code_executable,
            )

        w_edits = [_to_domain(e) for e in winner_edits]
        l_edits = [_to_domain(e) for e in loser_edits]

        manifest: IntegrationManifest = self._engine.merge(
            winner_name=winner_name,
            winner_score=winner_score,
            winner_edits=w_edits,
            loser_name=loser_name,
            loser_score=loser_score,
            loser_edits=l_edits,
        )

        return IntegrationManifestData(
            base_winner=manifest.base_winner,
            winner_score=manifest.winner_score,
            loser_score=manifest.loser_score,
            kept_from_loser=list(manifest.kept_from_loser),
            dropped_from_loser=list(manifest.dropped_from_loser),
            removed_as_redundant=list(manifest.removed_as_redundant),
        )

    def simulate_round(
        self,
        round_num: int,
        baseline_score: float,
        structural_edits: Sequence[HarnessEditData],
        guidance_edits: Sequence[HarnessEditData],
        structural_score: float,
        guidance_score: float,
    ) -> EvolutionRoundData:
        """Simulate a full 5-stage closed loop evolution and acceptance round."""
        def _to_domain(e: HarnessEditData) -> HarnessEdit:
            try:
                s = ComponentSurface(e.surface.lower())
            except ValueError:
                s = ComponentSurface.SYSTEMPROMPT
            return HarnessEdit(
                id=e.id,
                surface=s,
                description=e.description,
                target_file=e.target_file,
                content=e.content,
                action_type=e.action_type,
                is_advisory=e.is_advisory,
                is_code_executable=e.is_code_executable,
            )

        s_edits = [_to_domain(e) for e in structural_edits]
        g_edits = [_to_domain(e) for e in guidance_edits]

        r: EvolutionRound = self._engine.simulate_evolution_round(
            round_num=round_num,
            baseline_score=baseline_score,
            structural_edits=s_edits,
            guidance_edits=g_edits,
            structural_score=structural_score,
            guidance_score=guidance_score,
        )

        return EvolutionRoundData(
            round_num=r.round_num,
            baseline_score=r.baseline_score,
            structural_score=r.structural_score,
            guidance_score=r.guidance_score,
            winner_track=r.winner_track.value,
            winner_score=r.winner_score,
            manifest=IntegrationManifestData(
                base_winner=r.manifest.base_winner,
                winner_score=r.manifest.winner_score,
                loser_score=r.manifest.loser_score,
                kept_from_loser=list(r.manifest.kept_from_loser),
                dropped_from_loser=list(r.manifest.dropped_from_loser),
                removed_as_redundant=list(r.manifest.removed_as_redundant),
            ),
            accepted=r.accepted,
            notes=r.notes,
        )

    def generate_visual_brief(
        self, output_path: str | Path | None = None
    ) -> Path:
        """Generate interactive HTML Visual Brief with telemetry and Mermaid DAG."""
        return self._engine.generate_visual_brief(output_path=output_path)

    # --- Tool Entrypoints for External / Plugin Execution ---

    def validate_gate(
        self,
        id: str,
        surface: str,
        description: str,
        target_file: str,
        content: str,
        is_advisory: bool = False,
        is_code_executable: bool = False,
    ) -> dict[str, Any]:
        """Tool entrypoint for Generalization Gate validation."""
        edit = HarnessEditData(
            id=id,
            surface=surface,
            description=description,
            target_file=target_file,
            content=content,
            is_advisory=is_advisory,
            is_code_executable=is_code_executable,
        )
        return self.validate_edit(edit).model_dump()

    def ground_feedback_tool(
        self,
        kind: str,
        component: str,
        friction: str,
        desired_change: str,
        trace_refs: list[str] | None = None,
        attribution: str = "harness",
        trajectory_turns: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Tool entrypoint for feedback grounding."""
        item = FeedbackItemData(
            kind=kind,
            component=component,
            friction=friction,
            desired_change=desired_change,
            trace_refs=trace_refs or [],
            attribution=attribution,
        )
        return self.ground_feedback(item, trajectory_turns or []).model_dump()

    def merge_r3(
        self,
        winner_name: str,
        winner_score: float,
        winner_edits: list[dict[str, Any]],
        loser_name: str,
        loser_score: float,
        loser_edits: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Tool entrypoint for R3 integration."""
        w_edits = [HarnessEditData(**e) for e in winner_edits]
        l_edits = [HarnessEditData(**e) for e in loser_edits]
        return self.execute_r3_merge(
            winner_name=winner_name,
            winner_score=winner_score,
            winner_edits=w_edits,
            loser_name=loser_name,
            loser_score=loser_score,
            loser_edits=l_edits,
        ).model_dump()

    def run_evolution_round(
        self,
        round_num: int,
        baseline_score: float,
        structural_edits: list[dict[str, Any]],
        guidance_edits: list[dict[str, Any]],
        structural_score: float,
        guidance_score: float,
    ) -> dict[str, Any]:
        """Tool entrypoint for full round simulation."""
        s_edits = [HarnessEditData(**e) for e in structural_edits]
        g_edits = [HarnessEditData(**e) for e in guidance_edits]
        return self.simulate_round(
            round_num=round_num,
            baseline_score=baseline_score,
            structural_edits=s_edits,
            guidance_edits=g_edits,
            structural_score=structural_score,
            guidance_score=guidance_score,
        ).model_dump()

    def harness_compass_visual_brief(self, output_path: str | None = None) -> str:
        """Tool entrypoint for generating interactive visual brief."""
        brief_path = self.generate_visual_brief(output_path)
        return str(brief_path)


# Rule 45: Plugin Module Singleton & IoC Provider Invariant
plugin = HarnessCompassPlugin()
