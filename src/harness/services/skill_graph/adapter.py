"""Adapter wrapping underlying skill registry or clustering engines to SkillIntelligenceService."""

from __future__ import annotations

from typing import Any

from harness.services.skill_clustering import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)
from harness.services.skill_graph.guard import AntiPatternGuard
from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    SkillCardDefinition,
    SkillExecutionGuidance,
)


class SkillIntelligenceAdapter:
    """Unified adapter wrapping any skill registry or clustering engine to SkillIntelligenceService."""

    def __init__(self, target: Any) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        if hasattr(self._target, "discover_all"):
            return self._target.discover_all(root_dir)
        if hasattr(self._target, "get_all"):
            return self._target.get_all()
        return []

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        if hasattr(self._target, "get_skill"):
            return self._target.get_skill(name)
        return None

    def get_topology(self, skill_name: str) -> Any:
        if hasattr(self._target, "get_topology"):
            return self._target.get_topology(skill_name)
        raise KeyError(
            f"Topology inspection not supported on target {type(self._target).__name__}"
        )

    def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        if hasattr(self._target, "get_prerequisite_closure"):
            return self._target.get_prerequisite_closure(skill_name)
        return []

    def export_html_brief(self, output_path: str | None = None) -> str:
        if hasattr(self._target, "export_html_brief"):
            return self._target.export_html_brief(output_path)
        from harness.services.skill_visualizer import SkillGraphVisualizer

        return SkillGraphVisualizer.render_html(self._target, output_path=output_path)

    def route_intent(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        if hasattr(self._target, "route_intent"):
            return self._target.route_intent(intent, top_k=top_k)
        return {
            "status": "ok",
            "intent": intent,
            "matches": [],
            "recommended_chain": [],
        }

    def get_chain(self, start_skill: str, target_skill: str, **kwargs: Any) -> Any:
        if hasattr(self._target, "get_chain"):
            return self._target.get_chain(start_skill, target_skill, **kwargs)
        from harness.services.skill_graph.models import SkillChainResult

        return SkillChainResult(
            status="no_path",
            start_skill=start_skill,
            target_skill=target_skill,
            chain=[],
            length=0,
        )

    def link_knowledge_vault(self, vault_dir: Any = ".harness/knowledge") -> int:
        if hasattr(self._target, "link_knowledge_vault"):
            return self._target.link_knowledge_vault(vault_dir)
        return 0

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None, **kwargs: Any
    ) -> tuple[bool, list[str]]:
        if hasattr(self._target, "evaluate_chain_feasibility"):
            return self._target.evaluate_chain_feasibility(
                chain, context=context, **kwargs
            )
        return True, []

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        if hasattr(self._target, "cluster_skills"):
            return self._target.cluster_skills(min_cluster_size=min_cluster_size)
        return []

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        if hasattr(self._target, "discover_emergent_capabilities"):
            return self._target.discover_emergent_capabilities(query=query)
        return []

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        if hasattr(self._target, "get_cross_cluster_bridges"):
            return self._target.get_cross_cluster_bridges()
        return []

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        if hasattr(self._target, "select_skills_for_task"):
            return self._target.select_skills_for_task(
                task, max_skills=max_skills, include_verifier=include_verifier
            )
        return SkillSelectionPlan(
            task=task,
            selected_skills=(),
            execution_pipeline=(),
            confidence=0.0,
        )

    def check_anti_patterns(
        self, skill_name: str, proposed_text: str
    ) -> list[AntiPatternViolation]:
        if hasattr(self._target, "check_anti_patterns"):
            return self._target.check_anti_patterns(skill_name, proposed_text)
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        return AntiPatternGuard.check_proposal(skill, proposed_text)

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        if hasattr(self._target, "intercept_action"):
            return self._target.intercept_action(
                action_name=action_name,
                action_input=action_input,
                active_skills=active_skills,
            )
        lookup = getattr(self._target, "get_skill", None)
        return AntiPatternGuard.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=lookup,
        )

    def evaluate_action_gate(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        if hasattr(self._target, "evaluate_action_gate"):
            return self._target.evaluate_action_gate(
                action_name=action_name,
                action_input=action_input,
                active_skills=active_skills,
            )
        lookup = getattr(self._target, "get_skill", None)
        return AntiPatternGuard.evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=lookup,
        )

    def compile_execution_guidance(
        self, task: str, max_skills: int = 4, include_verifier: bool = True
    ) -> SkillExecutionGuidance:
        if hasattr(self._target, "compile_execution_guidance"):
            return self._target.compile_execution_guidance(
                task, max_skills=max_skills, include_verifier=include_verifier
            )
        target_skills: list[str] = []
        if hasattr(self._target, "select_skills_for_task"):
            try:
                plan = self._target.select_skills_for_task(
                    task, max_skills=max_skills, include_verifier=include_verifier
                )
                if plan and getattr(plan, "execution_pipeline", None):
                    target_skills = list(plan.execution_pipeline)
            except Exception:
                pass
        if not target_skills and hasattr(self._target, "route_intent"):
            try:
                res = self._target.route_intent(task, top_k=max_skills)
                if isinstance(res, dict):
                    matches = res.get("matches") or []
                    for m in matches:
                        s_name = m.get("skill_name") or m.get("name")
                        if s_name:
                            target_skills.append(s_name)
            except Exception:
                pass

        stages: list[dict[str, Any]] = []
        anti_patterns: list[dict[str, Any]] = []
        if hasattr(self._target, "get_skill"):
            for s_name in target_skills:
                s_obj = self._target.get_skill(s_name)
                if s_obj:
                    for st in getattr(s_obj, "stages", []) or []:
                        stages.append(
                            {
                                "skill": s_obj.name,
                                "stage_num": getattr(st, "stage_num", 1),
                                "name": getattr(st, "name", ""),
                                "completion_gate": getattr(st, "completion_gate", ""),
                            }
                        )
                    for ap in getattr(s_obj, "anti_patterns", []) or []:
                        anti_patterns.append(
                            {
                                "skill": s_obj.name,
                                "anti_pattern": getattr(ap, "name", ""),
                                "symptom": getattr(ap, "symptom", ""),
                                "remedy": getattr(ap, "remedy", ""),
                            }
                        )

        return SkillExecutionGuidance(
            task=task,
            selected_skills=tuple(target_skills),
            execution_pipeline=tuple(target_skills),
            confidence=0.85 if target_skills else 0.0,
            stages=tuple(stages),
            active_anti_patterns=tuple(anti_patterns),
        )


__all__ = ["SkillIntelligenceAdapter"]
