"""Skill Knowledge Graph & Registry service protocol, typed models, and ServiceKey.

Provides an authoritative, in-tree built-in implementation for workspace skill discovery,
caching, topological BFS chaining, intent routing, and visual brief generation.
"""

from __future__ import annotations

import ast
import collections
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.graph import DependencyGraph, GraphCycleError
from harness.plugins.base import HarnessPlugin
from harness.services.skill_clustering import (
    SKILL_CLUSTERING_KEY,
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillClusteringService,
    SkillSelectionPlan,
)

logger = structlog.get_logger()


@dataclass(slots=True, frozen=True)
class SkillExecutionGuidance:
    """Slotted and frozen execution guidance plan synthesized from skill graph (Rule 12 & Rule 43)."""

    task: str
    selected_skills: tuple[str, ...] = field(default_factory=tuple)
    execution_pipeline: tuple[str, ...] = field(default_factory=tuple)
    stages: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    active_anti_patterns: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        assert isinstance(self.task, str), "task must be a string"

    @property
    def should_inject(self) -> bool:
        """Whether this guidance plan has sufficient confidence and pipeline steps for injection."""
        return self.confidence > 0.20 and len(self.execution_pipeline) > 0

    def format_system_prompt_block(self) -> str:
        """Render formatted system prompt Markdown block for ReAct / autonomous agent context injection."""
        if not self.should_inject:
            return ""
        lines = [
            "\n\n## Active Skill Knowledge Guidance",
            f"Recommended Pipeline: {' -> '.join(self.execution_pipeline)}",
        ]
        if self.stages:
            lines.append("Key Stage Gates:")
            for st in self.stages[:4]:
                gate = st.get("completion_gate", "")
                skill_name = st.get("skill", "")
                stage_name = st.get("name", "")
                lines.append(f" - [{skill_name}] {stage_name}: {gate}")
        if self.active_anti_patterns:
            lines.append("Guarded Anti-Patterns:")
            for ap in self.active_anti_patterns[:3]:
                ap_name = ap.get("anti_pattern", "")
                skill_name = ap.get("skill", "")
                lines.append(f" - {ap_name} ({skill_name})")
        return "\n".join(lines)

    def inject_into_message(self, message: Any) -> Any:
        """Inject execution guidance into an LLMMessage system prompt cleanly without caller string munging."""
        block = self.format_system_prompt_block()
        if not block:
            return message
        if hasattr(message, "content"):
            from harness.services.llm import LLMMessage

            return LLMMessage(
                role=getattr(message, "role", "system"),
                content=message.content + block,
            )
        return message



class SkillStageDefinition(BaseModel):
    """Execution stage within an agent skill."""

    stage_num: int = Field(..., description="Stage sequence number (1-indexed)")
    name: str = Field(..., description="Stage title")
    completion_gate: str = Field(default="", description="Crisp completion criterion")
    objective: str = Field(default="", description="Stage objective summary")
    primary_artifact: str = Field(
        default="", description="Artifact produced by this stage"
    )

    @property
    def title(self) -> str:
        """Alias for name."""
        return self.name


class SkillAntiPatternDefinition(BaseModel):
    """Guarded failure mode within a skill."""

    name: str = Field(..., description="Anti-pattern identifier")
    symptom: str = Field(default="", description="Telltale failure symptom")
    remedy: str = Field(default="", description="Prescribed corrective pattern")

    @property
    def description(self) -> str:
        """Alias for symptom."""
        return self.symptom

    @property
    def mitigation(self) -> str:
        """Alias for remedy."""
        return self.remedy


class AntiPatternViolation(BaseModel):
    """Identified anti-pattern violation within an execution proposal."""

    skill_name: str = Field(
        ..., description="Skill declaring the violated anti-pattern"
    )
    anti_pattern: str = Field(..., description="Anti-pattern name")
    symptom: str = Field(default="", description="Declared failure symptom")
    remedy: str = Field(default="", description="Prescribed corrective action")
    matched_phrase: str = Field(
        default="", description="Phrase or token triggering the violation"
    )


class InvariantViolation(BaseModel):
    """Identified invariant violation within an execution proposal."""

    skill_name: str = Field(
        ..., description="Skill declaring the violated invariant"
    )
    rule: str = Field(..., description="Invariant rule description or assertion")
    matched_phrase: str = Field(
        default="", description="Phrase or token triggering the violation"
    )
    is_blocking: bool = Field(
        default=True, description="Whether violation blocks execution"
    )
    remedy: str = Field(
        default="Adhere strictly to the skill invariant rule",
        description="Prescribed corrective action",
    )

    @property
    def anti_pattern(self) -> str:
        """Alias for anti_pattern to provide unified polymorphism with AntiPatternViolation."""
        return f"Invariant Violation: {self.rule}"

    @property
    def symptom(self) -> str:
        """Alias for symptom."""
        return f"Violation of mandatory invariant: {self.rule}"


@dataclass(slots=True, frozen=True)
class ActionGateResult:
    """Slotted and frozen action gate evaluation result (Rule 12)."""

    action_name: str
    is_blocked: bool = False
    violations: tuple[Any, ...] = field(default_factory=tuple)
    observation: dict[str, Any] = field(default_factory=dict)

    def to_observation(self) -> dict[str, Any]:
        """Return the actionable ReAct observation dictionary for in-flight self-repair."""
        return dict(self.observation) if self.observation else {"status": "ok"}


