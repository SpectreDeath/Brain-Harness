"""Contract test suite for R Editor Bridge Plugin."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure plugin directory is on sys.path
_PLUGIN_DIR = Path(__file__).parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.r_runtime import (
    R_RUNTIME_SERVICE_KEY,
    RRuntimeProtocol,
)
from plugins.developer_tooling.r_editor_bridge.main import (
    REditorBridgePlugin,
    plugin,
    r_inspect_session,
    r_parse_diagnostics,
    r_stream_plot,
    r_validate_config,
)


@pytest.mark.unit
class TestREditorBridgePlugin:
    """Validate R Editor Bridge Plugin lifecycle, IoC registration, and tool entrypoints."""

    def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = PluginValidator.validate_sync(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.r_editor_bridge"
        assert plugin.version == "1.0.0"
        assert R_RUNTIME_SERVICE_KEY in plugin.provides
        assert isinstance(plugin, REditorBridgePlugin)
        assert isinstance(plugin, RRuntimeProtocol)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via R_RUNTIME_SERVICE_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(R_RUNTIME_SERVICE_KEY)
        assert resolved is plugin

    def test_r_inspect_session_tool(self) -> None:
        """Verify session inspection reports clean state and active packages."""
        res = r_inspect_session(
            pid=12345,
            working_dir="/home/user/project",
            loaded_packages=["stats", "graphics", "utils"],
            global_symbols=["df", "model", "calculate_summary"],
            active_device="jgd",
        )
        assert res["pid"] == 12345
        assert res["working_dir"] == "/home/user/project"
        assert "stats" in res["loaded_packages"]
        assert "df" in res["global_symbols"]
        assert res["is_clean"] is True

    def test_r_inspect_session_detects_leak(self) -> None:
        """Verify session inspection flags leaked internal .vsc symbols."""
        res = r_inspect_session(
            pid=12345,
            working_dir="/tmp",
            global_symbols=[".vsc.attach", "x"],
        )
        assert res["is_clean"] is False

    def test_r_parse_diagnostics_tool(self) -> None:
        """Verify diagnostic parsing maps LSP ranges and severity strings."""
        raw = [
            {
                "file_path": "script.R",
                "range": {"start": {"line": 10, "character": 4}},
                "severity": 1,
                "message": "Undefined variable 'foo'",
                "code": "undesirable_function_linter",
            },
            {
                "uri": "analysis.R",
                "line": 2,
                "column": 0,
                "severity": "warning",
                "message": "Lines should not exceed 80 characters",
            },
        ]
        parsed = r_parse_diagnostics(raw)
        assert len(parsed) == 2
        assert parsed[0]["line"] == 10
        assert parsed[0]["column"] == 4
        assert parsed[0]["severity"] == "Error"
        assert parsed[0]["code"] == "undesirable_function_linter"
        assert parsed[1]["severity"] == "Warning"

    def test_r_stream_plot_tool(self) -> None:
        """Verify plot display-list serialization packet."""
        plot = r_stream_plot(
            plot_index=1,
            width=1024.0,
            height=768.0,
            format="json",
            payload_size=4096,
        )
        assert plot["plot_index"] == 1
        assert plot["width"] == 1024.0
        assert plot["height"] == 768.0
        assert plot["format"] == "json"
        assert plot["payload_size"] == 4096

    def test_r_validate_config_tool(self) -> None:
        """Verify configuration boundaries for language server parameters."""
        valid = r_validate_config(
            r_path="C:\\Program Files\\R\\R-4.4.1\\bin\\R.exe",
            debounce_ms=300,
            lint_on_change=True,
            max_payload_mb=10,
        )
        assert valid is True

        # Fails on too small debounce (thrashing)
        invalid = r_validate_config(
            r_path="R.exe",
            debounce_ms=10,
        )
        assert invalid is False

