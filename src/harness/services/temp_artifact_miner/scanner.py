"""Temporary Directory Scanner for HTML Visual Briefs (Rule 32, Rule 52)."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from harness.services.temp_artifact_miner.models import (
    BriefCatalog,
    BriefCatalogItem,
)
from harness.services.temp_artifact_miner.parser import parse_html_brief

logger = logging.getLogger("harness.services.temp_artifact_miner")


def scan_briefs(
    temp_dir: Path | str | None = None,
    max_depth: int = 2,
    heavy_threshold: int = 100000,
    default_temp_dir: Path | None = None,
) -> BriefCatalog:
    """Scan the temporary directory for HTML visual briefs with bounded traversal (Rule 52).

    Employs defensive batch exception handling (Rule 32).
    """
    if temp_dir is not None:
        target_path = Path(temp_dir)
    elif default_temp_dir is not None:
        target_path = default_temp_dir
    else:
        target_path = Path(".")

    total_scanned = 0
    brief_items: list[BriefCatalogItem] = []
    total_bytes = 0
    heavy_count = 0
    by_category: dict[str, list[BriefCatalogItem]] = defaultdict(list)

    if not target_path.exists():
        logger.warning("Temp directory path does not exist: %s", target_path)
        return BriefCatalog(0, 0, 0, 0, {})

    try:
        for entry in target_path.glob("*.html"):
            total_scanned += 1
            try:
                item = parse_html_brief(entry, heavy_threshold=heavy_threshold)
                brief_items.append(item)
                total_bytes += item.size_bytes
                if item.is_heavy_topology:
                    heavy_count += 1
                by_category[item.category].append(item)
            except (NameError, TypeError, AttributeError):
                raise
            except Exception as e:
                logger.warning("Error parsing visual brief %s: %s", entry.name, e)
    except (NameError, TypeError, AttributeError):
        raise
    except Exception as e:
        logger.warning("Error scanning temp directory for HTML files: %s", e)

    return BriefCatalog(
        total_scanned=total_scanned,
        brief_count=len(brief_items),
        total_bytes=total_bytes,
        heavy_count=heavy_count,
        items_by_category={k: tuple(v) for k, v in by_category.items()},
    )