class AntiPatternGuard:
    """Active runtime interceptor evaluating proposed agent actions against skill anti-patterns."""

    @classmethod
    def evaluate_action(
        cls,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
        skill_lookup: Any = None,
    ) -> list[AntiPatternViolation]:
        """Authoritative action evaluator checking proposed tool calls and arguments.

        Performs:
        1. Parameter flattening across strings, dicts, and nested collections.
        2. AST syntax tree scanning for blocked calls (eval, exec, input, __import__) in codeblocks or raw arguments.
        3. Fallback regex analysis for direct invocation patterns.
        4. Active skill anti-pattern symptom and keyword detection.
        """
        violations: list[AntiPatternViolation] = []

        # 1. Collect all textual content from action_name and action_input
        text_parts: list[str] = [action_name]
        for val in action_input.values():
            if isinstance(val, str):
                text_parts.append(val)
            elif isinstance(val, (dict, list)):
                try:
                    text_parts.append(json.dumps(val))
                except Exception:
                    text_parts.append(str(val))
        combined_text = "\n".join(text_parts)

        # 2. Blocked AST call checks (eval, exec, input, __import__)
        blocked_calls = {"eval", "exec", "input", "__import__"}
        code_blocks = re.findall(
            r"```(?:python)?\s*\n(.*?)\n```", combined_text, re.DOTALL
        )
        if not code_blocks:
            code_blocks = [combined_text]

        system_guard_name = active_skills[0] if active_skills else "system_guard"

        for block in code_blocks:
            try:
                tree = ast.parse(block)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func_name = None
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        if func_name and func_name in blocked_calls:
                            violations.append(
                                AntiPatternViolation(
                                    skill_name=system_guard_name,
                                    anti_pattern=f"Blocked Call: {func_name}()",
                                    symptom=f"Direct call to {func_name}() detected in proposed action parameters",
                                    remedy="Use sandboxed execution or approved kernel tools instead",
                                    matched_phrase=f"{func_name}()",
                                )
                            )
            except Exception:
                pass

            # Fallback regex search for direct blocked call patterns (eval(...) etc.)
            for call in blocked_calls:
                pattern = rf"(?:^|[^\w.]){re.escape(call)}\s*\("
                if re.search(pattern, block):
                    match_already_found = any(call in v.anti_pattern for v in violations)
                    if not match_already_found:
                        violations.append(
                            AntiPatternViolation(
                                skill_name=system_guard_name,
                                anti_pattern=f"Blocked Call: {call}()",
                                symptom=f"Direct invocation of {call}() detected in action input",
                                remedy="Use sandboxed execution or approved kernel tools instead",
                                matched_phrase=f"{call}()",
                            )
                        )

        # 3. Check declared anti-patterns and invariants for active skills
        if active_skills and skill_lookup:
            for skill_name in active_skills:
                skill = (
                    skill_lookup(skill_name)
                    if callable(skill_lookup)
                    else (
                        skill_lookup.get(skill_name)
                        if isinstance(skill_lookup, dict)
                        else None
                    )
                )
                if skill:
                    violations.extend(cls.check_proposal(skill, combined_text))
                    violations.extend(
                        cls.check_invariants(
                            skill=skill,
                            action_name=action_name,
                            action_input=action_input,
                            combined_text=combined_text,
                        )
                    )

        return violations

    @classmethod
    def evaluate_action_gate(
        cls,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
        skill_lookup: Any = None,
    ) -> ActionGateResult:
        """Authoritative action gate evaluation returning a slotted ActionGateResult."""
        violations = cls.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=skill_lookup,
        )
        if not violations:
            return ActionGateResult(
                action_name=action_name,
                is_blocked=False,
                violations=(),
                observation={"status": "ok"},
            )
        obs = cls.format_self_repair_observation(violations)
        return ActionGateResult(
            action_name=action_name,
            is_blocked=True,
            violations=tuple(violations),
            observation=obs,
        )

    @classmethod
    def check_invariants(
        cls,
        skill: SkillCardDefinition,
        action_name: str,
        action_input: dict[str, Any],
        combined_text: str,
    ) -> list[InvariantViolation]:
        """Scan proposed action and input against declared mandatory invariants for a skill."""
        violations: list[InvariantViolation] = []
        text_lower = combined_text.lower()
        negation_markers = ("avoid", "do not", "don't", "prevent", "never", "without")

        for inv in getattr(skill, "invariants", []) or []:
            inv_rule = getattr(inv, "rule", "") or ""
            if not inv_rule:
                continue
            inv_lower = inv_rule.lower()

            # Invariant: Artifact Metadata Restricted (Rule 31)
            if (
                "artifact metadata" in inv_lower
                and ("restricted" in inv_lower or "only accepts" in inv_lower)
                and action_name in ("write_to_file", "write_file", "create_file")
                and (
                    "artifactmetadata" in text_lower
                    or any("artifactmetadata" in str(k).lower() for k in action_input)
                )
            ):
                target_path = str(
                    action_input.get("target_file")
                    or action_input.get("TargetFile")
                    or action_input.get("path")
                    or action_input.get("file_path")
                    or ""
                ).replace("\\", "/")
                if target_path and not ("brain" in target_path or ".gemini" in target_path or "artifact" in target_path):
                    violations.append(
                        InvariantViolation(
                            skill_name=skill.name,
                            rule=inv_rule,
                            matched_phrase="ArtifactMetadata on workspace file",
                            is_blocking=getattr(inv, "is_blocking", True),
                            remedy="Omit ArtifactMetadata when writing files outside the artifact directory",
                        )
                    )

            # Invariant: Scratch File Execution over Inline -c Strings (Rule 29)
            if (
                ("scratch file execution" in inv_lower or "inline -c" in inv_lower)
                and "never" in inv_lower
                and (
                    action_name in ("run_command", "bash", "execute_command")
                    or "command" in action_input
                    or "CommandLine" in action_input
                )
            ):
                cmd_val = str(action_input.get("CommandLine") or action_input.get("command") or combined_text)
                if "python -c" in cmd_val or 'python -c "' in cmd_val or "python -c '" in cmd_val:
                    violations.append(
                        InvariantViolation(
                            skill_name=skill.name,
                            rule=inv_rule,
                            matched_phrase="python -c inline string",
                            is_blocking=getattr(inv, "is_blocking", True),
                            remedy="Write logic to a scratch script and execute via python <path>",
                        )
                    )

            # Invariant: General prohibited pattern assertion
            prohibit_markers = ("never ", "do not ", "prohibit ", "prohibits ", "disallow ", "disallows ")
            for marker in prohibit_markers:
                if marker in inv_lower:
                    prohibited_clause = inv_lower.split(marker, 1)[1].split(".")[0].split(",")[0].strip()
                    tokens = [
                        tok for tok in re.findall(r"[\w-]+", prohibited_clause)
                        if len(tok) >= 4 and tok not in ("allowed", "permitted", "using", "when", "with", "than", "that", "this")
                    ]
                    if tokens and all(t in text_lower for t in tokens):
                        min_idx = min(text_lower.find(t) for t in tokens if text_lower.find(t) != -1)
                        window = text_lower[max(0, min_idx - 50) : min_idx]
                        if not any(neg in window for neg in negation_markers):
                            violations.append(
                                InvariantViolation(
                                    skill_name=skill.name,
                                    rule=inv_rule,
                                    matched_phrase=" ".join(tokens),
                                    is_blocking=getattr(inv, "is_blocking", True),
                                    remedy=f"Comply strictly with invariant: {inv_rule}",
                                )
                            )
                    break

        return violations

    @classmethod
    def _check_code_ast(
        cls, code_block: str, skill: SkillCardDefinition
    ) -> list[AntiPatternViolation]:
        """Inspect Python code blocks for security-critical anti-pattern call invocations."""
        violations: list[AntiPatternViolation] = []
        try:
            tree = ast.parse(code_block)
        except Exception:
            return violations

        blocked_calls = {"eval", "exec", "input", "__import__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name and func_name in blocked_calls:
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill.name,
                            anti_pattern=f"Blocked Call: {func_name}()",
                            symptom=f"Direct call to {func_name}() detected in proposed code block",
                            remedy="Use sandboxed execution or approved kernel tools instead",
                            matched_phrase=f"{func_name}()",
                        )
                    )
        return violations

    @classmethod
    def format_self_repair_observation(
        cls, violations: list[Any]
    ) -> dict[str, Any]:
        """Format violations into an actionable ReAct observation dictionary for in-flight self-repair."""
        if not violations:
            return {"status": "ok"}
        v = violations[0]
        if isinstance(v, InvariantViolation) or hasattr(v, "is_blocking"):
            return {
                "status": "error",
                "invariant_violation": f"{getattr(v, 'rule', '')} ({getattr(v, 'skill_name', '')})",
                "rule": getattr(v, "rule", ""),
                "is_blocking": getattr(v, "is_blocking", True),
                "prescribed_remedy": getattr(v, "remedy", "Adhere strictly to the skill invariant rule"),
                "matched_phrase": getattr(v, "matched_phrase", ""),
                "corrective_action_required": True,
            }
        return {
            "status": "error",
            "anti_pattern_violation": f"{v.anti_pattern} ({v.skill_name})",
            "symptom": v.symptom,
            "prescribed_remedy": v.remedy,
            "matched_phrase": v.matched_phrase,
            "corrective_action_required": True,
        }

    @classmethod
    def check_proposal(
        cls,
        skill: SkillCardDefinition,
        proposed_action_or_plan: str,
    ) -> list[AntiPatternViolation]:
        """Scan proposed plan or tool arguments for symptoms of declared anti-patterns."""
        violations: list[AntiPatternViolation] = []
        text_lower = proposed_action_or_plan.lower()
        negation_markers = ("avoid", "do not", "don't", "prevent", "never", "without")

        # AST analysis on fenced code blocks
        code_blocks = re.findall(
            r"```(?:python)?\s*\n(.*?)\n```", proposed_action_or_plan, re.DOTALL
        )
        for block in code_blocks:
            violations.extend(cls._check_code_ast(block, skill))

        for ap in skill.anti_patterns:
            ap_name_lower = ap.name.lower()
            ap_tokens = [
                tok.lower() for tok in re.findall(r"\w+", ap.name) if len(tok) > 3
            ]

            if ap_name_lower in text_lower:
                match_idx = text_lower.find(ap_name_lower)
                window = text_lower[max(0, match_idx - 50) : match_idx]
                if not any(marker in window for marker in negation_markers):
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill.name,
                            anti_pattern=ap.name,
                            symptom=ap.symptom,
                            remedy=ap.remedy,
                            matched_phrase=ap.name,
                        )
                    )
            elif ap_tokens and all(t in text_lower for t in ap_tokens):
                min_idx = min(
                    text_lower.find(t) for t in ap_tokens if text_lower.find(t) != -1
                )
                window = text_lower[max(0, min_idx - 50) : min_idx]
                if not any(marker in window for marker in negation_markers):
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill.name,
                            anti_pattern=ap.name,
                            symptom=ap.symptom,
                            remedy=ap.remedy,
                            matched_phrase=" ".join(ap_tokens),
                        )
                    )

        return violations


