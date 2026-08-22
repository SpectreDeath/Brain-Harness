"""Interactive HTML Visual Brief generator for the Skill Knowledge Graph."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from .graph import SkillKnowledgeGraph


class SkillGraphVisualizer:
    """Renders interactive HTML reports visualizing the agent skill network."""

    @classmethod
    def render_html(cls, graph: SkillKnowledgeGraph, output_path: str | None = None) -> str:
        """Generate and save an interactive HTML visual brief in %TEMP%."""
        timestamp = int(time.time())
        if output_path:
            target = Path(output_path)
        else:
            temp_dir = Path(tempfile.gettempdir())
            target = temp_dir / f"skill-graph-{timestamp}.html"

        mermaid_code = graph.generate_mermaid()
        snapshot = graph.get_snapshot()

        # Build skill cards HTML
        cards_html = []
        for name, node in sorted(graph.nodes.items()):
            triggers_badges = "".join(
                f'<span class="bg-[#1f242c] text-[#58a6ff] px-2 py-0.5 rounded text-xs mr-1 mb-1 inline-block border border-[#30363d]">{t}</span>'
                for t in node.triggers[:4]
            )
            stages_list = "".join(
                f'<li class="text-xs text-gray-400 mb-0.5"><span class="text-emerald-400 font-mono">Stage {s.stage_num}:</span> {s.name}</li>'
                for s in node.stages[:4]
            )
            ap_badges = "".join(
                f'<span class="bg-[#2d1f1f] text-[#ff7b72] px-2 py-0.5 rounded text-xs mr-1 mb-1 inline-block border border-[#492424]">{ap.name}</span>'
                for ap in node.anti_patterns[:3]
            )

            card = f"""
            <div class="bg-[#161b22] border border-[#30363d] rounded-lg p-4 hover:border-[#58a6ff] transition-all flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <h3 class="font-bold text-base text-white">{node.name}</h3>
                  <span class="text-xs px-2 py-0.5 rounded bg-[#21262d] text-gray-300 border border-[#30363d]">{node.category}</span>
                </div>
                <p class="text-xs text-gray-300 mb-3">{node.target or node.description[:120]}</p>
                <div class="mb-3">
                  <div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">Triggers</div>
                  <div class="flex flex-wrap">{triggers_badges or '<span class="text-xs text-gray-500">None</span>'}</div>
                </div>
                {f'<div class="mb-3"><div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">Stages</div><ul class="list-none pl-0">{stages_list}</ul></div>' if stages_list else ''}
                {f'<div><div class="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">Anti-Patterns Guarded</div><div class="flex flex-wrap">{ap_badges}</div></div>' if ap_badges else ''}
              </div>
              <div class="mt-4 pt-3 border-t border-[#21262d] flex justify-between items-center text-[11px] text-gray-400">
                <span>{node.invocation or f'/{node.name}'}</span>
                <span class="text-gray-500">v{node.version}</span>
              </div>
            </div>
            """
            cards_html.append(card)

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
        <span class="bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40 text-xs px-2.5 py-1 rounded-full font-mono">v1.0.0</span>
      </div>
      <p class="text-sm text-gray-400 mt-1">Autonomous Skill Topology, Chaining & Anti-Pattern Defense Network</p>
    </div>
    <div class="flex items-center gap-4 text-xs font-mono">
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">TOTAL SKILLS</div>
        <div class="text-lg font-bold text-emerald-400">{snapshot.total_skills}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">CATEGORIES</div>
        <div class="text-lg font-bold text-[#58a6ff]">{len(snapshot.categories)}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] px-3 py-2 rounded-lg text-center">
        <div class="text-gray-400 text-[10px]">RELATION EDGES</div>
        <div class="text-lg font-bold text-purple-400">{len(snapshot.edges)}</div>
      </div>
    </div>
  </header>

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
      {''.join(cards_html)}
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
