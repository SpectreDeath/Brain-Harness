"""Validation rules ensuring agent skills meet high-precision craft standards."""

from __future__ import annotations

import re

from harness.creator.validator import (
    RuleSeverity,
    ValidationContext,
    ValidationRule,
)


class SkillDirectoryRule(ValidationRule):
    """Verifies that the target skill path exists and is a directory."""

    @property
    def name(self) -> str:
        return "Skill Directory"

    @property
    def category(self) -> str:
        return "structural"

    async def validate(self, ctx: ValidationContext) -> bool:
        if not ctx.path.exists() or not ctx.path.is_dir():
            ctx.add_fail(
                self.name,
                f"Directory does not exist: {ctx.path}",
                severity=RuleSeverity.CRITICAL,
                category=self.category,
            )
            return False
        ctx.add_pass(self.name, f"Found directory: {ctx.path.name}", category=self.category)
        return True


class SkillFrontmatterRule(ValidationRule):
    """Verifies that SKILL.md exists and contains valid YAML frontmatter with name and description."""

    @property
    def name(self) -> str:
        return "SKILL.md File"

    @property
    def category(self) -> str:
        return "structural"

    async def validate(self, ctx: ValidationContext) -> bool:
        skill_file = ctx.path / "SKILL.md"
        if not skill_file.exists():
            ctx.add_fail(
                self.name,
                "Missing SKILL.md specification file",
                severity=RuleSeverity.CRITICAL,
                category=self.category,
            )
            return False

        skill_text = skill_file.read_text(encoding="utf-8", errors="ignore")
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", skill_text, re.DOTALL)
        if not frontmatter_match:
            ctx.add_fail(
                "YAML Frontmatter",
                "SKILL.md missing valid YAML frontmatter (--- delimiter)",
                severity=RuleSeverity.ERROR,
                category=self.category,
            )
            return False

        fm_body = frontmatter_match.group(1)
        has_name = bool(re.search(r"^name:\s*.+", fm_body, re.MULTILINE))
        has_desc = bool(re.search(r"^description:\s*.+", fm_body, re.MULTILINE))
        if not has_name or not has_desc:
            ctx.add_fail(
                "YAML Frontmatter",
                "Frontmatter must contain 'name' and 'description'",
                severity=RuleSeverity.ERROR,
                category=self.category,
            )
            return False

        ctx.add_pass("YAML Frontmatter", "Valid YAML frontmatter", category=self.category)
        return True


class SkillPillarRule(ValidationRule):
    """Verifies that SKILL.md implements the 3 foundational pillars of craft standards."""

    @property
    def name(self) -> str:
        return "Skill Pillars"

    @property
    def category(self) -> str:
        return "specification"

    async def validate(self, ctx: ValidationContext) -> bool:
        skill_file = ctx.path / "SKILL.md"
        if not skill_file.exists():
            return False

        skill_text = skill_file.read_text(encoding="utf-8", errors="ignore")

        # 1. Visual Brief Pillar
        has_visual_brief = bool(
            re.search(r"##.*Visual Brief|###.*Visual Brief|The Visual Brief|%TEMP%", skill_text, re.IGNORECASE)
        )
        if has_visual_brief:
            ctx.add_pass("Visual Brief Pillar", "Found Visual Brief specification", category=self.category)
        else:
            ctx.add_warn("Visual Brief Pillar", "SKILL.md lacks Visual Brief specifications", category=self.category)

        # 2. Mandatory Checkpoint Pillar
        has_checkpoint = bool(
            re.search(r"##.*Checkpoint|###.*Checkpoint|Mandatory Checkpoint|RequestFeedback", skill_text, re.IGNORECASE)
        )
        if has_checkpoint:
            ctx.add_pass("Mandatory Checkpoint", "Found Mandatory Checkpoint gate", category=self.category)
        else:
            ctx.add_warn("Mandatory Checkpoint", "SKILL.md lacks explicit Mandatory Checkpoint gates", category=self.category)

        # 3. Anti-Patterns Pillar
        has_anti_patterns = bool(
            re.search(r"##.*Anti-Pattern|###.*Anti-Pattern|##.*Guardrail|###.*Guardrail|Anti-Patterns|Behavioral Guardrails", skill_text, re.IGNORECASE)
        )
        if has_anti_patterns:
            ctx.add_pass("Anti-Patterns", "Found Anti-Patterns section", category=self.category)
        else:
            ctx.add_warn("Anti-Patterns", "SKILL.md lacks named Anti-Patterns", category=self.category)

        return True


class SkillCardRule(ValidationRule):
    """Verifies that the companion CARD.md summary card exists and is properly formatted."""

    @property
    def name(self) -> str:
        return "CARD.md Summary"

    @property
    def category(self) -> str:
        return "specification"

    async def validate(self, ctx: ValidationContext) -> bool:
        card_file = ctx.path / "CARD.md"
        if not card_file.exists():
            ctx.add_warn(self.name, "Missing companion CARD.md summary card", category=self.category)
            return True

        card_text = card_file.read_text(encoding="utf-8", errors="ignore")
        has_table = "|" in card_text and "---" in card_text
        has_ascii = "╔" in card_text or "==" in card_text or "SKILL:" in card_text
        if has_table and has_ascii:
            ctx.add_pass(self.name, "Valid CARD.md summary box & stage table", category=self.category)
        else:
            ctx.add_warn(self.name, "CARD.md missing stage table or ASCII card box", category=self.category)

        return True
