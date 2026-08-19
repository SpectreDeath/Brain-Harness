"""Ecosystem Locator — robust discovery seam for sibling ecosystem repositories.

Replaces hardcoded parent path traversal with multi-tiered resolution:
1. Explicit caller-provided path
2. Target environment variable (e.g. EM_CUBED_PATH, MEMTEXT_PATH)
3. Ecosystem root variable (ECOSYSTEM_ROOT, PROJECTS_DIR)
4. Sibling directory discovery relative to cwd and module hierarchy
5. Standard OS fallback paths
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class EcosystemLocator:
    """Discovers peer repositories in the ecosystem."""

    ENV_VARS: dict[str, str] = {
        "em-cubed": "EM_CUBED_PATH",
        "Memtext": "MEMTEXT_PATH",
        "Skill Flywheel": "SKILL_FLYWHEEL_PATH",
        "Brain Harness": "BRAIN_HARNESS_PATH",
    }

    @classmethod
    def locate(
        cls,
        project_name: str,
        *,
        explicit_path: Path | str | None = None,
        env_var: str | None = None,
    ) -> Path | None:
        """Locate an ecosystem repository root.

        Args:
            project_name: Name of the repository folder (e.g., 'em-cubed', 'Memtext').
            explicit_path: User or caller provided path override.
            env_var: Specific environment variable override.

        Returns:
            Resolved directory Path if found, else None.
        """
        # 1. Explicit path
        if explicit_path:
            p = Path(explicit_path).resolve()
            if p.exists():
                return p

        # 2. Project-specific env var
        target_env = env_var or cls.ENV_VARS.get(project_name)
        if target_env and os.getenv(target_env):
            p = Path(os.environ[target_env]).resolve()
            if p.exists():
                return p

        # 3. Ecosystem root env vars
        for root_var in ("ECOSYSTEM_ROOT", "PROJECTS_DIR", "WORKSPACE_ROOT"):
            if os.getenv(root_var):
                candidate = Path(os.environ[root_var]) / project_name
                if candidate.exists():
                    return candidate.resolve()

        # 4. Search parent directories of cwd and this file
        search_roots: list[Path] = []
        try:
            search_roots.append(Path.cwd().resolve())
        except Exception:
            pass

        try:
            search_roots.append(Path(__file__).resolve().parent)
        except Exception:
            pass

        for start_path in search_roots:
            current = start_path
            for _ in range(6):
                # Check sibling or child directory
                candidate = current / project_name
                if candidate.exists() and candidate.is_dir():
                    return candidate.resolve()
                if current.parent == current:
                    break
                current = current.parent

        # 5. Standard OS fallback paths
        fallbacks = [
            Path("d:/GitHub/projects") / project_name,
            Path("c:/GitHub/projects") / project_name,
            Path.home() / "projects" / project_name,
            Path.home() / "GitHub" / project_name,
        ]
        for fb in fallbacks:
            if fb.exists() and fb.is_dir():
                return fb.resolve()

        return None

    @classmethod
    def locate_em_cubed(cls, explicit_path: Path | str | None = None) -> Path | None:
        """Locate Em-Cubed repository."""
        return cls.locate("em-cubed", explicit_path=explicit_path)

    @classmethod
    def locate_memtext(cls, explicit_path: Path | str | None = None) -> Path | None:
        """Locate Memtext repository."""
        return cls.locate("Memtext", explicit_path=explicit_path)

    @classmethod
    def locate_flywheel(cls, explicit_path: Path | str | None = None) -> Path | None:
        """Locate Skill Flywheel repository."""
        return cls.locate("Skill Flywheel", explicit_path=explicit_path)

    @classmethod
    def status(cls) -> dict[str, dict[str, Any]]:
        """Return discovery status for all known ecosystem bridges."""
        report: dict[str, dict[str, Any]] = {}
        for name in cls.ENV_VARS:
            path = cls.locate(name)
            report[name] = {
                "available": path is not None,
                "path": str(path) if path else None,
                "env_var": cls.ENV_VARS[name],
            }
        return report
