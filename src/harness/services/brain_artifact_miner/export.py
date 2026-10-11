"""Visual brief generation and canonical Knowledge Vault exporting (Rule 40, Rule 41, Rule 51)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def generate_html_brief(data: dict[str, Any]) -> str:
    """Synthesize an HTML visual brief with double-brace escaped CSS/regex (Rule 51)."""
    title = data.get("title", "Brain Artifact Miner Visual Brief")
    total_dirs = data.get("total_dirs", 0)
    scratch_count = data.get("scratch_count", 0)
    task_count = data.get("task_count", 0)
    failed_tasks = data.get("failed_tasks", 0)
    categories = data.get("categories", {})

    category_rows = "".join(
        f"<tr><td class='px-4 py-2 font-mono text-sm'>{cat}</td><td class='px-4 py-2 text-right font-bold'>{len(items)}</td></tr>"
        for cat, items in categories.items()
    )

    # Rule 51: All literal CSS/JS braces must be doubled {{ }}
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{ startOnLoad: true }});</script>
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }}
    .card {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.1); }}
  </style>
</head>
<body class="p-8 max-w-6xl mx-auto">
  <div class="mb-8 border-b border-slate-700 pb-4">
    <h1 class="text-3xl font-extrabold text-indigo-400">{title}</h1>
    <p class="text-slate-400 mt-1">Filesystem-Native Epistemic Workspace Archaeology</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Conversation Workspaces</div>
      <div class="text-3xl font-bold text-white mt-1">{total_dirs}</div>
    </div>
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Scratch Tools</div>
      <div class="text-3xl font-bold text-emerald-400 mt-1">{scratch_count}</div>
    </div>
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Background Tasks</div>
      <div class="text-3xl font-bold text-blue-400 mt-1">{task_count}</div>
    </div>
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Failed / Deadlocked</div>
      <div class="text-3xl font-bold text-rose-400 mt-1">{failed_tasks}</div>
    </div>
  </div>

  <div class="card rounded-xl p-6 mb-8">
    <h2 class="text-xl font-bold text-slate-200 mb-4">Scratch Tool Domain Classification</h2>
    <table class="w-full text-left">
      <thead>
        <tr class="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
          <th class="px-4 py-2">Domain Category</th>
          <th class="px-4 py-2 text-right">Scripts Classified</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800">
        {category_rows}
      </tbody>
    </table>
  </div>
</body>
</html>"""
    return html


def export_knowledge_item(
    output_dir: Path,
    ki_id: str,
    title: str,
    category: str,
    summary: str,
    claims: list[dict[str, Any]],
) -> tuple[Path, Path]:
    """Export canonical dual-file Knowledge Vault item with isnad claims (Rule 40, 41).

    Guarantees metadata.json and summary.md dual-file format in output_dir / ki_id.
    """
    ki_dir = output_dir / ki_id
    ki_dir.mkdir(parents=True, exist_ok=True)

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"

    metadata = {
        "id": ki_id,
        "title": title,
        "category": category,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": "Brain Artifact Miner Service",
        "tags": ["brain_store", "artifact_archaeology", "epistemics"],
        "distilled_learning": summary,
        "isnad": {
            "decision_id": f"dec_{ki_id}",
            "status": "VERIFIED",
            "claims": claims,
        },
    }

    meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    summary_md = f"# {title}\n\n**ID:** `{ki_id}`\n\n## Summary\n\n{summary}\n"
    summary_file.write_text(summary_md, encoding="utf-8")

    return meta_file, summary_file


__all__ = [
    "export_knowledge_item",
    "generate_html_brief",
]
