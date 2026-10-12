"""Documentation internal link, anchor, and TOC integrity validator."""

from __future__ import annotations

import os
from pathlib import Path
import re

from harness.services.doc_builder.ast_analyzer import TocIntegrityAuditor
from harness.services.doc_builder.models import (
    LinkDiagnostic,
    LinkValidationReport,
    TocDiagnostic,
)


def verify_links(
    docs_dir: str | Path,
    check_anchors: bool = True,
    check_toc: bool = True,
) -> LinkValidationReport:
    """Verify internal Markdown links, anchors, and TOC integrity across documentation."""
    target_path = Path(docs_dir)
    if not target_path.exists():
        return LinkValidationReport(
            scanned_files_count=0,
            total_links_checked=0,
            broken_links=(
                LinkDiagnostic(
                    source_file=str(target_path),
                    target_link="",
                    is_valid=False,
                    error_reason=f"Docs directory does not exist: {target_path}",
                ),
            ),
            valid=False,
        )

    md_files = list(target_path.rglob("*.md")) + list(target_path.rglob("*.mdx"))
    if not md_files and target_path.is_file():
        md_files = [target_path]

    # 1. Build anchor index across all files
    anchor_index: dict[str, set[str]] = {}
    file_rel_paths: set[str] = set()

    for mf in md_files:
        rel = str(
            mf.relative_to(
                target_path if target_path.is_dir() else target_path.parent
            )
        ).replace("\\", "/")
        file_rel_paths.add(rel)
        base_rel = rel.rsplit(".", 1)[0]
        file_rel_paths.add(base_rel)

        text = mf.read_text(encoding="utf-8", errors="ignore")
        anchors: set[str] = set()
        for line in text.splitlines():
            if line.startswith("#"):
                title = re.sub(r"^#+\s*", "", line).strip()
                slug = (
                    re.sub(r"[^a-zA-Z0-9\-_ ]", "", title).lower().replace(" ", "-")
                )
                anchors.add(slug)
            for m in re.finditer(r'id=["\']([^"\']+)["\']', line):
                anchors.add(m.group(1))
        anchor_index[rel] = anchors
        anchor_index[base_rel] = anchors

    # 2. Check links
    diagnostics: list[LinkDiagnostic] = []
    total_links = 0

    for mf in md_files:
        rel_src = str(
            mf.relative_to(
                target_path if target_path.is_dir() else target_path.parent
            )
        ).replace("\\", "/")
        src_dir = str(Path(rel_src).parent).replace("\\", "/")
        text = mf.read_text(encoding="utf-8", errors="ignore")

        # Strip code fences before searching links per Rule 47
        clean_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        for line_idx, line in enumerate(clean_text.splitlines(), start=1):
            for match in re.finditer(r"\[([^\]]*)\]\(([^\)]+)\)", line):
                total_links += 1
                target_link = match.group(2).strip()

                # Skip external URLs
                if target_link.startswith(
                    ("http://", "https://", "mailto:", "ftp:")
                ):
                    continue

                target_url, _, anchor = target_link.partition("#")
                anchor = anchor.strip() if anchor else None

                # Anchor-only link (#heading)
                if not target_url:
                    if check_anchors and anchor:
                        current_anchors = anchor_index.get(rel_src, set())
                        if anchor not in current_anchors:
                            diagnostics.append(
                                LinkDiagnostic(
                                    source_file=rel_src,
                                    target_link=target_link,
                                    anchor=anchor,
                                    is_valid=False,
                                    line_number=line_idx,
                                    error_reason=f"Anchor #{anchor} not found in {rel_src}",
                                )
                            )
                    continue

                # Resolve target path relative to source file
                if target_url.startswith("/"):
                    resolved = target_url.lstrip("/")
                else:
                    norm = os.path.normpath(
                        f"{src_dir}/{target_url}" if src_dir != "." else target_url
                    ).replace("\\", "/")
                    resolved = norm

                resolved_clean = resolved.rstrip("/")
                valid_file = (
                    resolved_clean in file_rel_paths
                    or f"{resolved_clean}.md" in file_rel_paths
                    or f"{resolved_clean}.mdx" in file_rel_paths
                    or f"{resolved_clean}/index.md" in file_rel_paths
                )

                if not valid_file:
                    diagnostics.append(
                        LinkDiagnostic(
                            source_file=rel_src,
                            target_link=target_link,
                            anchor=anchor,
                            is_valid=False,
                            line_number=line_idx,
                            error_reason=f"Target file path does not resolve: {target_url}",
                        )
                    )
                elif check_anchors and anchor:
                    target_key = resolved_clean
                    if (
                        target_key not in anchor_index
                        and f"{resolved_clean}.md" in anchor_index
                    ):
                        target_key = f"{resolved_clean}.md"
                    target_anchors = anchor_index.get(target_key, set())
                    if target_anchors and anchor not in target_anchors:
                        diagnostics.append(
                            LinkDiagnostic(
                                source_file=rel_src,
                                target_link=target_link,
                                anchor=anchor,
                                is_valid=False,
                                line_number=line_idx,
                                error_reason=f"Anchor #{anchor} not found in target file {target_url}",
                            )
                        )

    # 3. Check Table of Contents integrity
    toc_diags: tuple[TocDiagnostic, ...] = ()
    orphans: tuple[str, ...] = ()
    if check_toc and target_path.is_dir():
        toc_diags, orphans = TocIntegrityAuditor.audit_toc(target_path)

    broken_toc_count = sum(1 for td in toc_diags if not td.is_valid)
    is_valid = len(diagnostics) == 0 and broken_toc_count == 0

    return LinkValidationReport(
        scanned_files_count=len(md_files),
        total_links_checked=total_links,
        broken_links=tuple(diagnostics),
        toc_diagnostics=toc_diags,
        orphaned_files=orphans,
        valid=is_valid,
    )