class SkillInvariantDefinition(BaseModel):
    """Guarded non-negotiable invariant rule within a skill."""

    rule: str = Field(..., description="Invariant rule description or assertion")
    is_blocking: bool = Field(
        default=True, description="Whether violation blocks execution"
    )


class SkillCardDefinition(BaseModel):
    """Parsed and validated Skill Card model."""

    name: str = Field(..., description="Skill kebab-case identifier")
    category: str = Field(default="general", description="Domain classification")
    invocation: str = Field(
        default="", description="Command / trigger format e.g. /deepen-architecture"
    )
    triggers: list[str] = Field(
        default_factory=list, description="Natural language trigger phrases"
    )
    version: str = Field(default="1.0.0", description="Semantic version")
    target: str = Field(default="", description="Operational target summary")
    stages: list[SkillStageDefinition] = Field(
        default_factory=list, description="Execution progression"
    )
    anti_patterns: list[SkillAntiPatternDefinition] = Field(
        default_factory=list, description="Guarded anti-patterns"
    )
    invariants: list[SkillInvariantDefinition] = Field(
        default_factory=list, description="Guarded invariants"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Referenced peer skills"
    )
    knowledge_items: list[str] = Field(
        default_factory=list,
        description="Linked Knowledge Item IDs from Knowledge Vault",
    )
    services: list[str] = Field(
        default_factory=list, description="Required micro-kernel ServiceKey identifiers"
    )
    tools: list[str] = Field(default_factory=list, description="Required tool names")
    card_path: str = Field(default="", description="Path to companion CARD.md")
    skill_path: str = Field(default="", description="Path to authoritative SKILL.md")

    @property
    def references(self) -> list[str]:
        """Alias for dependencies to provide model interop."""
        return self.dependencies

    @property
    def description(self) -> str:
        """Alias for target to provide model interop."""
        return self.target


class EdgeType(str, Enum):
    """Semantic relationship types between skills and graph entities."""

    PRECEDES = "PRECEDES"
    REQUIRES = "REQUIRES"
    MITIGATES = "MITIGATES"
    BELONGS_TO = "BELONGS_TO"
    MANDATES = "MANDATES"
    ACTIVATES = "ACTIVATES"
    COMPLEMENTS = "COMPLEMENTS"


class SkillEdge(BaseModel):
    """Directed relation between two nodes in the skill knowledge graph."""

    source: str = Field(..., description="Source node identifier")
    target: str = Field(..., description="Target node identifier")
    relation: EdgeType = Field(..., description="Semantic edge type")
    weight: float = Field(1.0, description="Graph edge traversal weight")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional relation metadata"
    )


class SkillTopologyReport(BaseModel):
    """Topological inspection report for a single skill."""

    skill: SkillCardDefinition
    prerequisites: list[str] = Field(
        default_factory=list, description="Upstream skills required"
    )
    downstream_handoffs: list[str] = Field(
        default_factory=list, description="Downstream skills enabled"
    )
    complements: list[str] = Field(
        default_factory=list, description="Complementary companion skills"
    )
    mitigated_anti_patterns: list[str] = Field(
        default_factory=list, description="Failure modes mitigated"
    )


class SkillChainResult(BaseModel):
    """Topological execution chain between skills."""

    status: str = Field(default="ok", description="ok or no_path")
    start_skill: str = Field(..., description="Origin skill")
    target_skill: str = Field(..., description="Destination skill")
    chain: list[str] = Field(default_factory=list, description="Ordered skill names")
    length: int = Field(default=0, description="Step count")


# Backward-compatible model aliases for plugins, swarms, and tests (Rule 49 & Deepening Seam)
SkillNode = SkillCardDefinition
StageNode = SkillStageDefinition
AntiPatternNode = SkillAntiPatternDefinition
InvariantNode = SkillInvariantDefinition


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

# Canonical pipeline precedence pairs (single source of truth for graph routing and synthetic DAG edges)
CANONICAL_PIPELINE_PRECEDENCE: list[tuple[str, str]] = [
    ("structured-data-scout", "data-topology-mapper"),
    ("data-topology-mapper", "epistemic-isnad-audit"),
    ("epistemic-isnad-audit", "questio-reflection"),
    ("codebase-design", "deepen-architecture"),
    ("questio-reflection", "deepen-architecture"),
    ("crafting-skills", "questio-reflection"),
    ("repo-reader", "repo-to-plugin-forge"),
    ("repo-to-plugin-forge", "deepen-architecture"),
    ("mind-reader", "repo-to-plugin-forge"),
    ("mind-reader", "harness-reflector"),
    ("deepen-architecture", "crafting-skills"),
]

# ============================================================================
# Authoritative Built-in Skill Registry Implementation
# ============================================================================


class BuiltinSkillRegistryService(SkillIntelligenceService):
    """Authoritative in-memory caching Skill Registry and Knowledge Graph engine.

    Parses SKILL.md and CARD.md specifications, builds directed dependency DAGs,
    calculates BFS shortest execution chains, and performs semantic token routing.
    """

    def __init__(self, default_root: str = ".") -> None:
        self._default_root = default_root
        self._skills_cache: dict[str, SkillCardDefinition] = {}
        self._adjacency: dict[str, set[str]] = collections.defaultdict(set)
        self._synthetic_adjacency: dict[str, set[str]] = collections.defaultdict(set)
        self._categories: set[str] = set()
        self._anti_pattern_map: dict[str, list[SkillAntiPatternDefinition]] = (
            collections.defaultdict(list)
        )
        self._edges: list[SkillEdge] = []
        self._edge_keys: set[tuple[str, str, EdgeType]] = set()
        self._adj_out: dict[str, list[SkillEdge]] = collections.defaultdict(list)
        self._adj_in: dict[str, list[SkillEdge]] = collections.defaultdict(list)
        self._last_scan_time: float = 0.0
        self._clustering_engine: Any = None
        self._invalidation_listeners: list[Any] = []
        self._is_invalidating: bool = False

    @property
    def edges(self) -> list[SkillEdge]:
        """All directed relationship edges in the skill knowledge graph."""
        self._ensure_scanned(self._default_root)
        return list(self._edges)

    def _add_edge(
        self, source: str, target: str, relation: EdgeType, weight: float = 1.0
    ) -> None:
        """Append directed edge and update bidirectional adjacency indices in O(1) time."""
        edge_key = (source, target, relation)
        if edge_key in self._edge_keys:
            return
        self._edge_keys.add(edge_key)
        edge = SkillEdge(source=source, target=target, relation=relation, weight=weight)
        self._edges.append(edge)
        self._adj_out[source].append(edge)
        self._adj_in[target].append(edge)

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        """Discover and parse all skill cards across .agents/skills, plugins/, and skills/."""
        self._ensure_scanned(root_dir)
        return list(self._skills_cache.values())

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        """Retrieve a skill definition by kebab-case name."""
        self._ensure_scanned(self._default_root)
        clean_name = name.strip().lower().replace("_", "-")
        return self._skills_cache.get(clean_name)

    def get_nodes(self) -> dict[str, SkillCardDefinition]:
        """Retrieve copy of registered skill nodes mapping."""
        self._ensure_scanned(self._default_root)
        return dict(self._skills_cache)

    def get_categories(self) -> set[str]:
        """Retrieve copy of registered categories set."""
        self._ensure_scanned(self._default_root)
        return set(self._categories)

    def get_outgoing_edges(self, skill_name: str) -> list[SkillEdge]:
        """Retrieve outgoing directed edges from a skill node."""
        self._ensure_scanned(self._default_root)
        clean_name = skill_name.strip().lower().replace("_", "-")
        return list(self._adj_out.get(clean_name, []))

    def get_incoming_edges(self, skill_name: str) -> list[SkillEdge]:
        """Retrieve incoming directed edges to a skill node."""
        self._ensure_scanned(self._default_root)
        clean_name = skill_name.strip().lower().replace("_", "-")
        return list(self._adj_in.get(clean_name, []))

    def check_anti_patterns(
        self, skill_name: str, proposed_text: str
    ) -> list[AntiPatternViolation]:
        """Verify proposed action or text against anti-patterns for a given skill."""
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
        """Intercept proposed tool invocation and parameters against anti-patterns and blocked AST calls."""
        self._ensure_scanned(self._default_root)
        return AntiPatternGuard.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=self.get_skill,
        )

    def evaluate_action_gate(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        """Evaluate proposed tool invocation and parameters against anti-patterns and blocked AST calls."""
        self._ensure_scanned(self._default_root)
        return AntiPatternGuard.evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=self.get_skill,
        )

    def compile_execution_guidance(
        self, task: str, max_skills: int = 4, include_verifier: bool = True
    ) -> SkillExecutionGuidance:
        """Compile an end-to-end execution guidance plan for an agent task with multi-tier fallback."""
        self._ensure_scanned(self._default_root)
        plan = self.select_skills_for_task(
            task, max_skills=max_skills, include_verifier=include_verifier
        )
        selected_skills = list(getattr(plan, "selected_skills", []) or [])
        execution_pipeline = list(getattr(plan, "execution_pipeline", []) or [])
        stages = list(getattr(plan, "stages", []) or [])
        anti_patterns = list(getattr(plan, "active_anti_patterns", []) or [])
        confidence = float(getattr(plan, "confidence", 0.0) or 0.0)

        # Tier 3 Fallback: If clustering yielded low confidence (<0.20) or empty pipeline,
        # fallback to semantic intent routing + topological BFS chaining
        if confidence < 0.20 or not execution_pipeline:
            routed = self.route_intent(task, top_k=max_skills)
            matches = routed.get("matches", [])
            recommended_chain = routed.get("recommended_chain", [])
            if matches:
                top_skill = matches[0]["skill_name"]
                if top_skill not in selected_skills:
                    selected_skills = [top_skill]
                confidence = max(confidence, float(matches[0].get("confidence", 0.35)))
                if recommended_chain:
                    execution_pipeline = list(recommended_chain)
                else:
                    execution_pipeline = [top_skill]
                # Attach tail verifier if requested
                if include_verifier:
                    verifier = "adversarial-agent-verifier"
                    if (
                        verifier in self._skills_cache
                        and verifier not in execution_pipeline
                    ):
                        execution_pipeline.append(verifier)
                        if verifier not in selected_skills:
                            selected_skills.append(verifier)
                # Populate stages and anti-patterns from selected skills
                stages = []
                anti_patterns = []
                for s_name in execution_pipeline:
                    s_obj = self.get_skill(s_name)
                    if s_obj:
                        for st in s_obj.stages:
                            stages.append(
                                {
                                    "skill": s_obj.name,
                                    "stage_num": st.stage_num,
                                    "name": st.name,
                                    "completion_gate": st.completion_gate,
                                }
                            )
                        for ap in s_obj.anti_patterns:
                            anti_patterns.append(
                                {
                                    "skill": s_obj.name,
                                    "anti_pattern": ap.name,
                                    "symptom": ap.symptom,
                                    "remedy": ap.remedy,
                                }
                            )

        return SkillExecutionGuidance(
            task=task,
            selected_skills=tuple(selected_skills),
            execution_pipeline=tuple(execution_pipeline),
            stages=tuple(stages),
            active_anti_patterns=tuple(anti_patterns),
            confidence=confidence,
        )

    def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        """Compute the full transitive prerequisite closure for a skill in topological execution order.

        Walks upstream through incoming PRECEDES (source PRECEDES target) and
        outgoing REQUIRES (target REQUIRES dependency) relations.
        """
        self._ensure_scanned(self._default_root)
        clean_name = skill_name.strip().lower().replace("_", "-")
        if clean_name not in self._skills_cache:
            return []

        queue: collections.deque[str] = collections.deque([clean_name])
        ancestors: set[str] = set()

        while queue:
            curr = queue.popleft()
            # Incoming PRECEDES: edge.source runs before curr
            for edge in self._adj_in.get(curr, []):
                if (
                    edge.relation == EdgeType.PRECEDES
                    and edge.source in self._skills_cache
                    and edge.source not in ancestors
                    and edge.source != clean_name
                ):
                    ancestors.add(edge.source)
                    queue.append(edge.source)
            # Outgoing REQUIRES: curr requires edge.target
            for edge in self._adj_out.get(curr, []):
                if (
                    edge.relation == EdgeType.REQUIRES
                    and edge.target in self._skills_cache
                    and edge.target not in ancestors
                    and edge.target != clean_name
                ):
                    ancestors.add(edge.target)
                    queue.append(edge.target)

        if not ancestors:
            return []

        # Topologically sort ancestors
        dag: DependencyGraph[str] = DependencyGraph()
        for anc in ancestors:
            dag.add_node(anc)

        for anc in ancestors:
            # Check dependencies among ancestors
            s_obj = self._skills_cache[anc]
            for dep in s_obj.dependencies:
                c_dep = dep.strip().lower().replace("_", "-").lstrip("/")
                if (
                    c_dep in ancestors
                    and c_dep != anc
                    and c_dep not in dag.transitive_dependents(anc)
                ):
                    dag.add_edge(from_node=c_dep, to_node=anc)

            # Check PRECEDES edges among ancestors
            for edge in self._adj_out.get(anc, []):
                if (
                    edge.relation == EdgeType.PRECEDES
                    and edge.target in ancestors
                    and edge.target != anc
                    and edge.target not in dag.transitive_dependents(anc)
                ):
                    dag.add_edge(from_node=anc, to_node=edge.target)

        try:
            sorted_order = dag.topological_sort()
            return [n for n in sorted_order if n in ancestors]
        except GraphCycleError:
            return sorted(ancestors)

    def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief synchronously."""
        from harness.services.skill_visualizer import SkillGraphVisualizer

        return SkillGraphVisualizer.render_html(self, output_path=output_path)

    def add_invalidation_listener(self, callback: Any) -> None:
        """Register a callback invoked when the skills cache is invalidated."""
        if callback not in self._invalidation_listeners:
            self._invalidation_listeners.append(callback)

    def remove_invalidation_listener(self, callback: Any) -> None:
        """Unregister an invalidation callback."""
        if callback in self._invalidation_listeners:
            self._invalidation_listeners.remove(callback)

    def invalidate_cache(self) -> None:
        """Invalidate scanned skills cache to force immediate re-scan on next query."""
        if getattr(self, "_is_invalidating", False):
            return
        self._is_invalidating = True
        try:
            self._last_scan_time = 0.0
            self._skills_cache.clear()
            self._categories.clear()
            self._adjacency.clear()
            self._synthetic_adjacency.clear()
            self._anti_pattern_map.clear()
            self._edges.clear()
            self._edge_keys.clear()
            self._adj_out.clear()
            self._adj_in.clear()
            self._clustering_engine = None
            for listener in list(self._invalidation_listeners):
                try:
                    listener()
                except Exception:
                    pass
        finally:
            self._is_invalidating = False

    def _get_clustering_engine(self) -> SkillClusteringEngine:
        self._ensure_scanned(self._default_root)
        if self._clustering_engine is None:
            self._clustering_engine = SkillClusteringEngine(
                self._skills_cache, registry=self
            )
        return self._clustering_engine

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Cluster workspace skills into functional capability domains."""
        return self._get_clustering_engine().cluster_skills(
            min_cluster_size=min_cluster_size
        )

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        """Discover novel macro-capabilities revealed by the graph clusters."""
        return self._get_clustering_engine().discover_emergent_capabilities(
            query=query
        )

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        return self._get_clustering_engine().get_cross_cluster_bridges()

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        """Select skills and generate an execution plan for an agent task."""
        return self._get_clustering_engine().select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )

    def _get_neighbors(
        self, node: str, *, include_synthetic: bool = False
    ) -> set[str]:
        """Retrieve adjacent nodes, optionally including synthetic precedence edges."""
        neighbors = set(self._adjacency.get(node, set()))
        if include_synthetic:
            neighbors.update(self._synthetic_adjacency.get(node, set()))
        return neighbors

    def evaluate_chain_feasibility(
        self,
        chain: list[str],
        context: Any = None,
        *,
        verify_prerequisites: bool = False,
    ) -> tuple[bool, list[str]]:
        """Check whether all declared service preconditions and prerequisite dependencies for a skill chain are satisfied."""
        self._ensure_scanned(self._default_root)
        missing_items: list[str] = []

        if verify_prerequisites and chain:
            chain_set = {s.strip().lower().replace("_", "-") for s in chain}
            for skill_name in chain:
                clean_name = skill_name.strip().lower().replace("_", "-")
                prereqs = self.get_prerequisite_closure(clean_name)
                for p in prereqs:
                    if p not in chain_set and p in self._skills_cache:
                        missing_items.append(f"prerequisite_missing:{clean_name}->{p}")

        if context is None:
            return len(missing_items) == 0, missing_items

        for skill_name in chain:
            skill = self.get_skill(skill_name)
            if not skill:
                continue
            if skill.services:
                for svc_name in skill.services:
                    from harness.kernel.context import ServiceKey

                    key: ServiceKey[Any] = ServiceKey(svc_name)
                    if hasattr(context, "has") and not context.has(key):
                        missing_items.append(f"{skill.name}:{svc_name}")

            if skill.tools and hasattr(context, "optional"):
                from harness.services.tools import TOOL_REGISTRY_KEY

                tool_reg = context.optional(TOOL_REGISTRY_KEY)
                if tool_reg is not None and hasattr(tool_reg, "get"):
                    for tool_name in skill.tools:
                        if not tool_reg.get(tool_name):
                            missing_items.append(
                                f"tool_missing:{skill.name}:{tool_name}"
                            )

        return len(missing_items) == 0, missing_items

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        """Inspect topological dependencies, upstream prerequisites, downstream handoffs, and anti-patterns."""
        self._ensure_scanned(self._default_root)
        clean_name = skill_name.strip().lower().replace("_", "-")
        skill = self._skills_cache.get(clean_name)
        if not skill:
            raise KeyError(f"Skill '{skill_name}' not found in registry.")

        prereqs: list[str] = []
        downstream: list[str] = []
        complements: list[str] = []
        mitigates: list[str] = []

        # Incoming edges:
        # edge.source PRECEDES clean_name -> edge.source runs before clean_name -> prerequisite
        # edge.source REQUIRES clean_name -> edge.source needs clean_name -> downstream dependent
        # edge.source COMPLEMENTS clean_name -> complementary
        for edge in self._adj_in.get(clean_name, []):
            if edge.source in self._skills_cache:
                if edge.relation == EdgeType.PRECEDES:
                    prereqs.append(edge.source)
                elif edge.relation == EdgeType.REQUIRES:
                    downstream.append(edge.source)
                elif edge.relation == EdgeType.COMPLEMENTS:
                    complements.append(edge.source)

        # Outgoing edges:
        # clean_name REQUIRES edge.target -> clean_name needs target -> target is prerequisite
        # clean_name PRECEDES edge.target -> clean_name runs before target -> target is downstream handoff
        # clean_name COMPLEMENTS edge.target -> target is complement
        # clean_name MITIGATES antipattern:... -> anti-pattern mitigated
        for edge in self._adj_out.get(clean_name, []):
            if edge.relation == EdgeType.REQUIRES and edge.target in self._skills_cache:
                prereqs.append(edge.target)
            elif (
                edge.relation == EdgeType.PRECEDES and edge.target in self._skills_cache
            ):
                downstream.append(edge.target)
            elif (
                edge.relation == EdgeType.COMPLEMENTS
                and edge.target in self._skills_cache
            ):
                complements.append(edge.target)
            elif edge.relation == EdgeType.MITIGATES:
                mitigates.append(edge.target.replace("antipattern:", ""))

        # Also ensure skill's direct anti-patterns are in mitigates
        for ap in skill.anti_patterns:
            if ap.name not in mitigates:
                mitigates.append(ap.name)

        return SkillTopologyReport(
            skill=skill,
            prerequisites=list(dict.fromkeys(prereqs)),
            downstream_handoffs=list(dict.fromkeys(downstream)),
            complements=list(dict.fromkeys(complements)),
            mitigated_anti_patterns=list(dict.fromkeys(mitigates)),
        )

    def route_intent(
        self, intent: str, top_k: int = 3, min_confidence: float = 0.20
    ) -> dict[str, Any]:
        """Route natural language task intent to candidate skills with confidence scores."""
        self._ensure_scanned(self._default_root)
        intent_lower = intent.lower().strip()
        intent_tokens = set(re.findall(r"\w+", intent_lower))

        # BM25-inspired term-frequency saturation and length normalization
        avg_tokens = 8.0
        n_tokens = max(1.0, float(len(intent_tokens)))
        len_norm = 0.75 + 0.25 * min(2.5, n_tokens / avg_tokens)

        # Character trigram overlap helper for vocabulary mismatch mitigation
        def _trigram_overlap(s1: str, s2: str) -> float:
            if len(s1) < 3 or len(s2) < 3:
                return 0.0
            tri1 = {s1[i : i + 3] for i in range(len(s1) - 2)}
            tri2 = {s2[i : i + 3] for i in range(len(s2) - 2)}
            if not tri1 or not tri2:
                return 0.0
            return len(tri1 & tri2) / min(len(tri1), len(tri2))

        matches: list[dict[str, Any]] = []

        for skill in self._skills_cache.values():
            score = 0.0
            matched_triggers: list[str] = []

            # Exact or partial name match
            if skill.name in intent_lower:
                score += 2.5
                matched_triggers.append(skill.name)

            # Slash command invocation match
            if skill.invocation and skill.invocation.lower() in intent_lower:
                score += 3.0
                matched_triggers.append(skill.invocation)

            # Trigger phrase match
            for trigger in skill.triggers:
                trig_lower = trigger.lower()
                if trig_lower in intent_lower:
                    score += 2.0
                    matched_triggers.append(trigger)
                else:
                    trig_tokens = set(re.findall(r"\w+", trig_lower))
                    overlap = intent_tokens.intersection(trig_tokens)
                    if overlap:
                        score += 0.5 * len(overlap)
                        matched_triggers.extend(list(overlap)[:2])

            # Description / target token overlap
            text_corpus = f"{skill.target} {skill.category}".lower()
            text_tokens = set(re.findall(r"\w+", text_corpus))
            text_overlap = intent_tokens.intersection(text_tokens)
            if text_overlap:
                score += 0.3 * len(text_overlap)

            # Character trigram overlap (asymmetric overlap for semantic/stemming resilience)
            tri_score = _trigram_overlap(intent_lower, text_corpus)
            if tri_score > 0.15:
                score += 1.2 * tri_score

            # Knowledge Item cross-link boost
            if skill.knowledge_items:
                for ki in skill.knowledge_items:
                    if (
                        ki.lower() in intent_lower
                        or ki.lower().replace("-", " ") in intent_lower
                    ):
                        score += 1.5
                        matched_triggers.append(ki)

            if score > 0.0:
                norm_score = score / (1.5 * len_norm + 1.0)
                confidence = min(0.98, max(0.20, norm_score / 2.2 + 0.25))
                if confidence >= min_confidence:
                    matches.append(
                        {
                            "skill_name": skill.name,
                            "category": skill.category,
                            "confidence": round(confidence, 3),
                            "target": skill.target,
                            "matched_triggers": list(dict.fromkeys(matched_triggers))[
                                :4
                            ],
                        }
                    )

        matches.sort(key=lambda m: float(m["confidence"]), reverse=True)
        top_matches = matches[:top_k]

        # Recommended execution chain
        recommended_chain: list[str] = []
        if len(top_matches) >= 2:
            s1, s2 = top_matches[0]["skill_name"], top_matches[1]["skill_name"]
            chain_res = self.get_chain(s1, s2, fallback_direct=False)
            if chain_res.status == "ok" and chain_res.chain:
                recommended_chain = chain_res.chain
            elif (
                abs(
                    float(top_matches[0]["confidence"])
                    - float(top_matches[1]["confidence"])
                )
                < 0.02
            ):
                # Disconnected tie: neither skill dominates and no reachability path exists
                recommended_chain = []
            else:
                recommended_chain = [s1]
        elif top_matches:
            recommended_chain = [top_matches[0]["skill_name"]]

        return {
            "status": "ok",
            "intent": intent,
            "matches": top_matches,
            "recommended_chain": recommended_chain,
            "total_indexed": len(self._skills_cache),
        }

    def get_chain(
        self,
        start_skill: str,
        target_skill: str,
        *,
        fallback_direct: bool = False,
        include_synthetic: bool = False,
    ) -> SkillChainResult:
        """Calculate the shortest directed execution path between two skills using BFS."""
        self._ensure_scanned(self._default_root)
        s_start = start_skill.strip().lower().replace("_", "-")
        s_target = target_skill.strip().lower().replace("_", "-")

        if s_start == s_target:
            return SkillChainResult(
                status="ok",
                start_skill=start_skill,
                target_skill=target_skill,
                chain=[s_start],
                length=1,
            )

        if s_start not in self._skills_cache or s_target not in self._skills_cache:
            if fallback_direct:
                return SkillChainResult(
                    status="ok",
                    start_skill=start_skill,
                    target_skill=target_skill,
                    chain=[s_start, s_target],
                    length=2,
                )
            return SkillChainResult(
                status="no_path",
                start_skill=start_skill,
                target_skill=target_skill,
                chain=[],
                length=0,
            )

        # BFS shortest path search
        queue: collections.deque[list[str]] = collections.deque([[s_start]])
        visited: set[str] = {s_start}

        while queue:
            path = queue.popleft()
            curr = path[-1]

            neighbors = self._get_neighbors(
                curr, include_synthetic=(include_synthetic or fallback_direct)
            )
            for neighbor in sorted(neighbors):
                if neighbor == s_target:
                    full_chain = path + [neighbor]
                    return SkillChainResult(
                        status="ok",
                        start_skill=start_skill,
                        target_skill=target_skill,
                        chain=full_chain,
                        length=len(full_chain),
                    )
                if neighbor not in visited and neighbor in self._skills_cache:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        if fallback_direct:
            return SkillChainResult(
                status="ok",
                start_skill=start_skill,
                target_skill=target_skill,
                chain=[s_start, s_target],
                length=2,
            )

        return SkillChainResult(
            status="no_path",
            start_skill=start_skill,
            target_skill=target_skill,
            chain=[],
            length=0,
        )

    def _ensure_scanned(self, root_dir: str) -> None:
        """Scan workspace directories if not yet populated or if 30s elapsed."""
        now = time.time()
        if self._skills_cache and (now - self._last_scan_time) < 30.0:
            return

        p = Path(root_dir).resolve()
        paths_to_scan = [
            p / ".agents" / "skills",
            p / "skills",
            p / "plugins",
        ]

        discovered: dict[str, SkillCardDefinition] = {}
        categories: set[str] = set()
        adjacency: dict[str, set[str]] = collections.defaultdict(set)

        ignored_parts = {
            ".venv",
            "venv",
            "venvs",
            ".git",
            "node_modules",
            "site-packages",
            "__pycache__",
        }

        for scan_dir in paths_to_scan:
            if not scan_dir.exists():
                continue
            for skill_file in scan_dir.rglob("SKILL.md"):
                # Guard against virtualenv and package directories
                parts = set(skill_file.parts)
                if any(part.lower() in ignored_parts for part in parts):
                    continue
                try:
                    card = self._parse_skill_directory(skill_file.parent)
                    if card and card.name not in discovered:
                        discovered[card.name] = card
                        categories.add(card.category)
                        for dep in card.dependencies:
                            clean_dep = (
                                dep.strip().lower().replace("_", "-").lstrip("/")
                            )
                            if clean_dep != card.name:
                                adjacency[card.name].add(clean_dep)
                except Exception as e:
                    logger.debug(
                        "Failed parsing skill directory",
                        path=str(skill_file.parent),
                        error=str(e),
                    )
                    continue

        # Known canonical pipeline precedence pairs (isolated into synthetic adjacency)
        synthetic_adj: dict[str, set[str]] = collections.defaultdict(set)
        for s1, s2 in CANONICAL_PIPELINE_PRECEDENCE:
            if s1 in discovered and s2 in discovered:
                synthetic_adj[s1].add(s2)
                adjacency[s1].add(s2)

        # Build bidirectional graph edges (BELONGS_TO, MITIGATES, REQUIRES, PRECEDES)
        self._edges.clear()
        self._edge_keys.clear()
        self._adj_out.clear()
        self._adj_in.clear()
        for card in discovered.values():
            self._add_edge(card.name, f"cat:{card.category}", EdgeType.BELONGS_TO)
            for ap in card.anti_patterns:
                self._add_edge(
                    card.name,
                    f"antipattern:{ap.name.lower().replace(' ', '-')}",
                    EdgeType.MITIGATES,
                )
            for dep in card.dependencies:
                clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
                if clean_dep != card.name:
                    self._add_edge(card.name, clean_dep, EdgeType.REQUIRES)

        for s1, s2 in CANONICAL_PIPELINE_PRECEDENCE:
            if s1 in discovered and s2 in discovered:
                self._add_edge(s1, s2, EdgeType.PRECEDES)

        self._skills_cache = discovered
        self._categories = categories
        self._adjacency = adjacency
        self._synthetic_adjacency = synthetic_adj
        self._last_scan_time = now

    def _parse_skill_directory(self, skill_dir: Path) -> SkillCardDefinition | None:
        """Parse SKILL.md and companion CARD.md from a skill directory via authoritative SkillCardParser."""
        from harness.services.skill_parser import SkillCardParser

        return SkillCardParser.parse_directory(skill_dir)

    def link_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        """Scan dual-file on-disk knowledge vault and link matching KIs to registered skills."""
        self._ensure_scanned(self._default_root)
        v_path = Path(vault_dir).resolve()
        if not v_path.exists() or not v_path.is_dir():
            return 0

        linked_count = 0
        for ki_dir in v_path.iterdir():
            if not ki_dir.is_dir():
                continue
            meta_path = ki_dir / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                ki_id = meta.get("id", ki_dir.name)
                raw_tags = meta.get("tags") or []
                tags = [
                    t.lower().replace("_", "-") for t in raw_tags if isinstance(t, str)
                ]
                title = (meta.get("title") or "").lower()

                for skill_name, skill in self._skills_cache.items():
                    s_tokens = set(skill_name.split("-"))
                    matched = False

                    # Exact skill name in tags or id
                    if (
                        skill_name in tags
                        or skill_name in ki_id.lower()
                        or skill_name.replace("-", "_") in ki_id.lower()
                        or any(tok in tags for tok in s_tokens if len(tok) > 3)
                        or any(tok in title for tok in s_tokens if len(tok) > 3)
                    ):
                        matched = True

                    if matched and ki_id not in skill.knowledge_items:
                        skill.knowledge_items.append(ki_id)
                        linked_count += 1
            except Exception as e:
                logger.debug(
                    "Failed processing knowledge vault item",
                    path=str(ki_dir),
                    error=str(e),
                )
                continue

        return linked_count


