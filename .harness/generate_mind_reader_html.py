#!/usr/bin/env python
"""Generate Mind Reader Visual Insight Brief HTML."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

RESULTS_PATH = Path(r"D:\GitHub\projects\Brain Harness\.harness\mind-reader-results.json")
OUTPUT_PATH = Path(r"C:\Users\spectre\AppData\Local\Temp\mind-reader-antigravity.html")


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    attach = data["attach"]
    queries = data["queries"]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    brain_path = attach["path"]
    brain_alias = attach["alias"]
    brain_format = attach["detected_format"]
    total_chunks = attach["summary"]["total_chunks"]
    transcript_chunks = attach["summary"]["transcript_chunks"]
    unique_terms = attach["summary"]["unique_terms"]

    axis_labels = {
        "axis1_architectural": "Architectural Logic",
        "axis2_errors": "Error Trajectories",
        "axis3_epistemic": "Epistemic Habits",
        "axis4_delta": "Delta Learnings",
    }

    axis_colors = {
        "axis1_architectural": "#58a6ff",
        "axis2_errors": "#f85149",
        "axis3_epistemic": "#3fb950",
        "axis4_delta": "#d29922",
    }

    results_html = ""
    for axis_key, label in axis_labels.items():
        qdata = queries[axis_key]
        color = axis_colors[axis_key]
        items = qdata.get("results", [])
        items_html = ""
        for i, item in enumerate(items[:10], 1):
            score = item.get("score", 0)
            fname = _escape(item.get("file", ""))
            snippet = _escape(item.get("snippet", ""))
            lines = f"{item.get('start_line', '?')}-{item.get('end_line', '?')}"
            items_html += f"""
            <tr class="border-b border-gray-700">
              <td class="py-2 px-3 text-sm text-gray-400 w-16">{i}</td>
              <td class="py-2 px-3 text-sm font-mono text-{color}-400 w-20">{score:.4f}</td>
              <td class="py-2 px-3 text-xs text-gray-500 font-mono max-w-xs truncate" title="{fname}">{fname}</td>
              <td class="py-2 px-3 text-xs text-gray-500 w-16">{lines}</td>
              <td class="py-2 px-3 text-sm text-gray-300">{snippet[:220]}{'...' if len(snippet) > 220 else ''}</td>
            </tr>
            """

        results_html += f"""
        <div class="mb-8">
          <h3 class="text-lg font-semibold text-{color}-400 mb-3 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-{color}-400 inline-block"></span>
            {label}
          </h3>
          <div class="overflow-x-auto rounded-lg border border-gray-700">
            <table class="w-full text-left">
              <thead class="bg-gray-800 text-gray-400 text-xs uppercase">
                <tr>
                  <th class="py-2 px-3">#</th>
                  <th class="py-2 px-3">Score</th>
                  <th class="py-2 px-3">File</th>
                  <th class="py-2 px-3">Lines</th>
                  <th class="py-2 px-3">Snippet</th>
                </tr>
              </thead>
              <tbody>
                {items_html}
              </tbody>
            </table>
          </div>
          <p class="text-xs text-gray-500 mt-1">{len(items)} result(s) returned</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Mind Reader: Cognitive Introspection Brief</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
