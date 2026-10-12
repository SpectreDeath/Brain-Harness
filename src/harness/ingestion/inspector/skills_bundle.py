"""Discovery strategy for Claude plugins and Agent skills bundles."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import structlog

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

logger = structlog.get_logger()


def parse_skill_frontmatter(content: str) -> tuple[str, str]:
    """Extract name and description from YAML frontmatter in SKILL.md."""
    name = ""
    desc = ""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                line_s = line.strip()
                if line_s.startswith("name:"):
                    name = line_s[5:].strip().strip("\"'")
                elif line_s.startswith("description:"):
                    desc = line_s[12:].strip().strip("\"'")
    return name, desc


def try_skills_bundle(repo_dir: Path) -> PluginManifest | None:
    """Check for a Claude plugin or Agent skills bundle repository."""
    claude_plugin = repo_dir / ".claude-plugin" / "plugin.json"
    agents_plugin = repo_dir / ".agents" / "plugin.json"
    root_plugin = repo_dir / "plugin.json"
    skills_dir = repo_dir / "skills"

    has_skills = skills_dir.exists() and any(skills_dir.rglob("SKILL.md"))
    has_plugin_spec = claude_plugin.exists() or agents_plugin.exists() or (
        root_plugin.exists() and "skills" in root_plugin.read_text(encoding="utf-8", errors="ignore")
    )

    if not (has_plugin_spec or has_skills):
        return None

    data: dict[str, str] = {}
    for target_json in (claude_plugin, agents_plugin, root_plugin):
        if target_json.exists():
            try:
                data = json.loads(target_json.read_text(encoding="utf-8", errors="ignore"))
                if "name" in data:
                    break
            except Exception:
                pass

    name = data.get("name", repo_dir.name)
    version = data.get("version", "1.0.0")
    description = data.get("description", f"Agent skills plugin bundle from {name}")

    entrypoints: list[EntrypointSpec] = []
    skill_files = sorted(repo_dir.rglob("SKILL.md"))

    for sfile in skill_files:
        try:
            raw = sfile.read_text(encoding="utf-8", errors="ignore")
            sname, sdesc = parse_skill_frontmatter(raw)
            if not sname:
                sname = sfile.parent.name
            if not sdesc:
                sdesc = f"Execute {sname} skill"

            entrypoints.append(
                EntrypointSpec(
                    name=sname,
                    description=sdesc[:300],
                    parameters=[
                        ParameterSpec(
                            name="task",
                            type="string",
                            description=f"Task description or input context for {sname}",
                            required=False,
                        ),
                        ParameterSpec(
                            name="context",
                            type="string",
                            description="Additional project context or file contents",
                            required=False,
                        ),
                    ],
                )
            )
        except Exception:
            continue

    if not entrypoints:
        return None

    entrypoint_file = repo_dir / "skills_entrypoint.py"
    entrypoint_code = textwrap.dedent('''\
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
    ''')
    try:
        entrypoint_file.write_text(entrypoint_code, encoding="utf-8")
    except Exception as e:
        logger.warning("Could not write skills_entrypoint.py", error=str(e))

    return PluginManifest(
        name=name,
        version=version,
        description=description,
        language="python",
        entrypoint="skills_entrypoint.py",
        entrypoints=entrypoints,
        isolation=IsolationMode.SUBPROCESS,
        metadata={"source_format": "agent_skills_bundle", "skills_count": len(entrypoints)},
    )
