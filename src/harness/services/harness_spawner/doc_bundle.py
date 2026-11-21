"""7-part documentation bundle builder, canonical digest hasher, and validator (Tracks 2.1-2.3)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from harness.services.icm_architect import IcmAuditor, IcmFormType, IcmVerifier
from harness.services.icm_architect.scaffolder import IcmScaffolder
from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.models import BRAIN_SURFACE, SurfaceSpec

from ._doc_templates import (
    _AUDIT_DOCS_SCRIPT,
    BlueprintLike,
    render_minimal_card,
    render_provenance,
    render_readme,
    render_root_context,
    render_runbook,
    render_use_cases,
)
from .blueprints import PRIME_SKILL_BASELINE_FALLBACK

TRACKED_DOC_PATHS: tuple[str, ...] = (
    "README.md",
    "CONTEXT.md",
    "docs/USE_CASES.md",
    "docs/PROVENANCE.md",
    "docs/RUNBOOK.md",
)


@dataclass(slots=True, frozen=True)
class HarnessDocContext:
    """Fallback documentation metadata when materializing without a graph blueprint."""

    name: str
    domain: str
    title: str
    mission: str
    icm_form: str
    skills: tuple[str, ...]
    graph_source: str
    cohesion_score: float
    bridge_count: int
    score: float
    seeded_kis: tuple[Any, ...]
    excluded_unverified_kis: tuple[str, ...]
    use_cases: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    prime_skill_count: int = PRIME_SKILL_BASELINE_FALLBACK
    estimated_token_savings_pct: float = 0.0


def fallback_doc_context(
    name: str,
    description: str,
    surface: SurfaceSpec,
    tree: Mapping[str, str],
) -> HarnessDocContext:
    """Build valid 7-part documentation metadata from a raw SurfaceSpec tree."""
    skills = tuple(surface_ops.skill_names(surface, dict(tree)))
    mission = description.strip() or f"Isolated domain harness `{name}` generated with minimal AGENTS.md surface."
    savings = round(100.0 * (1.0 - len(skills) / PRIME_SKILL_BASELINE_FALLBACK), 2)
    return HarnessDocContext(
        name=name,
        domain=name,
        title=f"Domain Harness: {name}",
        mission=mission,
        icm_form=IcmFormType.PIPELINE.value,
        skills=skills,
        graph_source="direct-tree-materialization",
        cohesion_score=0.0,
        bridge_count=0,
        score=0.0,
        seeded_kis=(),
        excluded_unverified_kis=(),
        use_cases=(f"Execute `{name}` bounded workflow under `AGENTS.md` and `CONTEXT.md`.",),
        out_of_scope=("Tasks outside the declared `AGENTS.md` domain scope", "Unreviewed auto-adoption into Prime"),
        prime_skill_count=PRIME_SKILL_BASELINE_FALLBACK,
        estimated_token_savings_pct=savings,
    )


def _resolve_prime_commit(skills_root: Path) -> str:
    for cand in (skills_root.parent.parent, Path(__file__).resolve().parents[4]):
        if (cand / ".git").exists():
            try:
                out = subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=str(cand),
                    stderr=subprocess.DEVNULL,
                    text=True,
                ).strip()
                if out:
                    return out
            except Exception:
                break
    return "unknown"


def compute_docs_sha256(repo_dir: Path | str, tracked_docs: Sequence[str] = TRACKED_DOC_PATHS) -> str:
    """Compute canonical SHA-256 digest across tracked documentation artifacts."""
    root = Path(repo_dir).resolve()
    payload: dict[str, str] = {}
    for rel in sorted(tracked_docs):
        norm_rel = rel.replace("\\", "/").lstrip("./")
        target = root / norm_rel
        payload[norm_rel] = target.read_text(encoding="utf-8").replace("\r\n", "\n") if target.is_file() else ""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _copy_skill_companions(repo_root: Path, skills_base: Path, skills: tuple[str, ...]) -> int:
    cards = 0
    for skill in skills:
        dest_dir = repo_root / ".agents" / "skills" / skill
        dest_dir.mkdir(parents=True, exist_ok=True)
        src_dir = skills_base / skill
        src_card = src_dir / "CARD.md"
        if src_card.is_file():
            shutil.copy2(src_card, dest_dir / "CARD.md")
        else:
            (dest_dir / "CARD.md").write_text(render_minimal_card(skill), encoding="utf-8")
        cards += 1
        src_cfg = src_dir / "config.default.yaml"
        if src_cfg.is_file():
            shutil.copy2(src_cfg, dest_dir / "config.default.yaml")
        src_refs = src_dir / "references"
        if src_refs.is_dir():
            shutil.copytree(src_refs, dest_dir / "references", dirs_exist_ok=True)
    return cards


def build_harness_docs(
    blueprint: BlueprintLike,
    *,
    repo_dir: Path | str,
    prime_commit: str = "",
    spawn_id: str = "",
    skills_root: Path | str = ".agents/skills",
) -> dict[str, Any]:
    """Generate the 7-part documentation bundle, ICM skeleton, and companion CARD.md files."""
    repo_root = Path(repo_dir).resolve()
    skills_base = Path(skills_root).resolve()
    resolved_commit = prime_commit.strip() or _resolve_prime_commit(skills_base)
    created_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    scaffold_res = IcmScaffolder().scaffold_form(repo_root, form=blueprint.icm_form, name=blueprint.name)
    if scaffold_res.status != "ok":
        raise RuntimeError(f"Failed to scaffold ICM form {blueprint.icm_form!r}: {scaffold_res.error}")

    (repo_root / "CONTEXT.md").write_text(render_root_context(blueprint), encoding="utf-8")
    (repo_root / "README.md").write_text(
        render_readme(blueprint, prime_commit=resolved_commit, spawn_id=spawn_id, created_utc=created_utc),
        encoding="utf-8",
    )
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "USE_CASES.md").write_text(render_use_cases(blueprint), encoding="utf-8")
    (docs_dir / "PROVENANCE.md").write_text(
        render_provenance(blueprint, prime_commit=resolved_commit, created_utc=created_utc),
        encoding="utf-8",
    )
    (docs_dir / "RUNBOOK.md").write_text(render_runbook(blueprint), encoding="utf-8")

    tools_dir = repo_root / "_tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "audit_docs.py").write_text(_AUDIT_DOCS_SCRIPT, encoding="utf-8")

    cards_written = _copy_skill_companions(repo_root, skills_base, blueprint.skills)
    docs_sha256 = compute_docs_sha256(repo_root, TRACKED_DOC_PATHS)
    return {
        "repo_dir": str(repo_root),
        "icm_form": blueprint.icm_form,
        "tracked_docs": list(TRACKED_DOC_PATHS),
        "docs_sha256": docs_sha256,
        "cards_written": cards_written,
        "prime_commit": resolved_commit,
    }


def validate_harness_docs(repo_dir: Path | str, *, surface: SurfaceSpec = BRAIN_SURFACE) -> dict[str, Any]:
    """Validate all 7 required documentation parts, headings, CARD.md parity, ICM audit, and links."""
    root = Path(repo_dir).resolve()
    errors: list[str] = []
    required_files = (*TRACKED_DOC_PATHS, "AGENTS.md", "CLAUDE.md", "GEMINI.md", "dock.yaml")
    for rel in required_files:
        fp = root / rel
        if not fp.is_file() or not fp.read_text(encoding="utf-8").strip():
            errors.append(f"Missing or empty required artifact: {rel}")

    agents_fp = root / "AGENTS.md"
    if agents_fp.is_file() and len(agents_fp.read_text(encoding="utf-8").splitlines()) >= 60:
        errors.append("AGENTS.md must remain under 60 lines")

    heading_rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("README.md", ("## Mission", "## Use Cases", "## Out of Scope", "## Lineage", "## Skills")),
        ("docs/PROVENANCE.md", ("## Graph Lineage", "## Seeded Knowledge Items")),
        ("docs/RUNBOOK.md", ("## Verification", "## Merge-Back")),
    )
    for rel, headings in heading_rules:
        fp = root / rel
        if fp.is_file():
            text = fp.read_text(encoding="utf-8")
            for h in headings:
                if h not in text:
                    errors.append(f"{rel} missing required heading {h!r}")

    uc_fp = root / "docs/USE_CASES.md"
    if uc_fp.is_file() and uc_fp.read_text(encoding="utf-8").count("## Scenario") < 2:
        errors.append("docs/USE_CASES.md must contain at least 2 worked `## Scenario` sections")

    skills_dir = root / surface.skill_dir
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file() and not (d / "CARD.md").is_file():
                errors.append(f"Missing companion CARD.md for skill {d.name!r}")

    audit = IcmAuditor().audit_workspace(root)
    if not audit.valid:
        errors.extend(
            f"ICM audit error #{v.invariant_number}: {v.description}" for v in audit.violations if v.severity == "error"
        )

    links = IcmVerifier().verify_links(root)
    if not links.valid:
        errors.extend(f"Broken link in {b['file']}: {b['link']}" for b in links.broken_links)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "icm_form": audit.form_detected,
        "invariants_passed": audit.invariants_passed,
        "links_checked": links.total_links,
    }


__all__ = [
    "HarnessDocContext",
    "TRACKED_DOC_PATHS",
    "build_harness_docs",
    "compute_docs_sha256",
    "fallback_doc_context",
    "validate_harness_docs",
]
