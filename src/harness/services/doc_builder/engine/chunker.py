"""Hierarchical markdown chunker for retrieval and search indexing."""

from __future__ import annotations

import re

from harness.services.doc_builder.models import DocChunk


def chunk_markdown(
    markdown_text: str,
    page_title: str = "Documentation",
    max_chunk_size: int = 1500,
) -> tuple[DocChunk, ...]:
    """Hierarchically partition Markdown text by headings for search indexing."""
    lines = markdown_text.splitlines()
    chunks: list[DocChunk] = []

    current_heading = page_title
    current_level = 1
    current_lines: list[str] = []
    heading_stack: list[str] = [page_title]
    chunk_idx = 0

    def flush_chunk() -> None:
        nonlocal chunk_idx, current_lines
        if not current_lines:
            return
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append(
                DocChunk(
                    chunk_id=f"chunk_{chunk_idx}",
                    title=current_heading,
                    heading_level=current_level,
                    content=body,
                    tokens_estimate=max(1, len(body) // 4),
                    breadcrumb=tuple(heading_stack),
                )
            )
            chunk_idx += 1
        current_lines = []

    for line in lines:
        header_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if header_match:
            flush_chunk()
            level = len(header_match.group(1))
            h_text = header_match.group(2).strip()

            while len(heading_stack) >= level and len(heading_stack) > 1:
                heading_stack.pop()
            heading_stack.append(h_text)

            current_heading = h_text
            current_level = level
        else:
            current_lines.append(line)

    flush_chunk()

    if not chunks:
        chunks.append(
            DocChunk(
                chunk_id="chunk_0",
                title=page_title,
                heading_level=1,
                content=markdown_text[:max_chunk_size],
                tokens_estimate=max(1, len(markdown_text[:max_chunk_size]) // 4),
                breadcrumb=(page_title,),
            )
        )

    return tuple(chunks)
