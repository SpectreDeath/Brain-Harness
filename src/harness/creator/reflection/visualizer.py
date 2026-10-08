"""Visual brief generator synthesizing interactive HTML reflection dashboards."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

from harness.creator.reflection.models import (
    DistilledHeuristic,
    ReportArtifact,
    TranscriptSession,
)
from harness.services.storage import KnowledgeItemRecord


def generate_reflection_html_brief(
    output_dir: Path,
    reflection_id: str,
    reports: Sequence[ReportArtifact],
    transcripts: Sequence[TranscriptSession],
    heuristics: Sequence[DistilledHeuristic],
    kis: Sequence[KnowledgeItemRecord],
) -> Path:
    """Generate an interactive dark-mode HTML reflection brief in the specified directory."""
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    temp_file = output_dir / f"harness-reflection-{date_str}.html"

    # Build heuristics table rows
    h_rows = []
    for h in heuristics:
        cat_badge = (
            f"<span class='px-2 py-0.5 rounded text-xs font-semibold bg-indigo-900/60 "
            f"text-indigo-300 border border-indigo-700'>{h.category}</span>"
        )
        sources_str = ", ".join(Path(s).name for s in h.source_artifacts[:3])
        h_rows.append(
            f"<tr class='border-b border-gray-800 hover:bg-gray-800/40 transition'>"
            f"<td class='py-3 px-4 font-medium text-gray-200'>{h.title}</td>"
            f"<td class='py-3 px-4'>{cat_badge}</td>"
            f"<td class='py-3 px-4 text-sm text-gray-300'>{h.heuristic}</td>"
            f"<td class='py-3 px-4 text-xs font-mono text-gray-400'>{sources_str}</td>"
            f"</tr>"
        )
    h_table_html = "\n".join(h_rows) if h_rows else "<tr><td colspan='4' class='p-4 text-center text-gray-500'>No new heuristics distilled.</td></tr>"

    # Build Mermaid lineage DAG
    mermaid_lines = [
        "graph TD",
        "  subgraph EphemeralMemory[\"1. Ephemeral Execution Residue\"]",
        f"    R[\"{len(reports)} HTML Visual Briefs in %TEMP%\"]",
        f"    T[\"{len(transcripts)} Conversation Transcripts\"]",
        "  end",
        "  subgraph ReflectionEngine[\"2. Harness Reflector Engine\"]",
        "    H[\"MemoryPatternPipeline Distillation\"]",
        "    I[\"Aquinas Isnad Provenance Audit\"]",
        "  end",
        "  subgraph KnowledgeVault[\"3. Persistent Knowledge Vault\"]",
        f"    V[\"{len(kis)} Verified Knowledge Items (KIs)\"]",
        "    G[\"Skill & Module Knowledge Graph\"]",
        "  end",
        "  R --> H",
        "  T --> H",
        "  H --> I",
        "  I --> V",
        "  V --> G",
    ]
    mermaid_code = "\n".join(mermaid_lines)

    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Harness Memory Reflection — {reflection_id}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
</head>
<body class="bg-[#0d1117] text-gray-100 min-h-screen p-8 font-sans">
  <div class="max-w-6xl mx-auto space-y-8">
    
    <!-- Header -->
    <header class="border-b border-gray-800 pb-6">
      <div class="flex items-center justify-between">
        <div>
          <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 mb-3">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Endogenous Memory Reflection
          </div>
          <h1 class="text-3xl font-bold tracking-tight text-white">Autobiographical Cognitive Synthesis</h1>
          <p class="text-sm text-gray-400 mt-1">Distilling internal HTML reviews, conversation transcripts, and execution trajectories into the Knowledge Vault.</p>
        </div>
        <div class="text-right text-xs text-gray-500 font-mono">
          <div>ID: {reflection_id}</div>
          <div>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
      </div>
    </header>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Harvested Reports</div>
        <div class="text-3xl font-bold text-indigo-400 mt-2">{len(reports)}</div>
        <div class="text-xs text-gray-500 mt-1">HTML briefs in %TEMP%</div>
      </div>
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Parsed Transcripts</div>
        <div class="text-3xl font-bold text-cyan-400 mt-2">{len(transcripts)}</div>
        <div class="text-xs text-gray-500 mt-1">Conversation step logs</div>
      </div>
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Distilled Heuristics</div>
        <div class="text-3xl font-bold text-emerald-400 mt-2">{len(heuristics)}</div>
        <div class="text-xs text-gray-500 mt-1">Actionable invariants</div>
      </div>
      <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
        <div class="text-xs uppercase tracking-wider text-gray-400 font-semibold">Committed KIs</div>
        <div class="text-3xl font-bold text-purple-400 mt-2">{len(kis)}</div>
        <div class="text-xs text-gray-500 mt-1">Ground-truth vault items</div>
      </div>
    </div>

    <!-- Lineage Graph -->
    <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Memory Ingestion & Isnad Lineage Topology</h2>
      <div class="mermaid bg-black/40 p-4 rounded-lg flex justify-center">
{mermaid_code}
      </div>
    </div>

    <!-- Distilled Heuristics Matrix -->
    <div class="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Distilled Architectural Invariants & Heuristics</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-gray-800 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-950/50">
              <th class="py-3 px-4">Title</th>
              <th class="py-3 px-4">Category</th>
              <th class="py-3 px-4">Actionable Heuristic & Invariant</th>
              <th class="py-3 px-4">Grounding Sources</th>
            </tr>
          </thead>
          <tbody>
            {h_table_html}
          </tbody>
        </table>
      </div>
    </div>

    <footer class="text-center text-xs text-gray-600 pt-4 border-t border-gray-900">
      Brain Harness Endogenous Reflection Engine • Grounded Epistemic Isnad
    </footer>
  </div>
</body>
</html>
"""
    temp_file.write_text(html_content, encoding="utf-8")
    return temp_file


__all__ = [
    "generate_reflection_html_brief",
]
