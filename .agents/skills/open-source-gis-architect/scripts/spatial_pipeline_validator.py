# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Validates spatial execution pipeline DAGs for CRS projection safety and format consistency."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

workspace_src = script_dir.parent.parent.parent.parent / "src"
if workspace_src.exists() and str(workspace_src) not in sys.path:
    sys.path.insert(0, str(workspace_src))

from harness.services.open_source_gis import (
    DefaultOpenSourceGisService,
)


def validate_steps(raw_steps: list[dict]) -> tuple[bool, list[str]]:
    """Validate a list of pipeline step dicts and build SpatialPipelineDAG via DefaultOpenSourceGisService."""
    service = DefaultOpenSourceGisService()
    valid, messages, _ = service.validate_pipeline_dag(raw_steps)
    return valid, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Spatial Pipeline DAG and CRS Safety Validator")
    parser.add_argument("--pipeline-json", type=str, help="Path to pipeline DAG JSON definition")
    parser.add_argument("--mock", action="store_true", help="Run self-test on built-in mock valid pipeline")
    parser.add_argument("--mock-invalid", action="store_true", help="Run self-test on built-in invalid CRS pipeline")

    args = parser.parse_args()

    if args.mock:
        raw = [
            {
                "step_id": 1,
                "operation": "reproject",
                "engine": "qgis",
                "input_crs": "EPSG:4326",
                "output_crs": "EPSG:32632",
                "input_format": "GeoPackage",
                "output_format": "GeoPackage",
            },
            {
                "step_id": 2,
                "operation": "buffer",
                "engine": "qgis",
                "input_crs": "EPSG:32632",
                "output_crs": "EPSG:32632",
                "input_format": "GeoPackage",
                "output_format": "GeoPackage",
            },
        ]
    elif args.mock_invalid:
        raw = [
            {
                "step_id": 1,
                "operation": "buffer",
                "engine": "qgis",
                "input_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "input_format": "GeoPackage",
                "output_format": "GeoPackage",
            }
        ]
    elif args.pipeline_json:
        p = Path(args.pipeline_json)
        if not p.exists():
            sys.stderr.write(f"[ERROR] File not found: {p}\n")
            return 1
        raw = json.loads(p.read_text(encoding="utf-8"))
    else:
        sys.stderr.write("[ERROR] Must specify --pipeline-json or --mock\n")
        return 1

    valid, messages = validate_steps(raw)
    out = {
        "is_valid": valid,
        "messages": messages,
    }
    sys.stdout.write(json.dumps(out, indent=2) + "\n")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
