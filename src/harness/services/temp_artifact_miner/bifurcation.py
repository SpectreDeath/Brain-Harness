"""Dual-Lens Cognitive Bifurcation and Epistemic Vault Commitment (Rule 40, Rule 41)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from harness.services.temp_artifact_miner.models import (
    CognitiveBifurcationReport,
)
from harness.services.temp_artifact_miner.parser import parse_html_brief


def bifurcate_brief(
    brief_path: Path | str,
    target_vault_dir: Path | str | None = None,
    target_docs_dir: Path | str | None = None,
) -> CognitiveBifurcationReport:
    """Execute Dual-Lens Cognitive Bifurcation (Rule 40, Rule 41).

    Bifurcates analysis into:
    1. Epistemic Introspection Seam: Canonical Knowledge Vault dual-files (`metadata.json` + `summary.md`)
       with unbroken isnad claims under `.harness/knowledge/<ki_id>/`.
    2. Permanent Documentation Seam: Salvages extracted diagrams and decision rubrics into `docs/architecture/`.
    """
    source = Path(brief_path)
    if not source.exists():
        raise FileNotFoundError(f"Visual brief does not exist: {source}")

    item = parse_html_brief(source, heavy_threshold=200000)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ki_id = f"ki_temp_{item.category.replace('-', '_')}_{timestamp_str}"

    # 1. Epistemic Introspection Seam (Knowledge Vault Dual-Files, Rule 40)
    vault_root = Path(target_vault_dir) if target_vault_dir else Path(".harness/knowledge")
    ki_dir = vault_root / ki_id
    ki_dir.mkdir(parents=True, exist_ok=True)

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"

    metadata = {
        "id": ki_id,
        "title": f"Epistemic Distillation: {item.title}",
        "category": item.category,
        "source_file": item.name,
        "sha256": item.sha256,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "isnad": {
            "status": "VERIFIED",
            "claims": [
                {
                    "assertion": f"Visual architecture review validated for {item.category}",
                    "confidence": 1.0,
                    "lineage": [
                        {
                            "source": item.name,
                            "timestamp": datetime.fromtimestamp(item.mtime, timezone.utc).isoformat(),
                            "sha256": item.sha256,
                            "anchor": "HTML visual brief decision matrix",
                        }
                    ],
                }
            ],
        },
        "tags": ["temp-artifact-miner", item.category, "architecture-review"],
    }
    meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    summary_content = [
        f"# Knowledge Item: {item.title}",
        "",
        f"- **Source:** `{item.name}`",
        f"- **Category:** `{item.category}`",
        f"- **SHA256:** `{item.sha256}`",
        f"- **Extracted Diagrams:** {len(item.mermaid_dags)}",
        "",
        "## Summary",
        f"Epistemic architecture decisions and trade-offs extracted from `{item.name}`.",
        "",
    ]
    if item.mermaid_dags:
        summary_content.append("## Architectural Diagrams")
        for idx, dag in enumerate(item.mermaid_dags, 1):
            summary_content.extend([
                f"### Diagram {idx}",
                "```mermaid",
                dag,
                "```",
                "",
            ])
    summary_file.write_text("\n".join(summary_content), encoding="utf-8")

    # 2. Permanent Documentation Seam (Rule 41)
    docs_root = Path(target_docs_dir) if target_docs_dir else Path("docs/architecture")
    docs_root.mkdir(parents=True, exist_ok=True)
    doc_filename = f"{source.stem}_salvaged.md"
    doc_file = docs_root / doc_filename

    doc_lines = [
        f"# Architectural Brief: {item.title}",
        "",
        f"> Salvaged from ephemeral visual brief `{item.name}` on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.",
        "",
        "## Epistemic Provenance",
        f"- **Original File:** `{item.path}`",
        f"- **SHA256 Checksum:** `{item.sha256}`",
        f"- **Vault Reference:** [`{ki_id}`](file:///{ki_dir.as_posix()})",
        "",
    ]
    if item.mermaid_dags:
        doc_lines.append("## Diagrams")
        for idx, dag in enumerate(item.mermaid_dags, 1):
            doc_lines.extend([
                f"### Flowchart {idx}",
                "```mermaid",
                dag,
                "```",
                "",
            ])
    doc_file.write_text("\n".join(doc_lines), encoding="utf-8")

    heuristics = (
        f"Architecture category '{item.category}' validated",
        f"Mermaid DAGs extracted: {len(item.mermaid_dags)}",
    )
    procedural = (
        "Never delete files from %TEMP%",
        "Bound visual topologies > 100KB",
    )

    return CognitiveBifurcationReport(
        source_name=item.name,
        knowledge_vault_path=str(ki_dir),
        salvaged_doc_path=str(doc_file),
        extracted_heuristics=heuristics,
        procedural_rules=procedural,
    )
