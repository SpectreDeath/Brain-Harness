"""Directed Knowledge Graph engine for indexing, routing, and chaining skills."""

from __future__ import annotations

import re
from collections import defaultdict, deque

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
    """In-memory directed knowledge graph representing skills, categories, and relationships."""

    def __init__(self) -> None:
        self.nodes: dict[str, SkillNode] = {}
        self.edges: list[SkillEdge] = []
        self._adj_out: dict[str, list[SkillEdge]] = defaultdict(list)
        self._adj_in: dict[str, list[SkillEdge]] = defaultdict(list)
        self.categories: set[str] = set()

    def add_skill(self, skill: SkillNode) -> None:
        """Add a skill node and construct its internal relationships."""
        self.nodes[skill.name] = skill
        self.categories.add(skill.category)

        # 1. Category Edge
        self._add_edge(
            source=skill.name,
            target=f"cat:{skill.category}",
            relation=EdgeType.BELONGS_TO,
            weight=1.0,
        )

        # 2. Anti-Pattern Edges
        for ap in skill.anti_patterns:
            self._add_edge(
                source=skill.name,
                target=f"antipattern:{ap.name.lower().replace(' ', '-')}",
                relation=EdgeType.MITIGATES,
                weight=1.0,
            )

    def build_derived_edges(self) -> None:
        """Build cross-skill relationships (REQUIRES, PRECEDES, COMPLEMENTS)."""
        # Cross-reference edges
        for skill_name, node in self.nodes.items():
            for ref in node.references:
                if ref in self.nodes:
                    self._add_edge(
                        source=skill_name,
                        target=ref,
                        relation=EdgeType.REQUIRES,
                        weight=1.0,
                    )

        # Known pipeline precedence pairs
        pipeline_pairs = [
            ("structured-data-scout", "data-topology-mapper"),
            ("data-topology-mapper", "epistemic-isnad-audit"),
            ("epistemic-isnad-audit", "questio-reflection"),
            ("codebase-design", "deepen-architecture"),
            ("questio-reflection", "deepen-architecture"),
            ("crafting-skills", "questio-reflection"),
        ]

        for s1, s2 in pipeline_pairs:
            if s1 in self.nodes and s2 in self.nodes:
                self._add_edge(
                    source=s1,
                    target=s2,
                    relation=EdgeType.PRECEDES,
                    weight=1.0,
                )

    def _add_edge(self, source: str, target: str, relation: EdgeType, weight: float = 1.0) -> None:
        """Helper to append directed edge and update adjacency index."""
        # Avoid duplicate edges
        for existing in self._adj_out[source]:
            if existing.target == target and existing.relation == relation:
                return

        edge = SkillEdge(source=source, target=target, relation=relation, weight=weight)
        self.edges.append(edge)
        self._adj_out[source].append(edge)
        self._adj_in[target].append(edge)

    def query_router(self, intent: str, top_k: int = 3) -> SkillRouterResult:
        """Route natural language intent or task prompt to matching skills."""
        clean_intent = intent.lower()
        intent_tokens = set(re.findall(r"\w+", clean_intent))
        matches: list[SkillMatch] = []

        for name, skill in self.nodes.items():
            score = 0.0
            matched_triggers: list[str] = []

            # 1. Exact trigger phrase match
            for trigger in skill.triggers:
                t_lower = trigger.lower()
                if t_lower in clean_intent:
                    score += 5.0
                    matched_triggers.append(trigger)
                else:
                    # Token overlap
                    t_tokens = set(re.findall(r"\w+", t_lower))
                    overlap = len(t_tokens & intent_tokens)
                    if overlap > 0:
                        score += overlap * 1.5

            # 2. Skill Name & Category match
            if name.replace("-", " ") in clean_intent:
                score += 4.0
            if skill.category.lower() in clean_intent:
                score += 2.0

            # 3. Description & Target token overlap
            desc_tokens = set(re.findall(r"\w+", skill.description.lower() + " " + skill.target.lower()))
            score += len(desc_tokens & intent_tokens) * 0.2

            if score > 0:
                matches.append(
                    SkillMatch(
                        skill_name=name,
                        category=skill.category,
                        confidence=round(min(score / 10.0, 1.0), 3),
                        matched_triggers=matched_triggers,
                        reasoning=f"Matched triggers: {matched_triggers or ['keyword overlap']}",
                    )
                )

        matches.sort(key=lambda m: m.confidence, reverse=True)
        top_matches = matches[:top_k]

        # Compute recommended chain from top matches
        recommended_chain: list[str] = []
        if top_matches:
            primary = top_matches[0].skill_name
            recommended_chain.append(primary)
            # Find downstream handoffs
            for edge in self._adj_out.get(primary, []):
                if edge.relation == EdgeType.PRECEDES and edge.target in self.nodes:
                    recommended_chain.append(edge.target)

        return SkillRouterResult(
            query=intent,
            matches=top_matches,
            recommended_chain=recommended_chain,
        )

    def find_chain(self, start_skill: str, target_skill: str) -> list[str]:
        """Find shortest execution path between two skills using BFS."""
        if start_skill not in self.nodes or target_skill not in self.nodes:
            return []
        if start_skill == target_skill:
            return [start_skill]

        queue: deque[list[str]] = deque([[start_skill]])
        visited: set[str] = {start_skill}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == target_skill:
                return path

            for edge in self._adj_out.get(current, []):
                # Follow PRECEDES, REQUIRES, or COMPLEMENTS
                if edge.relation in {EdgeType.PRECEDES, EdgeType.REQUIRES, EdgeType.COMPLEMENTS}:
                    nxt = edge.target
                    if nxt in self.nodes and nxt not in visited:
                        visited.add(nxt)
                        queue.append(path + [nxt])

        return []

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        """Inspect topology for a single skill."""
        if skill_name not in self.nodes:
            raise KeyError(f"Skill '{skill_name}' not found in knowledge graph.")

        skill = self.nodes[skill_name]
        prereqs: list[str] = []
        downstream: list[str] = []
        complements: list[str] = []
        mitigates: list[str] = []

        for edge in self._adj_in.get(skill_name, []):
            if edge.relation in {EdgeType.REQUIRES, EdgeType.PRECEDES} and edge.source in self.nodes:
                prereqs.append(edge.source)

        for edge in self._adj_out.get(skill_name, []):
            if edge.relation == EdgeType.PRECEDES and edge.target in self.nodes:
                downstream.append(edge.target)
            elif edge.relation == EdgeType.COMPLEMENTS and edge.target in self.nodes:
                complements.append(edge.target)
            elif edge.relation == EdgeType.MITIGATES:
                mitigates.append(edge.target.replace("antipattern:", ""))

        return SkillTopologyReport(
            skill=skill,
            prerequisites=list(dict.fromkeys(prereqs)),
            downstream_handoffs=list(dict.fromkeys(downstream)),
            complements=list(dict.fromkeys(complements)),
            mitigated_anti_patterns=list(dict.fromkeys(mitigates)),
        )

    def generate_mermaid(self) -> str:
        """Generate Mermaid diagram markdown representing the full skill knowledge graph."""
        lines = ["flowchart TD"]

        # Group by category
        cat_to_skills: dict[str, list[str]] = defaultdict(list)
        for name, node in self.nodes.items():
            cat_to_skills[node.category].append(name)

        for cat, s_names in cat_to_skills.items():
            clean_cat = cat.replace("/", "_").replace("-", "_")
            lines.append(f'    subgraph sg_{clean_cat} ["{cat.upper()}"]')
            for s in s_names:
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
