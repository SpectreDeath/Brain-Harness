"""Mermaid DAG diagram generator for multi-agent swarm executions."""

from __future__ import annotations

import re
from typing import Any


def build_swarm_mermaid_graph(run_id: str, tree_data: dict[str, Any]) -> str:
    """Render high-fidelity dark-mode Mermaid DAG with stateful classes and critical path highlighting."""
    raw_nodes = tree_data.get("nodes") or {}
    if isinstance(raw_nodes, list):
        nodes = {n.get("id", f"node_{i}"): n for i, n in enumerate(raw_nodes)}
    elif isinstance(raw_nodes, dict):
        nodes = raw_nodes
    else:
        nodes = {}
    critical_path = set(tree_data.get("critical_path") or [])

    lines = [
        "graph TD",
        "    classDef completed fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#ecfdf5;",
        "    classDef completedCritical fill:#064e3b,stroke:#f59e0b,stroke-width:3px,color:#ecfdf5;",
        "    classDef running fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#eff6ff;",
        "    classDef runningCritical fill:#1e3a8a,stroke:#f59e0b,stroke-width:3px,color:#eff6ff;",
        "    classDef failed fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fef2f2;",
        "    classDef pending fill:#1e293b,stroke:#475569,stroke-width:1px,color:#94a3b8;",
    ]

    if not nodes:
        lines.append(f'    root["Swarm Run: {run_id}<br/>No active nodes"]')
        return "\n".join(lines)

    node_styles: list[str] = []
    edges: list[str] = []

    for nid, raw_node in nodes.items():
        node = (
            raw_node
            if isinstance(raw_node, dict)
            else (raw_node.to_dict() if hasattr(raw_node, "to_dict") else {})
        )
        role = node.get("role") or node.get("agent_name") or "specialist"
        st = (node.get("status") or node.get("state") or "pending").lower()
        dur = round(float(node.get("duration", 0.0)), 2)
        tok = node.get("tokens_used", 0)
        clean_nid = re.sub(r"[^a-zA-Z0-9_]", "_", nid)
        is_critical = nid in critical_path

        label = f"<b>{nid}</b><br/>{role}<br/>{st} | {dur}s | {tok}t"
        escaped_label = label.replace('"', "'")
        lines.append(f'    {clean_nid}["{escaped_label}"]')

        if st == "completed":
            cls_name = "completedCritical" if is_critical else "completed"
        elif st == "running":
            cls_name = "runningCritical" if is_critical else "running"
        elif st == "failed":
            cls_name = "failed"
        else:
            cls_name = "pending"
        node_styles.append(f"    class {clean_nid} {cls_name};")

        deps = node.get("dependencies") or []
        for dep in deps:
            clean_dep = re.sub(r"[^a-zA-Z0-9_]", "_", dep)
            edge_line = f"    {clean_dep} --> {clean_nid}"
            if edge_line not in edges:
                edges.append(edge_line)

    raw_edges = tree_data.get("edges") or []
    for edge in raw_edges:
        if isinstance(edge, dict):
            src = re.sub(r"[^a-zA-Z0-9_]", "_", str(edge.get("source", "")))
            tgt = re.sub(r"[^a-zA-Z0-9_]", "_", str(edge.get("target", "")))
            if src and tgt:
                edge_line = f"    {src} --> {tgt}"
                if edge_line not in edges:
                    edges.append(edge_line)

    lines.extend(edges)
    lines.extend(node_styles)

    return "\n".join(lines)


__all__ = [
    "build_swarm_mermaid_graph",
]
