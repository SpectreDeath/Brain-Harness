"""Interactive HTML Visual Brief generator for the Skill Knowledge Graph.

Renders rich dark-mode HTML reports visualizing the agent skill network,
clusters, emergent capabilities, and dependency DAG topology in %TEMP%.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

from harness.services.skill_clustering import SkillClusteringEngine


class SkillGraphVisualizer:
    """Renders interactive HTML reports visualizing the agent skill network."""

    @classmethod
    def render_html(
        cls, graph: Any, output_path: str | None = None
    ) -> str:
        """Generate and save an interactive HTML visual brief in %TEMP%."""
        timestamp = int(time.time())
        if output_path:
            target = Path(output_path)
        else:
            temp_dir = Path(tempfile.gettempdir())
            target = temp_dir / f"skill-graph-{timestamp}.html"

        # Determine nodes and edges from either SkillKnowledgeGraph or BuiltinSkillRegistryService
        if hasattr(graph, "nodes") and isinstance(graph.nodes, dict):
            nodes_dict = graph.nodes
            total_skills = len(nodes_dict)
            edges_list = getattr(graph, "edges", [])
        elif hasattr(graph, "_skills_cache"):
            nodes_dict = graph._skills_cache
            total_skills = len(nodes_dict)
            edges_list = getattr(graph, "_edges", [])
        elif hasattr(graph, "discover_all"):
            skills = graph.discover_all()
            nodes_dict = {s.name: s for s in skills}
            total_skills = len(nodes_dict)
            edges_list = getattr(graph, "edges", [])
        else:
            nodes_dict = {}
            total_skills = 0
            edges_list = []

        # Generate Mermaid code
        if hasattr(graph, "generate_mermaid"):
            mermaid_code = graph.generate_mermaid()
        else:
            mermaid_lines = ["flowchart TD"]
            for s_name, s_def in sorted(nodes_dict.items()):
                clean_id = s_name.replace("-", "_")
                mermaid_lines.append(f'  {clean_id}["{s_name}"]')
                deps = getattr(s_def, "dependencies", []) or getattr(s_def, "references", [])
                for dep in deps:
                    clean_dep = dep.replace("-", "_")
                    mermaid_lines.append(f"  {clean_id} -.->|requires| {clean_dep}")
            mermaid_code = "\n".join(mermaid_lines)

        # Build skill cards HTML
        cards_html = []
        for name, node in sorted(nodes_dict.items()):
            triggers = getattr(node, "triggers", []) or []
            triggers_badges = "".join(
                f'<span class="bg-[#1f242c] text-[#58a6ff] px-2 py-0.5 rounded text-xs mr-1 mb-1 inline-block border border-[#30363d]">{t}</span>'
                for t in triggers[:4]
            )
            stages = getattr(node, "stages", []) or []
            stages_list = "".join(
                f'<li class="text-xs text-gray-400 mb-0.5"><span class="text-emerald-400 font-mono">Stage {getattr(s, "stage_num", idx)}:</span> {getattr(s, "name", str(s))}</li>'
                for idx, s in enumerate(stages[:4], start=1)
            )
            anti_patterns = getattr(node, "anti_patterns", []) or []
            ap_badges = "".join(
                f'<span class="bg-[#2d1f1f] text-[#ff7b72] px-2 py-0.5 rounded text-xs mr-1 mb-1 inline-block border border-[#492424]">{getattr(ap, "name", str(ap))}</span>'
                for ap in anti_patterns[:3]
            )

            target_text = getattr(node, "target", "") or getattr(node, "description", "") or ""
            card = f"""
            <div class="bg-[#161b22] border border-[#30363d] rounded-lg p-4 hover:border-[#58a6ff] transition-all flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <h3 class="font-bold text-base text-white">{node.name}</h3>
                  <span class="text-xs px-2 py-0.5 rounded bg-[#21262d] text-gray-300 border border-[#30363d]">{getattr(node, "category", "general")}</span>
                </div>
                <p class="text-xs text-gray-300 mb-3">{target_text[:120]}</p>
                <div class="mb-3">
                  <div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">Triggers</div>
                  <div class="flex flex-wrap">{triggers_badges or '<span class="text-xs text-gray-500">None</span>'}</div>
                </div>
                {f'<div class="mb-3"><div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">Stages</div><ul class="list-none pl-0">{stages_list}</ul></div>' if stages_list else ""}
                {f'<div><div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">Anti-Patterns Guarded</div><div class="flex flex-wrap">{ap_badges}</div></div>' if ap_badges else ""}
              </div>
              <div class="mt-4 pt-3 border-t border-[#21262d] flex justify-between items-center text-[11px] text-gray-400">
                <span>{getattr(node, "invocation", "") or f"/{node.name}"}</span>
                <span class="text-gray-500">v{getattr(node, "version", "1.0.0")}</span>
              </div>
            </div>
            """
            cards_html.append(card)

        # Compute clusters and emergent capabilities
        engine = SkillClusteringEngine(nodes_dict)
        clusters = engine.cluster_skills(min_cluster_size=2)
        capabilities = engine.discover_emergent_capabilities()

        clusters_html = []
        for c in clusters:
            emergent_items = "".join(
                f'<div class="mt-2 bg-[#0d1117] p-2.5 rounded border border-[#238636]/40">'
                f'<div class="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">'
                f"<span>✨</span><span>{cap.title}</span>"
                f"</div>"
                f'<p class="text-[11px] text-gray-300 mt-1">{cap.novelty_rationale}</p>'
                f'<div class="text-[10px] text-gray-400 mt-1.5"><span class="text-gray-500 font-mono">Pipeline:</span> {" &rarr; ".join(cap.recommended_pipeline)}</div>'
                f"</div>"
                for cap in c.emergent_capabilities
            )
            member_badges = "".join(
                f'<span class="bg-[#1f242c] text-[#58a6ff] px-2 py-0.5 rounded text-[11px] mr-1 mb-1 inline-block border border-[#30363d]">{s}</span>'
                for s in c.skills
            )
            c_card = f"""
            <div class="bg-[#161b22] border border-[#30363d] rounded-xl p-5 hover:border-[#58a6ff] transition-all">
              <div class="flex items-center justify-between mb-2">
                <h3 class="font-bold text-base text-white">{c.name}</h3>
                <span class="text-xs px-2 py-0.5 rounded bg-emerald-900/40 text-emerald-300 border border-emerald-700/50 font-mono">Cohesion {int(c.cohesion_score * 100)}%</span>
              </div>
              <div class="text-xs text-gray-400 mb-3 flex items-center gap-2">
                <span>Hub: <strong class="text-cyan-400 font-mono">{c.central_hub_skill}</strong></span>
                <span>&bull;</span>
                <span>{len(c.skills)} Skills</span>
                <span>&bull;</span>
                <span>{c.internal_edge_count} Edges</span>
              </div>
              <div class="mb-3">
                <div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1.5">Domain Skills</div>
                <div class="flex flex-wrap">{member_badges}</div>
              </div>
              {f'<div><div class="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold mb-1">Emergent Macro-Capabilities</div>{emergent_items}</div>' if emergent_items else ""}
            </div>
            """
            clusters_html.append(c_card)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Skill Knowledge Graph Topology</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        primaryColor: '#1f6feb',
        primaryTextColor: '#f0f6fc',
        primaryBorderColor: '#388bfd',
        lineColor: '#58a6ff',
        secondaryColor: '#238636',
        tertiaryColor: '#161b22',
        background: '#0d1117'
      }}
    }});
  </script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] font-sans antialiased p-6 md:p-10 max-w-7xl mx-auto min-h-screen">
  
  <!-- Header -->
  <header class="border-b border-[#30363d] pb-6 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div>
      <div class="flex items-center gap-3">
        <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight">Agent Skill Knowledge Graph</h1>
        <span class="bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40 text-xs px-2.5 py-1 rounded-full font-mono">v1.1.0</span>
      </div>
      <p class="text-sm text-gray-400 mt-1">Autonomous Skill Topology, Graph Clusters & Emergent Capability Network</p>
    </div>
    <div class="flex flex-wrap items-center gap-3 text-xs font-mono">
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">TOTAL SKILLS</div>
        <div class="text-lg font-bold text-emerald-400">{total_skills}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">CLUSTERS</div>
        <div class="text-lg font-bold text-cyan-400">{len(clusters)}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">CAPABILITIES</div>
        <div class="text-lg font-bold text-amber-400">{len(capabilities)}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">RELATION EDGES</div>
        <div class="text-lg font-bold text-purple-400">{len(edges_list)}</div>
      </div>
    </div>
  </header>

  <!-- Discovered Skill Clusters & Emergent Capabilities Section -->
  <section class="mb-10">
    <div class="flex items-center justify-between mb-4 border-b border-[#21262d] pb-3">
      <h2 class="text-lg font-semibold text-white flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
        Discovered Capability Clusters & Emergent Super-Pipelines
      </h2>
      <span class="text-xs text-gray-400 font-mono">{len(clusters)} functional clusters</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {"".join(clusters_html)}
    </div>
  </section>

  <!-- Interactive Mermaid Topology Graph -->
  <section class="mb-10 bg-[#161b22] border border-[#30363d] rounded-xl p-6 shadow-xl">
    <div class="flex items-center justify-between mb-4 border-b border-[#21262d] pb-3">
      <h2 class="text-lg font-semibold text-white flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        Skill Network DAG & Precedence Matrix
      </h2>
      <span class="text-xs text-gray-400 font-mono">Arrows: Solid = Precedes, Dashed = Requires</span>
    </div>
    <div class="mermaid flex justify-center overflow-x-auto py-4">
{mermaid_code}
    </div>
  </section>

  <!-- Skill Catalog Cards Grid -->
  <section>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-semibold text-white">Indexed Skill Cards</h2>
      <span class="text-xs text-gray-400">Parsed from .agents/skills/ and plugins/</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {"".join(cards_html)}
    </div>
  </section>

  <!-- Footer -->
  <footer class="mt-12 pt-6 border-t border-[#30363d] text-center text-xs text-gray-500">
    Harness Knowledge Graph Engine &bull; Generated dynamically in %TEMP%
  </footer>

</body>
</html>
"""
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html_content, encoding="utf-8")
        return str(target.resolve())
