"""Main entrypoint and plugin registration for PyRIT Red-Teaming."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.pyrit_scanner import (
    PYRIT_SCANNER_SERVICE_KEY,
    DefaultPyritScannerService,
    PyritScannerService,
)
from plugins.security_and_forensics.pyrit_red_teaming.tools import (
    redteam_fuzz_prompt,
    redteam_jailbreak_audit,
    redteam_scorecard_report,
    redteam_tool_tampering_check,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.pyrit_red_teaming")


class PyritRedTeamPlugin(HarnessPlugin):
    """Harness Plugin for PyRIT GenAI Red-Teaming (Rules 1, 3, 7, 45)."""

    name = "domain.pyrit_red_teaming"
    version = "1.0.0"
    description = "Microsoft PyRIT GenAI red-teaming scanner with lazy subprocess venv isolation"
    trusted = True

    def __init__(self, service: PyritScannerService | None = None) -> None:
        self._service = service or DefaultPyritScannerService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [PYRIT_SCANNER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(PYRIT_SCANNER_SERVICE_KEY, self._service, provider=self.name)
        logger.info("PyritScannerService registered into IoC context", plugin=self.name)

    async def on_enable(self) -> None:
        logger.info("PyritRedTeamPlugin enabled", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("PyritRedTeamPlugin disabled", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("PyritRedTeamPlugin unloaded", plugin=self.name)


# Authoritative module singleton export (Rule 45)
plugin = PyritRedTeamPlugin()

__all__ = [
    "PYRIT_SCANNER_SERVICE_KEY",
    "PyritRedTeamPlugin",
    "plugin",
    "redteam_fuzz_prompt",
    "redteam_jailbreak_audit",
    "redteam_scorecard_report",
    "redteam_tool_tampering_check",
]
