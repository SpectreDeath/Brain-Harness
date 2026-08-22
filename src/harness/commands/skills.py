"""Skill commands — pure async and sync programmatic entry points for skill knowledge and authoring.

Provides an authoritative seam for indexing, routing, chain discovery, topology inspection,
scaffolding, and validation across agent skills. Replaces ad-hoc imports in CLI adapters.
"""

from __future__ import annotations

from pathlib import Path
import re
import tempfile
import time
from typing import Any, cast

import structlog

from harness.creator.skills import (
    SkillOptions,
    SkillResult,
    SkillScaffoldEngine,
    SkillValidator,
)
from harness.creator.validator import ValidationReport


logger = structlog.get_logger()


def _get_skill_graph_plugin() -> Any | None:
    """Attempt to resolve the SkillKnowledgeGraph plugin module dynamically."""
    try:
        from plugins.memory_and_epistemics.skill_knowledge_graph import main as skg_main

        return skg_main
    except ImportError:
        pass

    try:
        from plugins.skill_knowledge_graph import main as skg_main_fallback

        return skg_main_fallback
    except ImportError:
        pass

    return None


def index_skills_cmd(root_path: str | Path = ".") -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and construct the skill knowledge graph.

    Delegates to SkillKnowledgeGraph plugin if available; otherwise runs built-in fallback.
    """
    skg = _get_skill_graph_plugin()
    if skg and hasattr(skg, "index_skill_catalog"):
        return cast(dict[str, Any], skg.index_skill_catalog(str(root_path)))

    # Built-in fallback scanning
    p = Path(root_path).resolve()
    paths_to_scan = [p / ".agents" / "skills", p / "plugins", p]
    discovered_skills: dict[str, dict[str, Any]] = {}
    categories: set[str] = set()

    for scan_dir in paths_to_scan:
        if not scan_dir.exists():
            continue
        for skill_file in scan_dir.rglob("SKILL.md"):
            try:
                content = skill_file.read_text(encoding="utf-8")
                name_match = re.search(r"^name:\s*([^\n]+)", content, re.MULTILINE)
                desc_match = re.search(r"^description:\s*([^\n]+)", content, re.MULTILINE)
                skill_name = name_match.group(1).strip() if name_match else skill_file.parent.name
                description = desc_match.group(1).strip() if desc_match else ""
                category = "engineering / meta-skills"
                categories.add(category)

                discovered_skills[skill_name] = {
                    "name": skill_name,
                    "description": description,
                    "category": category,
                    "path": str(skill_file.parent),
                }
            except Exception as e:
                logger.debug("Failed parsing skill fallback", file=str(skill_file), error=str(e))

    return {
        "status": "ok",
        "indexed_skills": len(discovered_skills),
        "categories": sorted(categories),
        "total_nodes": len(discovered_skills),
        "total_edges": 0,
        "fallback_mode": True,
    }


def export_skill_graph_visual_cmd(output_path: str | Path | None = None) -> dict[str, Any]:
    """Generate an interactive HTML visual brief of the skill graph."""
    skg = _get_skill_graph_plugin()
    if skg and hasattr(skg, "export_skill_graph_visual"):
        return cast(dict[str, Any], skg.export_skill_graph_visual(str(output_path) if output_path else None))

    # Built-in fallback visual generator
    out = (
        Path(output_path).resolve()
        if output_path
        else Path(tempfile.gettempdir()) / f"skill-graph-visual-{int(time.time())}.html"
    )
    res = index_skills_cmd()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Skill Knowledge Graph</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-8 bg-slate-900 text-slate-100 font-sans">
  <h1 class="text-2xl font-bold text-white mb-2">Agent Skill Knowledge Graph</h1>
  <p class="text-sm text-slate-400 mb-6">Indexed {res.get('indexed_skills', 0)} skills across categories: {', '.join(res.get('categories', []))}</p>
  <div class="bg-slate-800 p-4 rounded border border-slate-700">
    <p class="text-xs text-slate-300">Skill Graph Visual Fallback Mode active.</p>
  </div>
</body>
</html>"""
    out.write_text(html_content, encoding="utf-8")
    return {"status": "ok", "html_path": str(out), "node_count": res.get("total_nodes", 0)}


