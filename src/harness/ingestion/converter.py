"""Repo converter — wraps an inspected repository as a live HarnessPlugin.

The converter takes a PluginManifest (produced by the RepoInspector)
and a repository directory, then:
    1. Writes a ``plugin.json`` if one doesn't already exist
    2. Creates a HarnessPlugin wrapper that delegates to the repo's code
    3. Sets up the appropriate sandbox executor
    4. Returns a ready-to-register plugin instance
"""

from __future__ import annotations

from pathlib import Path

import structlog

from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.plugins.sandbox import (
    SandboxExecutorFactory,
)

logger = structlog.get_logger()


class ConversionError(Exception):
    """Raised when repo-to-plugin conversion fails."""

    def __init__(self, repo: str, reason: str) -> None:
        self.repo = repo
        self.reason = reason
        super().__init__(f"Conversion failed for {repo!r}: {reason}")


class RepoConverter:
    """Converts an inspected repository into a live HarnessPlugin."""

    def convert(
        self,
        repo_dir: Path,
        manifest: PluginManifest,
        *,
        force_isolation: IsolationMode | None = None,
    ) -> HarnessPlugin:
        """Convert a repository into a HarnessPlugin.

        Args:
            repo_dir: Path to the extracted repository.
            manifest: The manifest produced by RepoInspector.
            force_isolation: Override the manifest's isolation mode.

        Returns:
            A ready-to-register HarnessPlugin instance.

        Raises:
            ConversionError: If conversion fails.
        """
        if not repo_dir.exists():
            raise ConversionError(str(repo_dir), "Directory does not exist")

        # Write manifest if it doesn't exist
        manifest_path = repo_dir / "plugin.json"
        if not manifest_path.exists():
            manifest.to_file(manifest_path)
            logger.info(
                "Generated plugin.json",
                plugin=manifest.name,
                path=str(manifest_path),
            )

        # Determine isolation mode
        isolation = force_isolation or manifest.isolation

        # Create the appropriate sandbox executor via centralized factory
        executor = SandboxExecutorFactory.create(
            manifest,
            repo_dir,
            force_isolation=isolation,
        )

        # Build the plugin wrapper using canonical SandboxedPlugin
        plugin = SandboxedPlugin(
            manifest=manifest,
            root=repo_dir,
            executor=executor,
        )

        logger.info(
            "Repository converted to plugin",
            plugin=manifest.name,
            version=manifest.version,
            isolation=isolation.value,
            entrypoints=len(manifest.entrypoints),
        )

        return plugin


from harness.plugins.sandboxed import SandboxedPlugin

# Backward compatibility alias
ConvertedPlugin = SandboxedPlugin
