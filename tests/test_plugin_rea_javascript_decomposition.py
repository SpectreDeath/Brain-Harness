"""Contract verification suite for rea_javascript modular subpackage decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.rea_javascript import REA_JAVASCRIPT_KEY
from plugins.data_engineering.rea_javascript.engine import (
    DotnetInspector,
    DotnetTypeInfo,
    ElectronInspector,
    HarEntryInfo,
    HarInspector,
    IpcChannelInfo,
    PinvokeImportInfo,
    ReaJavaScriptEngine,
    RecoveredChunk,
    WakaruRecoverer,
    WebCdpObserver,
    resolve_rea_javascript_engine,
)
from plugins.data_engineering.rea_javascript.main import (
    ReaJavaScriptPlugin,
    plugin,
    rea_javascript_dotnet_inspect,
    rea_javascript_electron_inspect,
    rea_javascript_har_inspect,
    rea_javascript_recover_sources,
    rea_javascript_web_observe,
)

repo_root = Path(__file__).resolve().parent.parent
plugin_dir = repo_root / "plugins" / "data_engineering" / "rea_javascript"
engine_dir = plugin_dir / "engine"


def test_rule_11_submodule_line_bounds():
    """Rule 11: All decomposed python files in engine/ and main.py must be <= 200 lines."""
    for p in sorted(engine_dir.glob("*.py")):
        lines = len(p.read_text(encoding="utf-8").splitlines())
        assert lines <= 200, f"Engine file {p.name} exceeds 200 LOC bound: {lines}"

    main_lines = len((plugin_dir / "main.py").read_text(encoding="utf-8").splitlines())
    assert main_lines <= 200, f"main.py exceeds 200 LOC bound: {main_lines}"


def test_slotted_frozen_models_immutability():
    """Rule 12 & 43: Domain models must use slots=True, frozen=True with __post_init__ assertions."""
    chunk = RecoveredChunk(relative_path="mod.js", size_bytes=100)
    assert chunk.relative_path == "mod.js"
    assert chunk.size_bytes == 100
    with pytest.raises((AttributeError, TypeError)):
        chunk.size_bytes = 200

    ipc = IpcChannelInfo(channel_name="test:event", direction="renderer-to-main", source_file="preload.js")
    with pytest.raises((AttributeError, TypeError)):
        ipc.channel_name = "mutated"

    with pytest.raises(AssertionError):
        IpcChannelInfo("invalid", "invalid-direction", "file.js")

    tinfo = DotnetTypeInfo(type_name="App", namespace="Core", methods_count=5)
    with pytest.raises((AttributeError, TypeError)):
        tinfo.type_name = "Mutated"

    pinfo = PinvokeImportInfo(library="kernel32.dll", function="GetProcessId")
    with pytest.raises((AttributeError, TypeError)):
        pinfo.library = "user32.dll"

    har_entry = HarEntryInfo(method="POST", url="https://api.example.com", status=200)
    with pytest.raises((AttributeError, TypeError)):
        har_entry.status = 500


def test_rule_58_single_seam_resolver():
    """Rule 58: resolve_rea_javascript_engine resolves from ServiceContext or provides fallback."""
    # 1. Fallback without context
    eng_default = resolve_rea_javascript_engine(None)
    assert isinstance(eng_default, ReaJavaScriptEngine)

    # 2. Resolution with context
    ctx = ServiceContext()
    p = ReaJavaScriptPlugin()
    ctx.provide(REA_JAVASCRIPT_KEY, p)
    resolved = resolve_rea_javascript_engine(ctx)
    assert resolved is p._engine


def test_rule_45_plugin_singleton_export():
    """Rule 45: Plugin entrypoint must export instantiated module-level singleton."""
    assert plugin is not None
    assert isinstance(plugin, ReaJavaScriptPlugin)
    assert plugin.name == "plugin.rea_javascript"


def test_composite_engine_delegation(tmp_path: Path):
    """Verify composite engine correctly delegates across all 5 reverse engineering modalities."""
    engine = ReaJavaScriptEngine()

    # 1. Wakaru
    bundle = tmp_path / "bundle.js"
    bundle.write_text("console.log('hello');", encoding="utf-8")
    out_dir = tmp_path / "out"
    res_wakaru = engine.recover_sources(str(bundle), str(out_dir))
    assert res_wakaru["status"] == "ok"
    assert res_wakaru["modules_count"] >= 1

    # 2. Electron
    asar = tmp_path / "app.asar"
    asar.write_text("simulated_asar", encoding="utf-8")
    res_elec = engine.electron_inspect(str(asar))
    assert res_elec["status"] == "ok"
    assert len(res_elec["ipc_channels"]) == 4

    # 3. Web CDP
    res_cdp = engine.web_observe("ws://127.0.0.1:9222/devtools/page/123")
    assert res_cdp["status"] == "ok"
    assert res_cdp["dom_nodes_count"] == 256

    # 4. Dotnet
    pe_file = tmp_path / "app.exe"
    pe_file.write_bytes(b"MZ\x90\x00\x03" + b"\x00" * 100)
    res_dotnet = engine.dotnet_inspect(str(pe_file))
    assert res_dotnet["status"] == "ok"
    assert len(res_dotnet["types"]) == 2

    # 5. HAR
    har_file = tmp_path / "capture.har"
    har_file.write_text('{"log": {"entries": [{"request": {"method": "GET", "url": "https://example.com"}, "response": {"status": 200, "content": {"size": 42}}}]}}', encoding="utf-8")
    res_har = engine.har_inspect(str(har_file))
    assert res_har["status"] == "ok"
    assert res_har["entries_count"] == 1
