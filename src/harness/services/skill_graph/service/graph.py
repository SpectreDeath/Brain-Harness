"""Authoritative Skill Graph service implementation fulfilling SkillGraphService protocol."""

from __future__ import annotations

from typing import Any

from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    SkillChainResult,
    SkillEdge,
    SkillExecutionGuidance,
)
from harness.services.skill_graph.protocols import SkillGraphService
from harness.services.skill_graph.service.registry import BuiltinSkillRegistryService


class BuiltinSkillGraphService(SkillGraphService):
    """Authoritative Skill Graph service implementation fulfilling SkillGraphService protocol."""

    def __init__(self, registry: BuiltinSkillRegistryService | None = None) -> None:
        self._registry = registry or BuiltinSkillRegistryService()

    @property
    def registry(self) -> BuiltinSkillRegistryService:
        return self._registry

    async def index(self, root_dir: str = ".") -> int:
        return len(self._registry.discover_all(root_dir))

    async def find_chain(self, start_skill: str, target_skill: str, fallback_direct: bool = False) -> list[str]:
        return list(self._registry.get_chain(start_skill, target_skill, fallback_direct=fallback_direct).chain)

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        return self._registry.route_intent(intent, top_k=top_k)

    async def get_topology(self, skill_name: str) -> dict[str, Any]:
        try:
            topo = self._registry.get_topology(skill_name)
            return {
                "status": "ok",
                "skill": skill_name,
                "topology": {
                    "skill": {"name": topo.skill.name, "category": topo.skill.category},
                    "prerequisites": list(topo.prerequisites),
                    "downstream_handoffs": list(topo.downstream_handoffs),
                    "complements": list(topo.complements),
                    "mitigated_anti_patterns": list(topo.mitigated_anti_patterns),
                },
            }
        except KeyError as e:
            return {"status": "error", "message": str(e)}

    async def export_html_brief(self, output_path: str | None = None) -> str:
        return self._registry.export_html_brief(output_path=output_path)

    async def link_knowledge_vault(self, vault_dir: str = ".harness/knowledge") -> int:
        return self._registry.link_knowledge_vault(vault_dir=vault_dir)

    async def cluster_skills(self, min_cluster_size: int = 2) -> list[dict[str, Any]]:
        clusters = self._registry.cluster_skills(min_cluster_size=min_cluster_size)
        return [
            c.model_dump()
            if hasattr(c, "model_dump")
            else {"cluster_id": c.cluster_id, "name": c.name, "skills": list(c.skills)}
            for c in clusters
        ]

    async def discover_emergent_capabilities(self, query: str | None = None) -> list[dict[str, Any]]:
        caps = self._registry.discover_emergent_capabilities(query=query)
        return [
            c.model_dump()
            if hasattr(c, "model_dump")
            else {
                "capability_id": getattr(c, "capability_id", getattr(c, "id", "")),
                "title": getattr(c, "title", getattr(c, "name", "")),
                "primary_skills": list(getattr(c, "primary_skills", [])),
            }
            for c in caps
        ]

    async def get_cross_cluster_bridges(self) -> list[dict[str, Any]]:
        bridges = self._registry.get_cross_cluster_bridges()
        return [
            b.model_dump()
            if hasattr(b, "model_dump")
            else {
                "source_cluster": b.source_cluster,
                "target_cluster": b.target_cluster,
                "bridge_skills": list(getattr(b, "bridge_skills", [])),
            }
            for b in bridges
        ]

    async def select_skills_for_task(
        self, task: str, max_skills: int = 5, include_verifier: bool = True
    ) -> dict[str, Any]:
        plan = self._registry.select_skills_for_task(task, max_skills=max_skills, include_verifier=include_verifier)
        if hasattr(plan, "model_dump"):
            return plan.model_dump()
        return {
            "task": plan.task,
            "selected_skills": list(plan.selected_skills),
            "ordered_pipeline": list(plan.ordered_pipeline),
            "execution_pipeline": list(plan.execution_pipeline),
            "confidence": plan.confidence,
            "rationale": plan.rationale,
            "stages": [
                {
                    "skill": s.skill,
                    "stage_num": s.stage_num,
                    "name": s.name,
                    "completion_gate": s.completion_gate,
                }
                for s in plan.stages
            ],
        }

    async def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        return self._registry.get_prerequisite_closure(skill_name)

    async def compile_execution_guidance(self, task: str, max_skills: int = 4) -> SkillExecutionGuidance:
        return self._registry.compile_execution_guidance(task, max_skills=max_skills)

    def get_edges(self, skill_name: str | None = None) -> list[SkillEdge]:
        if skill_name:
            out_edges = self._registry.get_outgoing_edges(skill_name)
            in_edges = self._registry.get_incoming_edges(skill_name)
            seen: set[tuple[str, str, Any]] = set()
            result: list[SkillEdge] = []
            for e in out_edges + in_edges:
                key = (e.source, e.target, e.relation)
                if key not in seen:
                    seen.add(key)
                    result.append(e)
            return result
        return self._registry.edges

    def find_shortest_chain(
        self, start_skill: str, target_skill: str, fallback_direct: bool = False
    ) -> SkillChainResult:
        return self._registry.get_chain(start_skill, target_skill, fallback_direct=fallback_direct)

    def evaluate_chain_feasibility(self, chain: list[str], context: Any = None) -> tuple[bool, list[str]]:
        return self._registry.evaluate_chain_feasibility(chain, context=context)

    def intercept_action(
        self, action_name: str, action_input: dict[str, Any], active_skills: list[str] | None = None
    ) -> list[AntiPatternViolation]:
        return self._registry.intercept_action(
            action_name=action_name, action_input=action_input, active_skills=active_skills
        )

    def evaluate_action_gate(
        self, action_name: str, action_input: dict[str, Any], active_skills: list[str] | None = None
    ) -> ActionGateResult:
        return self._registry.evaluate_action_gate(
            action_name=action_name, action_input=action_input, active_skills=active_skills
        )
