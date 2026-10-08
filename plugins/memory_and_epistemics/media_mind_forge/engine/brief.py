"""Interactive HTML visual brief generator with Mermaid cognitive DAG."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from ..models import CognitiveAnalysisReport


def generate_visual_brief_html(
    report: CognitiveAnalysisReport,
    target_dir: Path | str | None = None,
) -> str:
    """Render a self-contained, interactive HTML report with Mermaid cognitive DAG in %TEMP%."""
    out_dir = Path(target_dir).resolve() if target_dir else Path(tempfile.gettempdir())
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"media-mind-forge-{int(time.time())}.html"
    brief_path = out_dir / filename

    stages_rows = "\n".join(
        f"<tr><td><strong>{s.stage_num}. {s.name}</strong></td><td>{s.objective}</td><td><code>{s.completion_criterion}</code></td></tr>"
        for s in report.procedural_stages
    )

    ki_rows = "\n".join(
        f"<tr><td><code>{ki.id}</code></td><td><strong>{ki.title}</strong></td><td>{ki.summary}</td><td>{', '.join(ki.tags)}</td></tr>"
        for ki in report.knowledge_items
    )

    rubric_rows = "\n".join(
        f"<tr><td><strong>{q.question}</strong></td><td>{q.passing_criteria}</td><td style='color:#f87171;'>{', '.join(q.failing_indicators)}</td></tr>"
        for q in report.diagnostic_rubric
    )

    ap_rows = "\n".join(
        f"<tr><td><strong>{ap.name}</strong></td><td>{ap.telltale_symptom}</td><td style='color:#34d399;'>{ap.positive_rule}</td></tr>"
        for ap in report.anti_patterns
    )

    duration_fmt = f"{int(report.total_duration_s // 60)}m {int(report.total_duration_s % 60)}s"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Media Mind Forge — {report.target_title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 2rem;
        }}
        .card {{
            background: #161b22;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #30363d;
        }}
        h1, h2, h3 {{ color: #58a6ff; margin-top: 0; }}
        .badge {{
            display: inline-block;
            background: #1f6feb;
            color: #fff;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid #21262d;
            font-size: 0.9rem;
        }}
        th {{ color: #8b949e; font-weight: 600; background: #0d1117; }}
        code {{ background: #0d1117; padding: 0.2rem 0.4rem; border-radius: 4px; color: #79c0ff; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🧠 Media Mind Forge Brief</h1>
        <h2>{report.target_title}</h2>
        <div>
            <span class="badge">Speaker: {report.speaker}</span>
            <span class="badge">Duration: {duration_fmt}</span>
            <span class="badge">Words: {report.word_count}</span>
            <span class="badge">Pace: {report.words_per_minute} WPM</span>
            <span class="badge">Skill: {report.skill_name}</span>
        </div>
    </div>

    <div class="card">
        <h2>🗺️ Cognitive Topology DAG</h2>
        <div class="mermaid">
graph TD
    A[Raw Media: {report.target_title}] --> B[Transcript Deconstruction]
    B --> C1[Epistemic Mental Models: {len(report.mental_models)}]
    B --> C2[Decision Heuristics: {len(report.decision_heuristics)}]
    C1 --> D[Knowledge Vault KIs: {len(report.knowledge_items)}]
    C2 --> D
    B --> E1[Procedural Stages: {len(report.procedural_stages)}]
    B --> E2[Diagnostic Rubrics: {len(report.diagnostic_rubric)}]
    B --> E3[Anti-Patterns: {len(report.anti_patterns)}]
    E1 --> F[Executable Agent Skill: {report.skill_name}]
    E2 --> F
    E3 --> F
        </div>
    </div>

    <div class="card">
        <h2>🎯 Shu-Ha-Ri Execution Stages</h2>
        <table>
            <thead>
                <tr><th>Stage</th><th>Objective</th><th>Verifiable Completion Gate</th></tr>
            </thead>
            <tbody>
                {stages_rows}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>📚 Distilled Knowledge Items (KIs)</h2>
        <table>
            <thead>
                <tr><th>KI ID</th><th>Title</th><th>Summary</th><th>Tags</th></tr>
            </thead>
            <tbody>
                {ki_rows}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>🔍 Diagnostic Interrogation Rubric</h2>
        <table>
            <thead>
                <tr><th>Diagnostic Probe</th><th>Exemplary Passing Criteria</th><th>Failing Indicators</th></tr>
            </thead>
            <tbody>
                {rubric_rows}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>🛡️ Anti-Patterns & Defenses</h2>
        <table>
            <thead>
                <tr><th>Anti-Pattern</th><th>Observable Symptom</th><th>Invariant Positive Rule</th></tr>
            </thead>
            <tbody>
                {ap_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    brief_path.write_text(html_content, encoding="utf-8")
    return str(brief_path)
