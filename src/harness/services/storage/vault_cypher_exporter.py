"""Idempotent Cypher batch export following Neo4j knowledge graph standards (Track 5)."""

from __future__ import annotations

from pathlib import Path
from harness.services.storage.vault_graph_models import DerivedKnowledgeGraph


def _get_cypher_label(node_kind: str) -> str:
    if node_kind == "skill":
        return "Skill"
    elif node_kind == "plugin":
        return "Plugin"
    elif node_kind == "path":
        return "CodePath"
    elif node_kind == "source":
        return "SourceOrigin"
    return "KnowledgeItem"


def export_cypher(graph: DerivedKnowledgeGraph, out_path: Path | str) -> Path:
    """Export derived knowledge graph as an idempotent Cypher script for Neo4j."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "// Brain Harness — Knowledge Graph Cypher Ingestion Script",
        "// Generated automatically following neo4j-knowledge-graph-architect patterns",
        "",
        "// 1. Constraints",
        "CREATE CONSTRAINT ki_id_unique IF NOT EXISTS FOR (k:KnowledgeItem) REQUIRE k.id IS UNIQUE;",
        "CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;",
        "CREATE CONSTRAINT plugin_id_unique IF NOT EXISTS FOR (p:Plugin) REQUIRE p.id IS UNIQUE;",
        "CREATE CONSTRAINT path_id_unique IF NOT EXISTS FOR (f:CodePath) REQUIRE f.id IS UNIQUE;",
        "",
        "// 2. Node Materialization",
    ]

    for n in sorted(graph.nodes, key=lambda x: x.id):
        label = _get_cypher_label(n.node_kind)
        safe_name = n.label.replace('"', '\\"')
        safe_cat = n.category.replace('"', '\\"')
        safe_dom = n.domain.replace('"', '\\"')
        tags_str = "[" + ", ".join(f'"{t}"' for t in n.tags) + "]"
        lines.append(
            f'MERGE (n:{label} {{id: "{n.id}"}}) '
            f'ON CREATE SET n.label = "{safe_name}", n.category = "{safe_cat}", n.domain = "{safe_dom}", '
            f'n.tags = {tags_str}, n.status = "{n.status}", n.retrieval_count = {n.retrieval_count}, '
            f'n.created_at = "{n.created_at}" '
            f'ON MATCH SET n.retrieval_count = {n.retrieval_count}, n.status = "{n.status}";'
        )

    lines.append("")
    lines.append("// 3. Typed Relationship Edges")
    for idx, e in enumerate(sorted(graph.edges, key=lambda x: (x.source, x.target, x.type))):
        rel_type = e.type.upper()
        der_str = "true" if e.derived else "false"
        lines.append(
            f'MATCH (s {{id: "{e.source}"}}), (t {{id: "{e.target}"}}) '
            f'MERGE (s)-[r:{rel_type}]->(t) '
            f'ON CREATE SET r.derived = {der_str}, r.confidence = {e.confidence:.2f};'
        )

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

