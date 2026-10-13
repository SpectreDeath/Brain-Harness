"""3-tier zero-fork configuration resolver per Rule 44."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None  # type: ignore

logger = logging.getLogger("harness.services.codebase_context.config")


class ConfigResolver:
    """Resolves layered configuration: Project Override -> Skill Default -> Hardcoded Fallback."""

    DEFAULT_BUDGETS = {
        "AGENTS.md": 800,
        "CLAUDE.md": 300,
        ".github/copilot-instructions.md": 900,
        "src/AGENTS.md": 400,
    }
    CHARS_PER_TOKEN = 4

    @classmethod
    def resolve_config(cls, root: Path, skill_dir: Path | None = None) -> dict[str, Any]:
        config: dict[str, Any] = {
            "chars_per_token": cls.CHARS_PER_TOKEN,
            "budgets": dict(cls.DEFAULT_BUDGETS),
        }

        # 1. Skill Default config
        if skill_dir is None:
            skill_dir = root / ".agents" / "skills" / "codebase-context-architect"
        default_file = skill_dir / "config.default.yaml"
        if default_file.exists() and yaml is not None:
            try:
                parsed = yaml.safe_load(default_file.read_text(encoding="utf-8")) or {}
                if "chars_per_token" in parsed:
                    config["chars_per_token"] = parsed["chars_per_token"]
                if "budgets" in parsed and "always_loaded_files" in parsed["budgets"]:
                    for item in parsed["budgets"]["always_loaded_files"]:
                        p = item.get("path")
                        b = item.get("budget_tokens")
                        if p and b:
                            config["budgets"][p] = int(b)
            except Exception as err:
                logger.debug("Failed parsing default config: %s", err)

        # 2. Project Override config (.agents/skills.config.yaml)
        override_file = root / ".agents" / "skills.config.yaml"
        if override_file.exists() and yaml is not None:
            try:
                overrides = yaml.safe_load(override_file.read_text(encoding="utf-8")) or {}
                skill_overrides = overrides.get("codebase-context-architect") or {}
                if "chars_per_token" in skill_overrides:
                    config["chars_per_token"] = skill_overrides["chars_per_token"]
                if "budgets" in skill_overrides:
                    config["budgets"].update(skill_overrides["budgets"])
            except Exception as err:
                logger.debug("Failed parsing project override config: %s", err)

        return config
