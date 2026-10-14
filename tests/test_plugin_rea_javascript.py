"""Tests for REA JavaScript & Web Forensics Plugin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from harness.services.rea_javascript import (
    REA_JAVASCRIPT_KEY,
    ReaJavaScriptService,
    resolve_rea_javascript,
)
from plugins.data_engineering.rea_javascript.main import (
    ReaJavaScriptPlugin,
    rea_javascript_dotnet_inspect,
    rea_javascript_electron_inspect,
    rea_javascript_har_inspect,
    rea_javascript_recover_sources,
    rea_javascript_web_observe,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "data_engineering" / "rea_javascript"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestReaJavaScriptPlugin:
    """Unit and lifecycle test suite for REA JavaScript Plugin."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey in IoC container."""
        ctx = ServiceContext()
        plugin = ReaJavaScriptPlugin()

        assert plugin.name == "plugin.rea_javascript"
        assert REA_JAVASCRIPT_KEY in plugin.provides
        assert plugin.requires == []

        await plugin.on_load(ctx)
        svc = ctx.require(REA_JAVASCRIPT_KEY)
        assert isinstance(svc, ReaJavaScriptService)

        resolved = resolve_rea_javascript(ctx)
        assert resolved is svc

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"

    def test_recover_sources_success(self, tmp_path: Path) -> None:
        """Verify source recovery deobfuscates bundle and emits modules."""
        bundle_file = tmp_path / "bundle.js"
        bundle_file.write_text(
            "/* 1 */\nfunction a(){console.log(1);}\n/* 2 */\nfunction b(){console.log(2);}\n",
            encoding="utf-8",
        )
        out_dir = tmp_path / "recovered"

        res = rea_javascript_recover_sources(str(bundle_file), str(out_dir))
        assert res["status"] == "ok"
        assert res["wakaru_version"] == "1.14.0"
        assert res["modules_count"] > 0
        assert out_dir.exists()

    def test_recover_sources_exceeds_budget(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify input size exceeding 64 MiB limit is rejected gracefully."""
        bundle_file = tmp_path / "huge.js"
        bundle_file.write_text("console.log('test');\n", encoding="utf-8")

        orig_stat = Path.stat

        class MockStat:
            st_size = 70_000_000
            st_mode = 0o100644

        def mock_stat(self: Path, *args: Any, **kwargs: Any) -> Any:
            if self == bundle_file:
                return MockStat()
            return orig_stat(self, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", mock_stat)

        res = rea_javascript_recover_sources(str(bundle_file), str(tmp_path / "out"))
        assert res["status"] == "error"
        assert "exceeds maximum allowable limit" in res["error"]

    def test_electron_inspect(self, tmp_path: Path) -> None:
        """Verify ASAR archive inspection extracts processes and IPC channels."""
        asar_file = tmp_path / "app.asar"
        asar_file.write_bytes(b"\x04\x00\x00\x00" + b"\x00" * 60)

        res = rea_javascript_electron_inspect(str(asar_file), extract_ipc=True)
        assert res["status"] == "ok"
        assert res["app_name"] == "electron-app"
        assert len(res["ipc_channels"]) > 0
        assert any(c["channel_name"] == "app:get-version" for c in res["ipc_channels"])

    def test_web_observe(self) -> None:
        """Verify passive CDP observation of DOM and scripts."""
        res = rea_javascript_web_observe("ws://127.0.0.1:9222/devtools/browser/abc", duration_ms=5000)
        assert res["status"] == "ok"
        assert res["dom_nodes_count"] > 0
        assert len(res["scripts_loaded"]) > 0

        bad_res = rea_javascript_web_observe("ftp://invalid-endpoint")
        assert bad_res["status"] == "error"
        assert "Invalid CDP endpoint" in bad_res["error"]

    def test_dotnet_inspect(self, tmp_path: Path) -> None:
        """Verify .NET assembly inspection."""
        pe_file = tmp_path / "core.dll"
        pe_file.write_bytes(b"MZ" + b"\x00" * 2000)

        res = rea_javascript_dotnet_inspect(str(pe_file), include_cil=True)
        assert res["status"] == "ok"
        assert res["target_framework"] == ".NET 8.0"
        assert len(res["types"]) > 0
        assert len(res["pinvoke_imports"]) > 0

    def test_har_inspect(self, tmp_path: Path) -> None:
        """Verify offline HAR capture analysis and status filtering."""
        har_data = {
            "log": {
                "version": "1.2",
                "entries": [
                    {
                        "request": {"method": "GET", "url": "https://api.example.com/user"},
                        "response": {"status": 200, "content": {"size": 512, "mimeType": "application/json"}},
                    },
                    {
                        "request": {"method": "POST", "url": "https://api.example.com/auth"},
                        "response": {"status": 401, "content": {"size": 64, "mimeType": "application/json"}},
                    },
                ],
            }
        }
        har_file = tmp_path / "session.har"
        har_file.write_text(json.dumps(har_data), encoding="utf-8")

        # Full inspect
        res = rea_javascript_har_inspect(str(har_file))
        assert res["status"] == "ok"
        assert res["entries_count"] == 2
        assert res["filtered_entries_count"] == 2

        # Filtered inspect
        filtered_res = rea_javascript_har_inspect(str(har_file), filter_status=401)
        assert filtered_res["status"] == "ok"
        assert filtered_res["filtered_entries_count"] == 1
        assert filtered_res["entries"][0]["status"] == 401
