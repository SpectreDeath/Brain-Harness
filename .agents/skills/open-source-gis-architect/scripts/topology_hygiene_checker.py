# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Structural topology auditor detecting self-intersections, unclosed rings, and sliver polygons."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
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
    TopologyAuditReport,
)


def audit_polygon_rings(
    features: list[dict],
    sliver_threshold_m2: float = 0.05,
) -> TopologyAuditReport:
    """Audit geometry rings for basic topological defects via DefaultOpenSourceGisService."""
    service = DefaultOpenSourceGisService()
    return service.audit_topology(features, sliver_threshold_m2=sliver_threshold_m2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Spatial Geometry Topology Hygiene Auditor")
    parser.add_argument("--geometry-json", type=str, help="Path to GeoJSON feature collection")
    parser.add_argument("--sliver-threshold", type=float, default=0.05, help="Sliver area threshold in m²")
    parser.add_argument("--check-mock", action="store_true", help="Run auditor on synthetic test geometries")
    parser.add_argument("--check-mock-invalid", action="store_true", help="Run auditor on synthetic invalid geometries")

    args = parser.parse_args()

    if args.check_mock:
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]],
                },
                "properties": {"area_m2": 100.0},
            }
        ]
    elif args.check_mock_invalid:
        features = [
            {
                "type": "Feature",
                "_mock_self_intersection": True,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [10.0, 10.0], [10.0, 0.0], [0.0, 10.0], [0.0, 0.0]]],
                },
                "properties": {"area_m2": 0.01},
            }
        ]
    elif args.geometry_json:
        p = Path(args.geometry_json)
        if not p.exists():
            sys.stderr.write(f"[ERROR] File not found: {p}\n")
            return 1
        data = json.loads(p.read_text(encoding="utf-8"))
        features = data.get("features", [])
    else:
        sys.stderr.write("[ERROR] Must specify --geometry-json or --check-mock\n")
        return 1

    report = audit_polygon_rings(features, sliver_threshold_m2=args.sliver_threshold)
    payload = asdict(report)
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0 if report.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
