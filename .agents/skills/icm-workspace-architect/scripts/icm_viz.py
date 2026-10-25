# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Draw one or more graph files written by icm_links.py into an interactive HTML visualization.

Usage:
    python icm_viz.py graph.jsonl [-o viz.html]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Render interactive Cytoscape.js visualization from graph JSONL.")
    parser.add_argument("graph_files", nargs="+", help="JSONL graph file(s) from icm_links.py")
    parser.add_argument("-o", "--output", default="viz.html", help="Output HTML file path")
    args = parser.parse_args()

    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []

    for gf in args.graph_files:
        p = Path(gf)
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if "node" in item:
                nodes.append(item["node"])
            elif "edge" in item:
                edges.append(item["edge"])

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ICM Workspace Graph</title>
  <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
  <style>
    body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; margin: 0; }}
    #cy {{ width: 100vw; height: 100vh; display: block; }}
  </style>
</head>
<body>
  <div id="cy"></div>
  <script>
    const elements = [
      {", ".join(f"{{ data: {{ id: '{n['path']}', label: '{n.get('title', n['path'])}' }} }}" for n in nodes)},
      {", ".join(f"{{ data: {{ source: '{e['source']}', target: '{e['target']}' }} }}" for e in edges)}
    ];
    cytoscape({{
      container: document.getElementById('cy'),
      elements: elements,
      style: [
        {{ selector: 'node', style: {{ 'background-color': '#238636', 'label': 'data(label)', 'color': '#c9d1d9' }} }},
        {{ selector: 'edge', style: {{ 'width': 2, 'line-color': '#58a6ff', 'target-arrow-color': '#58a6ff', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' }} }}
      ],
      layout: {{ name: 'cose', animate: false }}
    }});
  </script>
</body>
</html>
"""
    out_p = Path(args.output).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(html_content, encoding="utf-8")
    print(f"Visualized {len(nodes)} nodes and {len(edges)} edges -> {out_p}")


if __name__ == "__main__":
    main()
