"""Skill Creator and Validator — authoritative engine for crafting, scaffolding, and validating agent skills.

Implements the high-precision craft standards defined in crafting-skills:
    1. The Visual Brief — Interactive HTML reports with Mermaid topology diagrams.
    2. The Mandatory Checkpoint — Human-in-the-loop gates (RequestFeedback: true).
    3. Explicit Anti-Patterns — Named behavioral boundaries.
    4. Companion Summary Card (CARD.md) — ASCII summary box, stage progression table, and invariants checklist.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import structlog

from harness.creator.validator import (
    RuleSeverity,
    ValidationContext,
    ValidationPipeline,
    ValidationReport,
    ValidationRule,
    _run_coro_sync,
)

logger = structlog.get_logger()


@dataclass
class SkillOptions:
    """Configuration options for scaffolding a high-precision agent skill."""

    name: str
    description: str = ""
    category: str = "engineering / meta-skills"
    version: str = "1.0.0"
    triggers: list[str] = field(default_factory=list)
    target: str = ""
    stages: list[dict[str, str]] = field(default_factory=list)
    anti_patterns: list[dict[str, str]] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    vocabulary: dict[str, str] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)
    include_card: bool = True
    include_readme: bool = True
    auto_validate: bool = False


@dataclass
class SkillResult(os.PathLike[str]):
    """Structured result returned from skill scaffolding."""

    path: Path
    skill_file: Path
    card_file: Path | None
    generated_files: list[Path] = field(default_factory=list)
    validation_report: ValidationReport | None = None

    @property
    def files_count(self) -> int:
        return len(self.generated_files)

    def __fspath__(self) -> str:
        return str(self.path)

    def __str__(self) -> str:
        return str(self.path)

    def __truediv__(self, other: str | Path) -> Path:
        return self.path / other

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "skill_file": str(self.skill_file),
            "card_file": str(self.card_file) if self.card_file else None,
            "generated_files": [str(f) for f in self.generated_files],
            "files_count": self.files_count,
            "validation_report": self.validation_report.to_dict() if self.validation_report else None,
        }


class SkillScaffoldEngine:
    """Authoritative code and markdown generation engine for agent skills."""

    @classmethod
    def generate_skill_md(cls, options: SkillOptions) -> str:
        """Generate high-precision SKILL.md following crafting-skills specification."""
        clean_name = options.name.strip().lower().replace("_", "-")
        title = clean_name.replace("-", " ").title()

        triggers_str = ", ".join(f'"{t}"' for t in options.triggers) if options.triggers else f'"{clean_name}"'
        desc = options.description or f"Execute high-leverage {title} workflows. Use when triggered by {triggers_str}."

        stages = options.stages or [
            {"num": "1", "name": "Analyze & Audit", "desc": "Survey system boundaries, collect telemetry, and identify concrete operational friction sites.", "criterion": "Concrete list of target friction sites identified."},
            {"num": "2", "name": "Assess & Formulate", "desc": "Score candidate opportunities along locality, leverage, and testability dimensions.", "criterion": "Prioritized action matrix with clear tradeoffs."},
            {"num": "3", "name": "The Visual Brief", "desc": f"Generate an interactive HTML report at %TEMP%/{clean_name}-review-<timestamp>.html with Before vs. After Mermaid diagrams.", "criterion": "Valid, self-contained HTML visual brief rendered and linked."},
            {"num": "4", "name": "Mandatory Checkpoint", "desc": "Author an implementation_plan.md artifact with RequestFeedback: true. STOP and await explicit user approval.", "criterion": "Explicit user confirmation received before modifying state."},
            {"num": "5", "name": "Execution & Verification", "desc": "Execute planned operations incrementally, verifying regression test suite after each atomic step.", "criterion": "100% test pass rate with zero unexpected regressions."},
            {"num": "6", "name": "Recording & Walkthrough", "desc": "Generate walkthrough.md summarizing completed changes, clickable links, and execution duration.", "criterion": "Comprehensive walkthrough artifact recorded."},
        ]

        anti_patterns = options.anti_patterns or [
            {"name": "Speculative Abstraction", "symptom": "Adding generic wrappers or premature layers not needed by immediate requirements.", "rule": "Never add abstractions ahead of direct concrete need."},
            {"name": "Bypassing The Checkpoint", "symptom": "Modifying code or executing destructive commands before receiving explicit plan approval.", "rule": "Always stop and wait at Stage 4 gate."},
            {"name": "Premature Completion", "symptom": "Declaring done before executing automated test suite verification.", "rule": "Always run pytest and verify zero regressions."},
        ]

        stages_md = []
        for s in stages:
            stages_md.append(
                f"### Stage {s['num']}: {s['name']}\n\n"
                f"{s['desc']}\n\n"
                f"> **Completion criterion**: {s['criterion']}\n"
            )
        stages_block = "\n---\n\n".join(stages_md)

        anti_patterns_md = []
        for ap in anti_patterns:
            anti_patterns_md.append(
                f"#### 🚫 {ap['name']}\n"
                f"- **Telltale symptom**: {ap['symptom']}\n"
                f"- **Rule**: {ap['rule']}\n"
            )
        anti_patterns_block = "\n".join(anti_patterns_md)

        return (
            f"---\n"
            f"name: {clean_name}\n"
            f"description: {desc}\n"
            f"---\n\n"
            f"# {title}\n\n"
            f"`{clean_name}` is a high-precision agent workflow engine designed for deep-module execution.\n\n"
            f"Every execution follows three foundational pillars:\n"
            f"1. **The Visual Brief** — Interactive HTML reports in `%TEMP%` with Tailwind and Mermaid diagrams.\n"
            f"2. **The Mandatory Checkpoint** — Explicit human-in-the-loop gates (`RequestFeedback: true`).\n"
            f"3. **Explicit Anti-Patterns** — Rigid behavioral guardrails eliminating speculative abstractions.\n\n"
            f"See [CARD.md](CARD.md) for the summary card and completion checklist.\n\n"
            f"---\n\n"
            f"## Execution Sequence\n\n"
            f"{stages_block}\n"
            f"---\n\n"
            f"## Behavioral Guardrails & Anti-Patterns\n\n"
            f"{anti_patterns_block}\n"
        )

    @classmethod
    def generate_card_md(cls, options: SkillOptions) -> str:
        """Generate compact companion summary CARD.md."""
        clean_name = options.name.strip().lower().replace("_", "-")
        title = clean_name.replace("-", " ").title()

        triggers_list = options.triggers or [f"/{clean_name}", clean_name.replace("-", " ")]
        triggers_formatted = ", ".join(f'"{t}"' for t in triggers_list)
        target_str = options.target or f"Deterministic execution of {title} workflows"

        stages = options.stages or [
            {"num": "1", "name": "Analyze & Audit", "gate": "Friction list"},
            {"num": "2", "name": "Assess & Score", "gate": "Scored matrix"},
            {"num": "3", "name": "Visual Brief", "gate": "HTML report"},
            {"num": "4", "name": "Checkpoint Gate", "gate": "User approval"},
            {"num": "5", "name": "Execute & Test", "gate": "Tests passing"},
            {"num": "6", "name": "Walkthrough", "gate": "Artifact written"},
        ]

        table_rows = []
        for s in stages:
            gate = s.get("gate") or s.get("criterion", "Done")
            table_rows.append(f"| **{s['num']}. {s['name']}** | {s.get('desc', s['name'])} | `{gate}` |")
        table_block = "\n".join(table_rows)

        invariants = options.invariants or [
            "Visual Brief HTML generated in %TEMP% before presenting changes",
            "implementation_plan.md submitted with RequestFeedback: true",
            "Zero destructive actions taken prior to explicit approval",
            "100% automated test pass rate verified on completion",
        ]
        invariants_block = "\n".join(f"- [ ] {inv}" for inv in invariants)

        vocab = options.vocabulary or {
            "Locality": "Changes concentrated within a single cohesive seam rather than scattered across modules.",
            "Leverage": "High ratio of behavioral impact to code changes (often net-negative LoC).",
            "Checkpoint Gate": "Mandatory pause requiring user approval before executing state modifications.",
        }
        vocab_block = "\n".join(f"- **{k}**: {v}" for k, v in vocab.items())

        return (
            f"```\n"
            f"╔══════════════════════════════════════════════════════════════════════╗\n"
            f"║ SKILL: {clean_name:<61} ║\n"
            f"║ Category: {options.category:<58} ║\n"
            f"║ Version:  {options.version:<58} ║\n"
            f"║ Invocation: /{clean_name:<56} ║\n"
            f"║ Triggers: {triggers_formatted[:58]:<58} ║\n"
            f"║ Target:   {target_str[:58]:<58} ║\n"
            f"╚══════════════════════════════════════════════════════════════════════╝\n"
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

    @classmethod
    def generate_readme_md(cls, options: SkillOptions) -> str:
        """Generate skill documentation README.md."""
        clean_name = options.name.strip().lower().replace("_", "-")
        title = clean_name.replace("-", " ").title()

        return (
            f"# {title} Skill\n\n"
            f"{options.description or f'Agent skill package for {title}.'}\n\n"
            f"## Structure\n"
            f"- `SKILL.md`: Authoritative specification and execution progression.\n"
            f"- `CARD.md`: Quick-reference cheat sheet and completion checklist.\n\n"
            f"## Invocation\n"
            f"Trigger in chat using `/{clean_name}` or relevant keywords.\n"
        )

    @classmethod
    def scaffold(
        cls,
        target_dir: Path | str,
        options: SkillOptions | None = None,
        *,
        name: str | None = None,
        description: str = "",
        category: str = "engineering / meta-skills",
        triggers: list[str] | None = None,
        target: str = "",
        auto_validate: bool = False,
    ) -> SkillResult:
        """Synchronously scaffold a compliant skill directory."""
        out_dir = Path(target_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        opts = options or SkillOptions(
            name=name or out_dir.name,
            description=description,
            category=category,
            triggers=triggers or [],
            target=target,
            auto_validate=auto_validate,
        )

        generated_files: list[Path] = []

        # 1. SKILL.md
        skill_path = out_dir / "SKILL.md"
        skill_path.write_text(cls.generate_skill_md(opts), encoding="utf-8")
        generated_files.append(skill_path)

        # 2. CARD.md
        card_path = None
        if opts.include_card:
            card_path = out_dir / "CARD.md"
            card_path.write_text(cls.generate_card_md(opts), encoding="utf-8")
            generated_files.append(card_path)

        # 3. README.md
        if opts.include_readme:
            readme_path = out_dir / "README.md"
            readme_path.write_text(cls.generate_readme_md(opts), encoding="utf-8")
            generated_files.append(readme_path)

        validation_report = None
        if opts.auto_validate:
            validation_report = SkillValidator.validate(out_dir)

        logger.info(
            "Scaffolded agent skill",
            name=opts.name,
            path=str(out_dir),
            files_count=len(generated_files),
        )

        return SkillResult(
            path=out_dir,
            skill_file=skill_path,
            card_file=card_path,
            generated_files=generated_files,
            validation_report=validation_report,
        )

    @classmethod
    async def scaffold_async(
        cls,
        target_dir: Path | str,
        options: SkillOptions | None = None,
        *,
        name: str | None = None,
        description: str = "",
        category: str = "engineering / meta-skills",
        triggers: list[str] | None = None,
        target: str = "",
        auto_validate: bool = False,
    ) -> SkillResult:
        """Asynchronously scaffold a compliant skill directory."""
        return await asyncio.to_thread(
            cls.scaffold,
            target_dir,
            options=options,
            name=name,
            description=description,
            category=category,
            triggers=triggers,
            target=target,
            auto_validate=auto_validate,
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


class SkillValidator:
    """Diagnostic validator verifying agent skills against craft standards."""

    @classmethod
    def default_pipeline(cls) -> ValidationPipeline:
        """Create a default ValidationPipeline with all skill craft rules."""
        return ValidationPipeline(
            rules=[
                SkillDirectoryRule(),
                SkillFrontmatterRule(),
                SkillPillarRule(),
                SkillCardRule(),
            ]
        )

    @classmethod
    async def validate_async(
        cls,
        skill_dir: Path | str,
        *,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Asynchronously validate an agent skill directory."""
        active_pipeline = pipeline or cls.default_pipeline()
        return await active_pipeline.execute(skill_dir)

    @classmethod
    def validate(
        cls,
        skill_dir: Path | str,
        *,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Validate an agent skill directory."""
        return cast(ValidationReport, _run_coro_sync(cls.validate_async(skill_dir, pipeline=pipeline)))

    @classmethod
    def validate_sync(
        cls,
        skill_dir: Path | str,
        *,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Synchronously validate an agent skill directory."""
        return cls.validate(skill_dir, pipeline=pipeline)


__all__ = [
    "SkillCardRule",
    "SkillDirectoryRule",
    "SkillFrontmatterRule",
    "SkillOptions",
    "SkillPillarRule",
    "SkillResult",
    "SkillScaffoldEngine",
    "SkillValidator",
]
