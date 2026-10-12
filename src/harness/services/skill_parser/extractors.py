"""Extraction of execution stages, anti-patterns, invariants, and references."""

from __future__ import annotations

import re

from harness.services.skill_graph.models import (
    SkillAntiPatternDefinition,
    SkillInvariantDefinition,
    SkillStageDefinition,
)


def extract_stages_from_skill_md(body: str) -> list[SkillStageDefinition]:
    """Extract numbered execution stages from markdown headings."""
    stages: list[SkillStageDefinition] = []
    stage_pattern = re.compile(r"^(?:##|###)\s+(\d+)\.\s+(.+)$", re.MULTILINE)
    alt_pattern = re.compile(r"^(?:##|###)\s+Stage\s+(\d+)[:\s]+(.+)$", re.MULTILINE)

    matches = list(stage_pattern.finditer(body)) or list(alt_pattern.finditer(body))
    for m in matches:
        num = int(m.group(1))
        name = m.group(2).strip()

        start = m.end()
        next_heading = body.find("\n##", start)
        section = body[start:next_heading] if next_heading != -1 else body[start:]

        criterion = ""
        crit_match = re.search(r">\s*\*\*Completion criterion\*\*:\s*(.+)", section)
        if crit_match:
            criterion = crit_match.group(1).strip()

        artifact = ""
        art_match = re.search(r"(?:Produces|Primary)\s+artifact(?:\*\*)?:\s*(.+)", section, re.IGNORECASE)
        if art_match:
            artifact = art_match.group(1).strip().strip("`").strip('"')

        consumes: list[str] = []
        cons_match = re.search(r"Consumes\s+artifact(?:s)?(?:\*\*)?:\s*(.+)", section, re.IGNORECASE)
        if cons_match:
            consumes = [c.strip().strip("`").strip('"') for c in cons_match.group(1).split(",") if c.strip()]

        stages.append(
            SkillStageDefinition(
                stage_num=num,
                name=name,
                completion_gate=criterion or f"Gate for Stage {num}",
                objective=name,
                primary_artifact=artifact,
                consumes=consumes,
            )
        )

    return stages


def extract_stages_from_card_table(content: str) -> list[SkillStageDefinition]:
    """Extract stage rows from markdown table in CARD.md."""
    stages: list[SkillStageDefinition] = []
    table_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("|")
    ]

    for line in table_lines:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if (
            len(cols) >= 4
            and not cols[0].startswith("---")
            and not cols[0].lower().startswith("stage")
        ):
            stage_raw = cols[0].replace("*", "").strip()
            num_match = re.search(r"(\d+)", stage_raw)
            num = int(num_match.group(1)) if num_match else len(stages) + 1
            name = (
                stage_raw.split(".", 1)[-1].strip()
                if "." in stage_raw
                else stage_raw
            )
            objective = cols[1].strip()
            artifact = cols[2].strip()
            gate = cols[3].strip()

            stages.append(
                SkillStageDefinition(
                    stage_num=num,
                    name=name,
                    completion_gate=gate or objective,
                    objective=objective,
                    primary_artifact=artifact,
                )
            )

    return stages


def extract_anti_patterns(body: str) -> list[SkillAntiPatternDefinition]:
    """Extract anti-patterns from '## Anti-Patterns' section."""
    anti_patterns: list[SkillAntiPatternDefinition] = []
    match = re.search(r"(?:^|\n)##\s+Anti-Patterns[^\n]*(?:\n|$)", body)
    if not match:
        return anti_patterns

    sub = body[match.end() :]
    next_sec = sub.find("\n## ")
    section = sub[:next_sec] if next_sec != -1 else sub

    for line in section.splitlines():
        line_s = line.strip()
        if line_s.startswith(("-", "*")):
            m = re.search(r"[\-\*]\s+\*\*([^*]+)\*\*\s*[—\-–:]\s*(.+)", line_s)
            if m:
                name = m.group(1).strip()
                desc = m.group(2).strip()
                anti_patterns.append(
                    SkillAntiPatternDefinition(
                        name=name,
                        symptom=desc,
                        remedy="Follow standard protocol",
                    )
                )

    return anti_patterns


def extract_invariants(content: str) -> list[SkillInvariantDefinition]:
    """Extract invariants and checklist items from CARD.md."""
    invariants: list[SkillInvariantDefinition] = []
    in_invariants_section = False

    for line in content.splitlines():
        line_s = line.strip()
        if re.search(
            r"^##\s+.*(invariant|guardrail|checklist)", line_s, re.IGNORECASE
        ):
            in_invariants_section = True
            continue
        elif line_s.startswith("## ") and in_invariants_section:
            in_invariants_section = False

        if line_s.startswith(("- [ ]", "- [x]")):
            clean = line_s.replace("- [ ]", "").replace("- [x]", "").strip()
            clean_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean).strip()
            invariants.append(
                SkillInvariantDefinition(rule=clean_text, is_blocking=True)
            )
        elif in_invariants_section and (
            line_s.startswith(("-", "*")) or re.match(r"^\d+\.", line_s)
        ):
            clean = re.sub(r"^[\-\*\d\.]+\s*", "", line_s).strip()
            clean_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean).strip()
            if clean_text:
                invariants.append(
                    SkillInvariantDefinition(rule=clean_text, is_blocking=True)
                )
    return invariants


def extract_references(text: str, exclude_self: str = "") -> list[str]:
    """Extract cross-skill references from markdown links and text."""
    refs: list[str] = []
    for match in re.findall(r"/([a-z0-9_\-]+)", text):
        if len(match) > 3 and match != exclude_self:
            refs.append(match)

    for match in re.findall(r"\[([a-z0-9_\-]+)\]", text):
        if (
            len(match) > 3
            and match != exclude_self
            and match not in {"card.md", "skill.md", "temp", "requestfeedback"}
        ):
            refs.append(match)

    return list(dict.fromkeys(refs))
