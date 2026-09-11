"""Omarchy Quattro Agent Telemetry & Skill Catalog Plugin.

Provides introspection of Omarchy's bundled agent skill guides, crash diagnosis
runbooks, and static inspection of Claude/Codex/Fireworks usage tracking scripts.
"""

from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

DEFAULT_OMARCHY_PATH = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
ENV_VAR_PATTERN = re.compile(r"""(?:os\.environ(?:\.get)?|getenv)\(\s*['"]([A-Z0-9_]+)['"]""")


@runtime_checkable
class OmarchyAgentTelemetryService(Protocol):
    """Protocol for Omarchy Agent Skill Catalog and Telemetry inspection."""

    def list_agent_skills(self, **kwargs: Any) -> list[dict[str, Any]]:
        ...

    def get_agent_skill(self, skill_name: str, **kwargs: Any) -> dict[str, Any]:
        ...

    def inspect_agent_usage_scripts(self, **kwargs: Any) -> list[dict[str, Any]]:
        ...


OMARCHY_AGENT_TELEMETRY_SERVICE_KEY = ServiceKey[OmarchyAgentTelemetryService](
    "service.omarchy_agent_telemetry"
)


class OmarchyAgentTelemetryServiceImpl:
    """Implementation of Omarchy Agent Telemetry and Skill Catalog service."""

    def __init__(self, source_dir: Path | str | None = None) -> None:
        self._source_dir_override = Path(source_dir) if source_dir else None
        self._skills_cache: dict[str, dict[str, Any]] | None = None

    @property
    def source_dir(self) -> Path:
        if self._source_dir_override:
            return self._source_dir_override
        env_path = os.environ.get("OMARCHY_PATH")
        if env_path:
            return Path(env_path)
        return DEFAULT_OMARCHY_PATH

    @property
    def developer_skills_dir(self) -> Path:
        return self.source_dir / "agents" / "skills"

    @property
    def runtime_skills_dir(self) -> Path:
        return self.source_dir / "default" / "agents" / "skills"

    @property
    def bin_dir(self) -> Path:
        return self.source_dir / "bin"

    def list_agent_skills(self, **kwargs: Any) -> list[dict[str, Any]]:
        """List all agent skills, developer runbooks, and runtime guides."""
        skills = []

        # 1. Developer guide skills in agents/skills/*.md
        dev_dir = self.developer_skills_dir
        if dev_dir.exists() and dev_dir.is_dir():
            for entry in sorted(dev_dir.glob("*.md")):
                skill_name = entry.stem
                meta = self._parse_markdown_header(entry)
                skills.append({
                    "name": skill_name,
                    "category": "developer_guide",
                    "path": str(entry.relative_to(self.source_dir)),
                    "size_bytes": entry.stat().st_size,
                    "title": meta.get("title", skill_name),
                    "summary": meta.get("summary", ""),
                    "companion_docs": [],
                })

        # 2. Runtime agent skills in default/agents/skills/*/SKILL.md
        rt_dir = self.runtime_skills_dir
        if rt_dir.exists() and rt_dir.is_dir():
            for entry in sorted(rt_dir.iterdir()):
                if not entry.is_dir():
                    continue

                skill_file = entry / "SKILL.md"
                if not skill_file.exists():
                    # Fallback to any markdown
                    md_files = list(entry.glob("*.md"))
                    if md_files:
                        skill_file = md_files[0]
                    else:
                        continue

                meta = self._parse_markdown_header(skill_file)
                companion_files = [
                    f.name for f in entry.glob("*.md")
                    if f.name != skill_file.name
                ]

                skills.append({
                    "name": entry.name,
                    "category": "runtime_skill",
                    "path": str(skill_file.relative_to(self.source_dir)),
                    "size_bytes": skill_file.stat().st_size,
                    "title": meta.get("title", entry.name),
                    "summary": meta.get("summary", ""),
                    "companion_docs": sorted(companion_files),
                })

        return skills

    def get_agent_skill(self, skill_name: str, **kwargs: Any) -> dict[str, Any]:
        """Retrieve full markdown content, outline, and companions for a skill."""
        clean_name = skill_name.strip().lower()

        # Search runtime skills first
        rt_skill_dir = self.runtime_skills_dir / clean_name
        skill_path = rt_skill_dir / "SKILL.md"
        companion_docs: dict[str, str] = {}

        if rt_skill_dir.exists() and rt_skill_dir.is_dir():
            if not skill_path.exists():
                md_files = list(rt_skill_dir.glob("*.md"))
                if md_files:
                    skill_path = md_files[0]

            for comp in rt_skill_dir.glob("*.md"):
                if comp.name != skill_path.name:
                    try:
                        companion_docs[comp.name] = comp.read_text(encoding="utf-8", errors="replace")
                    except Exception as exc:
                        companion_docs[comp.name] = f"Error reading file: {exc}"

        # Fallback to developer guides
        if not skill_path.exists():
            dev_candidate = self.developer_skills_dir / f"{clean_name}.md"
            if dev_candidate.exists():
                skill_path = dev_candidate

        if not skill_path.exists():
            return {
                "error": f"Agent skill '{skill_name}' not found",
                "available_skills": [s["name"] for s in self.list_agent_skills()],
            }

        try:
            content = skill_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return {"error": f"Failed to read skill file: {exc}"}

        outline = self._extract_outline(content)

        return {
            "name": clean_name,
            "path": str(skill_path.relative_to(self.source_dir)),
            "content": content,
            "outline": outline,
            "companion_docs": companion_docs,
            "line_count": len(content.splitlines()),
        }

    def inspect_agent_usage_scripts(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Statically inspect omarchy-agent-usage-* telemetry collectors."""
        bin_path = self.bin_dir
        if not bin_path.exists() or not bin_path.is_dir():
            return []

        scripts = []
        for file_path in sorted(bin_path.glob("omarchy-agent-usage*")):
            if not file_path.is_file():
                continue

            info: dict[str, Any] = {
                "script_name": file_path.name,
                "path": str(file_path.relative_to(self.source_dir)),
                "size_bytes": file_path.stat().st_size,
                "summary": "",
                "args": "",
                "docstring": "",
                "env_vars_detected": [],
                "target_provider": "unknown",
            }

            # Infer target provider
            if "claude" in file_path.name:
                info["target_provider"] = "anthropic_claude"
            elif "codex" in file_path.name:
                info["target_provider"] = "openai_codex"
            elif "fireworks" in file_path.name:
                info["target_provider"] = "fireworks_ai"
            elif "update" in file_path.name:
                info["target_provider"] = "updater"

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()

                # Parse header metadata
                for line in lines[:50]:
                    stripped = line.strip()
                    if stripped.startswith("# omarchy:summary="):
                        info["summary"] = stripped.split("=", 1)[1].strip()
                    elif stripped.startswith("# omarchy:args="):
                        info["args"] = stripped.split("=", 1)[1].strip()

                # Extract Python docstring if present
                docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if docstring_match:
                    info["docstring"] = docstring_match.group(1).strip()

                # Detect referenced environment variables
                env_vars = sorted(list(set(ENV_VAR_PATTERN.findall(content))))
                info["env_vars_detected"] = env_vars

            except Exception as exc:
                info["error"] = str(exc)

            scripts.append(info)

        return scripts

    def _parse_markdown_header(self, file_path: Path) -> dict[str, str]:
        """Extract title and summary from first markdown lines."""
        res = {"title": file_path.stem, "summary": ""}
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline().strip() for _ in range(25)]

            for idx, line in enumerate(lines):
                if line.startswith("# ") and not res.get("title_found"):
                    res["title"] = line.lstrip("#").strip()
                    res["title_found"] = "true"
                    # Try to find summary in following non-empty line
                    for subsequent in lines[idx + 1:]:
                        if subsequent and not subsequent.startswith("#"):
                            res["summary"] = subsequent[:200]
                            break
                    break
        except Exception:
            pass
        return res

    def _extract_outline(self, markdown_text: str) -> list[dict[str, Any]]:
        """Extract outline hierarchy from markdown text."""
        outline = []
        for line in markdown_text.splitlines():
            m = HEADING_PATTERN.match(line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                outline.append({"level": level, "title": title})
        return outline


_TELEMETRY_INSTANCE = OmarchyAgentTelemetryServiceImpl()


# Top-level tool entrypoints
def omarchy_list_agent_skills(**kwargs: Any) -> list[dict[str, Any]]:
    return _TELEMETRY_INSTANCE.list_agent_skills(**kwargs)


def omarchy_get_agent_skill(skill_name: str, **kwargs: Any) -> dict[str, Any]:
    return _TELEMETRY_INSTANCE.get_agent_skill(skill_name=skill_name, **kwargs)


def omarchy_inspect_agent_usage_scripts(**kwargs: Any) -> list[dict[str, Any]]:
    return _TELEMETRY_INSTANCE.inspect_agent_usage_scripts(**kwargs)


class OmarchyAgentTelemetryPlugin(HarnessPlugin):
    """Harness Plugin for Omarchy Agent Skill Catalog and Telemetry Script Introspection."""

    @property
    def name(self) -> str:
        return "plugin.omarchy_agent_telemetry"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Omarchy Quattro agent skill catalog navigator and usage "
            "telemetry script introspection engine."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OMARCHY_AGENT_TELEMETRY_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(OMARCHY_AGENT_TELEMETRY_SERVICE_KEY, _TELEMETRY_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = OmarchyAgentTelemetryPlugin()