# ============================================================================
# Authoritative Built-in Skill Graph Async Implementation
# ============================================================================


class BuiltinSkillGraphService(SkillGraphService):
    """Async facade over BuiltinSkillRegistryService."""

    def __init__(self, registry: BuiltinSkillRegistryService | None = None) -> None:
        self._registry = registry or BuiltinSkillRegistryService()

    async def index(self, root_dir: str = ".") -> int:
        skills = self._registry.discover_all(root_dir)
        return len(skills)

    async def find_chain(
        self, start_skill: str, target_skill: str, *, fallback_direct: bool = False
    ) -> list[str]:
        res = self._registry.get_chain(
            start_skill, target_skill, fallback_direct=fallback_direct
        )
        return res.chain

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        return self._registry.route_intent(intent, top_k=top_k)

    async def get_topology(self, skill_name: str) -> dict[str, Any]:
        """Inspect topological dependencies, handoffs, and anti-patterns for a skill."""
        try:
            topo = self._registry.get_topology(skill_name)
            return {
                "status": "ok",
                "topology": topo.model_dump(),
            }
        except KeyError as e:
            return {
                "status": "error",
                "reason": str(e),
            }

    async def link_knowledge_vault(self, vault_dir: str = ".harness/knowledge") -> int:
        return self._registry.link_knowledge_vault(vault_dir)

    async def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        """Compute the full transitive prerequisite closure for a skill in topological execution order."""
        return self._registry.get_prerequisite_closure(skill_name)

    async def export_html_brief(self, output_path: str | None = None) -> str:
        """Export an interactive HTML visual brief by delegating to the authoritative registry."""
        return self._registry.export_html_brief(output_path=output_path)

    async def cluster_skills(self, min_cluster_size: int = 2) -> list[dict[str, Any]]:
        clusters = self._registry.cluster_skills(min_cluster_size=min_cluster_size)
        return [c.model_dump() for c in clusters]

    async def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[dict[str, Any]]:
        caps = self._registry.discover_emergent_capabilities(query=query)
        return [c.model_dump() for c in caps]

    async def get_cross_cluster_bridges(self) -> list[dict[str, Any]]:
        bridges = self._registry.get_cross_cluster_bridges()
        return [b.model_dump() for b in bridges]

    async def select_skills_for_task(
        self, task: str, max_skills: int = 5, include_verifier: bool = True
    ) -> dict[str, Any]:
        plan = self._registry.select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )
        return plan.model_dump()

    async def compile_execution_guidance(
        self, task: str, max_skills: int = 4, include_verifier: bool = True
    ) -> SkillExecutionGuidance:
        """Compile an end-to-end execution guidance plan for an agent task."""
        return self._registry.compile_execution_guidance(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        """Intercept proposed action and evaluate against active skill anti-patterns and AST security gates."""
        return self._registry.intercept_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
        )

    def evaluate_action_gate(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        """Evaluate proposed action against skill anti-patterns and AST gates, returning a slotted ActionGateResult."""
        return self._registry.evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
        )


