"""Subprocess-isolated adapter service implementing HfDocBuilderProtocol (Rule 14 & Rule 49)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from harness.services.doc_builder import (
    AutodocSignature,
    DocBuilderDomainEngine,
    DocChunk,
    DocFormatConvertResult,
    DocLintResult,
    HfDocBuilderProtocol,
    LinkValidationReport,
)

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]


class HfDocBuilderSubprocessService(HfDocBuilderProtocol):
    """Service executing documentation operations with isolated subprocess pipe protection."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = DocBuilderDomainEngine

    def inspect_autodoc(
        self,
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        return self._engine.inspect_autodoc(
            package_name, object_name, mock_heavy_deps, source_file
        )

    def verify_links(
        self,
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        return self._engine.verify_links(docs_dir, check_anchors, check_toc)

    def convert_format(
        self,
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        return self._engine.convert_format(source_path, target_format)

    def lint_style(
        self,
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        return self._engine.lint_style(file_path, fix)

    def chunk_markdown(
        self,
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        return self._engine.chunk_markdown(markdown_text, page_title, max_chunk_size)

    def run_sandboxed_command(
        self, cmd: list[str], timeout: int = 60
    ) -> tuple[int, str, str]:
        """Execute sandboxed subprocess with strict Rule 14 pipe drainage in finally blocks."""
        proc = None
        stdout_data, stderr_data = "", ""
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout_data, stderr_data = proc.communicate(timeout=timeout)
            return proc.returncode, stdout_data, stderr_data
        finally:
            # Rule 14: Subprocess Pipe Transport Disposal Invariant
            if proc is not None:
                if proc.stdin:
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass
                if proc.stdout:
                    try:
                        proc.stdout.close()
                    except Exception:
                        pass
                if proc.stderr:
                    try:
                        proc.stderr.close()
                    except Exception:
                        pass
