"""Default built-in plugin discovery and suite construction for Harness Runtime."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harness.plugins.base import HarnessPlugin

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def get_default_plugins(
    db_path: Path | str | None = None,
    include_llm: bool = True,
    llm_model: str = "gpt-4o-mini",
) -> list[HarnessPlugin]:
    """Construct standard default plugins suite."""
    from harness.agent.react import ReActAgentPlugin
    from harness.agent.session import AgentSessionPlugin
    from harness.bridges.base import EcosystemBridgeCatalog
    from harness.services.llm import LLMPlugin
    from harness.services.storage import StoragePlugin
    from harness.services.tools import ToolRegistryPlugin

    target_db = db_path or (Path(".harness") / "storage.db")
    plugins: list[HarnessPlugin] = [
        StoragePlugin(db_path=target_db),
        AgentSessionPlugin(),
        ToolRegistryPlugin(),
    ]
    # Dynamically discover and attach registered ecosystem bridge plugins
    ecosystem_plugins = EcosystemBridgeCatalog.discover_available_plugins()
    plugins.extend(ecosystem_plugins)

    if include_llm:
        plugins.append(LLMPlugin(default_model=llm_model))
    plugins.append(ReActAgentPlugin())
    return plugins


__all__ = ["get_default_plugins"]
