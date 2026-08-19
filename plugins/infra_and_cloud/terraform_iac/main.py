"""Terraform / OpenTofu HCL parser, state drift detector, and cost estimator plugin."""

from __future__ import annotations

import re
from typing import Any

# Baseline cost heuristics (approx monthly USD)
_COST_HEURISTICS = {
    "aws_instance": {"t3.micro": 7.50, "t3.small": 15.00, "t3.medium": 30.00, "default": 25.00},
    "aws_db_instance": {"db.t3.micro": 15.00, "db.t3.small": 30.00, "default": 50.00},
    "aws_s3_bucket": {"default": 3.00},
    "aws_lb": {"default": 22.50},
    "aws_nat_gateway": {"default": 32.50},
}


def parse_hcl_blocks(hcl_content: str) -> dict[str, Any]:
    """Extract declared HCL blocks (resource, variable, provider, output, module)."""
    blocks: list[dict[str, Any]] = []

    pattern = re.compile(r'^(resource|variable|provider|output|module)\s+["\']?([^"\'\s{]+)["\']?(?:\s+["\']?([^"\'\s{]+)["\']?)?', re.MULTILINE)

    for match in pattern.finditer(hcl_content):
        block_type = match.group(1)
        name1 = match.group(2)
        name2 = match.group(3)

        if block_type == "resource":
            res_type = name1
            res_name = name2 or "unnamed"
            blocks.append({
                "block_type": block_type,
                "resource_type": res_type,
                "name": res_name,
            })
        else:
            blocks.append({
                "block_type": block_type,
                "name": name1,
            })

    return {
        "status": "ok",
        "total_blocks_found": len(blocks),
        "blocks": blocks,
    }


def detect_state_drift(
    declared_state: dict[str, Any],
    actual_state: dict[str, Any],
) -> dict[str, Any]:
    """Compute drift diff between declared state and actual state."""
    drifts: list[dict[str, Any]] = []

    all_keys = set(declared_state.keys()) | set(actual_state.keys())

    for key in sorted(all_keys):
        decl = declared_state.get(key)
        act = actual_state.get(key)

        if key not in declared_state:
            drifts.append({
                "attribute": key,
                "type": "unexpected_in_actual",
                "declared": None,
                "actual": act,
            })
        elif key not in actual_state:
            drifts.append({
                "attribute": key,
                "type": "missing_in_actual",
                "declared": decl,
                "actual": None,
            })
        elif decl != act:
            drifts.append({
                "attribute": key,
                "type": "value_mismatch",
                "declared": decl,
                "actual": act,
            })

    return {
        "status": "ok",
        "has_drift": len(drifts) > 0,
        "drift_count": len(drifts),
        "drifts": drifts,
    }


def estimate_resource_costs(resources: list[dict[str, Any]]) -> dict[str, Any]:
    """Estimate monthly cloud infrastructure costs."""
    cost_items: list[dict[str, Any]] = []
    total_monthly = 0.0

    for res in resources:
        res_type = res.get("type", "unknown")
        inst_type = res.get("instance_type", "default")
        name = res.get("name", res_type)

        monthly_cost = 10.0  # default fallback
        if res_type in _COST_HEURISTICS:
            type_costs = _COST_HEURISTICS[res_type]
            monthly_cost = type_costs.get(inst_type, type_costs.get("default", 10.0))

        cost_items.append({
            "name": name,
            "type": res_type,
            "monthly_cost_usd": round(monthly_cost, 2),
        })
        total_monthly += monthly_cost

    return {
        "status": "ok",
        "total_resources": len(resources),
        "estimated_monthly_usd": round(total_monthly, 2),
        "breakdown": cost_items,
    }
