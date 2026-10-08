"""Interactive HTML visual brief generator and Mermaid diagram builder for Open-Source GIS."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GisVisualBriefResult,
    SpatialPipelineDAG,
    SpatialWorkloadProfile,
    TopologyAuditReport,
)


def generate_visual_brief(
    profile: SpatialWorkloadProfile,
    selection: EngineSelectionResult,
    dag: SpatialPipelineDAG | None = None,
    topology: TopologyAuditReport | None = None,
    output_path: str | Path | None = None,
) -> GisVisualBriefResult:
    """Generate self-contained dark-theme HTML visual brief complying with Rule 51."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    if output_path:
        p = Path(output_path)
    else:
        temp_dir = Path(tempfile.gettempdir())
        p = temp_dir / f"gis-architect-{timestamp}.html"

    # Build Mermaid DAG diagram
    mermaid_lines = ["flowchart LR"]
    mermaid_lines.append(f'  Input["Data: {profile.geometry_type}<br/>Domain: {profile.domain}"]')
    mermaid_lines.append(f'  Engine["Primary: {selection.primary.engine.name}<br/>Score: {selection.primary.fitness_score}"]')
    mermaid_lines.append("  Input --> Engine")

    node_count = 2
    if dag and dag.steps:
        prev_node = "Engine"
        for step in dag.steps:
            s_name = f"Step{step.step_id}"
            mermaid_lines.append(f'  {s_name}["Step {step.step_id}: {step.operation}<br/>CRS: {step.input_crs} &rarr; {step.output_crs}"]')
            mermaid_lines.append(f"  {prev_node} --> {s_name}")
            prev_node = s_name
            node_count += 1
        mermaid_lines.append(f'  Out["Deliverable: {profile.output_type}"]')
        mermaid_lines.append(f"  {prev_node} --> Out")
        node_count += 1
    else:
        mermaid_lines.append(f'  Out["Deliverable: {profile.output_type}"]')
        mermaid_lines.append("  Engine --> Out")
        node_count += 1

    mermaid_str = "\n".join(mermaid_lines)

    topo_html = ""
    if topology:
        badge_color = "emerald" if topology.is_valid else ("amber" if topology.severity == "WARNING" else "rose")
        topo_html = f"""
        <div class="bg-gray-800/60 border border-gray-700 rounded-xl p-5 mb-6">
          <div class="flex justify-between items-center mb-3">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <span>📐</span> Topology Hygiene Audit
            </h3>
            <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-{badge_color}-900/60 text-{badge_color}-300 border border-{badge_color}-700">
              {topology.severity}
            </span>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div class="bg-gray-900/80 p-2.5 rounded border border-gray-800">
              <div class="text-gray-400">Self-Intersections</div>
              <div class="text-lg font-bold {'text-rose-400' if topology.self_intersection_count > 0 else 'text-gray-200'}">{topology.self_intersection_count}</div>
            </div>
            <div class="bg-gray-900/80 p-2.5 rounded border border-gray-800">
              <div class="text-gray-400">Unclosed Rings</div>
              <div class="text-lg font-bold {'text-rose-400' if topology.unclosed_rings > 0 else 'text-gray-200'}">{topology.unclosed_rings}</div>
            </div>
            <div class="bg-gray-900/80 p-2.5 rounded border border-gray-800">
              <div class="text-gray-400">Sliver Polygons</div>
              <div class="text-lg font-bold {'text-amber-400' if topology.sliver_count > 0 else 'text-gray-200'}">{topology.sliver_count}</div>
            </div>
            <div class="bg-gray-900/80 p-2.5 rounded border border-gray-800">
              <div class="text-gray-400">Duplicate Vertices</div>
              <div class="text-lg font-bold text-gray-200">{topology.duplicate_vertices}</div>
            </div>
          </div>
        </div>
        """

    sec_name = selection.secondary.engine.name if selection.secondary else "None"
    sec_score = f"{selection.secondary.fitness_score:.2f}" if selection.secondary else "N/A"

    # Static template conforming to Rule 51
    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>Spatial Architecture Brief: {profile.domain}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#0d1117',
        primaryColor: '#238636',
        primaryTextColor: '#c9d1d9',
        primaryBorderColor: '#30363d',
        lineColor: '#58a6ff'
      }}
    }});
  </script>
  <style>
    body {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  </style>
</head>
<body class="p-8 max-w-5xl mx-auto">
  <header class="border-b border-gray-700 pb-5 mb-6 flex justify-between items-center">
    <div>
      <span class="px-2.5 py-0.5 bg-emerald-900 text-emerald-300 text-xs font-semibold rounded-full border border-emerald-700">Stage 5 Visual Brief</span>
      <h1 class="text-2xl font-bold mt-2 text-white flex items-center gap-2">
        <span>🗺️</span> Spatial Architecture Decision Brief
      </h1>
      <p class="text-gray-400 text-xs mt-1">Domain: <code class="text-sky-400">{profile.domain}</code> &bull; Geometry: <code class="text-emerald-400">{profile.geometry_type}</code></p>
    </div>
    <div class="text-right text-xs text-gray-400">
      <div>Generated: {timestamp}</div>
      <div class="text-emerald-400 font-mono">Routing: {selection.routing_path}</div>
    </div>
  </header>

  <!-- Engine Selection Card -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
    <div class="bg-gray-800/60 border border-emerald-700/60 rounded-xl p-5">
      <div class="text-xs uppercase tracking-wider text-emerald-400 font-bold mb-1">Primary Engine Selection</div>
      <div class="text-2xl font-black text-white">{selection.primary.engine.name}</div>
      <div class="text-xs text-gray-300 mt-1">{selection.rationale}</div>
      <div class="mt-3 flex gap-2 text-xs font-medium">
        <span class="px-2 py-0.5 bg-emerald-950 text-emerald-300 rounded border border-emerald-800">Fitness: {selection.primary.fitness_score:.2f}</span>
        <span class="px-2 py-0.5 bg-gray-900 text-gray-300 rounded border border-gray-700">License: {selection.primary.engine.license}</span>
        <span class="px-2 py-0.5 bg-gray-900 text-gray-300 rounded border border-gray-700">Rating: {selection.primary.engine.star_rating}★</span>
      </div>
    </div>
    <div class="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
      <div class="text-xs uppercase tracking-wider text-gray-400 font-bold mb-1">Secondary / Fallback Engine</div>
      <div class="text-2xl font-bold text-gray-200">{sec_name}</div>
      <div class="text-xs text-gray-400 mt-1">Designated alternative for failover or secondary raster processing.</div>
      <div class="mt-3 flex gap-2 text-xs font-medium">
        <span class="px-2 py-0.5 bg-gray-900 text-gray-400 rounded border border-gray-800">Fitness: {sec_score}</span>
      </div>
    </div>
  </div>

  <!-- Topology Audit Card -->
  {topo_html}

  <!-- Pipeline DAG -->
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
    <h3 class="text-base font-bold text-white mb-3 flex items-center gap-2">
      <span>⚡</span> Spatial Execution Pipeline DAG
    </h3>
    <pre class="mermaid text-xs">
{mermaid_str}
    </pre>
  </div>

  <footer class="pt-4 border-t border-gray-800 text-xs text-center text-gray-500">
    Harness Open-Source GIS Architect Service &bull; Generated autonomously
  </footer>
</body>
</html>
"""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    report_url = p.as_uri()

    return GisVisualBriefResult(
        report_path=str(p),
        report_url=report_url,
        rendered_nodes=node_count,
        timestamp=timestamp,
    )


__all__ = ["generate_visual_brief"]
