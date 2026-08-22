"""Markdown AST and card parser for agent skill files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .models import AntiPatternNode, InvariantNode, SkillNode, StageNode


class SkillCardParser:
    """Parses CARD.md and SKILL.md files into structured SkillNode schemas."""

    @classmethod
    def parse_directory(cls, dir_path: Path) -> SkillNode | None:
        """Parse a skill directory containing SKILL.md and/or CARD.md."""
        skill_file = dir_path / "SKILL.md"
        card_file = dir_path / "CARD.md"

        if not skill_file.exists() and not card_file.exists():
            return None

        name = dir_path.name
        description = ""
        category = "general"
        version = "1.0.0"
        invocation = f"/{name}"
        triggers: list[str] = []
        target = ""
        stages: list[StageNode] = []
        anti_patterns: list[AntiPatternNode] = []
        invariants: list[InvariantNode] = []
        references: list[str] = []

        # 1. Parse SKILL.md if present
        if skill_file.exists():
            skill_text = skill_file.read_text(encoding="utf-8", errors="ignore")
            frontmatter, body = cls._extract_frontmatter(skill_text)

            if "name" in frontmatter:
                name = frontmatter["name"]
            if "description" in frontmatter:
                description = frontmatter["description"]

            # Parse stages from SKILL.md
            stages.extend(cls._extract_stages_from_skill_md(body))

            # Parse anti-patterns
            anti_patterns.extend(cls._extract_anti_patterns(body))

            # Parse references
            references.extend(cls._extract_references(body, exclude_self=name))

        # 2. Parse CARD.md if present
        if card_file.exists():
            card_text = card_file.read_text(encoding="utf-8", errors="ignore")
            card_meta = cls._extract_ascii_card(card_text)

            if card_meta.get("name"):
                name = card_meta["name"]
            if card_meta.get("category"):
                category = card_meta["category"]
            if card_meta.get("version"):
                version = card_meta["version"]
            if card_meta.get("invocation"):
                invocation = card_meta["invocation"]
            if card_meta.get("triggers"):
                triggers.extend(card_meta["triggers"])
            if card_meta.get("target"):
                target = card_meta["target"]

            # Extract stages from markdown table if SKILL.md stages are empty
            if not stages:
                stages.extend(cls._extract_stages_from_card_table(card_text))

            # Extract invariants from checklist
            invariants.extend(cls._extract_invariants(card_text))

            # Extract references
            references.extend(cls._extract_references(card_text, exclude_self=name))

        # Infer triggers from description if empty
        if not triggers and description:
            triggers = [t.strip().strip('"').strip("'") for t in re.findall(r'"([^"]+)"|\'([^\']+)\'', description) if t]
            if not triggers:
                triggers = [name.replace("-", " ")]

        # Deduplicate references & triggers
        clean_triggers = list(dict.fromkeys(triggers))
        clean_refs = list(dict.fromkeys([r for r in references if r != name]))

        return SkillNode(
            name=name,
            category=category,
            version=version,
            invocation=invocation,
            triggers=clean_triggers,
            target=target,
            description=description,
            card_path=str(card_file) if card_file.exists() else "",
            skill_path=str(skill_file) if skill_file.exists() else "",
            stages=stages,
            anti_patterns=anti_patterns,
            invariants=invariants,
            references=clean_refs,
        )

    @classmethod
    def scan_root(cls, root_path: Path) -> dict[str, SkillNode]:
        """Scan a root directory for all valid skill folders."""
        skills: dict[str, SkillNode] = {}
        if not root_path.exists():
            return skills

        # 1. Direct skills directories (e.g. .agents/skills/*)
        candidates = list(root_path.glob("**/*"))
        for candidate in candidates:
            if candidate.is_dir():
                if (candidate / "SKILL.md").exists() or (candidate / "CARD.md").exists():
                    try:
                        node = cls.parse_directory(candidate)
                        if node:
                            skills[node.name] = node
                    except Exception:
                        pass

        return skills

    # --- Internal Extraction Helpers ---

    @staticmethod
    def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
        """Extract YAML frontmatter between --- markers."""
        frontmatter: dict[str, Any] = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                body = parts[2]
                for line in yaml_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip().strip('"').strip("'")

        return frontmatter, body

    @staticmethod
    def _extract_ascii_card(content: str) -> dict[str, Any]:
        """Extract metadata from ASCII summary box in CARD.md."""
        meta: dict[str, Any] = {}
        triggers: list[str] = []

        for line in content.splitlines():
            clean = line.strip().strip("│").strip()
            if not clean:
                continue

            if clean.startswith("Name:"):
                meta["name"] = clean.split(":", 1)[1].strip()
            elif clean.startswith("Category:"):
                meta["category"] = clean.split(":", 1)[1].strip()
            elif clean.startswith("Invocation:"):
                meta["invocation"] = clean.split(":", 1)[1].strip()
            elif clean.startswith("Version:"):
                meta["version"] = clean.split(":", 1)[1].strip()
            elif clean.startswith("Trigger:") or clean.startswith("Triggers:"):
                val = clean.split(":", 1)[1].strip()
                extracted = re.findall(r'"([^"]+)"', val)
                if extracted:
                    triggers.extend(extracted)
                else:
                    triggers.append(val.strip('"'))
            elif clean.startswith("Target:"):
                meta["target"] = clean.split(":", 1)[1].strip()
            else:
                table_match = re.match(r"^\|\s*\*{0,2}([a-zA-Z]+)\*{0,2}\s*\|\s*(.*?)\s*\|?$", clean)
                if table_match:
                    k_norm = table_match.group(1).lower()
                    v_val = table_match.group(2).strip().strip("`")
                    if k_norm == "name":
                        meta["name"] = v_val
                    elif k_norm == "category":
                        meta["category"] = v_val
                    elif k_norm == "invocation":
                        meta["invocation"] = v_val
                    elif k_norm == "version":
                        meta["version"] = v_val
                    elif k_norm in ("trigger", "triggers"):
                        extracted = re.findall(r'"([^"]+)"', v_val)
                        if extracted:
                            triggers.extend(extracted)
                        else:
                            triggers.extend([t.strip().strip('"') for t in v_val.split(",") if t.strip()])
                    elif k_norm == "target":
                        meta["target"] = v_val

        if triggers:
            meta["triggers"] = triggers
        return meta

    @staticmethod
    def _extract_stages_from_skill_md(body: str) -> list[StageNode]:
        """Extract numbered execution stages from markdown headings."""
        stages: list[StageNode] = []
        stage_pattern = re.compile(r"^(?:##|###)\s+(\d+)\.\s+(.+)$", re.MULTILINE)
        alt_pattern = re.compile(r"^(?:##|###)\s+Stage\s+(\d+)[:\s]+(.+)$", re.MULTILINE)

        matches = list(stage_pattern.finditer(body)) or list(alt_pattern.finditer(body))
        for m in matches:
            num = int(m.group(1))
            name = m.group(2).strip()

            # Find completion criterion in section
            start = m.end()
            next_heading = body.find("\n##", start)
            section = body[start:next_heading] if next_heading != -1 else body[start:]

            criterion = ""
            crit_match = re.search(r">\s*\*\*Completion criterion\*\*:\s*(.+)", section)
            if crit_match:
                criterion = crit_match.group(1).strip()

            stages.append(
                StageNode(
                    stage_num=num,
                    name=name,
                    objective=name,
                    primary_artifact="",
                    completion_gate=criterion,
                )
            )

        return stages

    @staticmethod
    def _extract_stages_from_card_table(content: str) -> list[StageNode]:
        """Extract stage rows from markdown table in CARD.md."""
        stages: list[StageNode] = []
        table_lines = [line.strip() for line in content.splitlines() if line.strip().startswith("|")]

        for line in table_lines:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 4 and not cols[0].startswith("---") and not cols[0].lower().startswith("stage"):
                stage_raw = cols[0].replace("*", "").strip()
                num_match = re.search(r"(\d+)", stage_raw)
                num = int(num_match.group(1)) if num_match else len(stages) + 1
                name = stage_raw.split(".", 1)[-1].strip() if "." in stage_raw else stage_raw
                objective = cols[1].strip()
                artifact = cols[2].strip()
                gate = cols[3].strip()

                stages.append(
                    StageNode(
                        stage_num=num,
                        name=name,
                        objective=objective,
                        primary_artifact=artifact,
                        completion_gate=gate,
                    )
                )

        return stages

    @staticmethod
    def _extract_anti_patterns(body: str) -> list[AntiPatternNode]:
        """Extract anti-patterns from '## Anti-Patterns' section."""
        anti_patterns: list[AntiPatternNode] = []
        ap_idx = body.find("## Anti-Patterns")
        if ap_idx == -1:
            return anti_patterns

        sub = body[ap_idx:]
        next_sec = sub.find("\n## ", len("## Anti-Patterns"))
        section = sub[:next_sec] if next_sec != -1 else sub

        for line in section.splitlines():
            line_s = line.strip()
            if line_s.startswith("-") or line_s.startswith("*"):
                # Pattern: - **Name** — description
                m = re.search(r"[\-\*]\s+\*\*([^*]+)\*\*\s*[—\-–:]\s*(.+)", line_s)
                if m:
                    name = m.group(1).strip()
                    desc = m.group(2).strip()
                    anti_patterns.append(AntiPatternNode(name=name, description=desc, mitigation=""))

        return anti_patterns

    @staticmethod
    def _extract_invariants(content: str) -> list[InvariantNode]:
        """Extract invariants and checklist items from CARD.md."""
        invariants: list[InvariantNode] = []
        in_invariants_section = False

        for line in content.splitlines():
            line_s = line.strip()
            if re.search(r"^##\s+.*(invariant|guardrail|checklist)", line_s, re.IGNORECASE):
                in_invariants_section = True
                continue
            elif line_s.startswith("## ") and in_invariants_section:
                in_invariants_section = False

            if line_s.startswith("- [ ]") or line_s.startswith("- [x]"):
                clean = line_s.replace("- [ ]", "").replace("- [x]", "").strip()
                clean_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean).strip()
                invariants.append(InvariantNode(rule=clean_text, is_blocking=True))
            elif in_invariants_section and (line_s.startswith("-") or line_s.startswith("*") or re.match(r"^\d+\.", line_s)):
                clean = re.sub(r"^[\-\*\d\.]+\s*", "", line_s).strip()
                clean_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean).strip()
                if clean_text:
                    invariants.append(InvariantNode(rule=clean_text, is_blocking=True))
        return invariants

    @staticmethod
    def _extract_references(text: str, exclude_self: str = "") -> list[str]:
        """Extract cross-skill references from markdown links and text."""
        refs: list[str] = []
        # Match `/skill-name` or `[skill-name]`
        for match in re.findall(r"/([a-z0-9_\-]+)", text):
            if len(match) > 3 and match != exclude_self:
                refs.append(match)

        for match in re.findall(r"\[([a-z0-9_\-]+)\]", text):
            if len(match) > 3 and match != exclude_self and match not in {"card.md", "skill.md", "temp", "requestfeedback"}:
                refs.append(match)

        return list(dict.fromkeys(refs))
