"""Directed Knowledge Graph engine for indexing, routing, and chaining skills."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from harness.services.skill_graph import (
    CANONICAL_PIPELINE_PRECEDENCE,
    BuiltinSkillRegistryService,
    get_default_skill_registry,
)

from .models import (
    EdgeType,
    SkillEdge,
    SkillGraphSnapshot,
    SkillMatch,
    SkillNode,
    SkillRouterResult,
    SkillTopologyReport,
)


class SkillKnowledgeGraph:
    """In-memory directed knowledge graph representing skills, categories, and relationships.

    Acts as an authoritative facade over BuiltinSkillRegistryService, providing
    100% backward compatibility for plugins, tests, and CLI callers while
    eliminating split-brain dual-core state (Rule 1, Rule 49).
    """

    def __init__(self, registry: Any = None) -> None:
        self._registry: BuiltinSkillRegistryService = (
            registry if registry is not None else get_default_skill_registry()
        )

    @property
    def nodes(self) -> dict[str, SkillNode]:
        """Access registered nodes mapping."""
        self._registry._ensure_scanned(self._registry._default_root)
        return self._registry._skills_cache

    @nodes.setter
    def nodes(self, value: dict[str, SkillNode]) -> None:
        self._registry._skills_cache = value

    @property
    def edges(self) -> list[SkillEdge]:
        """All directed relationship edges in the skill knowledge graph."""
        return self._registry.edges

    @edges.setter
    def edges(self, value: list[SkillEdge]) -> None:
        self._registry._edges = value

    @property
    def categories(self) -> set[str]:
        self._registry._ensure_scanned(self._registry._default_root)
        return self._registry._categories

    @categories.setter
    def categories(self, value: set[str]) -> None:
        self._registry._categories = value

    @property
    def _adj_out(self) -> dict[str, list[SkillEdge]]:
        self._registry._ensure_scanned(self._registry._default_root)
        return self._registry._adj_out

    @property
    def _adj_in(self) -> dict[str, list[SkillEdge]]:
        self._registry._ensure_scanned(self._registry._default_root)
        return self._registry._adj_in

    def get_nodes(self) -> dict[str, SkillNode]:
        """Retrieve copy of registered skill nodes mapping."""
        return self._registry.get_nodes()

    def get_categories(self) -> set[str]:
        """Retrieve copy of registered categories set."""
        return self._registry.get_categories()

    def get_outgoing_edges(self, skill_name: str) -> list[SkillEdge]:
        """Retrieve outgoing directed edges from a skill node."""
        return self._registry.get_outgoing_edges(skill_name)

    def get_incoming_edges(self, skill_name: str) -> list[SkillEdge]:
        """Retrieve incoming directed edges to a skill node."""
        return self._registry.get_incoming_edges(skill_name)

    def add_skill(self, skill: SkillNode) -> None:
        """Add a skill node and construct its internal relationships."""
        self._registry._skills_cache[skill.name] = skill
        self._registry._categories.add(skill.category)
        self._registry._add_edge(
            source=skill.name,
            target=f"cat:{skill.category}",
            relation=EdgeType.BELONGS_TO,
            weight=1.0,
        )
        for ap in skill.anti_patterns:
            self._registry._add_edge(
                source=skill.name,
                target=f"antipattern:{ap.name.lower().replace(' ', '-')}",
                relation=EdgeType.MITIGATES,
                weight=1.0,
            )

    def build_derived_edges(self) -> None:
        """Build cross-skill relationships (REQUIRES, PRECEDES, COMPLEMENTS)."""
        for skill_name, node in list(self._registry._skills_cache.items()):
            for ref in node.references:
                if ref in self._registry._skills_cache:
                    self._registry._add_edge(
                        source=skill_name,
                        target=ref,
                        relation=EdgeType.REQUIRES,
                        weight=1.0,
                    )
        for s1, s2 in CANONICAL_PIPELINE_PRECEDENCE:
            if (
                s1 in self._registry._skills_cache
                and s2 in self._registry._skills_cache
            ):
                self._registry._add_edge(
                    source=s1,
                    target=s2,
                    relation=EdgeType.PRECEDES,
                    weight=1.0,
                )

    def _add_edge(
        self, source: str, target: str, relation: EdgeType, weight: float = 1.0
    ) -> None:
        """Helper to append directed edge and update adjacency index."""
        self._registry._add_edge(source, target, relation, weight=weight)

    def query_router(
        self, intent: str, top_k: int = 3, registry: Any = None
    ) -> SkillRouterResult:
        """Route natural language intent or task prompt to matching skills using calibrated BM25 engine."""
        reg = registry if registry is not None else self._registry
        routed = reg.route_intent(intent, top_k=top_k)

        matches: list[SkillMatch] = []
        for m in routed.get("matches", []):
            name = m["skill_name"]
            cat = m.get("category") or (
                self.nodes[name].category if name in self.nodes else "general"
            )
            matched_triggers = m.get("matched_triggers") or []
            matches.append(
                SkillMatch(
                    skill_name=name,
                    category=cat,
                    confidence=float(m.get("confidence", 0.0)),
                    matched_triggers=matched_triggers,
                    reasoning=f"Matched triggers: {matched_triggers or ['keyword overlap']}",
                )
            )

        recommended_chain = list(routed.get("recommended_chain") or [])
        if matches and not recommended_chain:
            primary = matches[0].skill_name
            recommended_chain.append(primary)
            for edge in self._adj_out.get(primary, []):
                if edge.relation == EdgeType.PRECEDES and edge.target in self.nodes:
                    recommended_chain.append(edge.target)

        return SkillRouterResult(
            query=intent,
            matches=matches[:top_k],
            recommended_chain=recommended_chain,
        )

    def find_chain(self, start_skill: str, target_skill: str) -> list[str]:
        """Find shortest execution path between two skills using BFS."""
        res = self._registry.get_chain(start_skill, target_skill)
        return res.chain if res.status == "ok" else []

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        """Inspect topology for a single skill."""
        return self._registry.get_topology(skill_name)

    def generate_mermaid(self) -> str:
        """Generate Mermaid diagram markdown representing the full skill knowledge graph."""
        lines = ["flowchart TD"]

        # Group by category
        cat_to_skills: dict[str, list[str]] = defaultdict(list)
        for name, node in self.nodes.items():
            cat_to_skills[node.category].append(name)

        for cat, s_names in sorted(cat_to_skills.items()):
            clean_cat = cat.replace("/", "_").replace("-", "_")
            lines.append(f'    subgraph sg_{clean_cat} ["{cat.upper()}"]')
            for s in sorted(s_names):
                skill = self.nodes[s]
                label = f"{skill.name}\\n({skill.invocation or skill.name})"
                lines.append(f'        node_{s.replace("-", "_")}["{label}"]')
            lines.append("    end")

        # Add Edges
        for edge in self.edges:
            if edge.source in self.nodes and edge.target in self.nodes:
                src_id = f"node_{edge.source.replace('-', '_')}"
                tgt_id = f"node_{edge.target.replace('-', '_')}"
                rel_label = edge.relation.value

                if edge.relation == EdgeType.PRECEDES:
                    lines.append(f"    {src_id} -->|{rel_label}| {tgt_id}")
                elif edge.relation == EdgeType.REQUIRES:
                    lines.append(f"    {src_id} -.->|{rel_label}| {tgt_id}")
                elif edge.relation == EdgeType.COMPLEMENTS:
                    lines.append(f"    {src_id} <-->|{rel_label}| {tgt_id}")

        return "\n".join(lines)

    def get_snapshot(self) -> SkillGraphSnapshot:
        """Serialize complete graph state into snapshot schema."""
        return SkillGraphSnapshot(
            total_skills=len(self.nodes),
            categories=sorted(self.categories),
            nodes=self.nodes,
            edges=self.edges,
        )

