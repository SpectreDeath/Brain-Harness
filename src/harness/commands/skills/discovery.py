"""Discovery, indexing, visualization, authoring, and headless execution commands for skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.commands.skills.seams import get_skill_registry
from harness.creator.skills import (
    SkillOptions,
    SkillResult,
    SkillScaffoldEngine,
    SkillValidator,
)
from harness.creator.validator import ValidationReport
from harness.services.skill_graph import SkillCardDefinition


def index_skills_cmd(
    root_path: str | Path = ".", context: Any = None
) -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and construct the skill knowledge graph."""
    registry = get_skill_registry(root_path, context=context)
    skills = registry.discover_all(str(root_path))
    categories = sorted({s.category for s in skills})

    total_edges = sum(len(s.dependencies) for s in skills)

    return {
        "status": "ok",
        "indexed_skills": len(skills),
        "categories": categories,
        "total_nodes": len(skills),
        "total_edges": total_edges,
    }


def export_skill_graph_visual_cmd(
    output_path: str | Path | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """Generate an interactive HTML visual brief of the skill graph."""
    registry = get_skill_registry(context=context)
    html_path = registry.export_html_brief(
        str(output_path) if output_path else None
    )
    skills = registry.discover_all()
    return {
        "status": "ok",
        "html_path": html_path,
        "total_skills": len(skills),
        "node_count": len(skills),
    }


def list_skills_cmd(
    root_path: str | Path = ".", context: Any = None
) -> list[SkillCardDefinition]:
    """List all discovered skill cards."""
    registry = get_skill_registry(root_path, context=context)
    return registry.discover_all(str(root_path))


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
    out_dir = (
        Path(target_dir) if target_dir else Path(".agents") / "skills" / clean_name
    )

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


def run_skill_cmd(
    skill_name: str,
    root_path: str | Path = ".",
    source: str | None = None,
) -> dict[str, Any]:
    """Execute an automated skill pipeline driver programmatically via SkillDriverResolver."""
    from harness.services.skill_pipeline import SkillDriverResolver

    return SkillDriverResolver.execute_driver(
        skill_name=skill_name,
        root_path=root_path,
        source=source,
    )
