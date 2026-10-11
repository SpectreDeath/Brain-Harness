"""Resource locating and default catalog/weights loading."""

from __future__ import annotations

import json
from pathlib import Path

import structlog
import yaml

from harness.services.open_source_gis.catalog.fallback import get_fallback_engine_catalog
from harness.services.open_source_gis.models import GISEngineRecord

logger = structlog.get_logger(__name__)


def find_resource_file(filename: str) -> Path | None:
    """Locate catalog or config file across workspace roots."""
    current = Path(__file__).resolve()
    workspace_root: Path | None = None
    for p in current.parents:
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            workspace_root = p
            break
    if workspace_root is None:
        workspace_root = current.parents[5]

    candidates = [
        workspace_root / ".agents" / "skills" / "open-source-gis-architect" / "resources" / filename,
        workspace_root / "plugins" / "geospatial_and_osint" / "open_source_gis" / filename,
        workspace_root / ".agents" / "skills" / "open-source-gis-architect" / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_default_catalog() -> list[GISEngineRecord]:
    """Load engines from gis_engine_matrix.json or fallback catalog."""
    matrix_path = find_resource_file("gis_engine_matrix.json")
    if not matrix_path or not matrix_path.exists():
        return get_fallback_engine_catalog()

    try:
        data = json.loads(matrix_path.read_text(encoding="utf-8"))
        records: list[GISEngineRecord] = []
        for item in data:
            records.append(
                GISEngineRecord(
                    name=item["name"],
                    star_rating=float(item["star_rating"]),
                    license=item["license"],
                    maturity=item["maturity"],
                    sector_flags=tuple(item.get("sector_flags") or []),
                    primary_domains=tuple(item.get("primary_domains") or []),
                    specialized_tools=tuple(item.get("specialized_tools") or []),
                    python_api=item.get("python_api"),
                    supported_formats=tuple(item.get("supported_formats") or []),
                    negative_boundary=item.get("negative_boundary", ""),
                    arcgis_parity=bool(item.get("arcgis_parity", False)),
                    article_note=item.get("article_note", ""),
                )
            )
        return records
    except Exception as err:
        logger.warning("failed_loading_engine_matrix", error=str(err))
        return get_fallback_engine_catalog()


def load_default_weights() -> dict[str, float]:
    """Load default scoring weights from config.default.yaml or static defaults."""
    cfg_path = find_resource_file("config.default.yaml")
    if cfg_path and cfg_path.exists():
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            if cfg and "scoring_weights" in cfg:
                return {str(k): float(v) for k, v in cfg["scoring_weights"].items()}
        except Exception as err:
            logger.debug("config_load_weights_fallback", error=str(err))
    return {
        "analytical_depth": 0.35,
        "cartography": 0.20,
        "specialized_tooling": 0.25,
        "automation_scripting": 0.20,
    }
