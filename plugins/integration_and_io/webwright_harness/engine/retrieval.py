"""Semantic skill retrieval and template ranking mixin."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


class SkillRetrievalMixin:
    """Provides semantic keyword matching and ranking over learned skills library."""

    base_dir: Path

    def retrieve_skills(
        self,
        task: str,
        k: int = 3,
        library_dir: str = "skills",
    ) -> dict[str, Any]:
        """Rank and retrieve skills relevant to the task."""
        resolved_lib = self.base_dir / library_dir
        if not resolved_lib.exists():
            return {
                "status": "ok",
                "task": task,
                "candidates": [],
                "error": None,
            }

        task_words = set(re.findall(r"\w+", task.lower()))
        candidates: list[dict[str, Any]] = []

        for item in resolved_lib.iterdir():
            if item.is_dir() and (item / "meta.json").exists():
                try:
                    meta = json.loads((item / "meta.json").read_text(encoding="utf-8", errors="ignore"))
                    tpl = meta.get("template", "")
                    summary = meta.get("summary", "")
                    target_words = set(re.findall(r"\w+", f"{tpl} {summary}".lower()))

                    if not task_words or not target_words:
                        score = 0.0
                    else:
                        overlap = len(task_words.intersection(target_words))
                        score = round(overlap / max(len(task_words), len(target_words)), 3)

                    candidates.append({
                        "skill_id": meta.get("skill_id", item.name),
                        "score": max(0.1, score),
                        "reason": f"Word overlap match on template '{tpl}'",
                        "template": tpl,
                    })
                except Exception:
                    continue

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return {
            "status": "ok",
            "task": task,
            "candidates": candidates[:k],
            "error": None,
        }
