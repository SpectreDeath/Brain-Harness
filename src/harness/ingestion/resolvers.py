"""Universal Ingestion Source Resolvers — pluggable source resolution seam.

Encapsulates protocol matching, fetching, and directory resolution across GitHub,
PyPI packages, OpenAPI/Swagger specifications, and local plugin directories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from harness.plugins.manifest import PluginManifest

logger = structlog.get_logger()


@dataclass
class ResolvedSource:
    """Canonical outcome of resolving an external or local plugin source."""

    source_str: str
    scheme: str
    directory: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    manifest_override: PluginManifest | None = None

    @property
    def exists(self) -> bool:
        return self.directory.exists()


class SourceResolver(ABC):
    """Abstract interface for resolving plugin sources into local directories."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the resolver."""

    @abstractmethod
    def matches(self, source: str | Path) -> bool:
        """Return True if this resolver can handle the specified source."""

    @abstractmethod
    async def resolve(
        self,
        source: str | Path,
        *,
        target_base_dir: Path,
        ref: str = "main",
        force: bool = False,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> ResolvedSource:
        """Fetch, convert, or resolve the source to a local directory."""


class PyPISourceResolver(SourceResolver):
    """Resolves PyPI package dependencies (e.g. 'pypi:requests', 'pypi:scikit-learn')."""

    @property
    def name(self) -> str:
        return "pypi"

    def matches(self, source: str | Path) -> bool:
        return str(source).strip().startswith("pypi:")

    async def resolve(
        self,
        source: str | Path,
        *,
        target_base_dir: Path,
        ref: str = "main",
        force: bool = False,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> ResolvedSource:
        from harness.ingestion.pypi_converter import PyPIConverter

        source_str = str(source).strip()
        pypi_conv = PyPIConverter(output_base_dir=target_base_dir)
        repo_dir = await pypi_conv.convert(source_str)
        return ResolvedSource(
            source_str=source_str,
            scheme="pypi",
            directory=repo_dir,
            metadata={"package": source_str.split(":", 1)[1]},
        )


class OpenAPISourceResolver(SourceResolver):
    """Resolves OpenAPI and Swagger schema URLs or files (e.g. 'openapi:https://api.example.com/spec.json')."""

    @property
    def name(self) -> str:
        return "openapi"

    def matches(self, source: str | Path) -> bool:
        s = str(source).strip()
        return s.startswith(("openapi:", "swagger:"))

    async def resolve(
        self,
        source: str | Path,
        *,
        target_base_dir: Path,
        ref: str = "main",
        force: bool = False,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> ResolvedSource:
        from harness.ingestion.openapi_converter import OpenAPIConverter

        source_str = str(source).strip()
        raw_source = source_str.split(":", 1)[1].strip()
        spec_content = raw_source

        if raw_source.startswith(("http://", "https://")):
            import httpx

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(raw_source)
                resp.raise_for_status()
                spec_content = resp.text
        elif Path(raw_source).exists():
            spec_content = Path(raw_source).read_text(encoding="utf-8")

        openapi_conv = OpenAPIConverter(output_base_dir=target_base_dir)
        repo_dir = openapi_conv.convert(spec_content)
        return ResolvedSource(
            source_str=source_str,
            scheme="openapi",
            directory=repo_dir,
            metadata={"raw_source": raw_source},
        )


class LocalDirectorySourceResolver(SourceResolver):
    """Resolves local filesystem directories or existing cached plugin folders."""

    @property
    def name(self) -> str:
        return "local"

    def matches(self, source: str | Path) -> bool:
        s = str(source).strip()
        if s.startswith(("http://", "https://", "pypi:", "openapi:", "swagger:", "github:")):
            return False
        p = Path(s)
        return p.is_dir() or (p.exists() and not s.endswith(".zip"))

    async def resolve(
        self,
        source: str | Path,
        *,
        target_base_dir: Path,
        ref: str = "main",
        force: bool = False,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> ResolvedSource:
        path = Path(source).resolve()
        if event_bus is not None:
            from harness.events.types import EventType, ingestion_event

            evt_start = ingestion_event(EventType.REPO_FETCH_STARTED, str(source))
            evt_comp = ingestion_event(EventType.REPO_FETCH_COMPLETED, str(source))
            await event_bus.emit(evt_start)
            await event_bus.emit(evt_comp)

        return ResolvedSource(
            source_str=str(source),
            scheme="local",
            directory=path,
            metadata={"absolute_path": str(path)},
        )


class GitHubSourceResolver(SourceResolver):
    """Resolves GitHub repositories, owner/repo shorthand, and ZIP archives via RepoFetcher."""

    def __init__(self, github_token: str | None = None) -> None:
        self.github_token = github_token

    @property
    def name(self) -> str:
        return "github"

    def matches(self, source: str | Path) -> bool:
        s = str(source).strip()
        if s.startswith(("pypi:", "openapi:", "swagger:")):
            return False
        # Catch-all for GitHub URLs, owner/repo, zip files, or un-matched remote paths
        return True

    async def resolve(
        self,
        source: str | Path,
        *,
        target_base_dir: Path,
        ref: str = "main",
        force: bool = False,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> ResolvedSource:
        from harness.ingestion.fetcher import RepoFetcher

        fetcher = RepoFetcher(
            plugin_dir=target_base_dir,
            github_token=github_token or self.github_token,
            event_bus=event_bus,
        )
        repo_dir = await fetcher.fetch(str(source), ref=ref, force=force)
        return ResolvedSource(
            source_str=str(source),
            scheme="github",
            directory=repo_dir,
            metadata={"ref": ref, "force": force},
        )


class UniversalSourceRegistry:
    """Authoritative registry and dispatcher for pluggable plugin source resolvers."""

    def __init__(self) -> None:
        self._resolvers: list[tuple[int, SourceResolver]] = []

    def register(self, resolver: SourceResolver, *, priority: int = 100) -> None:
        """Register a source resolver. Lower priority integer runs earlier."""
        self._resolvers.append((priority, resolver))
        self._resolvers.sort(key=lambda item: item[0])

    def get_resolver(self, source: str | Path) -> SourceResolver:
        """Find the first matching source resolver."""
        for _, resolver in self._resolvers:
            if resolver.matches(source):
                return resolver
        raise ValueError(f"No registered SourceResolver matches source: {source}")

    async def resolve(
        self,
        source: str | Path,
        *,
        target_base_dir: Path,
        ref: str = "main",
        force: bool = False,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> ResolvedSource:
        """Find matching resolver and resolve source to local directory."""
        resolver = self.get_resolver(source)
        logger.debug(
            "Resolving plugin source via resolver",
            resolver=resolver.name,
            source=str(source),
        )
        return await resolver.resolve(
            source,
            target_base_dir=target_base_dir,
            ref=ref,
            force=force,
            github_token=github_token,
            event_bus=event_bus,
        )

    @classmethod
    def create_default(cls, github_token: str | None = None) -> UniversalSourceRegistry:
        """Instantiate default registry with built-in resolvers."""
        registry = cls()
        registry.register(PyPISourceResolver(), priority=10)
        registry.register(OpenAPISourceResolver(), priority=20)
        registry.register(LocalDirectorySourceResolver(), priority=30)
        registry.register(GitHubSourceResolver(github_token=github_token), priority=999)
        return registry
