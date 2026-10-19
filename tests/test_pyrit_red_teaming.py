"""Contract verification tests for PyRIT GenAI Red-Teaming (Phase 3 Vector 3)."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.pyrit_scanner import (
    PYRIT_SCANNER_SERVICE_KEY,
    AttackVector,
    DefaultPyritScannerService,
    PyritScannerService,
    PyritSubprocessRunner,
    RedTeamTarget,
    VulnerabilityScorecard,
    resolve_pyrit_scanner,
)
from plugins.security_and_forensics.pyrit_red_teaming.main import (
    PyritRedTeamPlugin,
    plugin,
)


@pytest.mark.unit
class TestPyritDataStructures:
    """Verifies slotted frozen dataclass immutability and post-init assertions (Rule 12, Rule 43)."""

    def test_red_team_target_immutability(self) -> None:
        target = RedTeamTarget(target_type="agent_loop", endpoint="http://localhost:8080", max_turns=5)
        assert target.target_type == "agent_loop"
        assert target.max_turns == 5

        # Rule 43: direct assignment must raise AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            target.endpoint = "http://evil.com"  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            target.max_turns = 20  # type: ignore[misc]

    def test_red_team_target_post_init_validation(self) -> None:
        with pytest.raises(ValueError, match="target_type must be one of"):
            RedTeamTarget(target_type="invalid_type")

        with pytest.raises(ValueError, match="max_turns must be positive"):
            RedTeamTarget(max_turns=0)

    def test_attack_vector_validation(self) -> None:
        v = AttackVector(technique="crescendo", intensity=4, payload_count=15)
        assert v.technique == "crescendo"
        assert v.intensity == 4

        with pytest.raises(ValueError, match="technique must be one of"):
            AttackVector(technique="unsupported_technique")

        with pytest.raises(ValueError, match="intensity must be between 1 and 5"):
            AttackVector(intensity=6)

    def test_scorecard_immutability(self) -> None:
        card = VulnerabilityScorecard(
            attack_success_rate=0.25,
            leaked_system_tokens=(),
            bypassed_tool_boundaries=(),
            risk_level="medium",
            recommendations=("Apply token filtering",),
            elapsed_ms=12.5,
        )
        assert card.risk_level == "medium"
        assert card.attack_success_rate == 0.25

        with pytest.raises((AttributeError, TypeError)):
            card.risk_level = "critical"  # type: ignore[misc]


class TestPyritScannerService:
    """Verifies service operations, attack plans, and simulation fallbacks."""

    @pytest.mark.asyncio
    async def test_generate_attack_plan(self) -> None:
        svc = DefaultPyritScannerService()
        target = RedTeamTarget(target_type="system_prompt", endpoint="test")
        vector = AttackVector(technique="crescendo", intensity=3, payload_count=5)

        plan = await svc.generate_attack_plan(target, vector)
        assert len(plan) == 5
        assert plan[0]["step"] == 1
        assert plan[0]["technique"] == "crescendo"
        assert plan[4]["step"] == 5

    @pytest.mark.asyncio
    async def test_scan_target_simulation(self) -> None:
        svc = DefaultPyritScannerService()
        target = RedTeamTarget(target_type="agent_loop", endpoint="test")
        vector = AttackVector(technique="roleplay_jailbreak", intensity=2)

        card = await svc.scan_target(target, vector)
        assert isinstance(card, VulnerabilityScorecard)
        assert card.risk_level in ("low", "medium", "high", "critical")
        assert 0.0 <= card.attack_success_rate <= 1.0
        assert card.elapsed_ms >= 0.0

    def test_list_techniques(self) -> None:
        svc = DefaultPyritScannerService()
        techs = svc.list_available_techniques()
        assert "crescendo" in techs
        assert "roleplay_jailbreak" in techs
        assert "encoding_fuzz" in techs

    def test_single_seam_resolver(self) -> None:
        ctx = ServiceContext()
        custom = DefaultPyritScannerService()
        ctx.provide(PYRIT_SCANNER_SERVICE_KEY, custom)

        resolved = resolve_pyrit_scanner(ctx)
        assert resolved is custom
        fallback = resolve_pyrit_scanner(None)
        assert isinstance(fallback, PyritScannerService)


@pytest.mark.asyncio
class TestPyritPluginAndLifecycle:
    """Verifies IoC container registration, plugin lifecycle, and PluginValidator compliance."""

    async def test_plugin_on_load(self) -> None:
        ctx = ServiceContext()
        p = PyritRedTeamPlugin()
        assert PYRIT_SCANNER_SERVICE_KEY in p.provides

        await p.on_load(ctx)
        assert ctx.has(PYRIT_SCANNER_SERVICE_KEY)
        svc = ctx.require(PYRIT_SCANNER_SERVICE_KEY)
        assert isinstance(svc, PyritScannerService)

        # Module-level singleton export (Rule 45)
        assert plugin is not None
        assert plugin.name == "domain.pyrit_red_teaming"

    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/security_and_forensics/pyrit_red_teaming")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
