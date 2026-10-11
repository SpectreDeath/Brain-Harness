"""Anti-pattern action gating, execution guidance compilation, and HTML brief generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harness.services.skill_graph.guidance import (
    compile_execution_guidance_plan,
    export_html_brief as _export_html_brief,
)
from harness.services.skill_graph.guard import AntiPatternGuard
from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    SkillExecutionGuidance,
)
from harness.services.skill_graph.topology import compute_prerequisite_closure as _compute_prereqs

if TYPE_CHECKING:
    from harness.services.skill_graph.service.registry import BuiltinSkillRegistryService


class RegistryGatingMixin:
    """Anti-pattern guarding, action gating, guidance compilation, and visual brief export."""

    def check_anti_patterns(
        self: BuiltinSkillRegistryService, skill_name: str, proposed_text: str
    ) -> list[AntiPatternViolation]:
        skill = self.get_skill(skill_name)
        return AntiPatternGuard.check_proposal(skill, proposed_text) if skill else []

    def intercept_action(
        self: BuiltinSkillRegistryService,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        self._ensure_scanned(self._default_root)
        return AntiPatternGuard.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=self.get_skill,
        )

    def evaluate_action_gate(
        self: BuiltinSkillRegistryService,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        self._ensure_scanned(self._default_root)
        return AntiPatternGuard.evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=self.get_skill,
        )

    def compile_execution_guidance(
        self: BuiltinSkillRegistryService,
        task: str,
        max_skills: int = 4,
        include_verifier: bool = True,
    ) -> SkillExecutionGuidance:
        self._ensure_scanned(self._default_root)
        return compile_execution_guidance_plan(
            task=task,
            skills_cache=self._skills_cache,
            select_skills_fn=self.select_skills_for_task,
            route_intent_fn=self.route_intent,
            get_skill_fn=self.get_skill,
            max_skills=max_skills,
            include_verifier=include_verifier,
        )

    def get_prerequisite_closure(self: BuiltinSkillRegistryService, skill_name: str) -> list[str]:
        self._ensure_scanned(self._default_root)
        return _compute_prereqs(skill_name, self._skills_cache, self._adj_out, self._adj_in)

    def export_html_brief(self: BuiltinSkillRegistryService, output_path: str | None = None) -> str:
        return _export_html_brief(self, output_path=output_path)
