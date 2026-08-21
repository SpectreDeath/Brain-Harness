"""Plugin ingestion pipeline — unified GitHub and multi-source to plugin workflow.

Encapsulates fetching, inspecting, converting, and sandboxing any external
repository or archive into a live HarnessPlugin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.ingestion.converter import RepoConverter
from harness.ingestion.fetcher import RepoFetcher
from harness.ingestion.inspector import RepoInspector
from harness.ingestion.resolvers import (
    ResolvedSource,
    SourceResolver,
    UniversalSourceRegistry,
)
from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.plugins.sandboxed import SandboxedPlugin

logger = structlog.get_logger()


class PluginIngestionPipeline:
    """Unified ingestion pipeline from repository URL/path to live HarnessPlugin.

    Replaces multi-step manual choreography across fetcher, inspector, and
    converter with a single high-leverage interface.
    """

    def __init__(
        self,
        fetcher: RepoFetcher | None = None,
        inspector: RepoInspector | None = None,
        converter: RepoConverter | None = None,
        *,
        plugin_dir: Path | None = None,
        github_token: str | None = None,
        event_bus: Any | None = None,
        registry: UniversalSourceRegistry | None = None,
    ) -> None:
        self.plugin_dir = plugin_dir or Path("plugins")
        self._event_bus = event_bus
        self.fetcher = fetcher or RepoFetcher(
            plugin_dir=self.plugin_dir,
            github_token=github_token,
            event_bus=event_bus,
        )
        self.inspector = inspector or RepoInspector()
        self.converter = converter or RepoConverter()
        self.registry = registry or UniversalSourceRegistry.create_default(github_token=github_token)

    @property
    def event_bus(self) -> Any | None:
        """Attached event bus, if any."""
        return self._event_bus

    def attach_event_bus(self, event_bus: Any) -> None:
        """Attach an event bus for ingestion telemetry."""
        self._event_bus = event_bus
        if hasattr(self.fetcher, "attach_event_bus"):
            self.fetcher.attach_event_bus(event_bus)

    async def _emit_event(self, event_type: Any, url: str, **extra: Any) -> None:
        """Emit an ingestion event onto the attached event bus."""
        if self._event_bus is not None:
            from harness.events.types import ingestion_event

            evt = ingestion_event(event_type, url, **extra)
            await self._event_bus.emit(evt)

    async def ingest(
        self,
        source: str | Path,
        *,
        ref: str = "main",
        force: bool = False,
        isolation: IsolationMode | None = None,
        force_isolation: IsolationMode | None = None,
    ) -> SandboxedPlugin:
        """Download, inspect, and convert a repository into a ready-to-run plugin.

        Args:
            source: GitHub URL, local file path to zip, PyPI package, OpenAPI spec, or existing directory.
            ref: Git ref (branch/tag) when fetching from GitHub.
            force: Re-fetch if already cached.
            isolation: Optional override for isolation mode.
            force_isolation: Alias for isolation for backward compatibility.

        Returns:
            A configured SandboxedPlugin ready for lifecycle registration.
        """
        from harness.events.types import EventType

        source_str = str(source)
        logger.info("Ingesting plugin source", source=source_str)

        # 1. Resolve source via UniversalSourceRegistry
        resolved: ResolvedSource = await self.registry.resolve(
            source_str,
            target_base_dir=self.plugin_dir,
            ref=ref,
            force=force,
            github_token=self.fetcher.github_token,
            event_bus=self.event_bus,
        )
        repo_dir = resolved.directory

        # 2. Inspect codebase structure and synthesize manifest
        manifest = resolved.manifest_override or self.inspector.inspect(repo_dir)
        await self._emit_event(
            EventType.REPO_INSPECTED,
            source_str,
            plugin=manifest.name,
            version=manifest.version,
            isolation=manifest.isolation.value,
            entrypoints=len(manifest.entrypoints),
        )

        # 3. Apply isolation override if specified
        eff_isolation = isolation if isolation is not None else force_isolation
        if eff_isolation is not None:
            manifest.isolation = eff_isolation

        logger.info(
            "Synthesized plugin manifest from source",
            plugin=manifest.name,
            version=manifest.version,
            isolation=manifest.isolation.value,
            entrypoints=len(manifest.entrypoints),
        )

        # 4. Convert to sandboxed plugin
        plugin = self.converter.convert(repo_dir, manifest, force_isolation=eff_isolation)
        await self._emit_event(
            EventType.REPO_CONVERTED,
            source_str,
            plugin=plugin.name,
            version=getattr(plugin, "version", "0.1.0"),
            isolation=manifest.isolation.value,
        )
        return plugin

    def inspect(self, source: str | Path) -> PluginManifest:
        """Inspect a local or cached plugin directory without full conversion.

        Args:
            source: Directory path or cached plugin directory name.

        Returns:
            Parsed or synthesized PluginManifest.
        """
        path = Path(source).resolve()
        if not path.exists():
            path = self.fetcher.plugin_dir / source

        if not path.exists():
            raise FileNotFoundError(f"Plugin directory not found: {source}")

        return self.inspector.inspect(path)

    def list_cached(self) -> list[dict[str, Any]]:
        """List all cached plugins."""
        return self.fetcher.list_cached()

    def remove_cached(self, name: str) -> bool:
        """Remove a cached plugin from disk."""
        return self.fetcher.remove_cached(name)

    async def trial_run(
        self,
        plugin: Any,
        validator_fn: Any,
        *,
        parent_context: Any | None = None,
    ) -> dict[str, Any]:
        """Execute a sandboxed trial run for a synthesized or ingested plugin.

        Runs the plugin in a transactional context. If validator_fn succeeds, returns
        success metrics. If validator_fn fails or raises an exception, the entire trial
        state is cleanly rolled back with zero residual context pollution (Theorem 61).
        """
        from harness.kernel.context import ServiceContext

        base_ctx = parent_context or ServiceContext()
        async with base_ctx.transaction() as trial_ctx:
            scoped = trial_ctx.for_plugin(plugin.name)
            await plugin.on_load(scoped)
            await plugin.on_enable()

            import inspect

            if inspect.iscoroutinefunction(validator_fn):
                validation_result = await validator_fn(scoped)
            else:
                validation_result = validator_fn(scoped)
                if inspect.isawaitable(validation_result):
                    validation_result = await validation_result

            await plugin.on_disable()
            await plugin.on_unload()

        return {"status": "ok", "plugin": plugin.name, "result": validation_result}


# Backward compatibility alias
PluginIngestionEngine = PluginIngestionPipeline