# ============================================================================
# Built-in Harness Plugin Registration
# ============================================================================


class SkillRegistryPlugin(HarnessPlugin):
    """In-process Harness plugin providing BuiltinSkillRegistryService and BuiltinSkillGraphService."""

    name = "builtin.skill_registry"
    version = "1.0.0"
    description = "Authoritative workspace skill catalog, graph DAG indexer, and semantic intent router"
    trusted = True

    def __init__(self, root_dir: str = ".") -> None:
        self._registry = BuiltinSkillRegistryService(default_root=root_dir)
        self._graph = BuiltinSkillGraphService(registry=self._registry)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [
            SKILL_REGISTRY_KEY,
            SKILL_GRAPH_KEY,
            SKILL_CLUSTERING_KEY,
            SKILL_INTELLIGENCE_KEY,
        ]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SKILL_REGISTRY_KEY, self._registry)
        ctx.provide(SKILL_GRAPH_KEY, self._graph)
        ctx.provide(SKILL_CLUSTERING_KEY, self._registry)
        ctx.provide(SKILL_INTELLIGENCE_KEY, self._registry)
        try:
            from harness.events.bus import EVENT_BUS_KEY
            from harness.events.types import EventType

            bus = ctx.optional(EVENT_BUS_KEY)
            if bus:
                ctx.subscribe(EventType.FILE_MODIFIED, self._on_skill_file_changed)
                ctx.subscribe(EventType.FILE_CREATED, self._on_skill_file_changed)
                ctx.subscribe(EventType.FILE_DELETED, self._on_skill_file_changed)
        except Exception:
            pass

    def _on_skill_file_changed(self, event: Any) -> None:
        """Handle EventBus file change events by invalidating cache on skill/card modifications."""
        payload = getattr(event, "payload", {}) or {}
        path = str(payload.get("path", ""))
        if "SKILL.md" in path or "CARD.md" in path:
            self._registry.invalidate_cache()

    async def on_enable(self) -> None:
        self._registry.invalidate_cache()
        self._registry.discover_all()

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass


