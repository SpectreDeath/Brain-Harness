"""Markdown and audit-script templates for the 7-part spawned harness documentation bundle."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

_AUDIT_DOCS_SCRIPT = '''"""Standalone verification gate for spawned harness documentation contracts."""

from __future__ import annotations

import pathlib
import re
import sys

REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "CONTEXT.md",
    "docs/USE_CASES.md",
    "docs/PROVENANCE.md",
    "docs/RUNBOOK.md",
    "dock.yaml",
)
SKIP_PARTS = frozenset({".git", ".agents", ".harness", "__pycache__", ".venv", "node_modules"})
FENCE_RX = re.compile(r"```.*?```", re.DOTALL)
LINK_RX = re.compile(r"\\[[^\\]]*\\]\\((<[^>]+>|[^)\\s]+)\\)")


def main() -> int:
    root = pathlib.Path(".").resolve()
    missing = [r for r in REQUIRED_FILES if not (root / r).is_file() or not (root / r).read_text(encoding="utf-8").strip()]
    if missing:
        print(f"Missing or empty required docs: {missing}", file=sys.stderr)
        return 1

    skills_dir = root / ".agents" / "skills"
    if skills_dir.is_dir():
        missing_cards = [
            d.name
            for d in sorted(skills_dir.iterdir())
            if d.is_dir() and (d / "SKILL.md").is_file() and not (d / "CARD.md").is_file()
        ]
        if missing_cards:
            print(f"Missing companion CARD.md files: {missing_cards}", file=sys.stderr)
            return 1

    broken: list[tuple[str, str]] = []
    for md in root.rglob("*.md"):
        if any(part in SKIP_PARTS for part in md.relative_to(root).parts):
            continue
        cleaned = FENCE_RX.sub("", md.read_text(encoding="utf-8", errors="replace"))
        for m in LINK_RX.finditer(cleaned):
            target = m.group(1).strip("<>").split("#")[0]
            if not target or target.startswith(("http://", "https://", "mailto:")) or "{" in target:
                continue
            if not (md.parent / target).exists():
                broken.append((md.relative_to(root).as_posix(), target))

    if broken:
        print(f"Broken relative documentation links: {broken}", file=sys.stderr)
        return 1

    print("DOCS_AUDIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


@dataclass(slots=True, frozen=True)
class FormLayoutMeta:
    header_frontmatter: str
    routes: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    check_line: str


FORM_LAYOUTS: dict[str, FormLayoutMeta] = {
    "pipeline": FormLayoutMeta(
        header_frontmatter="",
        routes=(
            "- Stage 01 Research: [stages/01_research/CONTEXT.md](stages/01_research/CONTEXT.md)",
            "- Stage 02 Draft: [stages/02_draft/CONTEXT.md](stages/02_draft/CONTEXT.md)",
            "- Stage 03 Delivery: [stages/03_delivery/CONTEXT.md](stages/03_delivery/CONTEXT.md)",
            "- Factory voice: [_shared/voice.md](_shared/voice.md)",
        ),
        inputs=("- Shared harness conventions: `_shared/voice.md`", "- Stage specs under `stages/`"),
        outputs=("- Verified stage outputs under `stages/*/output/` and `check.md` verdicts",),
        check_line="Run `harness icm audit .`, `harness icm links .`, and verify each stage `check.md`.",
    ),
    "record_library": FormLayoutMeta(
        header_frontmatter="",
        routes=(
            "- Active records index: [records/_index.md](records/_index.md)",
            "- Record template: [_templates/record-template.md](_templates/record-template.md)",
            "- Factory voice: [_shared/voice.md](_shared/voice.md)",
        ),
        inputs=("- Existing records shelf: `records/_index.md`", "- Template schema: `_templates/record-template.md`"),
        outputs=("- Uniform frontmatter cards in `records/` with rebuilt `records/_index.md`",),
        check_line="Run `harness icm index records --root .`, `harness icm audit .`, and `harness icm links .`.",
    ),
    "knowledge_bundle": FormLayoutMeta(
        header_frontmatter="",
        routes=(
            "- Concepts index: [concepts/_index.md](concepts/_index.md)",
            "- Concept template: [_templates/concept-template.md](_templates/concept-template.md)",
            "- Factory voice: [_shared/voice.md](_shared/voice.md)",
        ),
        inputs=("- Raw source excerpts: `sources/raw/`", "- Keep-out rules: `_meta/keep-out.txt`"),
        outputs=("- Verbatim-grounded concepts in `concepts/` and rebuilt `concepts/_index.md`",),
        check_line="Run `harness icm quotes .`, `harness icm audit .`, and `harness icm links .`.",
    ),
    "context_map": FormLayoutMeta(
        header_frontmatter="---\nconsumes: _shared/voice.md\n---\n\n",
        routes=(
            "- Domains index: [teams/_index.md](teams/_index.md)",
            "- Core domain contract: [teams/core-domain.md](teams/core-domain.md)",
            "- Factory voice: [_shared/voice.md](_shared/voice.md)",
        ),
        inputs=("- Shared boundary rules: `_shared/voice.md`", "- Domain contracts in `teams/`"),
        outputs=("- Verified cross-domain boundary specs under `teams/`",),
        check_line="Run `harness icm audit .` and `harness icm links .` after boundary edits.",
    ),
    "system_map": FormLayoutMeta(
        header_frontmatter="",
        routes=(
            "- System objects: [objects/_index.md](objects/_index.md)",
            "- System processes: [processes/_index.md](processes/_index.md)",
            "- Object template: [_templates/object-template.md](_templates/object-template.md)",
            "- Factory voice: [_shared/voice.md](_shared/voice.md)",
        ),
        inputs=("- Architecture baseline: `_shared/voice.md`", "- Mapped entities under `objects/` and `processes/`"),
        outputs=("- Updated noun/verb indexes in `objects/_index.md` and `processes/_index.md`",),
        check_line="Run `harness icm audit .` and `harness icm links .` after seam mapping updates.",
    ),
}


class BlueprintLike(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def domain(self) -> str: ...
    @property
    def title(self) -> str: ...
    @property
    def mission(self) -> str: ...
    @property
    def icm_form(self) -> str: ...
    @property
    def skills(self) -> tuple[str, ...]: ...
    @property
    def graph_source(self) -> str: ...
    @property
    def cohesion_score(self) -> float: ...
    @property
    def bridge_count(self) -> int: ...
    @property
    def score(self) -> float: ...
    @property
    def seeded_kis(self) -> Sequence[Any]: ...
    @property
    def excluded_unverified_kis(self) -> tuple[str, ...]: ...
    @property
    def use_cases(self) -> tuple[str, ...]: ...
    @property
    def out_of_scope(self) -> tuple[str, ...]: ...
    @property
    def prime_skill_count(self) -> int: ...
    @property
    def estimated_token_savings_pct(self) -> float: ...


def render_minimal_card(skill: str) -> str:
    return (
        f"# {skill} — Summary Card\n\n"
        "```text\n"
        "┌────────────────────────────────────────────────────────────┐\n"
        f"│ SKILL: {skill:<52}│\n"
        "│ TYPE:  Domain Harness Companion Card                       │\n"
        "└────────────────────────────────────────────────────────────┘\n"
        "```\n\n"
        "## Mandatory Invariants Checklist\n"
        "- [ ] Keep active step context bounded under 8,000 tokens.\n"
        "- [ ] Stage candidate learnings via `harness spawn propose`; never auto-adopt.\n"
    )


def render_root_context(bp: BlueprintLike) -> str:
    layout = FORM_LAYOUTS.get(bp.icm_form, FORM_LAYOUTS["pipeline"])
    routes = "\n".join(layout.routes)
    inputs = "\n".join(layout.inputs)
    outputs = "\n".join(layout.outputs)
    return (
        f"{layout.header_frontmatter}"
        f"# {bp.name} — ICM Operational Contract\n\n"
        f"Form: `{bp.icm_form}` | Domain: `{bp.domain}`\n\n"
        "## Navigation\n"
        f"{routes}\n"
        "- Overview & scope: [README.md](README.md)\n\n"
        "## Inputs\n"
        f"{inputs}\n\n"
        "## Do NOT load\n"
        "- Do NOT load unbundled Prime skills outside `.agents/skills/`\n"
        "- Do NOT load raw archives outside the active step contract\n\n"
        "## Outputs\n"
        f"{outputs}\n\n"
        "## Check\n"
        f"{layout.check_line}\n"
    )


def render_readme(bp: BlueprintLike, *, prime_commit: str, spawn_id: str, created_utc: str) -> str:
    uc_lines = "\n".join(f"- **Use Case {i}:** {uc}" for i, uc in enumerate(bp.use_cases, 1))
    oos_lines = "\n".join(f"- Do NOT use for {item}" for item in bp.out_of_scope)
    if bp.skills:
        skill_rows = "\n".join(
            f"| `{s}` | [SKILL.md](.agents/skills/{s}/SKILL.md) | [CARD.md](.agents/skills/{s}/CARD.md) |"
            for s in bp.skills
        )
        skill_block = "| Skill | Spec | Companion Card |\n|---|---|---|\n" + skill_rows
    else:
        skill_block = "No domain skills bundled; uses root `AGENTS.md` routing only."

    if bp.seeded_kis:
        ki_rows = "\n".join(f"| `{k.ki_id}` | {k.title} | `{k.domain}` | `{k.isnad_status}` |" for k in bp.seeded_kis)
        ki_block = "| KI ID | Title | Domain | Isnad |\n|---|---|---|---|\n" + ki_rows
    else:
        ki_block = "No `VERIFIED` KIs seeded at spawn time."

    return (
        f"# {bp.title} (`{bp.name}`)\n\n"
        "## Mission\n\n"
        f"{bp.mission}\n\n"
        "## Use Cases\n\n"
        f"{uc_lines}\n\n"
        "## Out of Scope\n\n"
        f"{oos_lines}\n\n"
        "## Lineage\n\n"
        "| Field | Value |\n|---|---|\n"
        f"| Prime Commit | `{prime_commit}` |\n"
        f"| Spawn ID | `{spawn_id or 'materialized-direct'}` |\n"
        f"| Graph Source | `{bp.graph_source}` |\n"
        f"| ICM Form | `{bp.icm_form}` |\n"
        f"| Generated (UTC) | `{created_utc}` |\n\n"
        "## Quick Start\n\n"
        "Run from this harness directory (or via Prime's `.venv\\Scripts\\harness.exe` if not on PATH):\n\n"
        "```powershell\n"
        f"harness dock inspect .\n"
        f"harness dock run {bp.name} validate\n"
        f"harness dock run {bp.name} audit-docs\n"
        f"harness dock run {bp.name} icm-audit\n"
        f"harness dock run {bp.name} icm-links\n"
        "harness icm audit .\n"
        "harness icm links .\n"
        "```\n\n"
        "Without an activated venv, standalone doc verification also runs directly via `python _tools/audit_docs.py`.\n\n"
        "Deep references: [CONTEXT.md](CONTEXT.md), [Worked Use Cases](docs/USE_CASES.md), "
        "[Graph Provenance](docs/PROVENANCE.md), [Operations Runbook](docs/RUNBOOK.md).\n\n"
        "## Skills\n\n"
        f"{skill_block}\n\n"
        "## Seeded Knowledge Items\n\n"
        f"{ki_block}\n"
    )


def render_use_cases(bp: BlueprintLike) -> str:
    sections: list[str] = [
        f"# Worked Use Cases: `{bp.name}`",
        "",
        "Links: [README](../README.md) | [Operational Contract](../CONTEXT.md) | [Runbook](RUNBOOK.md)",
        "",
    ]
    for i, uc in enumerate(bp.use_cases, 1):
        sections.extend(
            [
                f"## Scenario {i}",
                "",
                f"- **Trigger / Input:** {uc}",
                f"- **Command / Stage Sequence:** Inspect [../CONTEXT.md](../CONTEXT.md), execute step workflow under `{bp.icm_form}`, and record structured outputs on disk.",
                "- **Expected Artifact:** Verified output artifact in the harness workspace folder matching ICM shelf/stage schema.",
                f"- **Pass/Fail Check:** `harness icm audit .`, `harness icm links .`, and `harness dock run {bp.name} audit-docs` pass with zero errors.",
                "",
            ]
        )
    sections.extend(
        [
            f"## Scenario {len(bp.use_cases) + 1}: Cold-Agent & Drift Verification",
            "",
            "- **Trigger / Input:** Cold agent or scheduled governance audit on the materialized directory.",
            f"- **Command / Stage Sequence:** Read [../AGENTS.md](../AGENTS.md) and [../CONTEXT.md](../CONTEXT.md), then run `harness dock run {bp.name} validate`, `harness dock run {bp.name} audit-docs`, and `harness spawn check-drift .`.",
            "- **Expected Artifact:** `DOCK_HARNESS_OK`, `DOCS_AUDIT_OK`, and JSON drift report with `drifted: false`.",
            "- **Pass/Fail Check:** Exit code 0 across all validation commands.",
            "",
        ]
    )
    return "\n".join(sections)


def render_provenance(bp: BlueprintLike, *, prime_commit: str, created_utc: str) -> str:
    if bp.seeded_kis:
        ki_rows = "\n".join(
            f"| `{k.ki_id}` | {k.title} | `{k.domain}` | `{k.status}` | `{k.isnad_status}` |" for k in bp.seeded_kis
        )
        seeded_section = "| KI ID | Title | Domain | Status | Isnad |\n|---|---|---|---|---|\n" + ki_rows
    else:
        seeded_section = "None seeded at spawn time."

    if bp.excluded_unverified_kis:
        excluded_section = "\n".join(
            f"- `{kid}` — excluded because `isnad_status` != `VERIFIED`" for kid in bp.excluded_unverified_kis
        )
    else:
        excluded_section = "None — zero unverified KIs returned for this query scope."

    return (
        f"# Graph & Knowledge Provenance: `{bp.name}`\n\n"
        "Links: [README](../README.md) | [Operational Contract](../CONTEXT.md)\n\n"
        "## Graph Lineage\n\n"
        f"- **Graph Source:** `{bp.graph_source}`\n"
        f"- **Cohesion Score:** `{bp.cohesion_score:.4f}`\n"
        f"- **Cross-Cluster Bridges:** `{bp.bridge_count}`\n"
        f"- **Composite Blueprint Score:** `{bp.score:.4f}`\n"
        f"- **Prime Commit:** `{prime_commit}`\n"
        f"- **Generated (UTC):** `{created_utc}`\n\n"
        "## Token Budget Savings\n\n"
        f"- **Prime Workspace Baseline:** `{bp.prime_skill_count}` skills\n"
        f"- **Spawned Domain Harness:** `{len(bp.skills)}` skills\n"
        f"- **Estimated Catalog Skill Reduction:** `{bp.estimated_token_savings_pct:.2f}%`\n\n"
        "## Seeded Knowledge Items\n\n"
        f"{seeded_section}\n\n"
        "## Excluded Unverified Candidates\n\n"
        f"{excluded_section}\n"
    )


def render_runbook(bp: BlueprintLike) -> str:
    return (
        f"# Operations Runbook: `{bp.name}`\n\n"
        "Links: [README](../README.md) | [Operational Contract](../CONTEXT.md) | [Provenance](PROVENANCE.md)\n\n"
        "## Lifecycle & Inspection\n\n"
        "```powershell\n"
        "harness dock inspect .\n"
        "harness dock list\n"
        "```\n\n"
        "## Verification\n\n"
        "All commands below run either from `Brain Harness` or directly inside this harness directory "
        "(invoke Prime `.venv\\Scripts\\harness.exe` if `harness` is not on global `PATH`):\n\n"
        "```powershell\n"
        f"harness dock run {bp.name} validate\n"
        f"harness dock run {bp.name} audit-docs\n"
        f"harness dock run {bp.name} icm-audit\n"
        f"harness dock run {bp.name} icm-links\n"
        "harness icm audit .\n"
        "harness icm links .\n"
        "harness icm quotes .\n"
        "harness spawn check-drift .\n"
        "```\n\n"
        "## Re-Materializing From Prime\n\n"
        "When upstream skills or docs change on `Brain Harness`, run `harness spawn review` first to verify "
        "the canonical SHA-256 digest before running `harness spawn run --materialize ... --approve-dock`.\n\n"
        "## Merge-Back & Adoption\n\n"
        "1. Stage candidate insights only with empirical evidence:\n"
        '   `harness spawn propose <SPAWN_ID> --task-id <TASK> --cue "..." --lesson "..." --evidence "..."`\n'
        "2. Review and explicitly approve or reject from Prime:\n"
        "   `harness spawn adopt <PROPOSAL_ID>` or `harness spawn reject <PROPOSAL_ID>`\n\n"
        "> **Guardrail:** Never silently auto-adopt child learnings and never raw `git merge` a trimmed "
        "domain harness branch into `Brain Harness` `main`.\n"
    )
