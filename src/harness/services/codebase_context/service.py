"""Authoritative DefaultCodebaseContextService implementing CodebaseContextService protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ConfigResolver
from .governor import ContextGovernor
from .linter import ContextLinter
from .models import (
    ContextGovernanceReport,
    ContextLintReport,
    ContextSmellViolation,
    GovernanceStageResult,
    SyncResult,
)
from .protocol import CodebaseContextService
from .synchronizer import BANNER_TEMPLATE, DEFAULT_CLAUDE_EXTRAS, ContextSynchronizer


class DefaultCodebaseContextService(CodebaseContextService):
    """Default slotted implementation of CodebaseContextService."""

    PATH_LIKE_RE = ContextLinter.PATH_LIKE_RE
    BANNER_TEMPLATE = BANNER_TEMPLATE
    DEFAULT_CLAUDE_EXTRAS = DEFAULT_CLAUDE_EXTRAS

    def __init__(self, root: Path | str = ".", config: dict[str, Any] | None = None) -> None:
        self.root = Path(root).resolve()
        self.config = config or ConfigResolver.resolve_config(self.root)

    def estimate_tokens(self, text: str) -> int:
        cpt = self.config.get("chars_per_token", 4)
        return ContextLinter.estimate_tokens(text, cpt=cpt)

    def strip_fenced_blocks(self, text: str) -> str:
        return ContextLinter.strip_fenced_blocks(text)

    def extract_inline_spans(self, text: str) -> list[str]:
        return ContextLinter.extract_inline_spans(text)

    def looks_like_path(self, span: str) -> bool:
        return ContextLinter.looks_like_path(span)

    def lint(self, root: str | Path | None = None) -> ContextLintReport:
        target_root = Path(root).resolve() if root else self.root
        return ContextLinter.run_lint(target_root, self.config)

    def render_claude_md(self, source_name: str = "AGENTS.md") -> str:
        return ContextSynchronizer.render_claude_md(source_name)

    def render_copilot_md(self, source_name: str, source_content: str) -> str:
        return ContextSynchronizer.render_copilot_md(source_name, source_content)

    def sync(self, root: str | Path | None = None, source_rel: str = "AGENTS.md", dry_run: bool = False) -> SyncResult:
        target_root = Path(root).resolve() if root else self.root
        return ContextSynchronizer.run_sync(target_root, source_rel=source_rel, dry_run=dry_run)

    def audit_smells(self, target_file: Path | str | None = None) -> tuple[GovernanceStageResult, list[ContextSmellViolation]]:
        return ContextGovernor.audit_smells(self.root, target_file=target_file)

    def verify_partitioning(self) -> GovernanceStageResult:
        return ContextGovernor.verify_partitioning(self.root)

    def verify_synchronization(self) -> GovernanceStageResult:
        return ContextGovernor.verify_synchronization(self.root)

    def run_ci_lint(self) -> GovernanceStageResult:
        return ContextGovernor.run_ci_lint(self.root, self.config)

    def assess_compute_tier(self, complexity_score: float = 0.5) -> tuple[GovernanceStageResult, str]:
        return ContextGovernor.assess_compute_tier(complexity_score)

    def govern(
        self,
        root: str | Path | None = None,
        target_file: str | Path | None = None,
        complexity_score: float = 0.5,
    ) -> ContextGovernanceReport:
        target_root = Path(root).resolve() if root else self.root
        return ContextGovernor.run_govern(
            root=target_root,
            target_file=target_file,
            complexity_score=complexity_score,
            config=self.config,
        )
