"""Idempotent Cypher batch export following Neo4j knowledge graph standards (Track 5)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence
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


def export_cypher(
    graph: DerivedKnowledgeGraph,
    out_path: Path | str,
    items: Sequence[Any] | None = None,
) -> Path:
    """Export derived knowledge graph as an idempotent Cypher script for Neo4j."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    s = graph.summary
    non_ki_count = s.total_nodes - s.ki_nodes
    mega_str = ", ".join(s.excluded_mega_tags) if s.excluded_mega_tags else "none"

    lines: list[str] = [
        "// Brain Harness — Knowledge Graph Cypher Ingestion Script",
        "// Generated automatically following neo4j-knowledge-graph-architect patterns",
        f"// Summary: {s.total_nodes} nodes ({s.ki_nodes} KIs, {non_ki_count} external), {s.total_edges} edges ({s.asserted_edge_count} asserted, {s.derived_edge_count} derived)",
        f"// Components: {s.component_count} (largest: {s.largest_component_size}), Isolated KIs: {s.isolated_ki_count}",
        f"// Excluded mega-tags: {mega_str}",
        "",
        "// 1. Constraints",
        "CREATE CONSTRAINT ki_id_unique IF NOT EXISTS FOR (k:KnowledgeItem) REQUIRE k.id IS UNIQUE;",
        "CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;",
        "CREATE CONSTRAINT plugin_id_unique IF NOT EXISTS FOR (p:Plugin) REQUIRE p.id IS UNIQUE;",
        "CREATE CONSTRAINT path_id_unique IF NOT EXISTS FOR (f:CodePath) REQUIRE f.id IS UNIQUE;",
    ]

    claims_data: list[tuple[str, str, str, str, float, str, str, str, str]] = []
    if items:
        lines.append("CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:IsnadClaim) REQUIRE c.id IS UNIQUE;")
        for item in items:
            isnad = getattr(item, "isnad", None)
            claims = getattr(isnad, "claims", []) if isnad else []
            if isinstance(isnad, dict):
                claims = isnad.get("claims", [])
            if not claims:
                claims = getattr(item, "claims", []) if hasattr(item, "claims") else (item.get("claims", []) if isinstance(item, dict) else [])
            for idx, c in enumerate(claims):
                cid = (
                    getattr(c, "claim_id", None)
                    or (c.get("claim_id") or c.get("id") if isinstance(c, dict) else None)
                    or f"{item.id}-c{idx+1}"
                )
                assertion = getattr(c, "assertion", "") if hasattr(c, "assertion") else (c.get("assertion", "") if isinstance(c, dict) else "")
                if not assertion and isinstance(c, dict):
                    assertion = c.get("claim", "")
                status = getattr(c, "status", "VERIFIED") if hasattr(c, "status") else (c.get("status", "VERIFIED") if isinstance(c, dict) else "VERIFIED")
                raw_conf = getattr(c, "confidence", 1.0) if hasattr(c, "confidence") else (c.get("confidence", 1.0) if isinstance(c, dict) else 1.0)
                try:
                    conf = float(raw_conf)
                except (ValueError, TypeError):
                    if isinstance(raw_conf, str) and raw_conf.upper() in ("VERIFIED", "HIGH", "TRUE"):
                        conf = 1.0
                    elif isinstance(raw_conf, str) and raw_conf.upper() in ("CHALLENGED", "LOW"):
                        conf = 0.5
                    else:
                        conf = 1.0
                etype = getattr(c, "evidence_type", "") or (c.get("evidence_type", "") if isinstance(c, dict) else "") or ""
                src = getattr(c, "source", "") or (c.get("source", "") or c.get("source_file", "") if isinstance(c, dict) else "") or ""
                ver = "true" if (getattr(c, "verified", True) if hasattr(c, "verified") else (c.get("verified", True) if isinstance(c, dict) else True)) else "false"
                vby = getattr(c, "verified_by", "") or (c.get("verified_by", "") if isinstance(c, dict) else "") or ""
                claims_data.append((item.id, cid, assertion, status, conf, etype, src, ver, vby))

    lines.append("")
    lines.append("// 2. Node Materialization")

    for n in sorted(graph.nodes, key=lambda x: x.id):
        label = _get_cypher_label(n.node_kind)
        safe_name = n.label.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        safe_cat = n.category.replace("\\", "\\\\").replace('"', '\\"')
        safe_dom = n.domain.replace("\\", "\\\\").replace('"', '\\"')
        tags_str = "[" + ", ".join(f'"{t}"' for t in n.tags) + "]"
        lines.append(
            f'MERGE (n:{label} {{id: "{n.id}"}}) '
            f'ON CREATE SET n.label = "{safe_name}", n.category = "{safe_cat}", n.domain = "{safe_dom}", '
            f'n.tags = {tags_str}, n.status = "{n.status}", n.retrieval_count = {n.retrieval_count}, '
            f'n.created_at = "{n.created_at}" '
            f'ON MATCH SET n.retrieval_count = {n.retrieval_count}, n.status = "{n.status}";'
        )

    for item_id, cid, assertion, status, conf, etype, src, ver, vby in claims_data:
        safe_assert = assertion.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        safe_etype = etype.replace("\\", "\\\\").replace('"', '\\"')
        safe_src = src.replace("\\", "\\\\").replace('"', '\\"')
        safe_vby = vby.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            f'MERGE (c:IsnadClaim {{id: "{cid}"}}) '
            f'ON CREATE SET c.assertion = "{safe_assert}", c.status = "{status}", c.confidence = {conf:.2f}, '
            f'c.evidence_type = "{safe_etype}", c.source = "{safe_src}", c.verified = {ver}, c.verified_by = "{safe_vby}";'
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

    for item_id, cid, _, _, _, _, _, _, _ in claims_data:
        lines.append(
            f'MATCH (k:KnowledgeItem {{id: "{item_id}"}}), (c:IsnadClaim {{id: "{cid}"}}) '
            f'MERGE (k)-[:ASSERTS_CLAIM]->(c);'
        )

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

