"""Omarchy Quattro Command Router & Introspection Plugin.

Provides structural inspection and query capabilities for Omarchy Quattro's 455+
modular CLI commands, metadata headers (# omarchy:key=value), and routing groups.
"""

from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

DEFAULT_OMARCHY_PATH = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")
METADATA_SCAN_LIMIT = 80
METADATA_PATTERN = re.compile(r"^#\s*omarchy:([a-zA-Z0-9_-]+)=(.*)$")


@runtime_checkable
class OmarchyCommandRouterService(Protocol):
    """Protocol for Omarchy CLI command discovery and routing inspection."""

    def list_commands(
        self,
        group: str | None = None,
        include_hidden: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        ...

    def get_command(
        self,
        command_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...

    def search_commands(
        self,
        query: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        ...

    def list_groups(self, **kwargs: Any) -> list[dict[str, Any]]:
        ...


OMARCHY_COMMAND_ROUTER_SERVICE_KEY = ServiceKey[OmarchyCommandRouterService](
    "service.omarchy_command_router"
)


class OmarchyCommandRouterServiceImpl:
    """Implementation of Omarchy Command Router inspection service with lazy caching."""

    def __init__(
        self,
        source_dir: Path | str | None = None,
        metadata_scan_limit: int = METADATA_SCAN_LIMIT,
    ) -> None:
        self._source_dir_override = Path(source_dir) if source_dir else None
        self._metadata_scan_limit = metadata_scan_limit
        self._index: dict[str, dict[str, Any]] | None = None
        self._alias_map: dict[str, str] = {}
        self._group_map: dict[str, list[str]] = {}

    @property
    def source_dir(self) -> Path:
        """Resolve Omarchy root directory via override, env var, or default path."""
        if self._source_dir_override:
            return self._source_dir_override
        env_path = os.environ.get("OMARCHY_PATH")
        if env_path:
            return Path(env_path)
        return DEFAULT_OMARCHY_PATH

    @property
    def bin_dir(self) -> Path:
        return self.source_dir / "bin"

    def _ensure_index(self) -> None:
        """Build lazy in-memory index from bin/ directory."""
        if self._index is not None:
            return

        self._index = {}
        self._alias_map = {}
        self._group_map = {}

        bin_path = self.bin_dir
        if not bin_path.exists() or not bin_path.is_dir():
            logger.warning(
                "omarchy_bin_dir_not_found",
                bin_dir=str(bin_path),
                source_dir=str(self.source_dir),
            )
            return

        for entry in bin_path.iterdir():
            if not entry.is_file():
                continue

            name = entry.name
            metadata = self._parse_file_metadata(entry)
            self._index[name] = metadata

            # Populate alias map
            for alias in metadata.get("aliases", []):
                self._alias_map[alias.lower()] = name

            # Populate group map
            grp = metadata.get("group", "ungrouped")
            self._group_map.setdefault(grp, []).append(name)

        logger.info(
            "omarchy_command_index_loaded",
            total_commands=len(self._index),
            total_groups=len(self._group_map),
        )

    def _parse_file_metadata(self, file_path: Path) -> dict[str, Any]:
        """Parse # omarchy:key=value header tags within scan limit."""
        metadata: dict[str, Any] = {
            "name": file_path.name,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "shebang": None,
            "group": "ungrouped",
            "summary": "",
            "usage": "",
            "args": "",
            "examples": "",
            "requires_sudo": False,
            "hidden": False,
            "aliases": [],
            "raw_tags": {},
        }

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line_idx, line in enumerate(f):
                    if line_idx >= self._metadata_scan_limit:
                        break

                    stripped = line.strip()
                    if line_idx == 0 and stripped.startswith("#!"):
                        metadata["shebang"] = stripped[2:].strip()
                        continue

                    match = METADATA_PATTERN.match(stripped)
                    if match:
                        key = match.group(1).strip()
                        val = match.group(2).strip()
                        metadata["raw_tags"][key] = val

                        if key == "group":
                            metadata["group"] = val
                        elif key == "summary":
                            metadata["summary"] = val
                        elif key == "usage":
                            metadata["usage"] = val
                        elif key == "args":
                            metadata["args"] = val
                        elif key == "examples":
                            metadata["examples"] = val
                        elif key == "requires_sudo":
                            metadata["requires_sudo"] = val.lower() in ("true", "1", "yes")
                        elif key == "hidden":
                            metadata["hidden"] = val.lower() in ("true", "1", "yes")
                        elif key == "aliases":
                            metadata["aliases"] = [a.strip() for a in val.split(",") if a.strip()]
        except Exception as exc:
            logger.warning("omarchy_metadata_parse_failed", file=str(file_path), error=str(exc))

        return metadata

    def list_commands(
        self,
        group: str | None = None,
        include_hidden: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """List commands filtered by functional group and hidden status."""
        self._ensure_index()
        assert self._index is not None

        results = []
        target_group = group.strip().lower() if group else None

        for cmd_name, meta in sorted(self._index.items()):
            if not include_hidden and meta.get("hidden", False):
                continue
            if target_group and meta.get("group", "").lower() != target_group:
                continue
            results.append(meta)

        return results

    def get_command(
        self,
        command_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Retrieve command metadata by primary name or alias."""
        self._ensure_index()
        assert self._index is not None

        clean_name = command_name.strip()
        # Check exact name
        if clean_name in self._index:
            return self._index[clean_name]

        # Check prefixed name (e.g., 'theme-set' -> 'omarchy-theme-set')
        prefixed = f"omarchy-{clean_name}" if not clean_name.startswith("omarchy-") else clean_name
        if prefixed in self._index:
            return self._index[prefixed]

        # Check unprefixed name (e.g., 'omarchy-theme-set' -> 'theme-set')
        unprefixed = clean_name.replace("omarchy-", "", 1) if clean_name.startswith("omarchy-") else clean_name
        if unprefixed in self._index:
            return self._index[unprefixed]

        # Check aliases
        lookup_key = clean_name.lower()
        if lookup_key in self._alias_map:
            target_name = self._alias_map[lookup_key]
            return self._index[target_name]

        return {
            "error": f"Command '{command_name}' not found in Omarchy bin repository",
            "searched": clean_name,
            "available": False,
            "bin_dir": str(self.bin_dir),
        }

    def search_commands(
        self,
        query: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search commands by keywords across name, summary, usage, and group."""
        self._ensure_index()
        assert self._index is not None

        q = query.strip().lower()
        if not q:
            return []

        matched = []
        for cmd_name, meta in self._index.items():
            name_match = q in cmd_name.lower()
            summary_match = q in meta.get("summary", "").lower()
            usage_match = q in meta.get("usage", "").lower()
            group_match = q in meta.get("group", "").lower()
            examples_match = q in meta.get("examples", "").lower()

            if name_match or summary_match or usage_match or group_match or examples_match:
                score = 0
                if name_match:
                    score += 5
                if summary_match:
                    score += 3
                if usage_match:
                    score += 2
                if group_match:
                    score += 1
                if examples_match:
                    score += 1

                item = dict(meta)
                item["_match_score"] = score
                matched.append(item)

        matched.sort(key=lambda x: (-x["_match_score"], x["name"]))
        for m in matched:
            m.pop("_match_score", None)

        return matched

    def list_groups(self, **kwargs: Any) -> list[dict[str, Any]]:
        """List all functional groups, command counts, and samples."""
        self._ensure_index()
        assert self._index is not None
        assert self._group_map is not None

        groups_summary = []
        for grp_name, cmd_names in sorted(self._group_map.items()):
            visible_cmds = [
                name for name in cmd_names
                if not self._index.get(name, {}).get("hidden", False)
            ]
            groups_summary.append({
                "group": grp_name,
                "total_commands": len(cmd_names),
                "visible_commands": len(visible_cmds),
                "hidden_commands": len(cmd_names) - len(visible_cmds),
                "sample_commands": sorted(visible_cmds[:5]),
            })

        return groups_summary


_ROUTER_INSTANCE = OmarchyCommandRouterServiceImpl()


# Top-level tool entrypoints
def omarchy_list_commands(
    group: str | None = None,
    include_hidden: bool = False,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return _ROUTER_INSTANCE.list_commands(group=group, include_hidden=include_hidden, **kwargs)


def omarchy_get_command(
    command_name: str,
    **kwargs: Any,
) -> dict[str, Any]:
    return _ROUTER_INSTANCE.get_command(command_name=command_name, **kwargs)


def omarchy_search_commands(
    query: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return _ROUTER_INSTANCE.search_commands(query=query, **kwargs)


def omarchy_list_groups(**kwargs: Any) -> list[dict[str, Any]]:
    return _ROUTER_INSTANCE.list_groups(**kwargs)


class OmarchyCommandRouterPlugin(HarnessPlugin):
    """Harness Plugin for Omarchy Quattro CLI command routing and introspection."""

    @property
    def name(self) -> str:
        return "plugin.omarchy_command_router"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Introspects and queries Omarchy Quattro's 455 modular CLI commands, "
            "routing architecture, and metadata headers."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OMARCHY_COMMAND_ROUTER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(OMARCHY_COMMAND_ROUTER_SERVICE_KEY, _ROUTER_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = OmarchyCommandRouterPlugin()
