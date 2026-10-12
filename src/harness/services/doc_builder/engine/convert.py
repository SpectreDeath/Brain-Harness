"""Format transpiler converting Sphinx directives and Markdown alerts to Svelte components."""

from __future__ import annotations

from pathlib import Path
import re

from harness.services.doc_builder.models import DocFormatConvertResult


def convert_format(
    source_path: str | Path,
    target_format: str = "mdx",
) -> DocFormatConvertResult:
    """Transpile Markdown, RST, or IPYNB into MDX with Svelte tags."""
    p = Path(source_path)
    content = (
        p.read_text(encoding="utf-8", errors="ignore")
        if p.exists()
        else str(source_path)
    )

    injected_components: list[str] = []

    # Convert Sphinx directives to Svelte components
    if ".. note::" in content or ".. warning::" in content or ".. tip::" in content:
        content = re.sub(
            r"\.\. note::\s*(.*?)(?=\n\S|\Z)",
            r"<Tip>\n\1\n</Tip>",
            content,
            flags=re.DOTALL,
        )
        injected_components.append("<Tip>")
        content = re.sub(
            r"\.\. warning::\s*(.*?)(?=\n\S|\Z)",
            r"<Warning>\n\1\n</Warning>",
            content,
            flags=re.DOTALL,
        )
        injected_components.append("<Warning>")
        content = re.sub(
            r"\.\. tip::\s*(.*?)(?=\n\S|\Z)",
            r"<Tip>\n\1\n</Tip>",
            content,
            flags=re.DOTALL,
        )
        injected_components.append("<Tip>")

    # Normalize markdown blockquotes: > [!NOTE] -> <Tip>
    if "> [!NOTE]" in content or "> [!TIP]" in content:
        content = re.sub(
            r"> \[!(?:NOTE|TIP)\]\s*\n?(.*?)(?=\n\s*\n|\Z)",
            r"<Tip>\n\1\n</Tip>",
            content,
            flags=re.DOTALL,
        )
        injected_components.append("<Tip>")
    if "> [!WARNING]" in content or "> [!CAUTION]" in content:
        content = re.sub(
            r"> \[!(?:WARNING|CAUTION)\]\s*\n?(.*?)(?=\n\s*\n|\Z)",
            r"<Warning>\n\1\n</Warning>",
            content,
            flags=re.DOTALL,
        )
        injected_components.append("<Warning>")

    return DocFormatConvertResult(
        source_path=str(p),
        target_format=target_format,
        converted_content=content,
        svelte_components_injected=tuple(sorted(set(injected_components))),
    )
