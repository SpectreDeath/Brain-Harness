"""Interactive HTML visual brief generator for Deep Repo Auditor (Rule 51)."""

from __future__ import annotations

import html
import json
import tempfile
import time
from pathlib import Path

from .models import DeepAuditReport, VisualBriefPaths

_HTML_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>__TITLE__</title>
<style>
  body { background:#0f172a; color:#e2e8f0; font-family:system-ui,sans-serif; margin:0; padding:24px; }
  .card { background:#1e293b; border:1px solid #334155; border-radius:10px; padding:16px; margin-bottom:16px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:6px; background:#0284c7; color:#fff; font-size:12px; }
  table { width:100%; border-collapse:collapse; margin-top:8px; }
  th, td { text-align:left; padding:8px; border-bottom:1px solid #334155; font-size:13px; }
  pre { background:#020617; padding:12px; border-radius:8px; overflow-x:auto; color:#a5f3fc; }
</style>
</head>
<body>
  <div class="card">
    <span class="badge">Deep Repo Auditor</span>
    <h1>__TITLE__</h1>
    <p>__SUBTITLE__</p>
  </div>
  __BODY_HTML__
  <div class="card">
    <h3>Structured Audit Payload</h3>
    <pre>__PAYLOAD_JSON__</pre>
  </div>
</body>
</html>
"""


def _render_shell(*, title: str, subtitle: str, body_html: str, payload: object) -> str:
    payload_str = html.escape(json.dumps(payload, indent=2))
    return (
        _HTML_SHELL.replace("__TITLE__", html.escape(title))
        .replace("__SUBTITLE__", html.escape(subtitle))
        .replace("__BODY_HTML__", body_html)
        .replace("__PAYLOAD_JSON__", payload_str)
    )


def _render_compute_body(report: DeepAuditReport) -> str:
    c = report.compute
    rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in (
            ("Ambiguity", c.ambiguity),
            ("Span", c.span),
            ("Depth", c.depth),
            ("Rigor", c.rigor),
            ("Concurrency", c.concurrency),
            ("Composite", c.composite),
            ("Tier", html.escape(c.tier)),
            ("Thinking Budget", html.escape(c.thinking_budget)),
        )
    )
    return f'<div class="card"><h2>5D Compute Vector</h2><table><tr><th>Dimension</th><th>Score</th></tr>{rows}</table></div>'


def _render_topology_body(report: DeepAuditReport) -> str:
    t = report.topology
    mods = "\n".join(f"  Root --> M{idx}[{html.escape(m)}]" for idx, m in enumerate(t.blast_radius_modules, 1))
    mermaid = f"graph TD\n  Root[{html.escape(t.root_manifest)}] --> Pattern[{html.escape(t.topology_pattern)}]\n{mods}"
    return (
        '<div class="card"><h2>Structural & Data Topology</h2>'
        f"<p>Pattern: <strong>{html.escape(t.topology_pattern)}</strong> | Files: {t.total_files_scanned} | Tests: {t.test_file_count}</p>"
        f'<pre class="mermaid">{mermaid}</pre></div>'
    )


def _render_axes_body(report: DeepAuditReport) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(a.axis)}</td><td>{html.escape(a.status)}</td><td>{html.escape(a.summary)}</td></tr>"
        for a in report.axes
    )
    return (
        '<div class="card"><h2>4-Axis Introspection Matrix</h2>'
        f"<table><tr><th>Axis</th><th>Status</th><th>Summary</th></tr>{rows}</table></div>"
    )


def generate_audit_visual_briefs(
    report: DeepAuditReport,
    output_dir: Path | str | None = None,
) -> VisualBriefPaths:
    """Write the three dark-mode HTML visual briefs cleanly to disk."""
    target_dir = Path(output_dir) if output_dir is not None else Path(tempfile.gettempdir())
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())

    compute_file = target_dir / f"compute-assessor-{ts}.html"
    topology_file = target_dir / f"data-topology-review-{ts}.html"
    repo_file = target_dir / f"repo-reader-{ts}.html"

    compute_file.write_text(
        _render_shell(
            title="Compute Complexity Assessment",
            subtitle=f"Target: {report.resolved_root} | Tier: {report.compute.tier}",
            body_html=_render_compute_body(report),
            payload=report.compute.to_dict(),
        ),
        encoding="utf-8",
    )
    topology_file.write_text(
        _render_shell(
            title="Data Topology & Blast Radius Review",
            subtitle=f"Pattern: {report.topology.topology_pattern}",
            body_html=_render_topology_body(report),
            payload=report.topology.to_dict(),
        ),
        encoding="utf-8",
    )
    repo_file.write_text(
        _render_shell(
            title="4-Axis Codebase Introspection Matrix",
            subtitle=f"Root: {report.resolved_root}",
            body_html=_render_axes_body(report),
            payload=report.to_dict(),
        ),
        encoding="utf-8",
    )

    return VisualBriefPaths(
        compute_brief=str(compute_file.resolve()),
        topology_brief=str(topology_file.resolve()),
        repo_reader_brief=str(repo_file.resolve()),
        output_dir=str(target_dir.resolve()),
    )


__all__ = ["generate_audit_visual_briefs"]
