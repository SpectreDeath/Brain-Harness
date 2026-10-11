"""Data management maturity assessment commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from harness.services.data_management import DataManagementEngine


async def assess_maturity_cmd(
    scores_path: str | None = None,
    survey_path: str | None = None,
    target_level: int = 4,
    org_name: str = "Enterprise Organization",
    out_path: str | None = None,
) -> dict[str, Any]:
    """Evaluate Level 0–5 Data Management Maturity."""
    s_path = survey_path or scores_path
    scores: dict[str, int] = {}
    organization = org_name
    if s_path:
        p = Path(s_path)
        if p.exists():
            loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        else:
            loaded = yaml.safe_load(s_path)
        if isinstance(loaded, dict):
            if "organization" in loaded:
                organization = loaded["organization"]
            if "capabilities" in loaded:
                for k, v in loaded["capabilities"].items():
                    if isinstance(v, dict) and "level" in v:
                        scores[k] = int(v["level"])
                    elif isinstance(v, (int, float)):
                        scores[k] = int(v)
            else:
                scores = loaded
    else:
        scores = {
            "data_governance": 2,
            "data_architecture": 3,
            "data_modeling": 3,
            "data_quality": 2,
            "data_security_privacy": 3,
            "data_engineering_ops": 2,
        }

    engine = DataManagementEngine()
    report = engine.assess_maturity(scores, target_level=target_level, organization_name=organization)

    ret = {
        "organization": report.organization_name,
        "overall_level": report.overall_maturity_level,
        "target_level": report.target_maturity_level,
        "stage": report.maturity_stage,
        "capabilities": {k: v.to_dict() for k, v in report.dimension_scores.items()},
        "roadmap": list(report.prioritized_roadmap),
        "report": report,
    }
    if out_path:
        Path(out_path).write_text(
            json.dumps({k: v for k, v in ret.items() if k != "report"}, indent=2),
            encoding="utf-8",
        )

    return ret
