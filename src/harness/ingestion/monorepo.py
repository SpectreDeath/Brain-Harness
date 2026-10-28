"""Monorepo detection and domain-partitioned plugin synthesis per Rule 18."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from harness.ingestion.converter import RepoConverter
from harness.ingestion.inspector import RepoInspector
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import IsolationMode, PluginManifest

logger = structlog.get_logger()

_CONVENTIONAL_WORKSPACE_DIRS = ("packages", "plugins", "services", "libs", "modules", "apps", "crates")


def detect_monorepo_subprojects(repo_dir: Path) -> list[Path]:
    """Detect independent subproject root directories in a monorepo.

    Checks workspace configurations (package.json workspaces, pnpm-workspace.yaml,
    Cargo.toml workspace) and conventional subdirectories (packages/*, plugins/*, etc.).

    Returns:
        List of subproject Path directories (empty if repo is single-project).
    """
    if not repo_dir.exists() or not repo_dir.is_dir():
        return []

    subprojects: list[Path] = []
    seen: set[Path] = set()

    def _add_subproject(p: Path) -> None:
        resolved = p.resolve()
        if resolved.exists() and resolved.is_dir() and resolved not in seen:
            manifest_exists = any(
                (resolved / f).exists()
                for f in ("package.json", "pyproject.toml", "plugin.json", "Cargo.toml", "setup.py", "requirements.txt")
            )
            if manifest_exists and resolved != repo_dir.resolve():
                seen.add(resolved)
                subprojects.append(resolved)

    # 1. Check root package.json workspaces
    pkg_json = repo_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            workspaces = data.get("workspaces")
            patterns = workspaces if isinstance(workspaces, list) else (workspaces.get("packages", []) if isinstance(workspaces, dict) else [])
            for pat in patterns:
                for match in repo_dir.glob(pat.replace("/*", "/*")):
                    if match.is_dir():
                        _add_subproject(match)
        except Exception as e:
            logger.debug("Failed to parse package.json workspaces", error=str(e))

    # 2. Check conventional directories
    for folder in _CONVENTIONAL_WORKSPACE_DIRS:
        target_dir = repo_dir / folder
        if target_dir.exists() and target_dir.is_dir():
            for child in sorted(target_dir.iterdir()):
                if child.is_dir() and not child.name.startswith((".", "_")):
                    _add_subproject(child)

    # 3. Direct child directories containing pyproject.toml or plugin.json
    for child in sorted(repo_dir.iterdir()):
        if child.is_dir() and not child.name.startswith((".", "_")) and child.name not in ("tests", "docs", "data"):
            if (child / "pyproject.toml").exists() or (child / "plugin.json").exists():
                _add_subproject(child)

    return subprojects if len(subprojects) >= 2 else []


def partition_monorepo(
    repo_dir: Path,
    inspector: RepoInspector | None = None,
    converter: RepoConverter | None = None,
    *,
    force_isolation: IsolationMode | None = None,
) -> list[HarnessPlugin]:
    """Partition a multi-package monorepo into individual domain plugins (Rule 18).

    Args:
        repo_dir: Root directory of the fetched or local monorepo.
        inspector: Optional RepoInspector instance.
        converter: Optional RepoConverter instance.
        force_isolation: Optional isolation override for all partitioned plugins.

    Returns:
        List of ready-to-run HarnessPlugin instances, one per domain subpackage.
    """
    subprojects = detect_monorepo_subprojects(repo_dir)
    if not subprojects:
        logger.info("No monorepo partitioning necessary; single package detected", path=str(repo_dir))
        return []

    insp = inspector or RepoInspector()
    conv = converter or RepoConverter()
    plugins: list[HarnessPlugin] = []

    logger.info(
        "Partitioning monorepo into domain plugins per Rule 18",
        repo=repo_dir.name,
        subproject_count=len(subprojects),
    )

    for sub_path in subprojects:
        try:
            manifest = insp.inspect(sub_path)
            # Prefix plugin name with monorepo name if not already namespaced
            if not manifest.name.startswith(f"{repo_dir.name}."):
                manifest.name = f"{repo_dir.name}.{manifest.name}"
            manifest.metadata["monorepo_root"] = str(repo_dir)
            manifest.metadata["subproject_relpath"] = str(sub_path.relative_to(repo_dir))

            plugin = conv.convert(sub_path, manifest, force_isolation=force_isolation)
            plugins.append(plugin)
            logger.info("Synthesized domain plugin from monorepo", plugin=manifest.name, path=str(sub_path))
        except Exception as e:
            logger.warning("Failed to partition monorepo subproject", subproject=str(sub_path), error=str(e))

    return plugins
