"""Discovery strategies for explicit plugin.json, MCP tool.json, and package manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import structlog

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

logger = structlog.get_logger()


def try_plugin_json(repo_dir: Path) -> PluginManifest | None:
    """Check for an explicit plugin.json."""
    path = repo_dir / "plugin.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            # If this is a Claude plugin format with "skills" key, let skills_bundle handle it
            if "skills" in data and "entrypoints" not in data and "provides" not in data:
                return None
            return PluginManifest.from_file(path)
        except Exception as e:
            logger.warning("Invalid plugin.json", error=str(e))
    return None


def convert_mcp_json(path: Path, repo_dir: Path) -> PluginManifest:
    """Convert an MCP/tool JSON spec to a PluginManifest."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    entrypoints: list[EntrypointSpec] = []
    tools = data.get("tools", [])
    for tool in tools:
        params: list[ParameterSpec] = []
        schema = tool.get("inputSchema", {}).get("properties", {})
        required = tool.get("inputSchema", {}).get("required", [])
        for pname, pspec in schema.items():
            params.append(
                ParameterSpec(
                    name=pname,
                    type=pspec.get("type", "string"),
                    description=pspec.get("description", ""),
                    required=pname in required,
                )
            )
        entrypoints.append(
            EntrypointSpec(
                name=tool.get("name", "unknown"),
                description=tool.get("description", ""),
                parameters=params,
            )
        )

    return PluginManifest(
        name=data.get("name", repo_dir.name),
        version=data.get("version", "0.0.0"),
        description=data.get("description", ""),
        entrypoints=entrypoints,
        isolation=IsolationMode.SUBPROCESS,
        metadata={"source_format": path.name},
    )


def try_mcp_json(repo_dir: Path) -> PluginManifest | None:
    """Check for mcp.json or tool.json."""
    for filename in ("mcp.json", "tool.json"):
        path = repo_dir / filename
        if path.exists():
            try:
                return convert_mcp_json(path, repo_dir)
            except Exception as e:
                logger.warning(f"Invalid {filename}", error=str(e))
    return None


def try_pyproject(
    repo_dir: Path,
    extract_entrypoints_fn: Callable[[Path], list[EntrypointSpec]],
    guess_entrypoint_fn: Callable[[Path], str],
) -> PluginManifest | None:
    """Check for pyproject.toml and enrich with AST entrypoints."""
    path = repo_dir / "pyproject.toml"
    if path.exists():
        try:
            manifest = PluginManifest.from_pyproject(path)
            entrypoints = extract_entrypoints_fn(repo_dir)
            if entrypoints:
                manifest = manifest.model_copy(update={"entrypoints": entrypoints})
            ep = guess_entrypoint_fn(repo_dir)
            if ep:
                manifest = manifest.model_copy(update={"entrypoint": ep})
            return manifest
        except Exception as e:
            logger.warning("Invalid pyproject.toml", error=str(e))
    return None


def try_package_json(repo_dir: Path) -> PluginManifest | None:
    """Check for package.json."""
    path = repo_dir / "package.json"
    if path.exists():
        try:
            return PluginManifest.from_package_json(path)
        except Exception as e:
            logger.warning("Invalid package.json", error=str(e))
    return None
