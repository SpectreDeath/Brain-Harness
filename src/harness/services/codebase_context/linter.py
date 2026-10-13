"""Context verification engine checking token budgets, path links, scripts, and drift."""

from __future__ import annotations

import math
from pathlib import Path
import re
from typing import Any

from .classifier import SemanticPathClassifier
from .config import ConfigResolver
from .manifest import ManifestScriptInspector
from .models import (
    CheckResult,
    ContextLintReport,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SyncDriftCheck,
    TokenBudgetCheck,
)


class ContextLinter:
    """Verifies repository context files across token, path, script, and drift dimensions."""

    PATH_LIKE_RE = re.compile(
        r"^(?:[\w.-]+/)+[\w.-]+(?:\.\w+)?$|"
        r"^\.?\.?/[\w.-]+|"
        r"^[\w.-]+\.(?:md|js|mjs|ts|py|json|ya?ml|sh|rs|go|txt|toml)$"
    )

    @classmethod
    def estimate_tokens(cls, text: str, cpt: int = 4) -> int:
        """Estimate token volume from raw text using chars_per_token heuristic."""
        return math.ceil(len(text) / cpt) if text else 0

    @classmethod
    def strip_fenced_blocks(cls, text: str) -> str:
        """Strip markdown code fences so illustrative snippet examples are not evaluated as real paths (Rule 47)."""
        return re.sub(r"```[\s\S]*?```", "", text)

    @classmethod
    def extract_inline_spans(cls, text: str) -> list[str]:
        """Extract backtick code spans from prose text, evaluating link targets for formatted labels."""
        prose = cls.strip_fenced_blocks(text)
        prose = re.sub(r"\[`[^`\n]+`\]\(([^)\s]+)\)", r"`\1`", prose)
        return [m.group(1).strip() for m in re.finditer(r"`([^`\n]+)`", prose)]

    @classmethod
    def looks_like_path(cls, span: str) -> bool:
        """Determine whether an inline backtick span resembles a repository filesystem path."""
        if span.startswith(("-", "npm ", "node ", "python ", "pytest ", "git ", "ruff ", "cargo ", "make ")):
            return False
        if " " in span or span in {"const", "var", "let", "return", "true", "false", "null", "undefined"}:
            return False
        if SemanticPathClassifier.is_mime_type(span):
            return False
        if SemanticPathClassifier.is_api_route(span):
            return False
        if SemanticPathClassifier.is_archetype_template(span):
            return False
        return bool(cls.PATH_LIKE_RE.match(span))

    @classmethod
    def run_lint(cls, root: Path, config: dict[str, Any]) -> ContextLintReport:
        """Execute complete 4-check context verification suite."""
        target_root = root.resolve()
        checks: list[CheckResult] = []
        budgets: dict[str, int] = config.get("budgets") or ConfigResolver.DEFAULT_BUDGETS
        cpt = config.get("chars_per_token", 4)

        # 1. Token budget checks
        for rel_path, ceiling in budgets.items():
            target = target_root / rel_path
            if not target.exists():
                continue
            text = target.read_text(encoding="utf-8", errors="ignore")
            tok_count = cls.estimate_tokens(text, cpt=cpt)
            passed = tok_count <= ceiling
            msg = f"{rel_path}: {tok_count}/{ceiling} tokens" + (" (EXCEEDED)" if not passed else " (OK)")
            checks.append(
                TokenBudgetCheck(
                    file_path=rel_path,
                    token_count=tok_count,
                    token_ceiling=ceiling,
                    passed=passed,
                    message=msg,
                )
            )

        # 2. Path & Script checks across markdown context files
        available_scripts = ManifestScriptInspector.extract_available_scripts(target_root)
        md_files = [target_root / "AGENTS.md", target_root / "CLAUDE.md"]
        if (target_root / ".github").exists():
            md_files.extend((target_root / ".github").glob("*.md"))
        if (target_root / "src").exists():
            md_files.extend((target_root / "src").glob("**/*.md"))
        if (target_root / "docs").exists():
            md_files.extend((target_root / "docs").glob("**/*.md"))

        for mf in md_files:
            if not mf.exists():
                continue
            rel_file = str(mf.relative_to(target_root)).replace("\\", "/")
            text = mf.read_text(encoding="utf-8", errors="ignore")
            spans = cls.extract_inline_spans(text)

            for span in spans:
                # Path check
                if cls.looks_like_path(span):
                    path_target = target_root / span
                    path_rel = mf.parent / span
                    if not path_target.exists() and not path_rel.exists():
                        checks.append(
                            PathIntegrityCheck(
                                file_path=rel_file,
                                target_path=span,
                                resolved_path=str(path_target),
                                passed=False,
                                message=f"{rel_file} points at non-existent path: `{span}`",
                            )
                        )

                # Script check
                npm_m = re.match(r"^npm run ([\w:-]+)$", span) or re.match(r"^npm (test|start|build)$", span)
                if npm_m:
                    s_name = npm_m.group(1)
                    if available_scripts and s_name not in available_scripts:
                        checks.append(
                            ScriptIntegrityCheck(
                                file_path=rel_file,
                                raw_command=span,
                                runner="npm",
                                script_name=s_name,
                                passed=False,
                                message=f"{rel_file} mentions script not in package.json: `{span}`",
                            )
                        )

        # 3. Sync drift checks
        canonical = target_root / "AGENTS.md"
        if canonical.exists():
            claude_file = target_root / "CLAUDE.md"
            if claude_file.exists():
                content = claude_file.read_text(encoding="utf-8", errors="ignore")
                if (
                    "Generated from AGENTS.md" in content
                    and "@AGENTS.md" not in content
                    and "@./AGENTS.md" not in content
                ):
                    checks.append(
                        SyncDriftCheck(
                            target_file="CLAUDE.md",
                            canonical_source="AGENTS.md",
                            passed=False,
                            message="CLAUDE.md missing @AGENTS.md pointer import reference",
                        )
                    )

            copilot_file = target_root / ".github" / "copilot-instructions.md"
            if copilot_file.exists():
                content = copilot_file.read_text(encoding="utf-8", errors="ignore")
                if "Generated from AGENTS.md" in content:
                    source_content = canonical.read_text(encoding="utf-8", errors="ignore")
                    sample = source_content.strip()[:80]
                    if sample and sample not in content:
                        checks.append(
                            SyncDriftCheck(
                                target_file=".github/copilot-instructions.md",
                                canonical_source="AGENTS.md",
                                passed=False,
                                message=".github/copilot-instructions.md is out of sync with AGENTS.md",
                            )
                        )

        problems = [c for c in checks if not c.passed]
        return ContextLintReport(
            root_path=str(target_root),
            passed=len(problems) == 0,
            checks=tuple(checks),
            problems_count=len(problems),
            checks_count=len(checks),
        )
