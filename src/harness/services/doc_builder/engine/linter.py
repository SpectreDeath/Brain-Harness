"""Code example style linter and trailing whitespace sanitizer."""

from __future__ import annotations

from pathlib import Path
import re

from harness.services.doc_builder.models import DocLintResult


def lint_style(
    file_path: str | Path,
    fix: bool = False,
) -> DocLintResult:
    """Lint and format code examples inside docstrings or MDX files."""
    p = Path(file_path)
    content = (
        p.read_text(encoding="utf-8", errors="ignore")
        if p.exists()
        else str(file_path)
    )

    diagnostics: list[str] = []
    code_blocks = re.findall(r"```python(.*?)```", content, flags=re.DOTALL)
    for idx, block in enumerate(code_blocks, start=1):
        lines = block.strip().splitlines()
        if not lines:
            diagnostics.append(f"Block #{idx}: Empty python code block")
        for l_idx, line in enumerate(lines, start=1):
            if line.endswith((" ", "\t")):
                diagnostics.append(
                    f"Block #{idx} Line {l_idx}: Trailing whitespace detected"
                )

    formatted = content
    if fix:
        formatted = re.sub(
            r"```python(.*?)```",
            lambda m: (
                "```python\n"
                + "\n".join(l.rstrip() for l in m.group(1).strip().splitlines())
                + "\n```"
            ),
            content,
            flags=re.DOTALL,
        )

    return DocLintResult(
        file_path=str(p),
        issues_count=len(diagnostics),
        diagnostics=tuple(diagnostics),
        formatted_content=formatted if fix else None,
    )
