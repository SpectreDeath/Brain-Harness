"""Polyglot manifest inspector extracting scripts and targets from package manifests."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None  # type: ignore

logger = logging.getLogger("harness.services.codebase_context.manifest")


class ManifestScriptInspector:
    """Extracts declared executable scripts and CLI tools across polyglot project manifests."""

    KNOWN_PYTHON_TOOLS = {"pytest", "python", "ruff", "mypy", "harness", "uv", "pip", "tox", "black", "isort"}

    @classmethod
    def extract_available_scripts(cls, root: Path) -> set[str]:
        """Extract all valid script names and CLI commands from repo manifests."""
        scripts: set[str] = set()

        # 1. package.json (Node.js)
        pkg_file = root / "package.json"
        if pkg_file.exists():
            try:
                data = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
                npm_scripts = data.get("scripts") or {}
                scripts.update(npm_scripts.keys())
                scripts.update({"test", "start", "build"})  # standard npm defaults
            except Exception as err:
                logger.debug("Failed parsing package.json scripts: %s", err)

        # 2. pyproject.toml (Python)
        pyproj_file = root / "pyproject.toml"
        if pyproj_file.exists():
            scripts.update(cls.KNOWN_PYTHON_TOOLS)
            if tomllib is not None:
                try:
                    data = tomllib.loads(pyproj_file.read_text(encoding="utf-8", errors="ignore"))
                    # [project.scripts]
                    proj_scripts = (data.get("project") or {}).get("scripts") or {}
                    scripts.update(proj_scripts.keys())
                    # [tool.poetry.scripts]
                    poetry_scripts = ((data.get("tool") or {}).get("poetry") or {}).get("scripts") or {}
                    scripts.update(poetry_scripts.keys())
                except Exception as err:
                    logger.debug("Failed parsing pyproject.toml scripts: %s", err)

        # 3. Makefile
        make_file = root / "Makefile"
        if make_file.exists():
            try:
                content = make_file.read_text(encoding="utf-8", errors="ignore")
                targets = re.findall(r"^([a-zA-Z0-9_-]+):", content, re.MULTILINE)
                scripts.update(targets)
            except Exception as err:
                logger.debug("Failed parsing Makefile targets: %s", err)

        return scripts
