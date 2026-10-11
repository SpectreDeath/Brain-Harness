"""Declarative configuration parsing and runtime state reconciliation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from harness.kernel.reconciler import HarnessConfigTree, ReconciliationResult
    from harness.kernel.runtime.coordinator import HarnessRuntime

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def parse_runtime_config(config: Any) -> HarnessConfigTree:
    """Parse a runtime configuration from file path, dict, list, or HarnessConfigTree."""
    from harness.kernel.reconciler import HarnessConfigTree, PluginConfigEntry

    if isinstance(config, (str, Path)):
        p = Path(config)
        if p.exists():
            text = p.read_text(encoding="utf-8")
            try:
                import yaml

                data = yaml.safe_load(text)
            except ImportError:
                data = json.loads(text)
            return HarnessConfigTree.model_validate(data)
        else:
            try:
                data = json.loads(str(config))
                return HarnessConfigTree.model_validate(data)
            except Exception:
                raise ValueError(f"Config path does not exist and is not valid JSON: {config}")
    elif isinstance(config, HarnessConfigTree):
        return config
    elif isinstance(config, dict):
        return HarnessConfigTree.model_validate(config)
    elif isinstance(config, list):
        return HarnessConfigTree(
            plugins=[PluginConfigEntry.model_validate(item) for item in config]
        )
    else:
        raise TypeError(f"Unsupported config type: {type(config)}")


async def reconcile_runtime(runtime: HarnessRuntime, config: Any) -> ReconciliationResult:
    """Reconcile runtime state against a declarative configuration tree (Section 5.2)."""
    from harness.kernel.reconciler import ConfigurationReconciler

    config_tree = parse_runtime_config(config)

    if not hasattr(runtime, "_reconciler") or runtime._reconciler is None:
        runtime._reconciler = ConfigurationReconciler(runtime)

    return await runtime._reconciler.reconcile(config_tree)


__all__ = [
    "parse_runtime_config",
    "reconcile_runtime",
]
