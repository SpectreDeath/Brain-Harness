"""Brain Bridge and Repository Attachment service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class BrainAttachResult(BaseModel):
    """Result of attaching an external brain or repository."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    alias: str | None = Field(default=None, description="Assigned mount alias")
    path: str | None = Field(default=None, description="Local directory path")
    original_source: str | None = Field(default=None, description="Original source or repository URL")
    detected_format: str | None = Field(default=None, description="Detected brain or repository format")
    mode: str = Field(default="lens", description="Attachment mode (lens, full, snapshot)")
    summary: dict[str, Any] = Field(default_factory=dict, description="Index statistics and detected metadata")
    error: str | None = Field(default=None, description="Error explanation if attachment failed")


class BrainQueryResult(BaseModel):
    """Result of querying across attached brains and repositories."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    query: str = Field(default="", description="Queried search terms")
    searched_brains: list[str] = Field(default_factory=list, description="Aliases of searched brain mounts")
    results_count: int = Field(default=0, description="Total matching results returned")
    results: list[dict[str, Any]] = Field(default_factory=list, description="Scored document and trajectory chunks")
    note: str | None = Field(default=None, description="Informational notice")
    error: str | None = Field(default=None, description="Error explanation if query failed")


class BrainListResult(BaseModel):
    """Result of enumerating all attached foreign brains and repositories."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    attached_count: int = Field(default=0, description="Total active brain mounts")
    brains: list[dict[str, Any]] = Field(default_factory=list, description="List of brain mount metadata objects")


class BrainDetachResult(BaseModel):
    """Result of detaching and unloading a foreign brain."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    detached_alias: str | None = Field(default=None, description="Detached mount alias")
    path: str | None = Field(default=None, description="Unmounted directory path")
    error: str | None = Field(default=None, description="Error explanation if detachment failed")


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
        """Inspect and mount an external brain, repository, or remote Git URL asynchronously."""
        ...

    def query(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        """Query across one or all mounted external brains/repos synchronously."""
        ...

    async def query_async(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        """Query across one or all mounted external brains/repos asynchronously."""
        ...

    def list_attached(self) -> BrainListResult:
        """List all currently mounted external brains and repositories."""
        ...

    def detach(self, brain_alias: str) -> BrainDetachResult:
        """Unmount a foreign brain or repository and release memory indexes."""
        ...


BRAIN_BRIDGE_KEY: ServiceKey[BrainBridgeService] = ServiceKey("service.brain_bridge")
