"""Deprecated compatibility shim forwarding ``harness.kernel.runtime`` to ``harness.runtime``."""

from __future__ import annotations

import importlib
import warnings
from typing import Any

_EXPORTED_NAMES: tuple[str, ...] = (
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
)


def __getattr__(name: str) -> Any:
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    warnings.warn(
        "harness.kernel.runtime is deprecated; import from harness.runtime instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    mod = importlib.import_module("harness.runtime")
    if not hasattr(mod, name):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(mod, name)


def __dir__() -> list[str]:
    return list(_EXPORTED_NAMES)
