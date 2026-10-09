"""HTML Visual Brief Parser with Heavy Topology Slicing (Rule 48)."""

from __future__ import annotations

import re
from pathlib import Path

from harness.services.temp_artifact_miner.models import (
    BriefCatalogItem,
    compute_file_sha256,
    detect_brief_category,
)


def parse_html_brief(
    file_path: Path,
    heavy_threshold: int = 100000,
) -> BriefCatalogItem:
    """Extract structured decision logic and Mermaid DAGs from an HTML visual brief.

    Bounds heavy topology graphs exceeding heavy_threshold to prevent context window blowout (Rule 48).
    """
    file_stat = file_path.stat()
    size = file_stat.st_size
    mtime = file_stat.st_mtime
    is_heavy = size >= heavy_threshold
    sha256_hash = compute_file_sha256(file_path)

    # For heavy files, read only the header and bounded slices (Rule 48)
    if is_heavy:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content_sample = f.read(16384)
    else:
        content_sample = file_path.read_text(encoding="utf-8", errors="ignore")

    title_match = re.search(r"<title>(.*?)</title>", content_sample, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "Untitled Brief"

    has_mermaid = bool(
        re.search(r"class=[\"']mermaid[\"']|<pre class=[\"']mermaid[\"']", content_sample, re.IGNORECASE)
    )
    has_scorecard = bool(
        re.search(r"scorecard|evaluation matrix|evaluation criteria|rubric", content_sample, re.IGNORECASE)
    )
    has_antipatterns = bool(
        re.search(r"anti-pattern|antipattern|defense matrix|failure mode", content_sample, re.IGNORECASE)
    )

    mermaid_dags: list[str] = []
    if has_mermaid and not is_heavy:
        blocks = re.findall(
            r"<div[^>]*class=[\"'][^\"']*mermaid[^\"']*[\"'][^>]*>(.*?)</div>",
            content_sample,
            re.DOTALL | re.IGNORECASE,
        )
        if not blocks:
            blocks = re.findall(
                r"<pre[^>]*class=[\"'][^\"']*mermaid[^\"']*[\"'][^>]*>(.*?)</pre>",
                content_sample,
                re.DOTALL | re.IGNORECASE,
            )
        for b in blocks:
            cleaned = b.strip()
            if cleaned:
                mermaid_dags.append(cleaned)

    category = detect_brief_category(file_path.name)

    return BriefCatalogItem(
        name=file_path.name,
        path=str(file_path),
        category=category,
        title=title,
        size_bytes=size,
        mtime=mtime,
        has_mermaid=has_mermaid,
        has_scorecard=has_scorecard,
        has_antipatterns=has_antipatterns,
        is_heavy_topology=is_heavy,
        mermaid_dags=tuple(mermaid_dags),
        sha256=sha256_hash,
    )
