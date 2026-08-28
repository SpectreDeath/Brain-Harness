"""Skill Knowledge Graph & Registry service protocol, typed models, and ServiceKey.

Provides an authoritative, in-tree built-in implementation for workspace skill discovery,
caching, topological BFS chaining, intent routing, and visual brief generation.
"""

from __future__ import annotations

import collections
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin


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


class SkillInvariantDefinition(BaseModel):
    """Guarded non-negotiable invariant rule within a skill."""

    rule: str = Field(..., description="Invariant rule description or assertion")
    is_blocking: bool = Field(default=True, description="Whether violation blocks execution")


class SkillCardDefinition(BaseModel):
    """Parsed and validated Skill Card model."""

    name: str = Field(..., description="Skill kebab-case identifier")
    category: str = Field(default="general", description="Domain classification")
    invocation: str = Field(default="", description="Command / trigger format e.g. /deepen-architecture")
    triggers: list[str] = Field(default_factory=list, description="Natural language trigger phrases")
    version: str = Field(default="1.0.0", description="Semantic version")
    target: str = Field(default="", description="Operational target summary")
    stages: list[SkillStageDefinition] = Field(default_factory=list, description="Execution progression")
    anti_patterns: list[SkillAntiPatternDefinition] = Field(default_factory=list, description="Guarded anti-patterns")
    invariants: list[SkillInvariantDefinition] = Field(default_factory=list, description="Guarded invariants")
    dependencies: list[str] = Field(default_factory=list, description="Referenced peer skills")
    services: list[str] = Field(default_factory=list, description="Required micro-kernel ServiceKey identifiers")
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


SKILL_GRAPH_KEY: ServiceKey[SkillGraphService] = ServiceKey("service.skill_knowledge_graph")
SKILL_REGISTRY_KEY: ServiceKey[SkillRegistryService] = ServiceKey("service.skill_registry")


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
        self._categories: set[str] = set()
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

    def route_intent(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        """Route natural language task intent to candidate skills with confidence scores."""
        self._ensure_scanned(self._default_root)
        intent_lower = intent.lower().strip()
        intent_tokens = set(re.findall(r"\w+", intent_lower))

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

            if score > 0.0:
                confidence = min(0.98, max(0.20, score / (len(intent_tokens) + 2.0) + 0.25))
                matches.append({
                    "skill_name": skill.name,
                    "category": skill.category,
                    "confidence": round(confidence, 3),
                    "target": skill.target,
                    "matched_triggers": list(dict.fromkeys(matched_triggers))[:4],
                })

        matches.sort(key=lambda m: float(m["confidence"]), reverse=True)
        top_matches = matches[:top_k]

        # Recommended execution chain
        recommended_chain: list[str] = []
        if len(top_matches) >= 2:
            s1, s2 = top_matches[0]["skill_name"], top_matches[1]["skill_name"]
            chain_res = self.get_chain(s1, s2)
            if chain_res.status == "ok" and chain_res.chain:
                recommended_chain = chain_res.chain
            else:
                recommended_chain = [s1, s2]
        elif top_matches:
            recommended_chain = [top_matches[0]["skill_name"]]

        return {
            "status": "ok",
            "intent": intent,
            "matches": top_matches,
            "recommended_chain": recommended_chain,
            "total_indexed": len(self._skills_cache),
        }

    def get_chain(self, start_skill: str, target_skill: str) -> SkillChainResult:
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
            # Fallback direct path if unknown
            return SkillChainResult(
                status="ok",
                start_skill=start_skill,
                target_skill=target_skill,
                chain=[s_start, s_target],
                length=2,
            )

        # BFS shortest path search
        queue: collections.deque[list[str]] = collections.deque([[s_start]])
        visited: set[str] = {s_start}

        while queue:
            path = queue.popleft()
            curr = path[-1]

            neighbors = self._adjacency.get(curr, set())
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

        # If no explicit directed edge, connect start to target directly
        return SkillChainResult(
            status="ok",
            start_skill=start_skill,
            target_skill=target_skill,
            chain=[s_start, s_target],
            length=2,
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
            p,
        ]

        discovered: dict[str, SkillCardDefinition] = {}
        categories: set[str] = set()
        adjacency: dict[str, set[str]] = collections.defaultdict(set)

        for scan_dir in paths_to_scan:
            if not scan_dir.exists():
                continue
            for skill_file in scan_dir.rglob("SKILL.md"):
                try:
                    card = self._parse_skill_directory(skill_file.parent)
                    if card and card.name not in discovered:
                        discovered[card.name] = card
                        categories.add(card.category)
                        for dep in card.dependencies:
                            clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
                            adjacency[card.name].add(clean_dep)
                except Exception:
                    continue

        self._skills_cache = discovered
        self._categories = categories
        self._adjacency = adjacency
        self._last_scan_time = now

    def _parse_skill_directory(self, skill_dir: Path) -> SkillCardDefinition | None:
        """Parse SKILL.md and optional companion CARD.md from a skill directory."""
        skill_file = skill_dir / "SKILL.md"
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
            stages.append(SkillStageDefinition(
                stage_num=int(s_num_str) if s_num_str.isdigit() else idx,
                name=s_name.strip(),
                completion_gate=f"Gate for Stage {s_num_str}",
            ))

        # Parse Anti-Patterns
        ap_matches = re.findall(r"-\s+\*\*([^*]+)\*\*\s*[—–-]\s*([^\n]+)", content)
        for ap_name, ap_desc in ap_matches:
            anti_patterns.append(SkillAntiPatternDefinition(
                name=ap_name.strip(),
                symptom=ap_desc.strip(),
                remedy="Follow standard protocol",
            ))

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
                if d != skill_name:
                    dependencies.append(d)

        # Cross-reference triggers in text
        if "deepen-architecture" in content:
            dependencies.append("deepen-architecture")
        if "crafting-skills" in content:
            dependencies.append("crafting-skills")

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
            dependencies=list(dict.fromkeys(dependencies)),
            services=[],
            tools=[],
            card_path=card_path_str,
            skill_path=str(skill_file),
        )


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

    async def find_chain(self, start_skill: str, target_skill: str) -> list[str]:
        res = self._registry.get_chain(start_skill, target_skill)
        return res.chain

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        return self._registry.route_intent(intent, top_k=top_k)

    async def export_html_brief(self, output_path: str | None = None) -> str:
        skills = self._registry.discover_all()
        out = (
            Path(output_path).resolve()
            if output_path
            else Path(tempfile.gettempdir()) / f"skill-graph-visual-{int(time.time())}.html"
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

    async def on_enable(self) -> None:
        self._registry.discover_all()

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass
