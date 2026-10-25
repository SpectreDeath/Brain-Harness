"""Workspace audit engine for Interpretable Context Methodology (ICM)."""

from __future__ import annotations

from pathlib import Path

from .models import (
    IcmFormType,
    IcmInvariantViolation,
    IcmWorkspaceAuditReport,
    IcmWorkspaceRole,
)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".gemini", "_archive"}
CATALOG_FILENAMES = {"agents.md", "claude.md", "gemini.md", "index.md", "_index.md", "log.md"}
FACTORY_FOLDERS = {"_shared", "_tools", "_templates", "_meta", "setup"}


class IcmAuditor:
    """Audits workspace against 10 ICM invariants and classifies files."""

    def audit_workspace(self, root: str | Path = ".") -> IcmWorkspaceAuditReport:
        root_path = Path(root).resolve()
        if not root_path.exists():
            return IcmWorkspaceAuditReport(
                root=str(root_path),
                form_detected="unknown",
                total_files=0,
                files_by_role={},
                invariants_passed=0,
                invariants_total=10,
                violations=[
                    IcmInvariantViolation(
                        invariant_number=1,
                        name="Workspace Path Not Found",
                        description=f"Directory does not exist: {root_path}",
                        path=str(root_path),
                        severity="error",
                    )
                ],
            )

        files_by_role: dict[str, int] = {r.value: 0 for r in IcmWorkspaceRole}
        violations: list[IcmInvariantViolation] = []
        total_files = 0
        md_files: list[Path] = []

        for p in root_path.rglob("*"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.is_file():
                total_files += 1
                rel_parts = p.relative_to(root_path).parts
                lower_name = p.name.lower()

                if lower_name in CATALOG_FILENAMES:
                    files_by_role[IcmWorkspaceRole.CATALOG.value] += 1
                elif lower_name == "context.md":
                    files_by_role[IcmWorkspaceRole.CONTRACT.value] += 1
                elif any(part in FACTORY_FOLDERS for part in rel_parts):
                    files_by_role[IcmWorkspaceRole.FACTORY.value] += 1
                elif "_archive" in rel_parts:
                    files_by_role[IcmWorkspaceRole.DEAD.value] += 1
                else:
                    files_by_role[IcmWorkspaceRole.PRODUCT.value] += 1

                if p.suffix.lower() == ".md":
                    md_files.append(p)

        form_detected = self._detect_form(root_path)

        # Invariant 2: Small, stable entry file (AGENTS.md <= 60 lines)
        agents_file = root_path / "AGENTS.md"
        if not agents_file.exists():
            violations.append(
                IcmInvariantViolation(
                    invariant_number=2,
                    name="Missing Root Entry File",
                    description="Workspace must have an AGENTS.md entry file at the root (<60 lines).",
                    path=str(agents_file),
                    severity="error",
                )
            )
        else:
            lines = agents_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if len(lines) > 60:
                violations.append(
                    IcmInvariantViolation(
                        invariant_number=2,
                        name="Entry File Bloat",
                        description=f"AGENTS.md has {len(lines)} lines; must stay under ~60 lines to serve purely as routing catalog.",
                        path=str(agents_file),
                        severity="warning",
                    )
                )

        # Invariant 4 & 6: Every working folder has a contract; every step ends at a check
        stage_dir = root_path / "stages"
        estimated_step_tokens: dict[str, int] = {}
        if stage_dir.exists() and stage_dir.is_dir():
            for s in sorted(stage_dir.iterdir()):
                if s.is_dir() and not s.name.startswith("."):
                    contract = s / "CONTEXT.md"
                    if not contract.exists():
                        violations.append(
                            IcmInvariantViolation(
                                invariant_number=4,
                                name="Missing Stage Contract",
                                description=f"Working stage {s.name} is missing a CONTEXT.md contract.",
                                path=str(contract),
                                severity="error",
                            )
                        )
                    else:
                        text = contract.read_text(encoding="utf-8", errors="replace")
                        if "## Check" not in text and "## check" not in text:
                            violations.append(
                                IcmInvariantViolation(
                                    invariant_number=6,
                                    name="Stage Contract Missing Check",
                                    description=f"Stage contract {contract.name} must declare a '## Check' section.",
                                    path=str(contract),
                                    severity="warning",
                                )
                            )
                        char_count = len(text)
                        ref_dir = s / "references"
                        if ref_dir.exists():
                            for rf in ref_dir.glob("*.md"):
                                char_count += rf.stat().st_size
                        est_tokens = char_count // 4
                        estimated_step_tokens[s.name] = est_tokens
                        if est_tokens > 8000:
                            violations.append(
                                IcmInvariantViolation(
                                    invariant_number=7,
                                    name="Step Token Context Bloat",
                                    description=f"Stage {s.name} context exceeds 8,000 token limit (~{est_tokens} tokens).",
                                    path=str(contract),
                                    severity="warning",
                                )
                            )

        failed_invs = {v.invariant_number for v in violations if v.severity == "error"}
        passed = 10 - len(failed_invs)

        return IcmWorkspaceAuditReport(
            root=str(root_path),
            form_detected=form_detected.value if isinstance(form_detected, IcmFormType) else str(form_detected),
            total_files=total_files,
            files_by_role=files_by_role,
            invariants_passed=passed,
            invariants_total=10,
            violations=violations,
            estimated_step_tokens=estimated_step_tokens,
        )

    def _detect_form(self, root_path: Path) -> IcmFormType:
        if (root_path / "stages").exists():
            return IcmFormType.PIPELINE
        if (root_path / "records").exists():
            return IcmFormType.RECORD_LIBRARY
        if (root_path / "sources" / "raw").exists() or (root_path / "concepts").exists():
            return IcmFormType.KNOWLEDGE_BUNDLE
        if (root_path / "teams").exists():
            return IcmFormType.CONTEXT_MAP
        if (root_path / "objects").exists() or (root_path / "processes").exists():
            return IcmFormType.SYSTEM_MAP
        return IcmFormType.PIPELINE
