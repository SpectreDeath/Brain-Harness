"""SKILL.md and CARD.md authoring and skill package scaffolding."""

from __future__ import annotations

from pathlib import Path

from ..models import CognitiveAnalysisReport


def generate_skill_md_content(report: CognitiveAnalysisReport, skill_name: str = "") -> str:
    """Generate high-precision SKILL.md conforming to crafting-skills and Rule 37."""
    target_name = skill_name or report.skill_name or "ontological-engineering-coach"
    clean_name = target_name.strip().lower().replace("_", "-")
    title = clean_name.replace("-", " ").title()

    stages_md = []
    for s in report.procedural_stages:
        action_items = "\n".join(f"- {act}" for act in s.action_steps)
        stages_md.append(
            f"### Stage {s.stage_num}: {s.name}\n\n"
            f"{s.objective}\n\n"
            f"{action_items}\n\n"
            f"> **Completion criterion**: {s.completion_criterion}\n"
        )
    stages_block = "\n---\n\n".join(stages_md)

    # Rule 37: exact ## Anti-Patterns heading with - **Name** — Description
    ap_md = []
    for ap in report.anti_patterns:
        ap_md.append(f"- **{ap.name}** — {ap.telltale_symptom} {ap.positive_rule}")
    ap_block = "\n".join(ap_md)

    return (
        f"---\n"
        f"name: {clean_name}\n"
        f"description: Master {report.target_title} using principles distilled from {report.speaker}. Use when designing domain ontologies, auditing knowledge graphs, applying Gruber's criteria, or balancing precision vs coverage.\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"`{clean_name}` is an executable cognitive workflow engine derived from *{report.target_title}* presented by {report.speaker}.\n\n"
        f"Every execution adheres to three foundational craft pillars:\n"
        f"1. **The Visual Brief** — Interactive HTML reports generated in `%TEMP%` rendering ontology schemas and competence DAGs.\n"
        f"2. **The Mandatory Checkpoint** — Explicit human-in-the-loop gates (`RequestFeedback: true`) before modifying domain schemas.\n"
        f"3. **Explicit Anti-Patterns** — Rigid behavioral boundaries eliminating speculative over-commitment and taxonomy confusion.\n\n"
        f"See [CARD.md](CARD.md) for the summary card and completion checklist.\n\n"
        f"---\n\n"
        f"## Execution Sequence\n\n"
        f"{stages_block}\n"
        f"---\n\n"
        f"## Anti-Patterns\n\n"
        f"{ap_block}\n"
    )


def generate_card_md_content(report: CognitiveAnalysisReport, skill_name: str = "") -> str:
    """Generate companion summary CARD.md conforming to Rule 37 single-pipe borders."""
    target_name = skill_name or report.skill_name or "ontological-engineering-coach"
    clean_name = target_name.strip().lower().replace("_", "-")
    title = clean_name.replace("-", " ").title()

    table_rows = []
    for s in report.procedural_stages:
        table_rows.append(f"| **{s.stage_num}. {s.name}** | {s.objective} | `{s.completion_criterion}` |")
    table_block = "\n".join(table_rows)

    invariants_block = "\n".join([
        "- [ ] Competency questions verified before asserting class hierarchies",
        "- [ ] Gruber's Minimal Ontological Commitment enforced (zero speculative classes)",
        "- [ ] Reasoner consistency check passes with zero logical contradictions",
        "- [ ] Representation encoding bias eliminated across serializations",
    ])

    vocab_block = "\n".join([
        "- **Competency Question**: Natural language query defining the questions the model must answer.",
        "- **Minimal Commitment**: Specifying only what is strictly necessary to satisfy target tasks.",
        "- **Subsumption Transitivity**: Formal verification that subclass members strictly belong to the superclass.",
        "- **Encoding Bias**: Erroneous dependency on specific syntactic quirks of a serialization format.",
    ])

    # Rule 37: Single-pipe │ borders in ASCII summary box with SKILL: header tag
    return (
        f"```\n"
        f"┌────────────────────────────────────────────────────────┐\n"
        f"│ SKILL:       {clean_name:<42} │\n"
        f"├────────────────────────────────────────────────────────┤\n"
        f"│ Name:        {clean_name:<42} │\n"
        f"│ Category:    memory_and_epistemics                    │\n"
        f"│ Invocation:  /{clean_name:<41} │\n"
        f"│ Triggers:    \"ontological engineering\", \"knowledge graph\"│\n"
        f"│ Version:     1.0.0                                     │\n"
        f"│ Isolation:   in_process                                │\n"
        f"├────────────────────────────────────────────────────────┤\n"
        f"│ Target:      Operational ontology and schema modeling  │\n"
        f"│              using Gruber and Guarino principles.      │\n"
        f"└────────────────────────────────────────────────────────┘\n"
        f"```\n\n"
        f"# {title} — Companion Summary Card\n\n"
        f"## Stage Progression Table\n\n"
        f"| Stage | Core Responsibility | Completion Gate |\n"
        f"|---|---|---|\n"
        f"{table_block}\n\n"
        f"---\n\n"
        f"## Vocabulary & Levers\n\n"
        f"{vocab_block}\n\n"
        f"---\n\n"
        f"## Mandatory Invariants Checklist\n\n"
        f"{invariants_block}\n"
    )


def scaffold_skill_directory(
    report: CognitiveAnalysisReport,
    output_dir: Path | str,
    skill_name: str | None = None,
) -> dict[str, str]:
    """Scaffold complete, valid agent skill directory (SKILL.md + CARD.md)."""
    resolved_name = skill_name or "ontological-engineering-coach"
    dest_dir = Path(output_dir) / resolved_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    skill_md = generate_skill_md_content(report, resolved_name)
    card_md = generate_card_md_content(report, resolved_name)

    (dest_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (dest_dir / "CARD.md").write_text(card_md, encoding="utf-8")

    return {
        "skill_dir": str(dest_dir),
        "skill_file": str(dest_dir / "SKILL.md"),
        "card_file": str(dest_dir / "CARD.md"),
        "skill_name": resolved_name,
    }
