# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""CLI and programmatic selector for open-source GIS engines based on workload profiling."""

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

# Ensure local package and workspace paths are resolved
script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

workspace_src = script_dir.parent.parent.parent.parent / "src"
if workspace_src.exists() and str(workspace_src) not in sys.path:
    sys.path.insert(0, str(workspace_src))

from engine import (
    DefaultOpenSourceGisService,
    FalconViewRestrictedDomainError,
    SpatialWorkloadProfile,
)


def load_workload_from_json(path: Path | str) -> SpatialWorkloadProfile:
    """Parse workload profile from JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Workload JSON not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    return SpatialWorkloadProfile(
        geometry_type=data.get("geometry_type") or "vector_polygon",
        domain=data.get("domain") or "general_gis",
        data_formats=tuple(data.get("data_formats") or []),
        sector=data.get("sector") or "civilian",
        output_type=data.get("output_type") or "analytical_report",
        scale_gb=float(data.get("scale_gb") or 0.0),
        has_lidar=bool(data.get("has_lidar", False)),
        has_time_series=bool(data.get("has_time_series", False)),
        needs_mobile=bool(data.get("needs_mobile", False)),
        needs_statistics=bool(data.get("needs_statistics", False)),
        analysis=data.get("analysis") or "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Open-Source GIS Engine Selector")
    parser.add_argument("--workload-json", type=str, help="Path to workload JSON profile")
    parser.add_argument("--domain", type=str, default="general_gis", help="Spatial analysis domain")
    parser.add_argument("--format", action="append", dest="formats", help="Input data formats (can repeat)")
    parser.add_argument("--geometry-type", type=str, default="vector_polygon", help="Geometry type")
    parser.add_argument("--sector", type=str, default="civilian", help="Sector context")
    parser.add_argument("--output-type", type=str, default="analytical_report", help="Output deliverable type")
    parser.add_argument("--scale-gb", type=float, default=0.0, help="Estimated data size in GB")
    parser.add_argument("--has-lidar", action="store_true", help="Workload contains LiDAR point clouds")
    parser.add_argument("--has-time-series", action="store_true", help="Workload contains temporal rasters")
    parser.add_argument("--needs-mobile", action="store_true", help="Requires field GPS or mobile capture")
    parser.add_argument("--needs-statistics", action="store_true", help="Requires spatial econometrics")
    parser.add_argument("--analysis", type=str, default="", help="Specific analytical operation (e.g. twi, moran_i)")
    parser.add_argument("--output-json", type=str, help="Optional path to write selection result JSON")
    parser.add_argument("--generate-brief", action="store_true", help="Render Stage 5 interactive HTML visual brief")
    parser.add_argument("--brief-html", type=str, help="Optional specific path for the generated visual brief")

    args = parser.parse_args()

    try:
        if args.workload_json:
            profile = load_workload_from_json(args.workload_json)
        else:
            profile = SpatialWorkloadProfile(
                geometry_type=args.geometry_type,
                domain=args.domain,
                data_formats=tuple(args.formats or []),
                sector=args.sector,
                output_type=args.output_type,
                scale_gb=args.scale_gb,
                has_lidar=args.has_lidar,
                has_time_series=args.has_time_series,
                needs_mobile=args.needs_mobile,
                needs_statistics=args.needs_statistics,
                analysis=args.analysis,
            )
    except FalconViewRestrictedDomainError as err:
        sys.stderr.write(f"[SAFETY HALT] {err}\n")
        sys.stderr.write("Reference documentation located at: references/restricted-domain-notes.md\n")
        return 2
    except Exception as err:
        sys.stderr.write(f"[ERROR] Failed to initialize workload profile: {err}\n")
        return 1

    service = DefaultOpenSourceGisService()
    try:
        result = service.route_workload(profile)
    except Exception as err:
        sys.stderr.write(f"[ERROR] Routing failed: {err}\n")
        return 1

    brief_path = None
    if args.generate_brief or args.brief_html:
        brief_res = service.generate_visual_brief(
            profile=profile,
            selection=result,
            output_path=args.brief_html,
        )
        brief_path = brief_res.report_path

    payload = {
        "routing_path": result.routing_path,
        "composite_score": result.composite_score,
        "primary_engine": {
            "name": result.primary.engine.name,
            "star_rating": result.primary.engine.star_rating,
            "fitness_score": result.primary.fitness_score,
            "license": result.primary.engine.license,
            "python_api": result.primary.engine.python_api,
            "matched_domains": list(result.primary.matched_domains),
            "matched_formats": list(result.primary.matched_formats),
            "warnings": list(result.primary.warnings),
        },
        "secondary_engine": (
            {
                "name": result.secondary.engine.name,
                "star_rating": result.secondary.engine.star_rating,
                "fitness_score": result.secondary.fitness_score,
                "license": result.secondary.engine.license,
                "python_api": result.secondary.engine.python_api,
                "matched_domains": list(result.secondary.matched_domains),
                "matched_formats": list(result.secondary.matched_formats),
                "warnings": list(result.secondary.warnings),
            }
            if result.secondary
            else None
        ),
        "rationale": result.rationale,
        "visual_brief_path": brief_path,
    }

    out_str = json.dumps(payload, indent=2)
    sys.stdout.write(out_str + "\n")

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(out_str, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
