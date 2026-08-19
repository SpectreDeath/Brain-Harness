"""Plugin loader — discovers and loads plugins from multiple sources.

Sources:
    1. Local directories (scan for plugin.json or HarnessPlugin subclasses)
    2. ZIP archives
    3. Python entry points (``harness.plugins`` group)
"""

from __future__ import annotations

import importlib.util
import threading
import zipfile
from pathlib import Path
from typing import Any

import structlog

from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import PluginManifest

logger = structlog.get_logger()


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded."""

    def __init__(self, source: str, reason: str) -> None:
        self.source = source
        self.reason = reason
        super().__init__(f"Failed to load plugin from {source!r}: {reason}")


class PluginLoader:
    """Discovers and loads HarnessPlugin instances from various sources."""

    def __init__(self, plugin_dirs: list[Path] | None = None) -> None:
        """Initialize the loader.

        Args:
            plugin_dirs: Directories to scan for plugins. Defaults to
                ``["plugins"]`` relative to the current working directory.
        """
        self._plugin_dirs = plugin_dirs or [Path("plugins")]
        self._loaded_modules: dict[str, Any] = {}

    def load_from_directory(self, directory: Path) -> list[HarnessPlugin]:
        """Scan a directory for plugins.

        Looks for:
        1. Subdirectories containing ``plugin.json`` — manifest-based plugins
        2. Python files containing ``HarnessPlugin`` subclasses

        Args:
            directory: The directory to scan.

        Returns:
            List of instantiated plugins found.
        """
        plugins: list[HarnessPlugin] = []

        if not directory.exists():
            logger.debug("Plugin directory does not exist", directory=str(directory))
            return plugins

        # Check if directory itself is a plugin
        direct_manifest = directory / "plugin.json"
        if direct_manifest.exists():
            try:
                plugin = self._load_manifest_plugin(directory, direct_manifest)
                if plugin:
                    plugins.append(plugin)
                    return plugins
            except Exception as e:
                logger.warning("Failed to load direct manifest plugin", error=str(e))

        for child in directory.iterdir():
            if child.is_dir():
                # Check for manifest-based plugin
                manifest_path = child / "plugin.json"
                if manifest_path.exists():
                    try:
                        plugin = self._load_manifest_plugin(child, manifest_path)
                        if plugin:
                            plugins.append(plugin)
                    except Exception as e:
                        logger.warning(
                            "Failed to load manifest plugin",
                            directory=str(child),
                            error=str(e),
                        )
                else:
                    # Scan for Python modules with HarnessPlugin subclasses
                    for py_file in child.glob("*.py"):
                        try:
                            found = self._load_python_module(py_file)
                            plugins.extend(found)
                        except Exception as e:
                            logger.warning(
                                "Failed to load module",
                                file=str(py_file),
                                error=str(e),
                            )

            elif child.suffix == ".py":
                try:
                    found = self._load_python_module(child)
                    plugins.extend(found)
                except Exception as e:
                    logger.warning(
                        "Failed to load module",
                        file=str(child),
                        error=str(e),
                    )

        if plugins:
            logger.info(
                "Plugins loaded from directory",
                directory=str(directory),
                count=len(plugins),
            )

        return plugins

    def load_from_zip(self, zip_path: Path, extract_to: Path) -> list[HarnessPlugin]:
        """Extract a ZIP archive and load plugins from it.

        Args:
            zip_path: Path to the ZIP file.
            extract_to: Directory to extract into.

        Returns:
            List of plugins found in the archive.
        """
        if not zip_path.exists():
            raise PluginLoadError(str(zip_path), "ZIP file does not exist")

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_to)
        except zipfile.BadZipFile as e:
            raise PluginLoadError(str(zip_path), f"Invalid ZIP: {e}") from e

        logger.info("Extracted ZIP", zip_path=str(zip_path), target=str(extract_to))
        return self.load_from_directory(extract_to)

    def load_from_entry_points(self, group: str = "harness.plugins") -> list[HarnessPlugin]:
        """Discover plugins via Python entry points.

        Args:
            group: Entry point group to scan.

        Returns:
            List of plugins found via entry points.
        """
        plugins: list[HarnessPlugin] = []
        discovered = _entry_points_with_timeout(group)

        for ep in discovered:
            try:
                plugin_class = ep.load()
                if isinstance(plugin_class, type) and issubclass(
                    plugin_class, HarnessPlugin
                ):
                    instance = plugin_class()
                    plugins.append(instance)
                    logger.info(
                        "Loaded entry point plugin",
                        name=ep.name,
                        plugin=instance.name,
                    )
            except Exception as e:
                logger.warning(
                    "Failed to load entry point plugin",
                    ep_name=getattr(ep, "name", "unknown"),
                    error=str(e),
                )

        return plugins

    def discover_all(self) -> list[HarnessPlugin]:
        """Discover plugins from all configured sources.

        Returns:
            Combined list of all discovered plugins.
        """
        plugins: list[HarnessPlugin] = []

        # Scan configured directories
        for directory in self._plugin_dirs:
            plugins.extend(self.load_from_directory(directory))

        # Scan entry points
        plugins.extend(self.load_from_entry_points())

        logger.info("Plugin discovery complete", total=len(plugins))
        return plugins

    # --- Catalog & Metadata Seam ---

    def list_catalog(self) -> list[dict[str, Any]]:
        """List all discovered, installed, and cached plugins in catalog format.

        Returns:
            List of dict summaries for all available plugins.
        """
        catalog: list[dict[str, Any]] = []
        seen_paths: set[str] = set()

        for p_dir in self._plugin_dirs:
            if not p_dir.exists() or not p_dir.is_dir():
                continue

            for item in sorted(p_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    resolved_path = str(item.resolve())
                    if resolved_path in seen_paths:
                        continue
                    seen_paths.add(resolved_path)

                    manifest_path = item / "plugin.json"
                    has_manifest = manifest_path.exists()
                    manifest = None
                    if has_manifest:
                        try:
                            manifest = PluginManifest.from_file(manifest_path)
                        except Exception:
                            pass

                    catalog.append({
                        "name": manifest.name if manifest else item.name,
                        "path": resolved_path,
                        "has_manifest": has_manifest,
                        "version": manifest.version if manifest else "0.0.0",
                        "description": manifest.description if manifest else "",
                        "isolation": manifest.isolation.value if manifest else "unknown",
                    })

        return catalog

    def find_plugin_dir(self, name: str) -> Path | None:
        """Find the root directory for a named plugin."""
        clean_name = name.lower().strip()

        for p_dir in self._plugin_dirs:
            if not p_dir.exists():
                continue

            # Exact folder match
            direct = p_dir / name
            if direct.exists() and direct.is_dir():
                return direct.resolve()

            # Iterate children to check manifest name or folder name match
            for item in p_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    if item.name.lower() == clean_name:
                        return item.resolve()
                    manifest_path = item / "plugin.json"
                    if manifest_path.exists():
                        try:
                            m = PluginManifest.from_file(manifest_path)
                            if m.name.lower() == clean_name:
                                return item.resolve()
                        except Exception:
                            pass

        return None

    def get_manifest(self, name: str) -> PluginManifest | None:
        """Inspect and return the manifest for a plugin by name or path."""
        # 1. Direct path check
        as_path = Path(name)
        if as_path.exists() and as_path.is_dir():
            from harness.ingestion.inspector import RepoInspector
            return RepoInspector().inspect(as_path.resolve())

        # 2. Search configured catalog directories
        target_dir = self.find_plugin_dir(name)
        if target_dir and target_dir.exists():
            from harness.ingestion.inspector import RepoInspector
            return RepoInspector().inspect(target_dir)

        return None

    def get_guide(self, name: str) -> tuple[PluginManifest, str] | None:
        """Return the manifest and formatted Quick Start Guide for a plugin."""
        manifest = self.get_manifest(name)
        if not manifest:
            return None
        guide = manifest.usage_guide or manifest.format_quickstart()
        return manifest, guide

    # --- Private helpers ---

    def _load_manifest_plugin(
        self, directory: Path, manifest_path: Path
    ) -> HarnessPlugin | None:
        """Load a plugin from a directory with a plugin.json manifest."""
        manifest = PluginManifest.from_file(manifest_path)

        # Enforce sandbox isolation policy: only load in-process if trusted and isolation is in_process
        if (
            manifest.trusted
            and str(manifest.isolation.value).lower() == "in_process"
            and manifest.entrypoint
            and manifest.language == "python"
        ):
            entrypoint_path = directory / manifest.entrypoint
            if entrypoint_path.exists():
                found = self._load_python_module(entrypoint_path)
                if found:
                    return found[0]

        # Use SandboxedPlugin wrapper for all subprocess/venv or untrusted plugins
        return ManifestPlugin(manifest, directory)

    def _load_python_module(self, py_file: Path) -> list[HarnessPlugin]:
        """Import a Python file and find HarnessPlugin subclasses."""
        plugins: list[HarnessPlugin] = []

        module_name = f"harness_plugin_{py_file.stem}"
        if module_name in self._loaded_modules:
            return []

        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec is None or spec.loader is None:
            return []

        module = importlib.util.module_from_spec(spec)
        self._loaded_modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.warning("Module execution failed", file=str(py_file), error=str(e))
            return []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, HarnessPlugin)
                and attr is not HarnessPlugin
            ):
                try:
                    instance = attr()
                    plugins.append(instance)
                    logger.debug(
                        "Found HarnessPlugin",
                        file=str(py_file),
                        plugin=instance.name,
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to instantiate plugin",
                        class_name=attr_name,
                        error=str(e),
                    )

        return plugins


from harness.plugins.sandboxed import SandboxedPlugin

# Backward compatibility alias
ManifestPlugin = SandboxedPlugin


# --- Utility ---


def _entry_points_with_timeout(group: str, timeout: float = 5.0) -> list[Any]:
    """Run entry_points() in a daemon thread with a timeout.

    Borrowed from Em-Cubed's plugin_discovery.py — importlib.metadata can
    be very slow on Windows when scanning many distributions.
    """
    result: list[Any] = []
    exc: list[Exception] = []

    def target() -> None:
        try:
            import importlib.metadata
            eps = importlib.metadata.entry_points(group=group)
            result.extend(eps)
        except Exception as e:
            exc.append(e)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        logger.debug("entry_points discovery timed out", timeout=timeout)
        return []
    if exc:
        logger.warning("entry_points discovery failed", error=str(exc[0]))
        return []
    return result
