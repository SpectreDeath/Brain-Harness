"""Agent Harness Architect Plugin — 5-Part Harness Audit, 4-Mechanism Reliability Gate, and Architectural Bet Matching."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "agent-harness-architect" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from agent_harness_architect import AgentHarnessArchitectEngine

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.agent_harness import (
    AGENT_HARNESS_ARCHITECT_SERVICE_KEY,
    ArchitecturalBetRecommendationData,
    FivePartHarnessAuditData,
    FourLayerStackAuditData,
    FourMechanismReliabilityGateData,
    HarnessAuditReportData,
    HarnessComponentStatusData,
    MechanismReliabilityScoreData,
    AgentHarnessArchitectService,
)

logger = structlog.get_logger(__name__)


class AgentHarnessArchitectPlugin(HarnessPlugin, AgentHarnessArchitectService):
    """Plugin providing in-memory harness architecture evaluation, scoring, and visual briefs."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = AgentHarnessArchitectEngine(root_dir=self._root)

    @property
    def name(self) -> str:
        return "plugin.agent_harness_architect"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "5-part harness auditing, 4-mechanism reliability scoring, "
            "4-layer stack decoupling, and architectural bet matching"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENT_HARNESS_ARCHITECT_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the AgentHarnessArchitectService into the IoC container."""
        context.provide(AGENT_HARNESS_ARCHITECT_SERVICE_KEY, self)
        logger.info(
            "agent_harness_architect_service_provided",
            service=str(AGENT_HARNESS_ARCHITECT_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- AgentHarnessArchitectService Implementation ---

    def audit(
        self,
        target_path: str | Path | None = None,
    ) -> HarnessAuditReportData:
        """Execute comprehensive 5-part architecture and 4-layer boundary audit."""
        report = self._engine.audit(target_path=target_path)
        d = report.to_dict()
        return HarnessAuditReportData.model_validate(d)

    def evaluate_reliability(
        self,
        config_or_path: dict[str, Any] | str | Path | None = None,
    ) -> FourMechanismReliabilityGateData:
        """Evaluate planning, sandbox, subagent, compression, and observability across Level 0 to Level 2."""
        gate = self._engine.evaluate_reliability(config_or_path=config_or_path)
        d = gate.to_dict()
        return FourMechanismReliabilityGateData.model_validate(d)

    def classify_bet(
        self,
        bottleneck: str | None = None,
        requirements: list[str] | None = None,
    ) -> ArchitecturalBetRecommendationData:
        """Classify operational bottleneck into one of four architectural harness bets."""
        bet = self._engine.classify_bet(bottleneck=bottleneck, requirements=requirements)
        d = bet.to_dict()
        return ArchitecturalBetRecommendationData.model_validate(d)

    def visual_brief(
        self,
        audit_report: Any | None = None,
        target_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Mermaid topology and reliability scorecard."""
        return self._engine.visual_brief(
            audit_report=audit_report,
            target_path=target_path,
            output_path=output_path,
        )


# Rule 45: Export module singleton plugin instance
plugin = AgentHarnessArchitectPlugin()


# Top-level entrypoints matching plugin.json tool declarations
def harness_audit(
    target: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for harness_audit tool invocation."""
    report = plugin.audit(target_path=target)
    return report.model_dump()


def harness_score(
    config_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for harness_score tool invocation."""
    gate = plugin.evaluate_reliability(config_or_path=config_path)
    return gate.model_dump()


def harness_classify_bet(
    bottleneck: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for harness_classify_bet tool invocation."""
    bet = plugin.classify_bet(bottleneck=bottleneck)
    return bet.model_dump()


def harness_visual_brief(
    target: str | None = None,
    output_path: str | None = None,
    **kwargs: Any,
) -> str:
    """Top-level entrypoint for harness_visual_brief tool invocation."""
    res = plugin.visual_brief(target_path=target, output_path=output_path)
    return str(res)