# ============================================================================
# Authoritative Global / Process-Scoped Factory Seams (Rule 49 & Seam Elevation)
# ============================================================================

_DEFAULT_REGISTRY_INSTANCE: BuiltinSkillRegistryService | None = None
_DEFAULT_GRAPH_INSTANCE: BuiltinSkillGraphService | None = None


def get_default_skill_registry(root_dir: str = ".") -> BuiltinSkillRegistryService:
    """Retrieve or initialize the process-level cached BuiltinSkillRegistryService."""
    global _DEFAULT_REGISTRY_INSTANCE
    resolved_root = str(Path(root_dir).resolve())
    if (
        _DEFAULT_REGISTRY_INSTANCE is None
        or str(Path(_DEFAULT_REGISTRY_INSTANCE._default_root).resolve())
        != resolved_root
    ):
        _DEFAULT_REGISTRY_INSTANCE = BuiltinSkillRegistryService(default_root=root_dir)
    return _DEFAULT_REGISTRY_INSTANCE


def get_default_skill_graph(root_dir: str = ".") -> BuiltinSkillGraphService:
    """Retrieve or initialize the process-level cached BuiltinSkillGraphService."""
    global _DEFAULT_GRAPH_INSTANCE
    reg = get_default_skill_registry(root_dir=root_dir)
    if _DEFAULT_GRAPH_INSTANCE is None or _DEFAULT_GRAPH_INSTANCE._registry is not reg:
        _DEFAULT_GRAPH_INSTANCE = BuiltinSkillGraphService(registry=reg)
    return _DEFAULT_GRAPH_INSTANCE


