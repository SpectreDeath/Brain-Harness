"""One export engine across four graph serialization formats: JSON, GEXF, GraphML, HTML."""

from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from harness.services.storage.vault_cypher_exporter import export_cypher
from harness.services.storage.vault_graph_models import DerivedKnowledgeGraph
from harness.services.storage.vault_html_exporter import export_html


def export_json(graph: DerivedKnowledgeGraph, out_path: Path | str) -> Path:
    """Export derived knowledge graph to canonically ordered JSON format."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = graph.to_dict()
    payload["nodes"] = sorted(payload["nodes"], key=lambda n: n["id"])
    payload["edges"] = sorted(payload["edges"], key=lambda e: (e["source"], e["target"], e["type"]))
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def export_gexf(graph: DerivedKnowledgeGraph, out_path: Path | str, dynamic: bool = False) -> Path:
    """Export derived knowledge graph to standard GEXF 1.3 XML format for Gephi."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    root = ET.Element("gexf", {
        "xmlns": "http://www.gexf.net/1.3draft",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.gexf.net/1.3draft http://www.gexf.net/1.3draft/gexf.xsd",
        "version": "1.3",
    })

    meta = ET.SubElement(root, "meta")
    ET.SubElement(meta, "creator").text = "Brain Harness"
    ET.SubElement(meta, "description").text = (
        f"Derived Knowledge Graph: {graph.summary.total_nodes} nodes, {graph.summary.total_edges} edges "
        f"({graph.summary.asserted_edge_count} asserted, {graph.summary.derived_edge_count} derived)"
    )

    g_attrs = {"defaultedgetype": "directed", "mode": "dynamic" if dynamic else "static"}
    if dynamic:
        g_attrs["timeformat"] = "date"
    graph_elem = ET.SubElement(root, "graph", g_attrs)

    node_attrs = ET.SubElement(graph_elem, "attributes", {"class": "node", "mode": "static"})
    node_keys = [
        ("0", "node_kind", "string"), ("1", "category", "string"), ("2", "domain", "string"),
        ("3", "tags", "string"), ("4", "status", "string"), ("5", "retrieval_count", "integer"),
        ("6", "success_count", "integer"), ("7", "created_at", "string"), ("8", "source_target", "string"),
    ]
    for attr_id, title, attr_type in node_keys:
        ET.SubElement(node_attrs, "attribute", {"id": attr_id, "title": title, "type": attr_type})

    edge_attrs = ET.SubElement(graph_elem, "attributes", {"class": "edge", "mode": "static"})
    edge_keys = [
        ("0", "edge_type", "string"), ("1", "derived", "boolean"),
        ("2", "confidence", "float"), ("3", "shared_tags", "string"),
    ]
    for attr_id, title, attr_type in edge_keys:
        ET.SubElement(edge_attrs, "attribute", {"id": attr_id, "title": title, "type": attr_type})

    node_map = {n.id: n for n in graph.nodes}
    nodes_elem = ET.SubElement(graph_elem, "nodes")
    for n in sorted(graph.nodes, key=lambda x: x.id):
        n_attrs = {"id": n.id, "label": n.label or n.id}
        if dynamic and n.created_at:
            n_attrs["start"] = n.created_at[:10]
            if n.status in ("SUPERSEDED", "ARCHIVED"):
                n_attrs["end"] = n.created_at[:10]
        n_elem = ET.SubElement(nodes_elem, "node", n_attrs)
        attvalues = ET.SubElement(n_elem, "attvalues")
        values = [
            ("0", n.node_kind), ("1", n.category), ("2", n.domain), ("3", ",".join(n.tags)),
            ("4", n.status), ("5", str(n.retrieval_count)), ("6", str(n.success_count)),
            ("7", n.created_at), ("8", n.source_target),
        ]
        for aid, val in values:
            if val:
                ET.SubElement(attvalues, "attvalue", {"for": aid, "value": str(val)})

    edges_elem = ET.SubElement(graph_elem, "edges")
    for idx, e in enumerate(sorted(graph.edges, key=lambda x: (x.source, x.target, x.type))):
        e_attrs = {
            "id": f"e{idx}", "source": e.source, "target": e.target, "weight": f"{e.confidence:.2f}",
        }
        if dynamic:
            s_node = node_map.get(e.source)
            if s_node and s_node.created_at:
                e_attrs["start"] = s_node.created_at[:10]
        e_elem = ET.SubElement(edges_elem, "edge", e_attrs)
        attvalues = ET.SubElement(e_elem, "attvalues")
        values = [
            ("0", e.type), ("1", "true" if e.derived else "false"),
            ("2", f"{e.confidence:.2f}"), ("3", ",".join(e.shared_tags)),
        ]
        for aid, val in values:
            if val:
                ET.SubElement(attvalues, "attvalue", {"for": aid, "value": str(val)})

    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def export_graphml(graph: DerivedKnowledgeGraph, out_path: Path | str) -> Path:
    """Export derived knowledge graph to standard GraphML format for Cytoscape and yEd."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    root = ET.Element("graphml", {
        "xmlns": "http://graphml.graphdrawing.org/xmlns",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd",
    })

    node_keys = [
        ("label", "label", "string"), ("node_kind", "node_kind", "string"),
        ("category", "category", "string"), ("domain", "domain", "string"),
        ("tags", "tags", "string"), ("status", "status", "string"),
        ("retrieval_count", "retrieval_count", "int"), ("success_count", "success_count", "int"),
        ("created_at", "created_at", "string"), ("source_target", "source_target", "string"),
    ]
    for k_id, k_name, k_type in node_keys:
        ET.SubElement(root, "key", {"id": k_id, "for": "node", "attr.name": k_name, "attr.type": k_type})

    edge_keys = [
        ("edge_type", "edge_type", "string"), ("derived", "derived", "boolean"),
        ("confidence", "confidence", "double"), ("shared_tags", "shared_tags", "string"),
    ]
    for k_id, k_name, k_type in edge_keys:
        ET.SubElement(root, "key", {"id": k_id, "for": "edge", "attr.name": k_name, "attr.type": k_type})

    graph_elem = ET.SubElement(root, "graph", {"id": "G", "edgedefault": "directed"})

    for n in sorted(graph.nodes, key=lambda x: x.id):
        n_elem = ET.SubElement(graph_elem, "node", {"id": n.id})
        data_map = [
            ("label", n.label or n.id), ("node_kind", n.node_kind), ("category", n.category),
            ("domain", n.domain), ("tags", ",".join(n.tags)), ("status", n.status),
            ("retrieval_count", str(n.retrieval_count)), ("success_count", str(n.success_count)),
            ("created_at", n.created_at), ("source_target", n.source_target),
        ]
        for key_id, val in data_map:
            if val:
                d = ET.SubElement(n_elem, "data", {"key": key_id})
                d.text = str(val)

    for idx, e in enumerate(sorted(graph.edges, key=lambda x: (x.source, x.target, x.type))):
        e_elem = ET.SubElement(graph_elem, "edge", {"id": f"e{idx}", "source": e.source, "target": e.target})
        data_map = [
            ("edge_type", e.type), ("derived", "true" if e.derived else "false"),
            ("confidence", f"{e.confidence:.2f}"), ("shared_tags", ",".join(e.shared_tags)),
        ]
        for key_id, val in data_map:
            if val:
                d = ET.SubElement(e_elem, "data", {"key": key_id})
                d.text = str(val)

    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def export_knowledge_graph(
    graph: DerivedKnowledgeGraph,
    out_path: Path | str,
    format: str = "json",
    dynamic: bool = False,
) -> Path:
    """Unified entrypoint dispatching knowledge graph serialization to specified format."""
    fmt = format.lower()
    if fmt == "json":
        return export_json(graph, out_path)
    elif fmt == "gexf":
        return export_gexf(graph, out_path, dynamic=dynamic)
    elif fmt == "graphml":
        return export_graphml(graph, out_path)
    elif fmt == "html":
        return export_html(graph, out_path)
    elif fmt == "cypher":
        return export_cypher(graph, out_path)
    else:
        raise ValueError(f"Unsupported export format '{format}'. Supported formats: json, gexf, graphml, html, cypher.")

