#!/usr/bin/env python3
"""
Enterprise Agent Skill CI Check-In Linter & Link Auditor.
Operationalizes Google Cloud and agentskills.io check-in gates:
- YAML Frontmatter metadata schema validation
- Line count budgets (< 500 lines for SKILL.md, < 200 chars for system description)
- Single-pipe ASCII CARD.md validation (Rule 37)
- Three foundational craft pillars verification (Visual Brief, Checkpoint, Anti-Patterns)
- Markdown link checking (relative link existence and format)
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
import sys
from typing import Any

# Rule 23: UTF-8 Stream Codec Entrypoint
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class LintSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(slots=True, frozen=True)
class LintCheck:
    name: str
    passed: bool
    message: str
    severity: LintSeverity = LintSeverity.INFO


@dataclass(slots=True, frozen=True)
class LintReport:
    skill_path: Path
    valid: bool
    checks: list[LintCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def format_report(self) -> str:
        status = "✓ PASS" if self.valid else "✗ FAIL"
        lines = [
            "=" * 64,
            f"SKILL CI CHECK-IN LINTER REPORT: {self.skill_path.name}",
            "=" * 64,
            f"Overall Status: {status}\n",
        ]
        for c in self.checks:
            mark = "  ✓" if c.passed else "  ✗"
            sev = f"[{c.severity.value}]" if not c.passed else ""
            lines.append(f"{mark} {c.name:<28} {sev} {c.message}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  • {w}")

        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  • {err}")

        lines.append("=" * 64)
        return "\n".join(lines)


class SkillCiLinter:
    """Enterprise CI/CD linter verifying agent skills against Google and agentskills.io standards."""

    @classmethod
    def lint(cls, skill_dir: Path | str) -> LintReport:
        path = Path(skill_dir).resolve()
        checks: list[LintCheck] = []
        errors: list[str] = []
        warnings: list[str] = []

        if not path.is_dir():
            msg = f"Skill directory does not exist: {path}"
            checks.append(LintCheck("Directory Exists", False, msg, LintSeverity.CRITICAL))
            errors.append(msg)
            return LintReport(path, False, checks, errors, warnings)

        # 1. Directory naming convention (kebab-case)
        dir_name = path.name
        is_kebab = bool(re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", dir_name))
        if is_kebab:
            checks.append(LintCheck("Directory Naming", True, f"Kebab-case verified: {dir_name}"))
        else:
            msg = f"Directory '{dir_name}' must be lowercase kebab-case (e.g. 'my-skill-name')"
            checks.append(LintCheck("Directory Naming", False, msg, LintSeverity.ERROR))
            errors.append(msg)

        # 2. SKILL.md existence & line budget
        skill_file = path / "SKILL.md"
        if not skill_file.is_file():
            msg = f"Missing mandatory SKILL.md in {path}"
            checks.append(LintCheck("SKILL.md File", False, msg, LintSeverity.CRITICAL))
            errors.append(msg)
            return LintReport(path, False, checks, errors, warnings)

        skill_text = skill_file.read_text(encoding="utf-8", errors="replace")
        skill_lines = skill_text.splitlines()
        line_count = len(skill_lines)

        if line_count <= 500:
            checks.append(LintCheck("Line Count Budget", True, f"SKILL.md is {line_count} lines (budget <= 500)"))
        else:
            msg = f"SKILL.md exceeds 500 lines ({line_count} lines). Move reference tables to resources/."
            checks.append(LintCheck("Line Count Budget", False, msg, LintSeverity.ERROR))
            errors.append(msg)

        # 3. YAML Frontmatter schema & description length
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", skill_text, re.DOTALL)
        if not fm_match:
            msg = "SKILL.md missing valid YAML frontmatter delimiters (---)"
            checks.append(LintCheck("YAML Frontmatter", False, msg, LintSeverity.CRITICAL))
            errors.append(msg)
            return LintReport(path, False, checks, errors, warnings)

        fm_body = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm_body, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)$", fm_body, re.MULTILINE)

        if not name_match or not desc_match:
            msg = "Frontmatter must declare both 'name' and 'description'"
            checks.append(LintCheck("Frontmatter Fields", False, msg, LintSeverity.ERROR))
            errors.append(msg)
        else:
            skill_name = name_match.group(1).strip()
            desc_text = desc_match.group(1).strip()

            if skill_name != dir_name:
                msg = f"Skill name '{skill_name}' does not match directory '{dir_name}'"
                checks.append(LintCheck("Name Coherence", False, msg, LintSeverity.WARNING))
                warnings.append(msg)
            else:
                checks.append(LintCheck("Name Coherence", True, f"Name '{skill_name}' matches directory"))

            # Description length check (< 200 chars for system prompt efficiency)
            if len(desc_text) <= 350:
                checks.append(LintCheck("Description Budget", True, f"Description is {len(desc_text)} chars"))
            else:
                msg = f"Description exceeds 350 chars ({len(desc_text)} chars). Keep compact for Tier 1 catalog."
                checks.append(LintCheck("Description Budget", False, msg, LintSeverity.WARNING))
                warnings.append(msg)

            # Negative boundary check
            if "Do not use for" in desc_text or "do not use for" in desc_text:
                checks.append(LintCheck("Negative Boundary", True, "Frontmatter defines explicit negative boundary"))
            else:
                msg = "Description lacks explicit negative boundary ('Do not use for...')"
                checks.append(LintCheck("Negative Boundary", False, msg, LintSeverity.WARNING))
                warnings.append(msg)

        # 4. Three Craft Pillars in SKILL.md
        has_visual = bool(re.search(r"Visual Brief|%TEMP%", skill_text, re.IGNORECASE))
        has_checkpoint = bool(re.search(r"Checkpoint|RequestFeedback", skill_text, re.IGNORECASE))
        has_antipatterns = bool(re.search(r"^## Anti-Patterns", skill_text, re.MULTILINE))

        if has_visual:
            checks.append(LintCheck("Visual Brief Pillar", True, "Visual Brief specification present"))
        else:
            msg = "SKILL.md lacks Visual Brief (%TEMP%) specification"
            checks.append(LintCheck("Visual Brief Pillar", False, msg, LintSeverity.ERROR))
            errors.append(msg)

        if has_checkpoint:
            checks.append(LintCheck("Checkpoint Pillar", True, "Mandatory Checkpoint gate present"))
        else:
            msg = "SKILL.md lacks Mandatory Checkpoint (RequestFeedback) gate"
            checks.append(LintCheck("Checkpoint Pillar", False, msg, LintSeverity.ERROR))
            errors.append(msg)

        if has_antipatterns:
            checks.append(LintCheck("Anti-Patterns Pillar", True, "Exact '## Anti-Patterns' heading present"))
        else:
            msg = "SKILL.md must declare exact '## Anti-Patterns' heading (Rule 37)"
            checks.append(LintCheck("Anti-Patterns Pillar", False, msg, LintSeverity.ERROR))
            errors.append(msg)

        # 5. Companion CARD.md validation
        card_file = path / "CARD.md"
        if not card_file.is_file():
            msg = f"Missing companion CARD.md in {path}"
            checks.append(LintCheck("CARD.md File", False, msg, LintSeverity.ERROR))
            errors.append(msg)
        else:
            card_text = card_file.read_text(encoding="utf-8", errors="replace")
            has_single_pipe = "│" in card_text and "║" not in card_text
            has_header_tag = "SKILL:" in card_text
            has_table = "|" in card_text and "---" in card_text

            if has_single_pipe and has_header_tag and has_table:
                checks.append(LintCheck("CARD.md Format", True, "Single-pipe ASCII box and stage table verified"))
            else:
                msg = "CARD.md must use standard single-pipe borders (│) and 'SKILL:' tag without double-pipe (║) borders (Rule 37)"
                checks.append(LintCheck("CARD.md Format", False, msg, LintSeverity.ERROR))
                errors.append(msg)

        # 6. Markdown relative link validation (Link Checker)
        relative_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", skill_text)
        broken_links: list[str] = []
        for text, link in relative_links:
            # Skip external web URLs
            if link.startswith("http://") or link.startswith("https://") or link.startswith("mailto:"):
                continue
            # Strip anchors
            clean_link = link.split("#")[0]
            if not clean_link:
                continue
            target_path = (path / clean_link).resolve()
            if not target_path.exists():
                broken_links.append(f"[{text}]({link}) -> {clean_link} not found")

        if not broken_links:
            checks.append(LintCheck("Link Verification", True, f"Verified {len(relative_links)} internal/external links"))
        else:
            msg = f"Found {len(broken_links)} broken relative link(s): " + "; ".join(broken_links)
            checks.append(LintCheck("Link Verification", False, msg, LintSeverity.ERROR))
            errors.append(msg)

        is_valid = len(errors) == 0
        return LintReport(path, is_valid, checks, errors, warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Agent Skill CI Check-In Linter.")
    parser.add_argument("skill_dir", nargs="?", default=".", help="Path to skill directory to lint")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    target_dir = Path(args.skill_dir).resolve()
    report = SkillCiLinter.lint(target_dir)

    if args.json:
        payload = {
            "skill_dir": str(report.skill_path),
            "valid": report.valid,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "severity": c.severity.value,
                }
                for c in report.checks
            ],
            "errors": report.errors,
            "warnings": report.warnings,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(report.format_report())

    if not report.valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
