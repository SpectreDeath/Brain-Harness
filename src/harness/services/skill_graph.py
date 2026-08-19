"""Skill Knowledge Graph service protocol and typed ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol

from harness.kernel.context import ServiceKey


class SkillGraphService(Protocol):
    """Protocol for the Skill Knowledge Graph service."""

    async def index(self, root_dir: str = ".") -> int:
        """Scan and index all skill cards in the workspace."""
        ...

    async def find_chain(self, start_skill: str, target_skill: str) -> list[str]:
        """Compute execution path between two skills."""
        ...

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        """Route natural language task intent to matching skills."""
        ...

    async def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief."""
        ...


SKILL_GRAPH_KEY: ServiceKey[SkillGraphService] = ServiceKey("service.skill_knowledge_graph")
