"""Runnable 8-Point ICM Cold Walk verifier for materialized domain harnesses (Track 3.1)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from harness.services.icm_architect import IcmAuditor, IcmVerifier
from harness.services.recursive_harnessing.models import BRAIN_SURFACE

from .blueprints import PRIME_SKILL_BASELINE_FALLBACK
from .doc_bundle import validate_harness_docs
from .materialize import check_materialized_drift

_FRONTMATTER_RX = re.compile(r"---\r?\n(.*?)\r?\n---", re.DOTALL)
_BACKTICK_PATH_RX = re.compile(r"`([^`\r\n]+)`")

_CANONICAL_POINTS: tuple[tuple[int, str, str], ...] = (
    (1, "Where am I", "human_judgment"),
    (2, "Exact Inputs", "automated"),
    (3, "Pure Disk Status", "automated"),
    (4, "No Content in Catalog", "automated"),
    (5, "Single Source of Truth", "human_judgment"),
    (6, "Resolving Links", "automated"),
    (7, "Token Budget Under 8k", "automated"),
    (8, "Broken Invariants Explained", "human_judgment"),
)


@dataclass(slots=True, frozen=True)
class ColdWalkPoint:
    """Single point outcome within ICM's canonical 8-Point Cold Walk Test."""

    point_number: int
    name: str
    evaluation_mode: str
    status: str
    precheck_passed: bool
    detail: str
    reader: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.point_number <= 8:
            raise ValueError(f"ColdWalkPoint point_number must be in 1..8, got {self.point_number}")
        if self.evaluation_mode not in {"automated", "human_judgment"}:
            raise ValueError(f"Invalid evaluation_mode: {self.evaluation_mode!r}")
        if self.status not in {"passed", "failed", "pending_human_judgment"}:
            raise ValueError(f"Invalid ColdWalkPoint status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "point_number": self.point_number,
            "name": self.name,
            "evaluation_mode": self.evaluation_mode,
            "status": self.status,
            "precheck_passed": self.precheck_passed,
            "detail": self.detail,
            "reader": self.reader,
        }


@dataclass(slots=True, frozen=True)
class ColdWalkReport:
    """Structured cold-walk evaluation distinguishing 8 walk points from 10/10 ICM auditor gates."""

    repo_dir: str
    harness_name: str
    icm_form: str
    evaluated_at_utc: str
    points: tuple[ColdWalkPoint, ...]
    automated_passed: bool
    human_points_verified: bool
    overall_passed: bool
    metrics: dict[str, Any]
    underlying_gates: dict[str, Any]

    def __post_init__(self) -> None:
        if len(self.points) != 8:
            raise ValueError(f"ColdWalkReport must contain all 8 canonical points, got {len(self.points)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_dir": self.repo_dir,
            "harness_name": self.harness_name,
            "icm_form": self.icm_form,
            "evaluated_at_utc": self.evaluated_at_utc,
            "points": [p.to_dict() for p in self.points],
            "automated_passed": self.automated_passed,
            "human_points_verified": self.human_points_verified,
            "overall_passed": self.overall_passed,
            "metrics": dict(self.metrics),
            "underlying_gates": dict(self.underlying_gates),
        }


