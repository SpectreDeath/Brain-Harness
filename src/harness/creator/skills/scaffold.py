"""Authoritative code and markdown generation engine for agent skills."""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from harness.creator.skills.models import SkillOptions, SkillResult
from harness.creator.skills.validator import SkillValidator

logger = structlog.get_logger()


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

        prov_row = ""
        if options.generated_by:
            prov_str = ", ".join(options.generated_by)
            prov_row = f"│ Provenance: {prov_str[:56]:<56} │\n"

        return (
            f"```\n"
            f"┌──────────────────────────────────────────────────────────────────────┐\n"
            f"│ SKILL: {clean_name:<61} │\n"
            f"│ Category: {options.category:<58} │\n"
            f"│ Version:  {options.version:<58} │\n"
            f"│ Invocation: /{clean_name:<56} │\n"
            f"│ Triggers: {triggers_formatted[:58]:<58} │\n"
            f"│ Target:   {target_str[:58]:<58} │\n"
            f"{prov_row}"
            f"└──────────────────────────────────────────────────────────────────────┘\n"
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

        # 4. .provenance.json (Track 1A P2)
        if opts.generated_by or opts.source_ki_id:
            import json
            from datetime import datetime, timezone
            prov_path = out_dir / ".provenance.json"
            prov_data = {
                "skill_name": opts.name,
                "generated_by": opts.generated_by,
                "source_ki_id": opts.source_ki_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            prov_path.write_text(json.dumps(prov_data, indent=2), encoding="utf-8")
            generated_files.append(prov_path)

            if opts.source_ki_id:
                vault_ki_meta = Path(".harness/knowledge") / opts.source_ki_id / "metadata.json"
                if vault_ki_meta.exists():
                    try:
                        ki_data = json.loads(vault_ki_meta.read_text(encoding="utf-8"))
                        edges = ki_data.get("edges", [])
                        if not any(e.get("type") == "became_skill" and e.get("target") == opts.name for e in edges):
                            edges.append({
                                "type": "became_skill",
                                "target": opts.name,
                                "target_kind": "skill",
                                "derived": False,
                                "confidence": 1.0,
                            })
                            ki_data["edges"] = edges
                            vault_ki_meta.write_text(json.dumps(ki_data, indent=2), encoding="utf-8")
                    except Exception as e:
                        logger.debug("Failed to record became_skill edge in source KI", ki_id=opts.source_ki_id, error=str(e))

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
