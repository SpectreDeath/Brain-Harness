"""Federated Brain Bridge & Repository Attachment Plugin for Brain Harness.

Thin IoC micro-kernel adapter delegating to DefaultBrainBridgeService.
Adheres to:
- Rule 1: Everything is a plugin.
- Rule 2: Typed service keys (BRAIN_BRIDGE_KEY).
- Rule 45: Plugin module singleton export (plugin = BrainBridgePlugin()).
- Rule 49: Skill-to-IoC micro-kernel seam elevation.
- Rule 58: Single-seam resolver compatibility.
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.brain_bridge import (
    BRAIN_BRIDGE_KEY,
    BrainAttachResult,
    BrainBridgeService,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
    DEFAULT_CODE_EXTS,
    DefaultBrainBridgeService,
    SPECIAL_FILENAMES,
    clone_remote_repo,
    compute_tf_idf_vector,
    detect_brain_format,
    index_text_files,
    is_git_url,
    parse_git_commits,
    parse_transcripts,
    tokenize_text,
)

logger = structlog.get_logger(__name__)

# Backward-compatible private helper aliases for existing callers/tests
_tokenize = tokenize_text
_compute_vector = compute_tf_idf_vector
_is_git_url = is_git_url
_detect_brain_format = detect_brain_format
_index_text_files = index_text_files
_parse_transcripts = parse_transcripts
_parse_git_commits = parse_git_commits
_clone_remote_repo = clone_remote_repo

# Global service instance for direct tool functions
_GLOBAL_SERVICE = DefaultBrainBridgeService()


# Backward-compatible BrainBridgeEngine alias
class BrainBridgeEngine(DefaultBrainBridgeService):
    """Backward-compatible alias for DefaultBrainBridgeService."""

    def attach_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.attach(*args, **kwargs).model_dump()


def brain_attach(
    folder_path: str,
    alias: str | None = None,
    read_transcripts: bool = True,
    read_commits: bool = True,
    max_commits: int = 100,
    attach_mode: str = "lens",
) -> dict[str, Any]:
    """Inspect and mount an external brain, repository, IDE state, or knowledge directory."""
    res = _GLOBAL_SERVICE.attach(
        folder_path=folder_path,
        alias=alias,
        read_transcripts=read_transcripts,
        read_commits=read_commits,
        max_commits=max_commits,
        attach_mode=attach_mode,
    )
    return res.model_dump()


def brain_query(
    query: str,
    brain_alias: str | None = None,
    include_trajectories: bool = True,
    top_k: int = 5,
) -> dict[str, Any]:
    """Query across one or all mounted external brains/repos for knowledge, code, solutions, or trajectories."""
    res = _GLOBAL_SERVICE.query(
        query=query,
        brain_alias=brain_alias,
        include_trajectories=include_trajectories,
        top_k=top_k,
    )
    return res.model_dump()


def brain_list_attached() -> dict[str, Any]:
    """List all currently mounted external brains/repositories, their detected formats, and index statistics."""
    res = _GLOBAL_SERVICE.list_attached()
    return res.model_dump()


def brain_detach(brain_alias: str) -> dict[str, Any]:
    """Unmount a foreign brain or repository and release its memory indexes."""
    res = _GLOBAL_SERVICE.detach(brain_alias=brain_alias)
    return res.model_dump()


class BrainBridgePlugin(HarnessPlugin, BrainBridgeService):
    """Harness Plugin providing federated external brain and Git repository attachment services."""

    name = "plugin.brain_bridge"
    version = "1.0.0"
    description = "Federated brain bridge, multi-repository attachment, and cross-codebase knowledge indexer"
    trusted = True

    def __init__(self, service: BrainBridgeService | None = None) -> None:
        self._service = service or _GLOBAL_SERVICE
        self._ctx: ServiceContext | None = None

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [BRAIN_BRIDGE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        self._ctx = ctx
        ctx.provide(BRAIN_BRIDGE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)
        if self._ctx is not None:
            self._ctx.revoke(BRAIN_BRIDGE_KEY)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)
        self._ctx = None

    # -------------------------------------------------------------------------
    # BrainBridgeService Protocol Delegation
    # -------------------------------------------------------------------------

    def attach(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> BrainAttachResult:
        return self._service.attach(
            folder_path=folder_path,
            alias=alias,
            read_transcripts=read_transcripts,
            read_commits=read_commits,
            max_commits=max_commits,
            attach_mode=attach_mode,
        )

    async def attach_async(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> BrainAttachResult:
        return await self._service.attach_async(
            folder_path=folder_path,
            alias=alias,
            read_transcripts=read_transcripts,
            read_commits=read_commits,
            max_commits=max_commits,
            attach_mode=attach_mode,
        )

    def query(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        return self._service.query(
            query=query,
            brain_alias=brain_alias,
            include_trajectories=include_trajectories,
            top_k=top_k,
        )

    async def query_async(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        return await self._service.query_async(
            query=query,
            brain_alias=brain_alias,
            include_trajectories=include_trajectories,
            top_k=top_k,
        )

    def list_attached(self) -> BrainListResult:
        return self._service.list_attached()

    async def list_attached_async(self) -> BrainListResult:
        return await self._service.list_attached_async()

    def detach(self, brain_alias: str) -> BrainDetachResult:
        return self._service.detach(brain_alias=brain_alias)

    async def detach_async(self, brain_alias: str) -> BrainDetachResult:
        return await self._service.detach_async(brain_alias=brain_alias)


# Module singleton export (Rule 45)
plugin = BrainBridgePlugin()
