"""Slotted runtime configuration models and typed service keys (Rule 2, 12, 43)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.kernel.runtime.coordinator import HarnessRuntime

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

RUNTIME_SERVICE_KEY: ServiceKey[HarnessRuntime] = ServiceKey("kernel.runtime")


@dataclass(slots=True, frozen=True)
class RuntimeConfig:
    """Immutable configuration specification for Harness runtime instances (Rule 12 & Rule 43)."""

    plugin_dirs: tuple[Path, ...] = field(default_factory=lambda: (Path("plugins"),))
    db_path: Path | str = ":memory:"
    event_log_path: Path | None = None
    llm_model: str = "gpt-4o-mini"
    auto_load_user_plugins: bool = True
    lazy_external_plugins: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "RUNTIME_SERVICE_KEY",
    "RuntimeConfig",
]
