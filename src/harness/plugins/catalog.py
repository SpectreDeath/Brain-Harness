"""Plugin catalog — authoritative indexed multi-domain plugin repository.

Provides high-leverage in-memory indexing, domain taxonomy aggregation,
O(1) lookups, multi-criteria filtering, search, and zero-cost cached
manifest / guide generation across flat and nested plugin directories.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from harness.plugins.manifest import IsolationMode, PluginManifest

logger = structlog.get_logger()


@dataclass(slots=True)
class PluginCatalogEntry:
    """Canonical indexed representation of an installed or discovered plugin."""

    name: str
    domain: str
    path: Path
    has_manifest: bool
    version: str = "0.0.0"
    description: str = ""
    isolation: str = "subprocess"
    trusted: bool = False
    language: str = "python"
    entrypoint: str = ""
    entrypoints: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    _cached_manifest: PluginManifest | None = None
    _cached_guide: str | None = None

    @property
    def resolved_path_str(self) -> str:
        return str(self.path.resolve())

    def get_manifest(self) -> PluginManifest | None:
        """Return the parsed manifest for this entry, caching the result."""
        if self._cached_manifest is not None:
            return self._cached_manifest

        manifest_file = self.path / "plugin.json"
        if manifest_file.exists():
            try:
                self._cached_manifest = PluginManifest.from_file(manifest_file)
                return self._cached_manifest
            except Exception as e:
                logger.warning(
                    "Failed to parse plugin.json for catalog entry",
                    path=str(manifest_file),
                    error=str(e),
                )

        # Fallback to repo inspection if no direct plugin.json
        if self.path.exists() and self.path.is_dir():
            try:
                from harness.ingestion.inspector import RepoInspector

                self._cached_manifest = RepoInspector().inspect(self.path)
                return self._cached_manifest
            except Exception as e:
                logger.debug(
                    "Inspection fallback failed for catalog entry",
                    path=str(self.path),
                    error=str(e),
                )

        return None

    def get_guide(self) -> str:
        """Return formatted Quick Start Guide for this plugin."""
        if self._cached_guide is not None:
            return self._cached_guide

        manifest = self.get_manifest()
        if manifest is not None:
            guide = manifest.usage_guide.strip() if manifest.usage_guide else manifest.format_quickstart()
            self._cached_guide = guide
            return guide

        return f"# {self.name}\n\nPlugin at `{self.resolved_path_str}`"

    def to_dict(self) -> dict[str, Any]:
        """Convert entry into catalog dictionary format (backward compatible)."""
        return {
            "name": self.name,
            "domain": self.domain,
            "path": self.resolved_path_str,
            "has_manifest": self.has_manifest,
            "version": self.version,
            "description": self.description,
            "isolation": self.isolation,
            "trusted": self.trusted,
            "language": self.language,
            "entrypoint": self.entrypoint,
            "entrypoints": list(self.entrypoints),
            "provides": list(self.provides),
            "requires": list(self.requires),
            "category": self.category,
            "tags": list(self.tags),
        }


class PluginCatalog:
    """Authoritative in-memory indexed catalog of harness plugins.

    Scans configured root directories (both flat and arbitrary domain-nested layouts),
    indexes plugins by name, alias, path, and domain, and provides O(1) lookups,
    multi-criteria filtering, and keyword search.
    """

    def __init__(self, plugin_dirs: list[Path] | None = None) -> None:
        self._plugin_dirs: list[Path] = [Path(p) for p in (plugin_dirs or [Path("plugins")])]
        self._entries_by_path: dict[str, PluginCatalogEntry] = {}
        self._entries_by_name: dict[str, PluginCatalogEntry] = {}
        self._entries_by_alias: dict[str, PluginCatalogEntry] = {}
        self._entries_by_domain: dict[str, list[PluginCatalogEntry]] = {}
        self._lock = threading.RLock()
        self.refresh()

    @property
    def plugin_dirs(self) -> list[Path]:
        return list(self._plugin_dirs)

    def refresh(self) -> int:
        """Rebuild the catalog index by scanning all configured plugin directories.

        Returns:
            Total count of indexed plugin entries.
        """
        with self._lock:
            self._entries_by_path.clear()
            self._entries_by_name.clear()
            self._entries_by_alias.clear()
            self._entries_by_domain.clear()

            processed_dirs: set[Path] = set()

            for p_dir in self._plugin_dirs:
                if not p_dir.exists() or not p_dir.is_dir():
                    continue
                self._scan_directory_recursive(p_dir, p_dir, processed_dirs)

            logger.debug(
                "Plugin catalog indexing complete",
                total_plugins=len(self._entries_by_path),
                domains=list(self._entries_by_domain.keys()),
            )
            return len(self._entries_by_path)

    def _scan_directory_recursive(
        self,
        current_dir: Path,
        root_dir: Path,
        processed_dirs: set[Path],
    ) -> None:
        """Recursively discover and index plugins within a directory tree."""
        if current_dir in processed_dirs:
            return
        if (current_dir.name.startswith(".") or current_dir.name.startswith("__")) and current_dir != root_dir:
            return

        manifest_file = current_dir / "plugin.json"
        is_plugin_dir = False
        manifest: PluginManifest | None = None

        if manifest_file.exists():
            is_plugin_dir = True
            try:
                manifest = PluginManifest.from_file(manifest_file)
            except Exception as e:
                logger.warning("Failed to load plugin manifest", path=str(manifest_file), error=str(e))
        elif current_dir != root_dir:
            nested_manifests = [p for p in current_dir.glob("**/plugin.json") if not p.name.startswith((".", "__"))]
            if not nested_manifests:
                is_plugin_dir = True

        if is_plugin_dir and current_dir != root_dir:
            processed_dirs.add(current_dir)
            entry = self._build_entry(current_dir, root_dir, manifest)
            self._index_entry(entry)
            return

        # Otherwise continue recursing into child directories
        try:
            for child in sorted(current_dir.iterdir()):
                if child.is_dir() and not child.name.startswith((".", "__")):
                    self._scan_directory_recursive(child, root_dir, processed_dirs)
        except (OSError, PermissionError) as e:
            logger.warning("Failed to scan directory for plugins", dir=str(current_dir), error=str(e))

    def _build_entry(
        self,
        plugin_dir: Path,
        root_dir: Path,
        manifest: PluginManifest | None,
    ) -> PluginCatalogEntry:
        """Construct a PluginCatalogEntry from a plugin directory and optional manifest."""
        rel_path = plugin_dir.relative_to(root_dir)
        # If nested within domain folders (e.g. data_engineering/data_transformer), domain is the parent name
        domain = rel_path.parent.as_posix() if rel_path.parent != Path(".") else ""

        name = manifest.name if manifest and manifest.name else plugin_dir.name
        version = manifest.version if manifest else "0.0.0"
        description = manifest.description if manifest else ""
        isolation = manifest.isolation.value if manifest else IsolationMode.SUBPROCESS.value
        trusted = manifest.trusted if manifest else False
        language = manifest.language if manifest else "python"
        entrypoint = manifest.entrypoint if manifest else ""
        entrypoints = [ep.name for ep in manifest.entrypoints] if manifest else []
        provides = list(manifest.provides) if manifest else []
        requires = list(manifest.requires) if manifest else []
        category = manifest.category if manifest else (domain or "general")
        tags = list(manifest.tags) if manifest else []

        return PluginCatalogEntry(
            name=name,
            domain=domain,
            path=plugin_dir.resolve(),
            has_manifest=manifest is not None,
            version=version,
            description=description,
            isolation=isolation,
            trusted=trusted,
            language=language,
            entrypoint=entrypoint,
            entrypoints=entrypoints,
            provides=provides,
            requires=requires,
            category=category,
            tags=tags,
            _cached_manifest=manifest,
        )

    def _index_entry(self, entry: PluginCatalogEntry) -> None:
        """Add entry into the in-memory indexes."""
        resolved_str = entry.resolved_path_str
        self._entries_by_path[resolved_str] = entry

        # Index by exact name
        self._entries_by_name[entry.name] = entry
        # Index by lowercase / stripped name
        self._entries_by_alias[entry.name.lower().strip()] = entry
        # Index by directory folder name
        self._entries_by_alias[entry.path.name.lower().strip()] = entry
        # Index without 'plugin.' prefix if applicable
        if entry.name.startswith("plugin."):
            short_name = entry.name[7:].lower().strip()
            self._entries_by_alias[short_name] = entry

        # Index by domain
        domain_key = entry.domain or "root"
        self._entries_by_domain.setdefault(domain_key, []).append(entry)

    # --- Query & Lookup Seams ---

    def get(self, name_or_path: str | Path) -> PluginCatalogEntry | None:
        """Lookup a plugin entry by exact name, alias, directory name, or filesystem path."""
        with self._lock:
            # 1. Path lookup
            if isinstance(name_or_path, Path) or (isinstance(name_or_path, str) and (Path(name_or_path).exists() or "/" in name_or_path or "\\" in name_or_path)):
                p_str = str(Path(name_or_path).resolve())
                if p_str in self._entries_by_path:
                    return self._entries_by_path[p_str]

            query_str = str(name_or_path).strip()
            # 2. Exact name lookup
            if query_str in self._entries_by_name:
                return self._entries_by_name[query_str]

            # 3. Alias / normalized lookup
            clean_query = query_str.lower()
            if clean_query in self._entries_by_alias:
                return self._entries_by_alias[clean_query]

            return None

    def find_dir(self, name: str) -> Path | None:
        """Find the root directory for a named plugin."""
        entry = self.get(name)
        return entry.path if entry else None

    def get_manifest(self, name_or_path: str | Path) -> PluginManifest | None:
        """Get the parsed manifest for a plugin by name or path."""
        entry = self.get(name_or_path)
        if entry is not None:
            return entry.get_manifest()

        # Fallback for dynamic paths not pre-indexed
        as_path = Path(name_or_path)
        if as_path.exists() and as_path.is_dir():
            from harness.ingestion.inspector import RepoInspector

            return RepoInspector().inspect(as_path.resolve())

        return None

    def get_guide(self, name: str) -> tuple[PluginManifest, str] | None:
        """Return the manifest and formatted Quick Start Guide for a plugin."""
        entry = self.get(name)
        if not entry:
            return None
        manifest = entry.get_manifest()
        if not manifest:
            return None
        return manifest, entry.get_guide()

    def list_all(self) -> list[dict[str, Any]]:
        """List all catalog entries as dictionary records (backward-compatible)."""
        with self._lock:
            return [
                entry.to_dict()
                for entry in sorted(self._entries_by_path.values(), key=lambda e: (e.domain, e.name))
            ]

    def filter(
        self,
        *,
        domain: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        isolation: str | None = None,
        trusted_only: bool = False,
        has_manifest_only: bool = False,
        provides_service: str | None = None,
        has_entrypoint: str | None = None,
    ) -> list[PluginCatalogEntry]:
        """Filter indexed plugins by multiple criteria."""
        with self._lock:
            results: list[PluginCatalogEntry] = []
            for entry in self._entries_by_path.values():
                if domain is not None and entry.domain.lower() != domain.lower():
                    continue
                if category is not None and entry.category.lower() != category.lower():
                    continue
                if tag is not None and tag.lower() not in [t.lower() for t in entry.tags]:
                    continue
                if isolation is not None and entry.isolation.lower() != isolation.lower():
                    continue
                if trusted_only and not entry.trusted:
                    continue
                if has_manifest_only and not entry.has_manifest:
                    continue
                if provides_service is not None and provides_service not in entry.provides:
                    continue
                if has_entrypoint is not None and has_entrypoint not in entry.entrypoints:
                    continue
                results.append(entry)
            return sorted(results, key=lambda e: (e.domain, e.name))

    def search(self, query: str) -> list[PluginCatalogEntry]:
        """Search catalog by matching query text against name, description, tags, and entrypoints."""
        clean_q = query.lower().strip()
        if not clean_q:
            return self.filter()

        with self._lock:
            matched: list[PluginCatalogEntry] = []
            for entry in self._entries_by_path.values():
                score = 0
                if clean_q in entry.name.lower():
                    score += 10
                if clean_q in entry.domain.lower():
                    score += 5
                if clean_q in entry.description.lower():
                    score += 4
                if any(clean_q in t.lower() for t in entry.tags):
                    score += 3
                if any(clean_q in ep.lower() for ep in entry.entrypoints):
                    score += 3
                if any(clean_q in p.lower() for p in entry.provides):
                    score += 2

                if score > 0:
                    matched.append(entry)

            return matched

    def domains(self) -> dict[str, int]:
        """Return a mapping of domain name to plugin count."""
        with self._lock:
            return {
                domain: len(entries)
                for domain, entries in sorted(self._entries_by_domain.items())
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries_by_path)

    def __repr__(self) -> str:
        return f"<PluginCatalog total={len(self)} domains={len(self._entries_by_domain)}>"
