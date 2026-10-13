"""Context file synchronizer generating vendor context files from canonical SSOT."""

from __future__ import annotations

from pathlib import Path
from .models import SyncResult

BANNER_TEMPLATE = "<!-- Generated from {source} by `python scripts/sync_context.py`. Edit {source} instead. -->"

DEFAULT_CLAUDE_EXTRAS = """## Claude Code specific

- Use plan mode for architectural modifications or changes touching more than three files.
- Execute atomic fixes directly without ceremony.
- Delegate codebase exploration to subagents so findings return summarized rather than consuming context.
"""


class ContextSynchronizer:
    """Synchronizes downstream context files against canonical source (AGENTS.md)."""

    @classmethod
    def render_claude_md(cls, source_name: str = "AGENTS.md") -> str:
        """Render CLAUDE.md using pointer syntax to minimize token overhead."""
        banner = BANNER_TEMPLATE.format(source=source_name)
        return f"{banner}\n\n@{source_name}\n\n{DEFAULT_CLAUDE_EXTRAS.strip()}\n"

    @classmethod
    def render_copilot_md(cls, source_name: str, source_content: str) -> str:
        """Render .github/copilot-instructions.md inlining the canonical source."""
        banner = BANNER_TEMPLATE.format(source=source_name)
        return f"{banner}\n\n{source_content.strip()}\n"

    @classmethod
    def run_sync(cls, root: Path, source_rel: str = "AGENTS.md", dry_run: bool = False) -> SyncResult:
        """Synchronize downstream context files against canonical source."""
        target_root = root.resolve()
        source_file = target_root / source_rel
        if not source_file.exists():
            return SyncResult(root_path=str(target_root), in_sync=False, actions=(f"Canonical source missing: {source_file}",))

        source_content = source_file.read_text(encoding="utf-8", errors="ignore")
        actions: list[str] = []
        has_drift = False

        targets = [
            ("CLAUDE.md", cls.render_claude_md(source_rel)),
            (".github/copilot-instructions.md", cls.render_copilot_md(source_rel, source_content)),
        ]

        for rel_path, expected_content in targets:
            target_file = target_root / rel_path
            exists = target_file.exists()
            current_content = target_file.read_text(encoding="utf-8", errors="ignore") if exists else ""

            if current_content != expected_content:
                has_drift = True
                if dry_run:
                    actions.append(f"[DRIFT] {rel_path} differs from generated canonical source.")
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(expected_content, encoding="utf-8")
                    actions.append(f"[UPDATED] Synchronized {rel_path} from {source_rel}")
            else:
                if not dry_run:
                    actions.append(f"[OK] {rel_path} already in sync.")

        return SyncResult(
            root_path=str(target_root),
            in_sync=not has_drift,
            actions=tuple(actions),
        )
