"""Contract test suite for Agent Desktop Operator domain models and engine."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure workspace and src are on sys.path
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_SKILL_SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "agent-desktop-operator"
    / "scripts"
)
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from desktop_operator_engine import AgentDesktopOperatorEngine
from harness.services.agent_desktop import (
    ActionDisposition,
    DesktopRefToken,
    EvidenceTriState,
)


@pytest.mark.unit
class TestAgentDesktopDomainModels:
    """Validate slotted/frozen dataclass immutability, ref tokens, and disposition logic."""

    def test_ref_token_immutability_and_slots(self) -> None:
        """Verify DesktopRefToken is frozen and slotted per Rule 12 and Rule 43."""
        token = DesktopRefToken(snapshot_id="s123", element_index=4, qualified="@s123:e4")
        assert token.snapshot_id == "s123"
        assert token.element_index == 4
        assert token.qualified == "@s123:e4"

        # Rule 43: Frozen dataclass mutation assertion via direct attribute assignment
        with pytest.raises((AttributeError, TypeError)):
            token.element_index = 5  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            token.qualified = "@s123:e5"  # type: ignore

    def test_ref_token_validation_and_parsing(self) -> None:
        """Verify parse rejects bare or malformed refs and accepts qualified tokens."""
        token = DesktopRefToken.parse("@s8f3k2p9:e12")
        assert token.snapshot_id == "s8f3k2p9"
        assert token.element_index == 12
        assert token.qualified == "@s8f3k2p9:e12"
        assert token.powershell_quoted() == "'@s8f3k2p9:e12'"

        # Bare ref refusal
        with pytest.raises(ValueError, match="Bare refs like '@e8' are refused"):
            DesktopRefToken.parse("@e8")

        with pytest.raises(ValueError):
            DesktopRefToken.parse("")

        with pytest.raises(ValueError):
            DesktopRefToken(snapshot_id="", element_index=1, qualified="@:e1")

        with pytest.raises(ValueError):
            DesktopRefToken(snapshot_id="s1", element_index=-1, qualified="@s1:e-1")

    def test_action_disposition_immutability_and_properties(self) -> None:
        """Verify ActionDisposition 2D matrix properties and immutability per Rule 43."""
        disp = ActionDisposition(delivery="delivered_verified", retry="safe")
        assert disp.is_retry_safe is True
        assert disp.should_rollback_transaction is False

        # Rule 43: Frozen dataclass mutation assertion via direct attribute assignment
        with pytest.raises((AttributeError, TypeError)):
            disp.delivery = "not_delivered"  # type: ignore

        # Uncertain delivery demands transaction rollback
        disp_uncertain = ActionDisposition(delivery="delivery_uncertain", retry="unsafe")
        assert disp_uncertain.is_retry_safe is False
        assert disp_uncertain.should_rollback_transaction is True

        # Invalid disposition states
        with pytest.raises(ValueError):
            ActionDisposition(delivery="invalid_state")

        with pytest.raises(ValueError):
            ActionDisposition(delivery="delivered_verified", retry="invalid_retry")

    def test_evidence_tri_state_semantics(self) -> None:
        """Verify EvidenceTriState non-collapsing predicates."""
        known = EvidenceTriState.KNOWN
        absent = EvidenceTriState.ABSENT
        unknown = EvidenceTriState.UNKNOWN

        assert known.is_known() is True
        assert known.is_absent() is False
        assert known.is_unknown() is False

        assert absent.is_known() is False
        assert absent.is_absent() is True
        assert absent.is_unknown() is False

        assert unknown.is_known() is False
        assert unknown.is_absent() is False
        assert unknown.is_unknown() is True


@pytest.mark.unit
class TestAgentDesktopOperatorEngine:
    """Validate AgentDesktopOperatorEngine execution and simulation fallbacks."""

    @pytest.fixture
    def engine(self) -> AgentDesktopOperatorEngine:
        return AgentDesktopOperatorEngine()

    @pytest.mark.asyncio
    async def test_engine_snapshot_simulation(self, engine: AgentDesktopOperatorEngine) -> None:
        res = await engine.snapshot(app="TestApp", interactive_only=True)
        assert res.status == "ok"
        assert res.ref_count > 0
        assert res.snapshot_id != ""
        assert "tree" in res.model_dump()

    @pytest.mark.asyncio
    async def test_engine_act_simulation(self, engine: AgentDesktopOperatorEngine) -> None:
        res = await engine.act(action="click", ref_id="@snap_test:e1")
        assert res.status == "ok"
        assert res.ok is True
        assert res.command == "click"
        assert res.ref_id == "@snap_test:e1"
        assert res.retry_safe is True

    @pytest.mark.asyncio
    async def test_engine_act_rejects_bare_ref(self, engine: AgentDesktopOperatorEngine) -> None:
        with pytest.raises(ValueError, match="Bare refs like '@e8' are refused"):
            await engine.act(action="click", ref_id="@e1")

    @pytest.mark.asyncio
    async def test_engine_find_and_window(self, engine: AgentDesktopOperatorEngine) -> None:
        find_res = await engine.find(app="TestApp", role="button")
        assert find_res.status == "ok"

        win_res = await engine.manage_window(operation="list-windows", app="TestApp")
        assert win_res.status == "ok"
        assert len(win_res.windows) >= 1

    @pytest.mark.asyncio
    async def test_engine_status(self, engine: AgentDesktopOperatorEngine) -> None:
        status_res = await engine.get_status()
        assert status_res.status == "ok"
        assert status_res.platform in ("win32", "windows", "linux", "darwin")
        assert len(status_res.supported_surfaces) >= 3