def route_skills_cmd(intent: str, top_k: int = 3, root_path: str | Path = ".") -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    skg = _get_skill_graph_plugin()
    if skg and hasattr(skg, "query_skill_router"):
        return cast(dict[str, Any], skg.query_skill_router(intent=intent, top_k=top_k))

    # Fallback keyword matching
    intent_tokens = set(re.findall(r"\w+", intent.lower()))

    # Basic fallback scoring
    matches = []
    p = Path(root_path).resolve()
    for skill_file in (p / ".agents" / "skills").rglob("SKILL.md") if (p / ".agents" / "skills").exists() else []:
        try:
            content = skill_file.read_text(encoding="utf-8").lower()
            name_match = re.search(r"^name:\s*([^\n]+)", content, re.MULTILINE)
            sname = name_match.group(1).strip() if name_match else skill_file.parent.name
            score = sum(1 for t in intent_tokens if t in content or t in sname)
            if score > 0:
                confidence = min(0.95, 0.3 + (score * 0.15))
                matches.append({
                    "skill_name": sname,
                    "category": "engineering / meta-skills",
                    "confidence": confidence,
                    "matched_triggers": [t for t in intent_tokens if t in content][:3],
                })
        except Exception:
            pass

    matches.sort(key=lambda m: m["confidence"], reverse=True)
    top_matches = matches[:top_k]
    recommended_chain = [m["skill_name"] for m in top_matches[:2]] if top_matches else []

    return {
        "intent": intent,
        "matches": top_matches,
        "recommended_chain": recommended_chain,
        "fallback_mode": True,
    }


def find_skill_chain_cmd(start_skill: str, target_skill: str) -> dict[str, Any]:
    """Find directed execution path between two skills."""
    skg = _get_skill_graph_plugin()
    if skg and hasattr(skg, "find_skill_chain"):
        return cast(dict[str, Any], skg.find_skill_chain(start_skill=start_skill, target_skill=target_skill))

    # Fallback direct path
    return {
        "status": "ok",
        "start": start_skill,
        "target": target_skill,
        "chain": [start_skill, target_skill],
        "length": 2,
        "fallback_mode": True,
    }


def get_skill_topology_cmd(skill_name: str) -> dict[str, Any]:
    """Inspect topological dependencies, prerequisites, and anti-patterns for a skill."""
    skg = _get_skill_graph_plugin()
    if skg and hasattr(skg, "get_skill_topology"):
        return cast(dict[str, Any], skg.get_skill_topology(skill_name))

    # Fallback inspection from .agents/skills
    skill_dir = Path(".agents") / "skills" / skill_name
    if skill_dir.exists():
        skill_file = skill_dir / "SKILL.md"
        desc = ""
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            desc_match = re.search(r"^description:\s*([^\n]+)", content, re.MULTILINE)
            desc = desc_match.group(1).strip() if desc_match else ""

        return {
            "status": "ok",
            "topology": {
                "skill": {
                    "name": skill_name,
                    "version": "1.0.0",
                    "category": "engineering / meta-skills",
                    "invocation": f"/{skill_name}",
                    "target": desc,
                    "description": desc,
                },
                "prerequisites": [],
                "downstream_handoffs": [],
                "mitigated_anti_patterns": [],
            },
            "fallback_mode": True,
        }

    return {"status": "error", "reason": f"Skill '{skill_name}' not found"}


def scaffold_skill_cmd(
    name: str,
    *,
    description: str = "",
    category: str = "engineering / meta-skills",
    target_dir: str | Path | None = None,
    triggers: list[str] | tuple[str, ...] | None = None,
    auto_validate: bool = False,
) -> SkillResult:
    """Scaffold a high-precision agent skill with SKILL.md and CARD.md specifications."""
    clean_name = name.strip().lower().replace("_", "-")
    out_dir = Path(target_dir) if target_dir else Path(".agents") / "skills" / clean_name

    opts = SkillOptions(
        name=clean_name,
        description=description,
        category=category,
        triggers=list(triggers) if triggers else [],
        auto_validate=auto_validate,
    )
    return SkillScaffoldEngine.scaffold(out_dir, options=opts)


def validate_skill_cmd(skill_dir: str | Path = ".") -> ValidationReport:
    """Validate an agent skill package against deep-module craft standards."""
    target = Path(skill_dir).resolve()
    return SkillValidator.validate(target)


__all__ = [
    "export_skill_graph_visual_cmd",
    "find_skill_chain_cmd",
    "get_skill_topology_cmd",
    "index_skills_cmd",
    "route_skills_cmd",
    "scaffold_skill_cmd",
    "validate_skill_cmd",
]
