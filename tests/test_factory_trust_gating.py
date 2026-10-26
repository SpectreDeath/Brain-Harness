"""Contract tests for SandboxExecutorFactory trust gating, Rule 2, and Rule 45 compliance."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.plugins.sandbox.factory import SandboxExecutorFactory
from harness.plugins.sandbox.in_process import InProcessExecutor
from harness.plugins.sandbox.subprocess import SubprocessExecutor
from harness.plugins.sandbox.venv import VenvExecutor


@pytest.mark.unit
class TestFactoryTrustGatingContracts:
    """Validate sandbox factory trust boundaries and kernel architectural rules."""

    def test_default_executor_is_subprocess_with_network_disabled(self, tmp_path: Path) -> None:
        """Rule 5: Untrusted plugins default to SubprocessExecutor with network air-gapping."""
        entry = tmp_path / "main.py"
        entry.write_text("print('hello')", encoding="utf-8")

        manifest = PluginManifest(
            name="test.untrusted",
            version="1.0.0",
            description="Untrusted test plugin",
            entrypoint="main.py",
            trusted=False,
        )

        executor = SandboxExecutorFactory.create(manifest, tmp_path)
        assert isinstance(executor, SubprocessExecutor)
        assert executor._network_disabled is True

    def test_untrusted_inprocess_request_demoted_to_subprocess(self, tmp_path: Path) -> None:
        """Rule 5: Untrusted plugins requesting IN_PROCESS isolation are forcibly demoted to SubprocessExecutor."""
        entry = tmp_path / "main.py"
        entry.write_text("print('hello')", encoding="utf-8")

        manifest = PluginManifest(
            name="test.demoted",
            version="1.0.0",
            description="Plugin requesting in-process without trust",
            entrypoint="main.py",
            isolation=IsolationMode.IN_PROCESS,
            trusted=False,
        )

        executor = SandboxExecutorFactory.create(manifest, tmp_path)
        assert isinstance(executor, SubprocessExecutor)
        assert executor._network_disabled is True

    def test_trusted_inprocess_creates_inprocess_executor(self, tmp_path: Path) -> None:
        """Rule 5: Only explicitly trusted plugins can use InProcessExecutor."""
        entry = tmp_path / "main.py"
        entry.write_text("VAL = 42\ndef compute(): return VAL\n", encoding="utf-8")

        manifest = PluginManifest(
            name="test.trusted_proc",
            version="1.0.0",
            description="Trusted in-process plugin",
            entrypoint="main.py",
            isolation=IsolationMode.IN_PROCESS,
            trusted=True,
        )

        executor = SandboxExecutorFactory.create(manifest, tmp_path)
        assert isinstance(executor, InProcessExecutor)

    def test_untrusted_with_dependencies_uses_venv_executor(self, tmp_path: Path) -> None:
        """Rule 7: Plugins with declared dependencies route to VenvExecutor for lazy sandbox staging."""
        entry = tmp_path / "main.py"
        entry.write_text("print('venv')", encoding="utf-8")

        manifest = PluginManifest(
            name="test.with_deps",
            version="1.0.0",
            description="Plugin with external dependencies",
            entrypoint="main.py",
            dependencies=["numpy>=1.20"],
            trusted=False,
        )

        executor = SandboxExecutorFactory.create(manifest, tmp_path)
        assert isinstance(executor, VenvExecutor)

    def test_rule_2_service_key_typed_enforcement(self) -> None:
        """Rule 2: Service registration and resolution enforce typed ServiceKey[T], rejecting raw strings."""
        ctx = ServiceContext()
        raw_string_key: Any = "raw.string.key"

        with pytest.raises((AttributeError, TypeError)):
            ctx.provide(raw_string_key, "value")  # type: ignore[arg-type]

        with pytest.raises((AttributeError, TypeError)):
            ctx.require(raw_string_key)  # type: ignore[arg-type]

        with pytest.raises((AttributeError, TypeError)):
            ctx.has(raw_string_key)  # type: ignore[arg-type]

        typed_key = ServiceKey[str]("typed.string.key")
        ctx.provide(typed_key, "valid_value")
        assert ctx.require(typed_key) == "valid_value"
        assert ctx.has(typed_key) is True

    def test_rule_45_module_singleton_pattern(self) -> None:
        """Rule 45: Entrypoint plugins subclass HarnessPlugin and define module-level plugin singleton."""
        class MyTestPlugin(HarnessPlugin):
            @property
            def name(self) -> str:
                return "test_plugin"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def provides(self) -> list[ServiceKey[Any]]:
                return [ServiceKey[str]("my.service")]

            def on_load(self, context: ServiceContext) -> None:
                context.provide(ServiceKey[str]("my.service"), "test", provider="test_plugin")

        inst = MyTestPlugin()
        assert isinstance(inst, HarnessPlugin)
        assert len(inst.provides) == 1
        assert inst.provides[0].name == "my.service"

        # Check a sampling of production plugin entrypoints for `plugin = ...` singleton
        sample_entry = Path("plugins/software_engineering/software_engineer/main.py")
        if sample_entry.exists():
            tree = ast.parse(sample_entry.read_text(encoding="utf-8"))
            has_plugin_var = any(
                isinstance(stmt, ast.Assign)
                and any(getattr(target, "id", None) == "plugin" for target in stmt.targets)
                for stmt in tree.body
            )
            assert has_plugin_var, "Plugin main.py must export instantiated module singleton 'plugin'"