class SkillIntelligenceAdapter:
    """Non-invasive adapter wrapping a SkillRegistryService or partial service to satisfy SkillIntelligenceService."""

    def __init__(self, target: Any) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        return (
            self._target.discover_all(root_dir)
            if hasattr(self._target, "discover_all")
            else []
        )

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        return (
            self._target.get_skill(name) if hasattr(self._target, "get_skill") else None
        )

    def get_topology(self, skill_name: str) -> Any:
        return (
            self._target.get_topology(skill_name)
            if hasattr(self._target, "get_topology")
            else None
        )

    def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        return (
            self._target.get_prerequisite_closure(skill_name)
            if hasattr(self._target, "get_prerequisite_closure")
            else []
        )

    def export_html_brief(self, output_path: str | None = None) -> str:
        return (
            self._target.export_html_brief(output_path)
            if hasattr(self._target, "export_html_brief")
            else ""
        )

    def route_intent(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        return (
            self._target.route_intent(intent, top_k=top_k)
            if hasattr(self._target, "route_intent")
            else {"status": "ok", "matches": []}
        )

    def get_chain(self, start_skill: str, target_skill: str, **kwargs: Any) -> Any:
        return (
            self._target.get_chain(start_skill, target_skill, **kwargs)
            if hasattr(self._target, "get_chain")
            else None
        )

    def link_knowledge_vault(self, vault_dir: Any = ".harness/knowledge") -> int:
        return (
            self._target.link_knowledge_vault(vault_dir)
            if hasattr(self._target, "link_knowledge_vault")
            else 0
        )

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None
    ) -> tuple[bool, list[str]]:
        return (
            self._target.evaluate_chain_feasibility(chain, context)
            if hasattr(self._target, "evaluate_chain_feasibility")
            else (True, [])
        )

    def cluster_skills(self, min_cluster_size: int = 2) -> list[Any]:
        return (
            self._target.cluster_skills(min_cluster_size)
            if hasattr(self._target, "cluster_skills")
            else []
        )

    def discover_emergent_capabilities(self, query: str | None = None) -> list[Any]:
        return (
            self._target.discover_emergent_capabilities(query)
            if hasattr(self._target, "discover_emergent_capabilities")
            else []
        )

    def get_cross_cluster_bridges(self) -> list[Any]:
        return (
            self._target.get_cross_cluster_bridges()
            if hasattr(self._target, "get_cross_cluster_bridges")
            else []
        )

    def select_skills_for_task(
        self, task: str, max_skills: int = 5, include_verifier: bool = True
    ) -> Any:
        if hasattr(self._target, "select_skills_for_task"):
            return self._target.select_skills_for_task(
                task, max_skills=max_skills, include_verifier=include_verifier
            )
        return None

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        if hasattr(self._target, "intercept_action"):
            return self._target.intercept_action(action_name, action_input, active_skills)
        lookup = getattr(self._target, "get_skill", None)
        return AntiPatternGuard.evaluate_action(
            action_name, action_input, active_skills, skill_lookup=lookup
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


def resolve_skill_intelligence(
    context: Any = None, root_dir: str = "."
) -> SkillIntelligenceService:
    """Authoritative single-source factory seam to resolve SkillIntelligenceService (Rule 1.1).

    Resolves from active IoC container context by inspecting SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY, and SKILL_CLUSTERING_KEY in priority order, falling back to
    the process-level cached BuiltinSkillRegistryService singleton.
    """
    if context is not None and hasattr(context, "optional"):
        intel = context.optional(SKILL_INTELLIGENCE_KEY)
        if intel is not None:
            if isinstance(intel, SkillIntelligenceService):
                return intel
            return SkillIntelligenceAdapter(intel)
        reg = context.optional(SKILL_REGISTRY_KEY)
        if reg is not None:
            if isinstance(reg, SkillIntelligenceService):
                return reg
            return SkillIntelligenceAdapter(reg)
        from harness.services.skill_clustering import SKILL_CLUSTERING_KEY

        clust = context.optional(SKILL_CLUSTERING_KEY)
        if clust is not None:
            if isinstance(clust, SkillIntelligenceService):
                return clust
            return SkillIntelligenceAdapter(clust)

    return get_default_skill_registry(root_dir=root_dir)
