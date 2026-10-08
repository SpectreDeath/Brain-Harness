"""Protocols and ServiceKey declarations for Skill Knowledge Graph and Registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.skill_clustering import SkillClusteringService
from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    SkillCardDefinition,
    SkillChainResult,
    SkillExecutionGuidance,
    SkillTopologyReport,
)


@runtime_checkable
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

    async def get_topology(self, skill_name: str) -> dict[str, Any]:
        """Inspect topological dependencies, handoffs, and anti-patterns for a skill."""
        ...

    async def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief."""
        ...

    async def link_knowledge_vault(self, vault_dir: str = ".harness/knowledge") -> int:
        """Cross-link knowledge vault items to skills."""
        ...

    async def cluster_skills(self, min_cluster_size: int = 2) -> list[dict[str, Any]]:
        """Cluster workspace skills into functional capability domains."""
        ...

    async def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[dict[str, Any]]:
        """Discover novel emergent capabilities across skill clusters."""
        ...

    async def get_cross_cluster_bridges(self) -> list[dict[str, Any]]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        ...

    async def select_skills_for_task(
        self, task: str, max_skills: int = 5, include_verifier: bool = True
    ) -> dict[str, Any]:
        """Select skills and generate an execution plan for an agent task."""
        ...

    async def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        """Compute the full transitive prerequisite closure for a skill in topological execution order."""
        ...

    async def compile_execution_guidance(
        self, task: str, max_skills: int = 4
    ) -> SkillExecutionGuidance:
        """Compile an end-to-end execution guidance plan for an agent task."""
        ...

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        """Intercept proposed action and evaluate against active skill anti-patterns and AST security gates."""
        ...


@runtime_checkable
class SkillRegistryService(Protocol):
    """Protocol for the authoritative workspace Skill Registry."""

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        """Discover and parse all skill cards across .agents/skills and skills/."""
        ...

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        """Retrieve a skill definition by kebab-case name."""
        ...

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        """Inspect topological dependencies, handoffs, and anti-patterns for a skill."""
        ...

    def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        """Compute the full transitive prerequisite closure for a skill in topological execution order."""
        ...

    def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief synchronously."""
        ...

    def route_intent(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        """Route natural language task intent to candidate skills."""
        ...

    def get_chain(self, start_skill: str, target_skill: str) -> SkillChainResult:
        """Calculate execution chain between two skills."""
        ...

    def link_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        """Cross-link knowledge vault items to skills."""
        ...

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None
    ) -> tuple[bool, list[str]]:
        """Check whether all declared service preconditions for a skill chain are satisfied."""
        ...

    def cluster_skills(self, min_cluster_size: int = 2) -> list[Any]:
        """Cluster workspace skills into functional capability domains."""
        ...

    def discover_emergent_capabilities(self, query: str | None = None) -> list[Any]:
        """Discover novel macro-capabilities revealed by the graph clusters."""
        ...

    def get_cross_cluster_bridges(self) -> list[Any]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        ...

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> Any:
        """Select skills and generate an execution plan for an agent task."""
        ...

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        """Intercept proposed action and evaluate against active skill anti-patterns and AST security gates."""
        ...


@runtime_checkable
class SkillIntelligenceService(SkillRegistryService, SkillClusteringService, Protocol):
    """Authoritative composite protocol unifying discovery, topology, routing, clustering, and execution guidance."""

    def compile_execution_guidance(
        self, task: str, max_skills: int = 4, include_verifier: bool = True
    ) -> SkillExecutionGuidance:
        """Compile an end-to-end execution guidance plan for an agent task."""
        ...

    def evaluate_action_gate(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        """Evaluate proposed action against skill anti-patterns and AST gates, returning a slotted ActionGateResult."""
        ...


SKILL_GRAPH_KEY: ServiceKey[SkillGraphService] = ServiceKey(
    "service.skill_knowledge_graph"
)
SKILL_REGISTRY_KEY: ServiceKey[SkillRegistryService] = ServiceKey(
    "service.skill_registry"
)
SKILL_INTELLIGENCE_KEY: ServiceKey[SkillIntelligenceService] = ServiceKey(
    "service.skill_intelligence"
)

# Compatibility alias for callers using SKILL_GRAPH_SERVICE_KEY
SKILL_GRAPH_SERVICE_KEY: ServiceKey[SkillGraphService] = SKILL_GRAPH_KEY

__all__ = [
    "SKILL_GRAPH_KEY",
    "SKILL_GRAPH_SERVICE_KEY",
    "SKILL_INTELLIGENCE_KEY",
    "SKILL_REGISTRY_KEY",
    "SkillGraphService",
    "SkillIntelligenceService",
    "SkillRegistryService",
]
