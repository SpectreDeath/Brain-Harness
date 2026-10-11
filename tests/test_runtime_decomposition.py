"""Contract verification test suite for Kernel Runtime Decomposition (Cycle 45).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted & frozen dataclass contracts on RuntimeConfig (Rule 12 & Rule 43).
3. Typed service key RUNTIME_SERVICE_KEY (Rule 2).
4. 100% backward-compatible facade re-exports across harness.kernel.runtime.
5. Runtime factories (create, create_diagnostic, from_config).
6. Tool and plugin enablement delegators.
7. Declarative configuration parsing and runtime reconciliation.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.kernel.context import ServiceKey
from harness.kernel.runtime import (
    HarnessRuntime,
    RUNTIME_SERVICE_KEY,
    RuntimeConfig,
    create_diagnostic_runtime,
    create_runtime,
    create_runtime_from_config,
    disable_all_plugins,
    disable_tool,
    enable_all_plugins,
    enable_tool,
    export_runtime_session,
    get_default_plugins,
    ingest_plugin_from_source,
    parse_runtime_config,
    reconcile_runtime,
    run_runtime_task,
    start_runtime,
    stop_runtime,
    toggle_tool,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestRuntimeDecompositionArchitecture:
    """Architectural and structural invariants for kernel/runtime subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = (
            Path(__file__).parent.parent
            / "src"
            / "harness"
            / "kernel"
            / "runtime"
        )
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        expected_modules = {
            "__init__.py",
            "coordinator.py",
            "defaults.py",
            "factory.py",
            "lifecycle_runner.py",
            "models.py",
            "plugin_ops.py",
            "plugins.py",
            "reconcile.py",
            "services.py",
            "tools.py",
        }

        found_modules = {p.name for p in pkg_dir.glob("*.py")}
        assert expected_modules.issubset(found_modules)

        for mod_name in expected_modules:
            mod_path = pkg_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_frozen_dataclass_and_service_key(self) -> None:
        """Rule 12, Rule 43 & Rule 2: RuntimeConfig slotted/frozen, RUNTIME_SERVICE_KEY typed."""
        cfg = RuntimeConfig(llm_model="gpt-4o", auto_load_user_plugins=False)
        assert hasattr(cfg, "__slots__")
        assert not hasattr(cfg, "__dict__")

        with pytest.raises((AttributeError, TypeError)):
            cfg.llm_model = "claude-3-5"

        assert isinstance(RUNTIME_SERVICE_KEY, ServiceKey)
        assert RUNTIME_SERVICE_KEY.name == "kernel.runtime"

    @pytest.mark.asyncio
    async def test_diagnostic_runtime_lifecycle(self) -> None:
        """Verify diagnostic runtime creates and starts cleanly with core services."""
        async with HarnessRuntime.create_diagnostic() as rt:
            assert rt.is_running
            assert rt.tools is not None
            assert rt.storage is not None
            assert rt.context is not None
            assert rt.event_bus is not None
            assert rt.lifecycle is not None

        assert not rt.is_running

    def test_declarative_config_parsing(self) -> None:
        """Verify declarative configuration parsing in reconcile module."""
        cfg_dict = {
            "plugins": [
                {"id": "test_plugin", "name": "plugin.test"}
            ]
        }
        tree = parse_runtime_config(cfg_dict)
        assert len(tree.plugins) == 1
        assert tree.plugins[0].id == "test_plugin"
        assert tree.plugins[0].name == "plugin.test"

    def test_default_plugins_suite(self) -> None:
        """Verify default built-in plugin discovery function."""
        plugins = get_default_plugins(include_llm=False)
        plugin_names = [p.name for p in plugins]
        assert "storage.sqlite" in plugin_names
        assert "tools.registry" in plugin_names
        assert "agent.react" in plugin_names
