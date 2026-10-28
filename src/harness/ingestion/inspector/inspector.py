"""Repo inspector coordinator — analyzes downloaded repositories and synthesizes manifests."""

from __future__ import annotations

from pathlib import Path

import structlog

from harness.ingestion.inspector.ast_extractor import (
    extract_python_entrypoints,
    guess_entrypoint,
    read_requirements,
    try_python_ast,
)
from harness.ingestion.inspector.exceptions import InspectionError
from harness.ingestion.inspector.js_ts_extractor import (
    extract_js_ts_entrypoints,
    try_js_ts_inspection,
)
from harness.ingestion.inspector.manifest_strategies import (
    convert_mcp_json,
    derive_plugin_name,
    try_mcp_json,
    try_package_json,
    try_plugin_json,
    try_pyproject,
)
from harness.ingestion.inspector.skills_bundle import (
    parse_skill_frontmatter,
    try_skills_bundle,
)
from harness.plugins.manifest import EntrypointSpec, PluginManifest

logger = structlog.get_logger()


class RepoInspector:
    """Inspects repository directories and synthesizes PluginManifests."""

    def inspect(self, repo_dir: Path) -> PluginManifest:
        """Inspect a repository directory and return a synthesized PluginManifest."""
        if not repo_dir.exists() or not repo_dir.is_dir():
            raise InspectionError(str(repo_dir), "Directory does not exist")

        manifest: PluginManifest | None = None

        # Strategy 1: Explicit Harness plugin.json
        manifest = try_plugin_json(repo_dir)
        if manifest:
            logger.info("Found plugin.json manifest", plugin=manifest.name)

        # Strategy 2: Claude plugin / Agent skills bundle
        if manifest is None:
            manifest = try_skills_bundle(repo_dir)
            if manifest:
                logger.info("Synthesized manifest from skills bundle", plugin=manifest.name, skills=len(manifest.entrypoints))

        # Strategy 3: MCP / tool.json
        if manifest is None:
            manifest = try_mcp_json(repo_dir)
            if manifest:
                logger.info("Found mcp.json manifest", plugin=manifest.name)

        # Strategy 4: pyproject.toml
        if manifest is None:
            manifest = try_pyproject(repo_dir, extract_python_entrypoints, guess_entrypoint)
            if manifest:
                logger.info("Synthesized manifest from pyproject.toml", plugin=manifest.name)

        # Strategy 5: JavaScript / TypeScript deep AST inspection & package.json
        if manifest is None:
            manifest = try_js_ts_inspection(repo_dir) or try_package_json(repo_dir)
            if manifest:
                logger.info("Synthesized manifest from JS/TS inspection", plugin=manifest.name, entrypoints=len(manifest.entrypoints))

        # Strategy 6: requirements.txt + AST extraction
        if manifest is None:
            manifest = try_python_ast(repo_dir)
            if manifest:
                logger.info("Synthesized manifest via AST extraction", plugin=manifest.name)

        # Fallback: minimal manifest
        if manifest is None:
            logger.warning("No metadata found, creating minimal manifest", directory=str(repo_dir))
            manifest = PluginManifest.minimal(
                name=derive_plugin_name(repo_dir),
                entrypoint=guess_entrypoint(repo_dir),
            )

        # Post-Inspection Standardization: Quick Start Guide & Metadata
        quickstart_path = repo_dir / "QUICKSTART.md"
        if quickstart_path.exists() and not manifest.usage_guide:
            try:
                manifest.usage_guide = quickstart_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        if not manifest.usage_guide:
            manifest.usage_guide = manifest.format_quickstart()

        if not quickstart_path.exists():
            try:
                quickstart_path.write_text(manifest.usage_guide, encoding="utf-8")
            except Exception as e:
                logger.warning("Could not write QUICKSTART.md", error=str(e))

        return manifest

    # Forwarding helper methods for backward compatibility
    def _try_plugin_json(self, repo_dir: Path) -> PluginManifest | None:
        return try_plugin_json(repo_dir)

    def _try_skills_bundle(self, repo_dir: Path) -> PluginManifest | None:
        return try_skills_bundle(repo_dir)

    def _parse_skill_frontmatter(self, content: str) -> tuple[str, str]:
        return parse_skill_frontmatter(content)

    def _try_mcp_json(self, repo_dir: Path) -> PluginManifest | None:
        return try_mcp_json(repo_dir)

    def _convert_mcp_json(self, path: Path, repo_dir: Path) -> PluginManifest:
        return convert_mcp_json(path, repo_dir)

    def _try_pyproject(self, repo_dir: Path) -> PluginManifest | None:
        return try_pyproject(repo_dir, extract_python_entrypoints, guess_entrypoint)

    def _try_package_json(self, repo_dir: Path) -> PluginManifest | None:
        return try_package_json(repo_dir)

    def _try_python_ast(self, repo_dir: Path) -> PluginManifest | None:
        return try_python_ast(repo_dir)

    def _extract_python_entrypoints(self, repo_dir: Path) -> list[EntrypointSpec]:
        return extract_python_entrypoints(repo_dir)

    def _read_requirements(self, repo_dir: Path) -> list[str]:
        return read_requirements(repo_dir)

    def _guess_entrypoint(self, repo_dir: Path) -> str:
        return guess_entrypoint(repo_dir)