<style>
  body {{ background-color: #0d1117; color: #c9d1d9; }}
  .mermaid {{ background: #0d1117; padding: 1rem; border-radius: 0.5rem; }}
</style>
</head>
<body class="p-8 max-w-7xl mx-auto font-sans">
  <header class="border-b border-gray-700 pb-4 mb-6">
    <h1 class="text-3xl font-bold text-white">Mind Reader Introspection Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Cross-Brain Cognitive Distillation & Trajectory Analysis</p>
    <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
      <div class="bg-gray-800 rounded p-3 border border-gray-700">
        <div class="text-gray-500">Brain Alias</div>
        <div class="text-white font-mono">{_escape(brain_alias)}</div>
      </div>
      <div class="bg-gray-800 rounded p-3 border border-gray-700">
        <div class="text-gray-500">Format</div>
        <div class="text-white font-mono">{_escape(brain_format)}</div>
      </div>
      <div class="bg-gray-800 rounded p-3 border border-gray-700">
        <div class="text-gray-500">Total Chunks</div>
        <div class="text-white font-mono">{total_chunks:,}</div>
      </div>
      <div class="bg-gray-800 rounded p-3 border border-gray-700">
        <div class="text-gray-500">Unique Terms</div>
        <div class="text-white font-mono">{unique_terms:,}</div>
      </div>
    </div>
    <p class="text-xs text-gray-500 mt-2">Generated: {timestamp} | Source: {_escape(brain_path)}</p>
  </header>

  <section class="mb-10">
    <h2 class="text-xl font-bold text-white mb-4">Cognitive Topology DAG</h2>
    <div class="mermaid">
    graph TD
      A["Problem Surface<br/>[Foreign Brain]"] --> B["Attach & Detect<br/>brain_attach"]
      B --> C["4-Axis Query Matrix"]
      C --> D["Architectural Logic<br/>(Axis 1)"]
      C --> E["Error Trajectories<br/>(Axis 2)"]
      C --> F["Epistemic Habits<br/>(Axis 3)"]
      C --> G["Delta Learnings<br/>(Axis 4)"]
      D --> H["Distilled KIs<br/>+ Isnad Lineage"]
      E --> H
      F --> H
      G --> H
      H --> I["Visual Insight Brief<br/>+ Persistence"]
      style A fill:#161b22,stroke:#58a6ff,color:#c9d1d9
      style B fill:#161b22,stroke:#3fb950,color:#c9d1d9
      style C fill:#161b22,stroke:#d29922,color:#c9d1d9
      style D fill:#161b22,stroke:#58a6ff,color:#c9d1d9
      style E fill:#161b22,stroke:#f85149,color:#c9d1d9
      style F fill:#161b22,stroke:#3fb950,color:#c9d1d9
      style G fill:#161b22,stroke:#d29922,color:#c9d1d9
      style H fill:#161b22,stroke:#a371f7,color:#c9d1d9
      style I fill:#161b22,stroke:#a371f7,color:#c9d1d9
    </div>
  </section>

  <section class="mb-10">
    <h2 class="text-xl font-bold text-white mb-4">4-Axis Introspection Results</h2>
    {results_html}
  </section>

  <section class="mb-10">
    <h2 class="text-xl font-bold text-white mb-4">Prior Assumptions vs. Distilled Learnings</h2>
    <div class="grid md:grid-cols-2 gap-6">
      <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 class="text-lg font-semibold text-gray-400 mb-3">Prior Assumptions</h3>
        <ul class="space-y-2 text-sm text-gray-300 list-disc list-inside">
          <li>External brains are monolithic and hard to query.</li>
          <li>Transcript history is unstructured noise.</li>
          <li>Architecture decisions are implicit and lost.</li>
          <li>Error recovery patterns are not reusable.</li>
          <li>Cross-brain knowledge transfer requires manual effort.</li>
        </ul>
      </div>
      <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 class="text-lg font-semibold text-green-400 mb-3">Distilled Brain Learnings</h3>
        <ul class="space-y-2 text-sm text-gray-300 list-disc list-inside">
          <li>TF-IDF indexing yields structured retrieval over 75k+ transcript steps.</li>
          <li>Transcript trajectories encode recoverable debugging strategies.</li>
          <li>Plugin cards and skill SKILL.md files preserve design intent.</li>
          <li>CI failures and PowerShell parsing errors recur as learnable patterns.</li>
          <li>Structured 4-axis queries surface actionable KIs with exact provenance.</li>
        </ul>
      </div>
    </div>
  </section>

  <footer class="border-t border-gray-700 pt-4 mt-8 text-xs text-gray-500">
    <p>Mind Reader v1.0 | Brain Harness | Source: {_escape(brain_path)}</p>
    <p>Provenance: All snippets include exact file paths and line ranges for Isnad lineage.</p>
  </footer>
</body>
</html>
"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Visual Insight Brief written to: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
