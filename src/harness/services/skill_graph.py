"""Skill Knowledge Graph & Registry service protocol, typed models, and ServiceKey.

Provides an authoritative, in-tree built-in implementation for workspace skill discovery,
caching, topological BFS chaining, intent routing, and visual brief generation.
"""

from __future__ import annotations

import ast
import collections
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


class SkillStageDefinition(BaseModel):
    """Execution stage within an agent skill."""

    stage_num: int = Field(..., description="Stage sequence number (1-indexed)")
    name: str = Field(..., description="Stage title")
    completion_gate: str = Field(default="", description="Crisp completion criterion")


class SkillAntiPatternDefinition(BaseModel):
    """Guarded failure mode within a skill."""

    name: str = Field(..., description="Anti-pattern identifier")
    symptom: str = Field(default="", description="Telltale failure symptom")
    remedy: str = Field(default="", description="Prescribed corrective pattern")


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


class AntiPatternGuard:
    """Active runtime interceptor evaluating proposed agent actions against skill anti-patterns."""

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
        cls, violations: list[AntiPatternViolation]
    ) -> dict[str, Any]:
        """Format violations into an actionable ReAct observation dictionary for in-flight self-repair."""
        if not violations:
            return {"status": "ok"}
        v = violations[0]
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


class SkillChainResult(BaseModel):
    """Topological execution chain between skills."""

    status: str = Field(default="ok", description="ok or no_path")
    start_skill: str = Field(..., description="Origin skill")
    target_skill: str = Field(..., description="Destination skill")
    chain: list[str] = Field(default_factory=list, description="Ordered skill names")
    length: int = Field(default=0, description="Step count")


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

    async def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief."""
        ...

    async def link_knowledge_vault(self, vault_dir: str = ".harness/knowledge") -> int:
        """Cross-link knowledge vault items to skills."""
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


SKILL_GRAPH_KEY: ServiceKey[SkillGraphService] = ServiceKey(
    "service.skill_knowledge_graph"
)
SKILL_REGISTRY_KEY: ServiceKey[SkillRegistryService] = ServiceKey(
    "service.skill_registry"
)


# ============================================================================
# Authoritative Built-in Skill Registry Implementation
# ============================================================================


class BuiltinSkillRegistryService(SkillRegistryService):
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
        self._last_scan_time: float = 0.0

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        """Discover and parse all skill cards across .agents/skills, plugins/, and skills/."""
        self._ensure_scanned(root_dir)
        return list(self._skills_cache.values())

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        """Retrieve a skill definition by kebab-case name."""
        self._ensure_scanned(self._default_root)
        clean_name = name.strip().lower().replace("_", "-")
        return self._skills_cache.get(clean_name)

    def check_anti_patterns(
        self, skill_name: str, proposed_text: str
    ) -> list[AntiPatternViolation]:
        """Verify proposed action or text against anti-patterns for a given skill."""
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        return AntiPatternGuard.check_proposal(skill, proposed_text)

    def invalidate_cache(self) -> None:
        """Invalidate scanned skills cache to force immediate re-scan on next query."""
        self._last_scan_time = 0.0
        self._skills_cache.clear()
        self._categories.clear()
        self._adjacency.clear()
        self._synthetic_adjacency.clear()
        self._anti_pattern_map.clear()

    def _get_neighbors(self, node: str, *, include_synthetic: bool = False) -> set[str]:
        """Retrieve adjacent nodes, optionally including synthetic precedence edges."""
        neighbors = set(self._adjacency.get(node, set()))
        if include_synthetic:
            neighbors.update(self._synthetic_adjacency.get(node, set()))
        return neighbors

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None
    ) -> tuple[bool, list[str]]:
        """Check whether all declared service preconditions for a skill chain are satisfied."""
        self._ensure_scanned(self._default_root)
        missing_services: list[str] = []
        if context is None:
            return True, []
        for skill_name in chain:
            skill = self.get_skill(skill_name)
            if not skill or not skill.services:
                continue
            for svc_name in skill.services:
                from harness.kernel.context import ServiceKey

                key: ServiceKey[Any] = ServiceKey(svc_name)
                if hasattr(context, "has") and not context.has(key):
                    missing_services.append(f"{skill_name}:{svc_name}")
        return len(missing_services) == 0, missing_services

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
                    if ki.lower() in intent_lower or ki.lower().replace("-", " ") in intent_lower:
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
            else:
                recommended_chain = []
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
        pipeline_pairs = [
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
        synthetic_adj: dict[str, set[str]] = collections.defaultdict(set)
        for s1, s2 in pipeline_pairs:
            if s1 in discovered and s2 in discovered:
                synthetic_adj[s1].add(s2)
                adjacency[s1].add(s2)

        self._skills_cache = discovered
        self._categories = categories
        self._adjacency = adjacency
        self._synthetic_adjacency = synthetic_adj
        self._last_scan_time = now

    def _parse_skill_directory(self, skill_dir: Path) -> SkillCardDefinition | None:
        """Parse SKILL.md and optional companion CARD.md from a skill directory.

        Delegates to the authoritative SkillCardParser when available, ensuring full
        ASCII metadata, blocking checklist invariants (Rule 37), and triggers are populated.
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists() and not (skill_dir / "CARD.md").exists():
            return None

        # Try authoritative AST parser first
        try:
            from plugins.memory_and_epistemics.skill_knowledge_graph.parser import (
                SkillCardParser,
            )

            node = SkillCardParser.parse_directory(skill_dir)
            if node is not None:
                return SkillCardDefinition(
                    name=node.name,
                    category=node.category,
                    invocation=node.invocation,
                    triggers=list(node.triggers),
                    version=node.version,
                    target=node.target or node.description,
                    stages=[
                        SkillStageDefinition(
                            stage_num=s.stage_num,
                            name=s.name,
                            completion_gate=s.completion_gate or s.objective,
                        )
                        for s in node.stages
                    ],
                    anti_patterns=[
                        SkillAntiPatternDefinition(
                            name=ap.name,
                            symptom=ap.description,
                            remedy=ap.mitigation or "Follow standard protocol",
                        )
                        for ap in node.anti_patterns
                    ],
                    invariants=[
                        SkillInvariantDefinition(
                            rule=inv.rule,
                            is_blocking=inv.is_blocking,
                        )
                        for inv in node.invariants
                    ],
                    dependencies=[
                        d
                        for d in list(dict.fromkeys(node.references))
                        if d != node.name
                    ],
                    knowledge_items=[],
                    services=[],
                    tools=[],
                    card_path=node.card_path,
                    skill_path=node.skill_path,
                )
        except Exception:
            pass

        # Fallback to local regex parsing if SkillCardParser unavailable
        if not skill_file.exists():
            return None

        content = skill_file.read_text(encoding="utf-8", errors="replace")

        # YAML Frontmatter
        name_match = re.search(r"^name:\s*([^\n]+)", content, re.MULTILINE)
        desc_match = re.search(r"^description:\s*([^\n]+)", content, re.MULTILINE)

        skill_name = name_match.group(1).strip() if name_match else skill_dir.name
        description = desc_match.group(1).strip() if desc_match else ""

        # Category and invocation defaults
        category = "general"
        invocation = f"/{skill_name}"
        triggers: list[str] = []
        target = description
        stages: list[SkillStageDefinition] = []
        anti_patterns: list[SkillAntiPatternDefinition] = []
        invariants: list[SkillInvariantDefinition] = []
        dependencies: list[str] = []

        # Parse stages (e.g. ## 1. Name or Stage 1: Name)
        stage_matches = re.findall(
            r"^(?:##|\#\#\#)?\s*(?:Stage\s*)?(\d+)[\.:\s]+([^\n]+)",
            content,
            re.MULTILINE,
        )
        for idx, (s_num_str, s_name) in enumerate(stage_matches, start=1):
            stages.append(
                SkillStageDefinition(
                    stage_num=int(s_num_str) if s_num_str.isdigit() else idx,
                    name=s_name.strip(),
                    completion_gate=f"Gate for Stage {s_num_str}",
                )
            )

        # Parse Anti-Patterns
        ap_matches = re.findall(r"-\s+\*\*([^*]+)\*\*\s*[—–-]\s*([^\n]+)", content)
        for ap_name, ap_desc in ap_matches:
            anti_patterns.append(
                SkillAntiPatternDefinition(
                    name=ap_name.strip(),
                    symptom=ap_desc.strip(),
                    remedy="Follow standard protocol",
                )
            )

        # Check for companion CARD.md
        card_file = skill_dir / "CARD.md"
        card_path_str = str(card_file) if card_file.exists() else ""
        if card_file.exists():
            card_content = card_file.read_text(encoding="utf-8", errors="replace")
            cat_match = re.search(r"\|\s*Domain:\s*([^|\n]+)", card_content)
            if cat_match:
                category = cat_match.group(1).strip()

            dep_matches = re.findall(r"`/([a-z0-9\-]+)`", card_content)
            for d in dep_matches:
                clean_d = d.strip().lower().replace("_", "-").lstrip("/")
                if clean_d != skill_name and clean_d not in dependencies:
                    dependencies.append(clean_d)

        # Parse explicit dependencies from YAML frontmatter (S2)
        dep_match = re.search(
            r"^dependencies:\s*\n((?:\s*-\s*[^\n]+\n)+)", content, re.MULTILINE
        )
        if dep_match:
            for d in re.findall(r"-\s*([a-zA-Z0-9\-_]+)", dep_match.group(1)):
                clean_d = d.strip().lower().replace("_", "-").lstrip("/")
                if clean_d and clean_d != skill_name and clean_d not in dependencies:
                    dependencies.append(clean_d)
        dep_inline_match = re.search(
            r"^dependencies:\s*\[([^\]]+)\]", content, re.MULTILINE
        )
        if dep_inline_match:
            for d in dep_inline_match.group(1).split(","):
                clean_d = (
                    d.strip()
                    .strip('"')
                    .strip("'")
                    .lower()
                    .replace("_", "-")
                    .lstrip("/")
                )
                if clean_d and clean_d != skill_name and clean_d not in dependencies:
                    dependencies.append(clean_d)

        # Cross-reference triggers, slash commands, and dependencies from SKILL.md
        slash_matches = re.findall(r"(?:^|[^\w])/([a-z0-9][a-z0-9\-]+)", content)
        for d in slash_matches:
            clean_d = d.strip().lower().replace("_", "-").lstrip("/")
            if clean_d != skill_name and clean_d not in dependencies:
                dependencies.append(clean_d)

        return SkillCardDefinition(
            name=skill_name,
            category=category,
            invocation=invocation,
            triggers=list(dict.fromkeys(triggers)),
            version="1.0.0",
            target=target,
            stages=stages,
            anti_patterns=anti_patterns,
            invariants=invariants,
            dependencies=[
                d for d in list(dict.fromkeys(dependencies)) if d != skill_name
            ],
            knowledge_items=[],
            services=[],
            tools=[],
            card_path=card_path_str,
            skill_path=str(skill_file),
        )

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

    async def link_knowledge_vault(self, vault_dir: str = ".harness/knowledge") -> int:
        return self._registry.link_knowledge_vault(vault_dir)

    async def export_html_brief(self, output_path: str | None = None) -> str:
        skills = self._registry.discover_all()
        out = (
            Path(output_path).resolve()
            if output_path
            else Path(tempfile.gettempdir())
            / f"skill-graph-visual-{int(time.time())}.html"
        )

        categories = sorted({s.category for s in skills})

        mermaid_nodes: list[str] = []
        for s in skills:
            clean_id = s.name.replace("-", "_")
            mermaid_nodes.append(f'  {clean_id}["{s.name}"]')
            for dep in s.dependencies:
                dep_id = dep.replace("-", "_")
                mermaid_nodes.append(f"  {clean_id} --> {dep_id}")

        mermaid_content = "\n".join(mermaid_nodes)

        html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Skill Knowledge Graph</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-7xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-6 mb-8">
    <h1 class="text-3xl font-bold tracking-tight text-white">Agent Skill Knowledge Graph</h1>
    <p class="text-sm text-gray-400 mt-1">Indexed {len(skills)} skills across {len(categories)} categories</p>
  </header>

  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
      <div class="text-xs uppercase text-gray-400 font-semibold">Total Skills</div>
      <div class="text-3xl font-bold text-cyan-400 mt-2">{len(skills)}</div>
    </div>
    <div class="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
      <div class="text-xs uppercase text-gray-400 font-semibold">Categories</div>
      <div class="text-3xl font-bold text-emerald-400 mt-2">{len(categories)}</div>
    </div>
  </div>

  <div class="bg-[#161b22] border border-[#30363d] rounded-xl p-6 mb-8">
    <h2 class="text-lg font-semibold text-white mb-4">Skill Dependency & Handoff Topology</h2>
    <div class="mermaid bg-black/40 p-4 rounded-lg flex justify-center">
graph TD
{mermaid_content}
    </div>
  </div>
</body>
</html>"""
        out.write_text(html_content, encoding="utf-8")
        return str(out)


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
        return [SKILL_REGISTRY_KEY, SKILL_GRAPH_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SKILL_REGISTRY_KEY, self._registry)
        ctx.provide(SKILL_GRAPH_KEY, self._graph)
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
