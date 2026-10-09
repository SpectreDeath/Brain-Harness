"""Documentation Salvage and High-Density Index Synthesis (Rule 41)."""

from __future__ import annotations

from pathlib import Path

from harness.services.temp_artifact_miner.models import (
    BriefCatalog,
    SandboxReport,
    VisualSalvageReport,
)
from harness.services.temp_artifact_miner.parser import parse_html_brief


def generate_salvage_markdown(
    catalog: BriefCatalog,
    sandbox: SandboxReport | None = None,
) -> str:
    """Generate a high-density Markdown summary of salvaged visual briefs and sandbox runs."""
    lines = [
        "# Ephemeral Visual Brief Salvage Index",
        "",
        f"- **Total Briefs Scanned:** {catalog.brief_count}",
        f"- **Total Payload Size:** {catalog.total_bytes / (1024 * 1024):.2f} MB",
        f"- **Heavy Topologies Bounded:** {catalog.heavy_count}",
        f"- **Distinct Categories:** {len(catalog.items_by_category)}",
    ]
    if sandbox is not None:
        lines.append(f"- **Pytest Sandbox Runs:** {sandbox.total_runs}")

    lines.extend([
        "",
        "## Category Distribution",
        "",
        "| Category | Count | Total Size (KB) | Mermaid DAGs | Scorecards |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])
    for cat, items in sorted(catalog.items_by_category.items(), key=lambda x: len(x[1]), reverse=True):
        sz_kb = sum(i.size_bytes for i in items) / 1024
        has_m = sum(1 for i in items if i.has_mermaid)
        has_sc = sum(1 for i in items if i.has_scorecard)
        lines.append(f"| `{cat}` | {len(items)} | {sz_kb:.1f} | {has_m} | {has_sc} |")

    lines.extend([
        "",
        "## Representative Extracted Decisions",
        "",
    ])
    for cat, items in sorted(catalog.items_by_category.items()):
        lines.append(f"### {cat.title().replace('-', ' ')}")
        for item in items[:3]:
            lines.append(f"- **{item.title}** (`{item.name}`)")
            lines.append(f"  * Size: {item.size_bytes} bytes | SHA256: `{item.sha256[:12]}...`")
            if item.mermaid_dags:
                lines.append(f"  * Mermaid Flowchart Extracted ({len(item.mermaid_dags[0])} chars)")
        lines.append("")

    if sandbox is not None and sandbox.runs:
        lines.extend([
            "## Pytest Sandbox Runs",
            "",
            "| Run | Fixtures | Mock Skills | Path |",
            "| :--- | :---: | :---: | :--- |",
        ])
        for r in sandbox.runs:
            skills_str = ", ".join(r.mock_skills) if r.mock_skills else "none"
            lines.append(f"| `{r.name}` | {r.fixture_count} | {skills_str} | `{r.path}` |")
        lines.append("")

    return "\n".join(lines)


def salvage_diagrams(
    brief_path: Path | str,
    target_docs_dir: Path | str | None = None,
) -> VisualSalvageReport:
    """Extract Mermaid DAGs and visual briefs into repository documentation."""
    source = Path(brief_path)
    item = parse_html_brief(source)
    docs_root = Path(target_docs_dir) if target_docs_dir else Path("docs/architecture")
    docs_root.mkdir(parents=True, exist_ok=True)
    doc_file = docs_root / f"{source.stem}_diagrams.md"

    lines = [
        f"# Visual Diagrams: {item.title}",
        "",
        f"- Source: `{item.name}`",
        f"- SHA256: `{item.sha256}`",
        "",
    ]
    for idx, dag in enumerate(item.mermaid_dags, 1):
        lines.extend([
            f"## Diagram {idx}",
            "```mermaid",
            dag,
            "```",
            "",
        ])
    doc_file.write_text("\n".join(lines), encoding="utf-8")

    return VisualSalvageReport(
        brief_name=item.name,
        knowledge_vault_path="",
        salvaged_doc_path=str(doc_file),
        extracted_diagrams_count=len(item.mermaid_dags),
        isnad_claims_count=1 if item.sha256 else 0,
    )
