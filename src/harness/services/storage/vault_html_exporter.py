"""Standalone interactive HTML brief exporter for Knowledge Graph visualization."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from harness.services.storage.vault_graph_models import DerivedKnowledgeGraph
from harness.services.storage.vault_html_template import HTML_TEMPLATE


def build_domain_mermaid(graph: DerivedKnowledgeGraph) -> str:
    """Build domain-level summary Mermaid flowchart TD showing inter-domain density."""
    dom_counts: Counter[str] = Counter()
    node_dom: dict[str, str] = {}
    for n in graph.nodes:
        dom_counts[n.domain] += 1
        node_dom[n.id] = n.domain

    inter_dom_edges: Counter[tuple[str, str]] = Counter()
    for e in graph.edges:
        s_dom = node_dom.get(e.source, "general")
        t_dom = node_dom.get(e.target, "general")
        if s_dom != t_dom:
            inter_dom_edges[(s_dom, t_dom)] += 1

    lines = ["flowchart TD"]
    clean_ids: dict[str, str] = {}
    for dom, count in dom_counts.most_common(20):
        c_id = dom.replace("/", "_").replace("-", "_")
        clean_ids[dom] = c_id
        label = dom.replace("_", " ").title()
        lines.append(f'  {c_id}["{label} ({count})"]')

    for (s_dom, t_dom), weight in inter_dom_edges.most_common(30):
        if s_dom in clean_ids and t_dom in clean_ids:
            lines.append(f"  {clean_ids[s_dom]} -->|{weight}| {clean_ids[t_dom]}")

    if len(lines) == 1:
        lines.append('  Overview["Vault Topology Empty"]')
    return "\n".join(lines)


def build_summary_cards(graph: DerivedKnowledgeGraph) -> str:
    """Construct HTML metric ribbon cards from graph summary."""
    s = graph.summary
    non_ki_count = s.total_nodes - s.ki_nodes
    mega_tags_str = ", ".join(s.excluded_mega_tags) if s.excluded_mega_tags else "None"

    cards = [
        f'<div class="card"><div class="card-label">Total Nodes</div><div class="card-value">{s.total_nodes}</div><div class="card-sub">{s.ki_nodes} KIs &bull; {non_ki_count} External</div></div>',
        f'<div class="card"><div class="card-label">Total Edges</div><div class="card-value">{s.total_edges}</div><div class="card-sub">{s.asserted_edge_count} Asserted &bull; {s.derived_edge_count} Derived</div></div>',
        f'<div class="card"><div class="card-label">Components</div><div class="card-value">{s.component_count}</div><div class="card-sub">Largest: {s.largest_component_size} nodes</div></div>',
        f'<div class="card"><div class="card-label">Isolated KIs</div><div class="card-value">{s.isolated_ki_count}</div><div class="card-sub">{s.untagged_ki_count} Untagged &bull; {s.uncategorized_ki_count} Uncategorized</div></div>',
        f'<div class="card"><div class="card-label">Excluded Mega-Tags</div><div class="card-value" style="font-size:1.1rem;word-break:break-all;">{len(s.excluded_mega_tags)}</div><div class="card-sub">{mega_tags_str}</div></div>',
    ]
    return "\n".join(cards)


def render_html(
    graph: DerivedKnowledgeGraph,
    title: str = "Brain Harness — Knowledge Graph Visual Brief",
) -> str:
    """Render derived knowledge graph to a self-contained interactive dark-mode HTML string."""
    json_payload = json.dumps(graph.to_dict(), ensure_ascii=False)
    mermaid_code = build_domain_mermaid(graph)
    summary_html = build_summary_cards(graph)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return (
        HTML_TEMPLATE.replace("__TITLE__", title)
        .replace("__TIMESTAMP__", timestamp)
        .replace("__SUMMARY_METRICS__", summary_html)
        .replace("__MERMAID_CODE__", mermaid_code)
        .replace("__JSON_PAYLOAD__", json_payload)
    )


def export_html(
    graph: DerivedKnowledgeGraph,
    out_path: Path | str,
    title: str = "Brain Harness — Knowledge Graph Visual Brief",
) -> Path:
    """Export derived knowledge graph to a self-contained interactive dark-mode HTML file."""
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(graph, title=title)
    out.write_text(html, encoding="utf-8")
    return out

