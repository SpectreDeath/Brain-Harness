"""Harness Runtime — unified orchestrator and lifecycle coordinator.

The HarnessRuntime is the primary entry point to a running Harness instance.
It encapsulates the ServiceContext (IoC container), PluginLifecycle manager,
EventBus (observability), and PluginLoader behind a clean, deep interface.
"""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.runtime.coordinator import HarnessRuntime
from harness.kernel.runtime.defaults import get_default_plugins
from harness.kernel.runtime.factory import (
    create_diagnostic_runtime,
    create_runtime,
    create_runtime_from_config,
)
from harness.kernel.runtime.lifecycle_runner import start_runtime, stop_runtime
from harness.kernel.runtime.models import RUNTIME_SERVICE_KEY, RuntimeConfig
from harness.kernel.runtime.plugins import (
    disable_all_plugins,
    enable_all_plugins,
    ingest_plugin_from_source,
)
from harness.kernel.runtime.reconcile import parse_runtime_config, reconcile_runtime
from harness.kernel.runtime.tools import (
    disable_tool,
    enable_tool,
    export_runtime_session,
    run_runtime_task,
    toggle_tool,
)

__all__ = [
    "HarnessRuntime",
    "RUNTIME_SERVICE_KEY",
    "RuntimeConfig",
    "create_diagnostic_runtime",
    "create_runtime",
    "create_runtime_from_config",
    "disable_all_plugins",
    "disable_tool",
    "enable_all_plugins",
    "enable_tool",
    "export_runtime_session",
    "get_default_plugins",
    "ingest_plugin_from_source",
    "parse_runtime_config",
    "reconcile_runtime",
    "run_runtime_task",
    "start_runtime",
    "stop_runtime",
    "toggle_tool",
]
