"""Artifact and report generator plugin for Brain Harness."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def diagram_generate_mermaid(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    direction: str = "TD",
) -> dict[str, Any]:
    """Synthesize valid Mermaid flowchart syntax."""
    lines: list[str] = [f"graph {direction}"]

    for node in nodes:
        node_id = str(node.get("id", "")).replace("-", "_").replace(" ", "_")
        label = html.escape(str(node.get("label", node_id)))
        shape = node.get("shape", "rect")

        if shape == "round":
            lines.append(f'  {node_id}("{label}")')
        elif shape == "diamond":
            lines.append(f'  {node_id}{{"{label}"}}')
        elif shape == "circle":
            lines.append(f'  {node_id}(("{label}"))')
        else:
            lines.append(f'  {node_id}["{label}"]')

    for edge in edges:
        source = str(edge.get("source", "")).replace("-", "_").replace(" ", "_")
        target = str(edge.get("target", "")).replace("-", "_").replace(" ", "_")
        label = edge.get("label")
        style = edge.get("style", "solid")

        arrow = "-->"
        if style == "dotted":
            arrow = "-.->"
        elif style == "thick":
            arrow = "==>"

        if label:
            lines.append(f'  {source} {arrow}|"{html.escape(str(label))}"| {target}')
        else:
            lines.append(f"  {source} {arrow} {target}")

    mermaid_code = "\n".join(lines)
    return {
        "status": "ok",
        "mermaid": mermaid_code,
        "nodes_count": len(nodes),
        "edges_count": len(edges),
    }


def report_generate_html(
    title: str,
    sections: list[dict[str, Any]],
    output_path: str | None = None,
    theme: str = "dark",
) -> dict[str, Any]:
    """Generate a responsive, standalone HTML report."""
    bg_color = "#0f172a" if theme == "dark" else "#f8fafc"
    card_bg = "#1e293b" if theme == "dark" else "#ffffff"
    text_color = "#f8fafc" if theme == "dark" else "#0f172a"
    sub_color = "#94a3b8" if theme == "dark" else "#64748b"
    border_color = "#334155" if theme == "dark" else "#e2e8f0"
    accent_color = "#38bdf8"

    sections_html = []
    for sec in sections:
        sec_title = html.escape(str(sec.get("title", "Section")))
        sec_content = sec.get("content", "")
        sec_type = sec.get("type", "text")

        content_rendered = ""
        if sec_type == "code":
            content_rendered = f'<pre style="background: #090d16; padding: 1rem; border-radius: 8px; overflow-x: auto; color: #a5f3fc;"><code>{html.escape(str(sec_content))}</code></pre>'
        elif sec_type == "table" and isinstance(sec.get("data"), list):
            rows = sec["data"]
            if rows:
                headers = list(rows[0].keys())
                header_html = "".join(f'<th style="text-align: left; padding: 8px; border-bottom: 1px solid {border_color};">{html.escape(h)}</th>' for h in headers)
                body_html = ""
                for row in rows:
                    cols = "".join(f'<td style="padding: 8px; border-bottom: 1px solid {border_color};">{html.escape(str(row.get(h, "")))}</td>' for h in headers)
                    body_html += f"<tr>{cols}</tr>"
                content_rendered = f'<table style="width: 100%; border-collapse: collapse; margin-top: 8px;"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>'
        else:
            content_rendered = f'<p style="color: {sub_color}; line-height: 1.6;">{html.escape(str(sec_content))}</p>'

        sections_html.append(f"""
        <div style="background: {card_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
          <h2 style="margin-top: 0; color: {accent_color}; font-size: 1.25rem;">{sec_title}</h2>
          {content_rendered}
        </div>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: {bg_color};
      color: {text_color};
      margin: 0;
      padding: 2rem;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: 2rem;
      margin-bottom: 0.5rem;
      border-bottom: 2px solid {border_color};
      padding-bottom: 1rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{html.escape(title)}</h1>
    {"".join(sections_html)}
  </div>
</body>
</html>"""

    if output_path:
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full_html, encoding="utf-8")

    return {
        "status": "ok",
        "title": title,
        "sections_count": len(sections),
        "output_path": output_path,
        "html_length": len(full_html),
    }


def report_create_briefing(
    title: str,
    summary: str,
    metrics: dict[str, Any] | None = None,
    recommendations: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Create a structured executive briefing document."""
    lines: list[str] = [
        f"# {title}",
        "",
        "## Executive Summary",
        summary,
        "",
    ]

    if metrics:
        lines.append("## Key Metrics")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        for k, v in metrics.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    if recommendations:
        lines.append("## Strategic Recommendations")
        for r in recommendations:
            lines.append(f"- {r}")
        lines.append("")

    doc = "\n".join(lines)

    if output_path:
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc, encoding="utf-8")

    return {
        "status": "ok",
        "title": title,
        "markdown": doc,
        "output_path": output_path,
    }
