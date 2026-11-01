"""Contract test suite for TokenEconomizer Plugin."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

_PLUGIN_DIR = Path(__file__).parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.token_economizer import (
    TOKEN_ECONOMIZER_SERVICE_KEY,
    TokenEconomizerService,
)
from plugins.memory_and_epistemics.token_economizer.main import (
    TokenEconomizerPlugin,
    plugin,
    te_evaluate_tool_pruning,
    te_evaluate_turn_guard,
    te_get_active_micro_skills,
    te_get_token_ledger,
    te_record_micro_skill,
)


@pytest.mark.unit
class TestTokenEconomizerPlugin:
    """Validate TokenEconomizer Plugin lifecycle, IoC registration, and service protocol."""

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = await PluginValidator.validate(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.token_economizer"
        assert plugin.version == "1.0.0"
        assert TOKEN_ECONOMIZER_SERVICE_KEY in plugin.provides
        assert isinstance(plugin, TokenEconomizerPlugin)
        assert isinstance(plugin, TokenEconomizerService)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via TOKEN_ECONOMIZER_SERVICE_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(TOKEN_ECONOMIZER_SERVICE_KEY)
        assert resolved is plugin

    def test_record_micro_skill_functional_entrypoint(self) -> None:
        """Verify te_record_micro_skill functional tool entrypoint."""
        res = te_record_micro_skill(
            key="pip_install_flag",
            success=True,
            edited_files=["setup.py"],
            assertion="Requires --no-build-isolation flag",
        )
        assert res["key"] == "pip_install_flag"
        assert res["state"] == "CANDIDATE"
        assert res["confirms_count"] == 1

    def test_evaluate_tool_pruning_entrypoint(self) -> None:
        """Verify te_evaluate_tool_pruning functional tool entrypoint."""
        res = te_evaluate_tool_pruning(
            loaded_tools=["read_file", "edit_file", "browser_click"],
            session_tool_history=[{"read_file": 3, "edit_file": 1, "browser_click": 0}],
            evidence_sessions_threshold=1,
        )
        assert res["status"] == "ok"
        assert "browser_click" in res["pruned_tools"]
        assert "read_file" not in res["pruned_tools"]

    def test_evaluate_turn_guard_entrypoint(self) -> None:
        """Verify te_evaluate_turn_guard functional tool entrypoint."""
        res = te_evaluate_turn_guard(
            turn_history=[{"tool": "read_file", "status": "ok"}],
            envelope_turn_p90=20,
        )
        assert res["is_stuck"] is False
        assert res["action"] == "continue"

    def test_get_token_ledger_entrypoint(self) -> None:
        """Verify te_get_token_ledger functional tool entrypoint."""
        metrics = te_get_token_ledger()
        assert "net_tokens_saved" in metrics
        assert "net_cost_saved_usd" in metrics

