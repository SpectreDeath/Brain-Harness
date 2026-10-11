"""Runtime construction and instantiation factories."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.kernel.runtime.defaults import get_default_plugins
from harness.kernel.runtime.reconcile import parse_runtime_config

if TYPE_CHECKING:
    from harness.events.bus import EventBus
    from harness.kernel.runtime.coordinator import HarnessRuntime
    from harness.plugins.base import HarnessPlugin
    from harness.plugins.loader import PluginLoader

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def create_runtime(
    runtime_cls: type[HarnessRuntime],
    *,
    plugin_dirs: list[Path] | None = None,
    db_path: Path | str | None = None,
    event_log_path: Path | None = None,
    builtins: list[HarnessPlugin] | None = None,
    llm: Any | None = None,
    fallback_llm: Any | None = None,
    llm_model: str = "gpt-4o-mini",
    auto_load_user_plugins: bool = True,
    lazy_external_plugins: bool = True,
) -> HarnessRuntime:
    """Factory for a standard Harness runtime instance with default plugins."""
    from harness.events.bus import EventBus
    from harness.plugins.loader import PluginLoader

    pdirs = plugin_dirs or [Path("plugins")]
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)
    bus = EventBus(log_file=event_log_path)
    loader = PluginLoader(plugin_dirs=pdirs)

    runtime = runtime_cls(
        context=ctx,
        lifecycle=lifecycle,
        event_bus=bus,
        loader=loader,
        plugin_dirs=pdirs,
        auto_load_user_plugins=auto_load_user_plugins,
        lazy_external_plugins=lazy_external_plugins,
    )

    active_llm = llm if llm is not None else fallback_llm
    if active_llm is not None:
        from harness.services.llm import LLM_SERVICE_KEY

        runtime.provide(LLM_SERVICE_KEY, active_llm)

    plugins_to_register = builtins
    if plugins_to_register is None:
        plugins_to_register = get_default_plugins(
            db_path=db_path,
            include_llm=(active_llm is None),
            llm_model=llm_model,
        )

    for p in plugins_to_register:
        runtime.register_plugin(p)

    runtime._auto_load_user_plugins = auto_load_user_plugins
    runtime._lazy_external_plugins = lazy_external_plugins
    runtime._initial_config_tree = None
    return runtime


def create_diagnostic_runtime(
    runtime_cls: type[HarnessRuntime],
    *,
    db_path: str = ":memory:",
    include_tools: bool = True,
    include_storage: bool = True,
) -> HarnessRuntime:
    """Lightweight runtime factory for zero-overhead diagnostics and tests."""
    from harness.agent.session import AgentSessionPlugin
    from harness.services.storage import StoragePlugin
    from harness.services.tools import ToolRegistryPlugin

    builtins: list[HarnessPlugin] = []
    if include_storage:
        builtins.append(StoragePlugin(db_path=db_path))
        builtins.append(AgentSessionPlugin())
    if include_tools:
        builtins.append(ToolRegistryPlugin())

    return runtime_cls.create(
        db_path=db_path,
        builtins=builtins,
        auto_load_user_plugins=False,
        lazy_external_plugins=True,
    )


def create_runtime_from_config(
    runtime_cls: type[HarnessRuntime],
    config: Any,
    *,
    plugin_dirs: list[Path] | None = None,
    event_log_path: Path | None = None,
    llm: Any | None = None,
    auto_load_user_plugins: bool = False,
) -> HarnessRuntime:
    """Create a HarnessRuntime pre-configured with a declarative configuration."""
    parsed_config = parse_runtime_config(config)
    runtime = runtime_cls.create(
        plugin_dirs=plugin_dirs,
        event_log_path=event_log_path,
        llm=llm,
        builtins=[],
        auto_load_user_plugins=auto_load_user_plugins,
    )
    runtime._initial_config_tree = parsed_config
    return runtime


__all__ = [
    "create_diagnostic_runtime",
    "create_runtime",
    "create_runtime_from_config",
]
