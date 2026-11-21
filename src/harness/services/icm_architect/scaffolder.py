"""Canonical form scaffolding engine for Interpretable Context Methodology (ICM)."""

from __future__ import annotations

from pathlib import Path

from .models import IcmFormType, IcmScaffoldResult


class IcmScaffolder:
    """Scaffolds starter workspaces from one of 5 canonical ICM forms."""

    def scaffold_form(
        self,
        target_dir: str | Path,
        form: str | IcmFormType = IcmFormType.PIPELINE,
        name: str | None = None,
    ) -> IcmScaffoldResult:
        out_dir = Path(target_dir).resolve()
        form_type = IcmFormType(form) if isinstance(form, str) else form
        workspace_name = name or out_dir.name
        created_files: list[str] = []

        try:
            out_dir.mkdir(parents=True, exist_ok=True)

            agents_md = (
                f"# {workspace_name}\n\n"
                f"ICM workspace operating as a {form_type.value}.\n\n"
                "## Routing Table\n"
                "- Pipeline & stages: [CONTEXT.md](CONTEXT.md)\n"
                "- Factory references: [_shared/](_shared/)\n"
                "- Tools & scripts: [_tools/](_tools/)\n\n"
                "## Rules\n"
                "- Read nearest CONTEXT.md before executing any task.\n"
                "- State status purely from files on disk.\n"
                "- Load only what the step needs (<8,000 tokens).\n"
            )
            (out_dir / "AGENTS.md").write_text(agents_md, encoding="utf-8")
            created_files.append("AGENTS.md")

            (out_dir / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
            created_files.append("CLAUDE.md")
            (out_dir / "GEMINI.md").write_text("@./AGENTS.md\n", encoding="utf-8")
            created_files.append("GEMINI.md")

            shared_dir = out_dir / "_shared"
            shared_dir.mkdir(exist_ok=True)
            (shared_dir / "voice.md").write_text(
                "# Factory Voice & Guidelines\n\nStable across runs.\n", encoding="utf-8"
            )
            created_files.append("_shared/voice.md")

            (out_dir / "_tools").mkdir(exist_ok=True)
            templates_dir = out_dir / "_templates"
            templates_dir.mkdir(exist_ok=True)

            if form_type == IcmFormType.PIPELINE:
                root_context = (
                    f"# Pipeline: {workspace_name}\n\n"
                    "Sequential production line where each stage output feeds downstream inputs.\n\n"
                    "## Stages\n"
                    "1. [01_research](stages/01_research/CONTEXT.md) -> outputs research.md\n"
                    "2. [02_draft](stages/02_draft/CONTEXT.md) -> outputs draft.md\n"
                    "3. [03_delivery](stages/03_delivery/CONTEXT.md) -> outputs deliverable.md\n"
                )
                (out_dir / "CONTEXT.md").write_text(root_context, encoding="utf-8")
                created_files.append("CONTEXT.md")

                for idx, stage in enumerate(["01_research", "02_draft", "03_delivery"], 1):
                    s_path = out_dir / "stages" / stage
                    (s_path / "output").mkdir(parents=True, exist_ok=True)
                    (s_path / "references").mkdir(parents=True, exist_ok=True)
                    stage_context = (
                        f"# {stage} Contract\n\n"
                        f"One job: execute stage {idx} of {workspace_name}.\n\n"
                        "## Inputs\n"
                        "- Reference (every run): `../../_shared/voice.md`\n"
                    )
                    if idx > 1:
                        prev = ["01_research", "02_draft"][idx - 2]
                        stage_context += f"- Working (this run): `../{prev}/output/output.md`\n"

                    stage_context += (
                        "\n## Process\n"
                        "1. Verify inputs exist.\n"
                        "2. Transform according to factory voice.\n"
                        "3. Write final result to output/.\n\n"
                        "## Outputs\n"
                        "- `output.md` -> `output/`\n\n"
                        "## Check\n"
                        "Validate output file is non-empty and passes checks. Write check.md with pass or fail: reason.\n"
                    )
                    (s_path / "CONTEXT.md").write_text(stage_context, encoding="utf-8")
                    created_files.append(f"stages/{stage}/CONTEXT.md")

            elif form_type == IcmFormType.RECORD_LIBRARY:
                root_context = (
                    f"# Record Library: {workspace_name}\n\n"
                    "Uniform records accumulating status across their lifecycle.\n\n"
                    "## Shelves\n"
                    "- Active records: [records/](records/_index.md)\n"
                )
                (out_dir / "CONTEXT.md").write_text(root_context, encoding="utf-8")
                created_files.append("CONTEXT.md")

                records_dir = out_dir / "records"
                records_dir.mkdir(exist_ok=True)
                (records_dir / "_index.md").write_text("# Records Index\n\nGenerated index.\n", encoding="utf-8")
                created_files.append("records/_index.md")

                template_card = (
                    "---\ntitle: Sample Record\nstatus: active\ndescription: Initial record card\n---\n\n"
                    "# Sample Record\n\n## Context\nRecord details here.\n"
                )
                (templates_dir / "record-template.md").write_text(template_card, encoding="utf-8")
                created_files.append("_templates/record-template.md")

            elif form_type == IcmFormType.KNOWLEDGE_BUNDLE:
                raw_dir = out_dir / "sources" / "raw"
                raw_dir.mkdir(parents=True, exist_ok=True)
                (raw_dir / ".gitkeep").write_text("", encoding="utf-8")
                created_files.append("sources/raw/.gitkeep")

                meta_dir = out_dir / "_meta"
                meta_dir.mkdir(exist_ok=True)
                (meta_dir / "keep-out.txt").write_text(
                    "# One forbidden phrase per line; checked by harness icm quotes.\n",
                    encoding="utf-8",
                )
                created_files.append("_meta/keep-out.txt")

                concepts_dir = out_dir / "concepts"
                concepts_dir.mkdir(exist_ok=True)
                (concepts_dir / "_index.md").write_text(
                    "# Concepts Index\n\nDistilled concepts and verbatim-grounded claims.\n",
                    encoding="utf-8",
                )
                created_files.append("concepts/_index.md")

                concept_tpl = (
                    "---\ntitle: Concept Template\nstatus: draft\nsource_key: example_source\n---\n\n"
                    "# Concept Title\n\n## Claim\nState distilled finding concisely.\n\n"
                    "## Verbatim Evidence\nAdd quoted excerpt cited with its sources/raw stem.\n\n"
                    "## Check\nRun `harness icm quotes .` and confirm zero broken quotes.\n"
                )
                (templates_dir / "concept-template.md").write_text(concept_tpl, encoding="utf-8")
                created_files.append("_templates/concept-template.md")

                root_context = (
                    f"# Knowledge Bundle: {workspace_name}\n\n"
                    "Raw sources, distilled concepts, and verbatim-verified claims.\n\n"
                    "## Routing\n"
                    "- Concepts catalog: [concepts/_index.md](concepts/_index.md)\n"
                    "- Concept template: [_templates/concept-template.md](_templates/concept-template.md)\n"
                    "- Factory voice: [_shared/voice.md](_shared/voice.md)\n\n"
                    "## Inputs\n"
                    "- Raw sources directory: `sources/raw/`\n"
                    "- Keep-out guardrails: `_meta/keep-out.txt`\n\n"
                    "## Outputs\n"
                    "- Concept notes in `concepts/` and updated `concepts/_index.md`\n\n"
                    "## Check\n"
                    "Run `harness icm quotes .` and `harness icm links .` before proposing updates.\n"
                )
                (out_dir / "CONTEXT.md").write_text(root_context, encoding="utf-8")
                created_files.append("CONTEXT.md")

            elif form_type == IcmFormType.CONTEXT_MAP:
                teams_dir = out_dir / "teams"
                teams_dir.mkdir(exist_ok=True)
                (teams_dir / "_index.md").write_text(
                    "# Domains & Teams Index\n\n- [Core Domain](core-domain.md)\n",
                    encoding="utf-8",
                )
                created_files.append("teams/_index.md")

                core_domain = (
                    "---\n"
                    "title: Core Domain\n"
                    "consumes: ../_shared/voice.md\n"
                    "produces: ../CONTEXT.md\n"
                    "---\n\n"
                    "# Core Domain Contract\n\n"
                    "## Scope\nDefine bounded context inputs, ownership, and handoffs.\n\n"
                    "## Inputs\n"
                    "- Shared conventions: `../_shared/voice.md`\n\n"
                    "## Check\nVerify relative links and upstream contracts with `harness icm links .`.\n"
                )
                (teams_dir / "core-domain.md").write_text(core_domain, encoding="utf-8")
                created_files.append("teams/core-domain.md")

                root_context = (
                    "---\n"
                    "consumes: _shared/voice.md\n"
                    "---\n\n"
                    f"# Context Map: {workspace_name}\n\n"
                    "Organizational map of domain boundaries, inputs, and handoff contracts.\n\n"
                    "## Domains\n"
                    "- Domains index: [teams/_index.md](teams/_index.md)\n"
                    "- Core domain contract: [teams/core-domain.md](teams/core-domain.md)\n"
                    "- Factory voice: [_shared/voice.md](_shared/voice.md)\n\n"
                    "## Inputs\n"
                    "- Shared voice and policy: `_shared/voice.md`\n\n"
                    "## Check\nRun `harness icm audit .` and `harness icm links .` after boundary edits.\n"
                )
                (out_dir / "CONTEXT.md").write_text(root_context, encoding="utf-8")
                created_files.append("CONTEXT.md")

            elif form_type == IcmFormType.SYSTEM_MAP:
                objects_dir = out_dir / "objects"
                objects_dir.mkdir(exist_ok=True)
                (objects_dir / "_index.md").write_text(
                    "# System Objects Index\n\nCore domain entities, interfaces, and schemas.\n",
                    encoding="utf-8",
                )
                created_files.append("objects/_index.md")

                processes_dir = out_dir / "processes"
                processes_dir.mkdir(exist_ok=True)
                (processes_dir / "_index.md").write_text(
                    "# System Processes Index\n\nWorkflow transitions, DAG seams, and impact paths.\n",
                    encoding="utf-8",
                )
                created_files.append("processes/_index.md")

                object_tpl = (
                    "---\ntitle: System Object\nstatus: mapped\nowner: architecture\n---\n\n"
                    "# System Object\n\n## Responsibilities\nDescribe seam ownership.\n\n"
                    "## Dependencies\nList upstream inputs and downstream consumers.\n\n"
                    "## Check\nRebuild index and verify links cleanly.\n"
                )
                (templates_dir / "object-template.md").write_text(object_tpl, encoding="utf-8")
                created_files.append("_templates/object-template.md")

                root_context = (
                    f"# System Map: {workspace_name}\n\n"
                    "Structural noun-and-verb map of architecture seams, entities, and impact paths.\n\n"
                    "## Map Shelves\n"
                    "- Objects (nouns): [objects/_index.md](objects/_index.md)\n"
                    "- Processes (verbs): [processes/_index.md](processes/_index.md)\n"
                    "- Object template: [_templates/object-template.md](_templates/object-template.md)\n"
                    "- Factory voice: [_shared/voice.md](_shared/voice.md)\n\n"
                    "## Inputs\n"
                    "- Stable architecture conventions: `_shared/voice.md`\n\n"
                    "## Check\nRun `harness icm audit .` and `harness icm links .` after mapping changes.\n"
                )
                (out_dir / "CONTEXT.md").write_text(root_context, encoding="utf-8")
                created_files.append("CONTEXT.md")

            return IcmScaffoldResult(
                target_dir=str(out_dir),
                form=form_type.value,
                created_files=created_files,
                status="ok",
            )
        except Exception as err:
            return IcmScaffoldResult(
                target_dir=str(out_dir),
                form=form_type.value,
                created_files=created_files,
                status="error",
                error=str(err),
            )