def _skill_catalog_stats(skills_dir: Path) -> tuple[int, int]:
    if not skills_dir.is_dir():
        return 0, 0
    total_chars = 0
    count = 0
    for d in sorted(skills_dir.iterdir()):
        sk = d / "SKILL.md"
        if d.is_dir() and sk.is_file():
            count += 1
            text = sk.read_text(encoding="utf-8", errors="replace")
            m = _FRONTMATTER_RX.match(text)
            total_chars += len(m.group(1)) if m else min(len(text), 400)
    return count, max(1, total_chars // 4) if count else 0


def _extract_section(md_text: str, heading_prefix: str) -> str:
    lines = md_text.splitlines()
    captured: list[str] = []
    in_sec = False
    target_low = heading_prefix.lower()
    for line in lines:
        low = line.strip().lower()
        if low.startswith("## "):
            if in_sec:
                break
            if low.startswith(target_low):
                in_sec = True
            continue
        if in_sec:
            captured.append(line)
    return "\n".join(captured)


def _check_inputs_section(root: Path, context_text: str) -> tuple[bool, str]:
    sec = _extract_section(context_text, "## inputs")
    if not sec.strip():
        return False, "CONTEXT.md missing non-empty ## Inputs section"
    tokens = [m.group(1).strip() for m in _BACKTICK_PATH_RX.finditer(sec)]
    if not tokens:
        return False, "CONTEXT.md ## Inputs lists no backticked exact paths"
    missing: list[str] = []
    for tok in tokens:
        clean = tok.replace("\\", "/").lstrip("./")
        if "/" in clean or clean.endswith((".md", ".txt", ".json", ".yaml", ".yml")):
            if not (root / clean).exists():
                missing.append(tok)
    if missing:
        return False, f"Unresolved input paths in CONTEXT.md: {missing}"
    return True, f"Verified {len(tokens)} backticked input path(s) in CONTEXT.md"


def _check_pure_disk_status(
    root: Path,
    icm_form: str,
    context_text: str,
    drift_report: Mapping[str, Any],
) -> tuple[bool, str]:
    check_sec = _extract_section(context_text, "## check")
    if not check_sec.strip():
        return False, "CONTEXT.md missing ## Check section"
    expected_paths: dict[str, tuple[str, ...]] = {
        "pipeline": ("stages",),
        "record_library": ("records/_index.md",),
        "knowledge_bundle": ("concepts/_index.md",),
        "context_map": ("teams/_index.md",),
        "system_map": ("objects/_index.md", "processes/_index.md"),
    }
    needed = expected_paths.get(icm_form, ())
    missing = [rel for rel in needed if not (root / rel).exists()]
    if missing:
        return False, f"Missing disk status artifacts for form {icm_form!r}: {missing}"
    if bool(drift_report.get("drifted")):
        return False, "Spawn drift detected (check_materialized_drift drifted=True)"
    return True, f"Disk status indexes present ({', '.join(needed) or icm_form}) and drift clean"


def _estimate_step_tokens(root: Path, context_text: str) -> int:
    total_chars = len(context_text)
    shared = root / "_shared"
    if shared.is_dir():
        for p in sorted(shared.glob("*.md")):
            total_chars += len(p.read_text(encoding="utf-8", errors="replace"))
    stages_dir = root / "stages"
    if stages_dir.is_dir():
        for st in sorted(stages_dir.iterdir()):
            if st.is_dir() and not st.name.startswith("."):
                st_ctx = st / "CONTEXT.md"
                if st_ctx.is_file():
                    total_chars += len(st_ctx.read_text(encoding="utf-8", errors="replace"))
                ref_dir = st / "references"
                if ref_dir.is_dir():
                    for rf in sorted(ref_dir.glob("*.md")):
                        total_chars += len(rf.read_text(encoding="utf-8", errors="replace"))
    return total_chars // 4


def _resolve_human_point(
    point_num: int,
    name: str,
    precheck_ok: bool,
    precheck_detail: str,
    human_judgments: Mapping[int | str, bool | Mapping[str, Any]] | None,
    default_reader: str,
) -> ColdWalkPoint:
    raw: bool | Mapping[str, Any] | None = None
    if human_judgments is not None:
        if point_num in human_judgments:
            raw = human_judgments[point_num]
        elif str(point_num) in human_judgments:
            raw = human_judgments[str(point_num)]

    if raw is None:
        status = "pending_human_judgment" if precheck_ok else "failed"
        return ColdWalkPoint(
            point_number=point_num,
            name=name,
            evaluation_mode="human_judgment",
            status=status,
            precheck_passed=precheck_ok,
            detail=f"{precheck_detail}; human judgment not yet supplied",
            reader="",
        )

    if isinstance(raw, bool):
        verdict = raw
        note = ""
        reader = default_reader
    else:
        verdict = bool(raw.get("passed", False))
        note = str(raw.get("note") or raw.get("detail") or "").strip()
        reader = str(raw.get("reader") or default_reader).strip()

    status = "passed" if (precheck_ok and verdict) else "failed"
    detail = f"{precheck_detail}; {note}" if note else precheck_detail
    return ColdWalkPoint(
        point_number=point_num,
        name=name,
        evaluation_mode="human_judgment",
        status=status,
        precheck_passed=precheck_ok,
        detail=detail,
        reader=reader,
    )


def run_cold_walk(
    repo_dir: Path | str,
    *,
    dock_name: str | None = None,
    prime_skills_root: Path | str = ".agents/skills",
    human_judgments: Mapping[int | str, bool | Mapping[str, Any]] | None = None,
    reader: str = "",
) -> ColdWalkReport:
    """Execute ICM's 8-Point Cold Walk Check, keeping automated checks distinct from human judgments."""
    root = Path(repo_dir).resolve()
    harness_name = dock_name or root.name
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    agents_fp = root / "AGENTS.md"
    context_fp = root / "CONTEXT.md"
    readme_fp = root / "README.md"
    agents_text = agents_fp.read_text(encoding="utf-8", errors="replace") if agents_fp.is_file() else ""
    context_text = context_fp.read_text(encoding="utf-8", errors="replace") if context_fp.is_file() else ""
    readme_text = readme_fp.read_text(encoding="utf-8", errors="replace") if readme_fp.is_file() else ""

    audit = IcmAuditor().audit_workspace(root)
    links = IcmVerifier().verify_links(root)
    doc_val = validate_harness_docs(root)
    drift = check_materialized_drift(root, BRAIN_SURFACE, dock_name=harness_name)

    agents_lines = len(agents_text.splitlines())
    agents_est_tokens = len(agents_text) // 4
    context_lines = len(context_text.splitlines())
    step_est_tokens = _estimate_step_tokens(root, context_text)

    h_skills, h_tokens = _skill_catalog_stats(root / ".agents" / "skills")
    p_skills, p_tokens = _skill_catalog_stats(Path(prime_skills_root).resolve())
    if p_skills == 0:
        p_skills = PRIME_SKILL_BASELINE_FALLBACK
        p_tokens = 8392
    savings_pct = round(100.0 * (1.0 - h_tokens / max(p_tokens, 1)), 2) if h_skills else 0.0

    # #1 Where am I (human judgment + structural precheck)
    p1_ok = (
        agents_fp.is_file()
        and 0 < agents_lines < 60
        and agents_est_tokens <= 500
        and "README.md" in agents_text
        and "CONTEXT.md" in agents_text
        and bool(readme_text.strip())
    )
    p1_detail = f"Precheck: AGENTS.md={agents_lines}L (~{agents_est_tokens} est. tok), links README.md + CONTEXT.md"
    pt1 = _resolve_human_point(1, "Where am I", p1_ok, p1_detail, human_judgments, reader)

    # #2 Exact Inputs (automated)
    p2_ok, p2_detail = _check_inputs_section(root, context_text)
    pt2 = ColdWalkPoint(2, "Exact Inputs", "automated", "passed" if p2_ok else "failed", p2_ok, p2_detail)

    # #3 Pure Disk Status (automated)
    p3_ok, p3_detail = _check_pure_disk_status(root, audit.form_detected, context_text, drift)
    pt3 = ColdWalkPoint(3, "Pure Disk Status", "automated", "passed" if p3_ok else "failed", p3_ok, p3_detail)

    # #4 No Content in Catalog (automated)
    has_payload_leak = agents_text.lstrip().startswith("---") or "```" in agents_text
    p4_ok = 0 < agents_lines < 60 and agents_est_tokens <= 500 and 0 < context_lines <= 80 and not has_payload_leak
    p4_detail = (
        f"AGENTS.md={agents_lines}L (~{agents_est_tokens} tok), "
        f"CONTEXT.md={context_lines}L, payload_leak={has_payload_leak}"
    )
    pt4 = ColdWalkPoint(4, "No Content in Catalog", "automated", "passed" if p4_ok else "failed", p4_ok, p4_detail)

    # #5 Single Source of Truth (human judgment + structural precheck)
    p5_ok = (
        "README.md" in agents_text
        and "CONTEXT.md" in agents_text
        and "docs/PROVENANCE.md" in agents_text
        and links.valid
        and bool(doc_val["valid"])
    )
    p5_detail = "Precheck: canonical files linked from AGENTS.md without broken cross-references"
    pt5 = _resolve_human_point(5, "Single Source of Truth", p5_ok, p5_detail, human_judgments, reader)

    # #6 Resolving Links (automated)
    p6_ok = bool(links.valid) and len(links.broken_links) == 0 and bool(doc_val["valid"])
    p6_detail = (
        f"IcmVerifier links={links.total_links} broken={len(links.broken_links)}; "
        f"doc_bundle_valid={bool(doc_val['valid'])}"
    )
    pt6 = ColdWalkPoint(6, "Resolving Links", "automated", "passed" if p6_ok else "failed", p6_ok, p6_detail)

    # #7 Token Budget Under 8k (automated)
    p7_ok = step_est_tokens < 8000
    p7_detail = (
        f"Step contract est_tokens={step_est_tokens} (<8000); "
        f"skills={h_skills}/{p_skills} (~{h_tokens} vs ~{p_tokens} tok, {savings_pct}% saved)"
    )
    pt7 = ColdWalkPoint(7, "Token Budget Under 8k", "automated", "passed" if p7_ok else "failed", p7_ok, p7_detail)

    # #8 Broken Invariants Explained (human judgment + IcmAuditor 10/10 precheck)
    warn_count = sum(1 for v in audit.violations if v.severity != "error")
    p8_ok = bool(audit.valid) and audit.invariants_passed == audit.invariants_total and warn_count == 0
    p8_detail = (
        f"Precheck: IcmAuditor={audit.invariants_passed}/{audit.invariants_total} invariants, warnings={warn_count}"
    )
    pt8 = _resolve_human_point(8, "Broken Invariants Explained", p8_ok, p8_detail, human_judgments, reader)

    points = (pt1, pt2, pt3, pt4, pt5, pt6, pt7, pt8)
    automated_passed = all(p.status == "passed" for p in points if p.evaluation_mode == "automated")
    human_points_verified = all(p.status == "passed" for p in points if p.evaluation_mode == "human_judgment")
    overall_passed = automated_passed and human_points_verified

    return ColdWalkReport(
        repo_dir=str(root),
        harness_name=harness_name,
        icm_form=audit.form_detected,
        evaluated_at_utc=now_utc,
        points=points,
        automated_passed=automated_passed,
        human_points_verified=human_points_verified,
        overall_passed=overall_passed,
        metrics={
            "agents_lines": agents_lines,
            "agents_est_tokens": agents_est_tokens,
            "context_lines": context_lines,
            "step_est_tokens": step_est_tokens,
            "prime_skills": p_skills,
            "prime_catalog_est_tokens": p_tokens,
            "harness_skills": h_skills,
            "harness_catalog_est_tokens": h_tokens,
            "catalog_token_reduction_pct": savings_pct,
        },
        underlying_gates={
            "icm_auditor_invariants": f"{audit.invariants_passed}/{audit.invariants_total}",
            "icm_auditor_valid": bool(audit.valid),
            "icm_verifier_links_checked": links.total_links,
            "icm_verifier_broken_links": len(links.broken_links),
            "doc_bundle_valid": bool(doc_val["valid"]),
            "doc_bundle_errors": list(doc_val["errors"]),
            "check_drift_dock_status": drift["dock_status"],
            "check_drift_drifted": bool(drift["drifted"]),
        },
    )


def format_cold_walk_markdown(report: ColdWalkReport) -> str:
    """Format a ColdWalkReport as deterministic Markdown showing automated vs human points."""
    lines = [
        f"### 8-Point Cold Walk: `{report.harness_name}` (`{report.icm_form}`)",
        "",
        f"- **Evaluated (UTC):** `{report.evaluated_at_utc}`",
        f"- **Automated Points (`#2,#3,#4,#6,#7`):** `{'PASS' if report.automated_passed else 'FAIL'}`",
        f"- **Human-Judged Points (`#1,#5,#8`):** `{'VERIFIED' if report.human_points_verified else 'PENDING_OR_FAILED'}`",
        f"- **Underlying Gates:** ICM Auditor `{report.underlying_gates['icm_auditor_invariants']}`, "
        f"Links `{report.underlying_gates['icm_verifier_links_checked']}` (`broken={report.underlying_gates['icm_verifier_broken_links']}`), "
        f"Docs Valid `{report.underlying_gates['doc_bundle_valid']}`, Drifted `{report.underlying_gates['check_drift_drifted']}`",
        "",
        "| # | Point | Mode | Status | Precheck | Detail | Reader |",
        "|---:|---|---|---|---|---|---|",
    ]
    for p in report.points:
        lines.append(
            f"| {p.point_number} | {p.name} | `{p.evaluation_mode}` | `{p.status}` | "
            f"`{p.precheck_passed}` | {p.detail} | {p.reader or '-'} |"
        )
    return "\n".join(lines) + "\n"


__all__ = [
    "ColdWalkPoint",
    "ColdWalkReport",
    "format_cold_walk_markdown",
    "run_cold_walk",
]
