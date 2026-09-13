"""Repo-Triad Forge Plugin entrypoint for Brain Harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.repo_triad_forge import (
    REPO_TRIAD_FORGE_SERVICE_KEY,
    KiCandidateData,
    RepoInspectionData,
    RepoTriadForgeService,
    TriadBriefData,
    TriadRunData,
)

try:
    from plugins.software_engineering.repo_triad_forge.service import (
        RepoTriadForgeServiceImpl,
    )
except ImportError:
    from service import RepoTriadForgeServiceImpl  # type: ignore

logger = structlog.get_logger(__name__)


class RepoTriadForgePlugin(HarnessPlugin, RepoTriadForgeService):
    """Brain Harness Plugin providing repository triad audit, visual briefs, and vault commits."""

    name = "plugin.repo_triad_forge"
    version = "1.0.0"
    description = "Authoritative Repo-Triad Forge plugin: 5-stage repository cognitive audit, visual brief generation, Knowledge Vault commits, and verification orchestration"
    trusted = False

    def __init__(self) -> None:
        super().__init__()
        self._impl = RepoTriadForgeServiceImpl()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [REPO_TRIAD_FORGE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(REPO_TRIAD_FORGE_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # RepoTriadForgeService Protocol Delegation
    # -------------------------------------------------------------------------

    def inspect(self, repo_path: str) -> RepoInspectionData:
        return self._impl.inspect(repo_path)

    def generate_briefs(
        self, repo_path: str, output_dir: str | None = None
    ) -> list[TriadBriefData]:
        return self._impl.generate_briefs(repo_path, output_dir)

    def extract_kis(self, repo_path: str) -> list[KiCandidateData]:
        return self._impl.extract_kis(repo_path)

    def commit_kis(
        self, kis_data: list[dict[str, Any]], vault_dir: str | None = None
    ) -> list[str]:
        return self._impl.commit_kis(kis_data, vault_dir)

    def run_pipeline(
        self, repo_path: str, options: dict[str, Any] | None = None
    ) -> TriadRunData:
        return self._impl.run_pipeline(repo_path, options)


# Export module-level singleton per Rule 45
plugin = RepoTriadForgePlugin()


# Top-level entrypoint functions declared in plugin.json for AST inspection
def triad_inspect(repo_path: str, **kwargs: Any) -> dict[str, Any]:
    res = plugin.inspect(repo_path)
    return res.model_dump()


def triad_briefs(
    repo_path: str, output_dir: str | None = None, **kwargs: Any
) -> list[dict[str, Any]]:
    res = plugin.generate_briefs(repo_path, output_dir)
    return [b.model_dump() for b in res]


def triad_ki_candidates(repo_path: str, **kwargs: Any) -> list[dict[str, Any]]:
    res = plugin.extract_kis(repo_path)
    return [k.model_dump() for k in res]


def triad_run(
    repo_path: str, options: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    res = plugin.run_pipeline(repo_path, options)
    return res.model_dump()
