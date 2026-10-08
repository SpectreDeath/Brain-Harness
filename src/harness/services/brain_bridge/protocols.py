"""Service protocol and typed ServiceKey for Brain Bridge service."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from .models import (
    BrainAttachResult,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
)


@runtime_checkable
class BrainBridgeService(Protocol):
    """Protocol for attaching, inspecting, and querying foreign brains and repositories."""

    def attach(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> BrainAttachResult:
        """Inspect and mount an external brain, repository, or knowledge directory synchronously."""
        ...

    async def attach_async(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> BrainAttachResult:
        """Inspect and mount an external brain or repository asynchronously in background thread."""
        ...

    def query(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        """Query across mounted brains synchronously with TF-IDF semantic scoring."""
        ...

    async def query_async(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        """Query across mounted brains asynchronously."""
        ...

    def list_attached(self) -> BrainListResult:
        """Enumerate all active brain mounts and their index summaries synchronously."""
        ...

    async def list_attached_async(self) -> BrainListResult:
        """Enumerate all active brain mounts asynchronously."""
        ...

    def detach(self, brain_alias: str) -> BrainDetachResult:
        """Detach and release memory indexes for an attached mount synchronously."""
        ...

    async def detach_async(self, brain_alias: str) -> BrainDetachResult:
        """Detach an attached brain mount asynchronously."""
        ...


BRAIN_BRIDGE_KEY: ServiceKey[BrainBridgeService] = ServiceKey("service.brain_bridge")
