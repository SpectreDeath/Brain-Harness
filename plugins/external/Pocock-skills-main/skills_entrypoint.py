"""Auto-generated entrypoint runner for Agent Skills Bundle."""
from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent

def _get_skill(skill_name: str, task: str = "", context: str = "", **kwargs: Any) -> dict[str, Any]:
    clean_name = skill_name.replace("_", "-")
    for p in ROOT.glob(f"skills/**/{clean_name}/SKILL.md"):
        if p.exists():
            return {
                "status": "ok",
                "skill": clean_name,
                "instructions": p.read_text(encoding="utf-8", errors="ignore"),
                "task": task,
                "context": context,
            }
    for p in ROOT.glob("skills/**/SKILL.md"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if f"name: {clean_name}" in txt:
                return {
                    "status": "ok",
                    "skill": clean_name,
                    "instructions": txt,
                    "task": task,
                    "context": context,
                }
        except Exception:
            continue
    return {"status": "error", "error": f"Skill '{clean_name}' not found in bundle."}

def __getattr__(name: str) -> Any:
    def _skill_caller(task: str = "", context: str = "", **kwargs: Any) -> dict[str, Any]:
        return _get_skill(name, task=task, context=context, **kwargs)
    return _skill_caller
