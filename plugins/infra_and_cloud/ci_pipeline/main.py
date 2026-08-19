"""CI/CD pipeline workflow validator and dependency auditor plugin."""

from __future__ import annotations

import re
from typing import Any


def validate_github_actions_workflow(workflow_yaml: str) -> dict[str, Any]:
    """Validate structure of a GitHub Actions YAML workflow."""
    issues: list[dict[str, Any]] = []

    if not re.search(r"^\s*on:\s*", workflow_yaml, re.MULTILINE):
        issues.append({
            "rule": "MissingOnTrigger",
            "severity": "critical",
            "detail": "Workflow must declare an 'on:' trigger block (e.g. push, pull_request).",
        })

    if not re.search(r"^\s*jobs:\s*", workflow_yaml, re.MULTILINE):
        issues.append({
            "rule": "MissingJobsBlock",
            "severity": "critical",
            "detail": "Workflow must declare at least one job under 'jobs:'.",
        })

    if "permissions:" not in workflow_yaml:
        issues.append({
            "rule": "MissingExplicitPermissions",
            "severity": "medium",
            "detail": "Top-level or job-level 'permissions:' block recommended for least privilege.",
        })

    return {
        "status": "ok",
        "valid": len(issues) == 0,
        "issues_count": len(issues),
        "issues": issues,
    }


def find_circular_job_dependencies(jobs: dict[str, Any]) -> dict[str, Any]:
    """Detect circular dependency cycles in job DAG."""
    # Build graph: job -> set of jobs it depends on
    adj: dict[str, set[str]] = {}
    for job_name, job_data in jobs.items():
        needs = job_data.get("needs", []) if isinstance(job_data, dict) else []
        if isinstance(needs, str):
            needs = [needs]
        adj[job_name] = set(needs)

    visited: set[str] = set()
    rec_stack: set[str] = set()
    cycle_found: list[str] = []

    def dfs(node: str, path: list[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                if dfs(neighbor, [*path, neighbor]):
                    return True
            elif neighbor in rec_stack:
                cycle_found.extend([*path, neighbor])
                return True

        rec_stack.remove(node)
        return False

    for j in jobs:
        if j not in visited and dfs(j, [j]):
            break

    return {
        "status": "ok",
        "has_cycle": len(cycle_found) > 0,
        "cycle_path": cycle_found,
    }


def audit_action_pins(workflow_yaml: str) -> dict[str, Any]:
    """Audit third-party GitHub Action references for mutable tags vs immutable SHA pins."""
    unpinned: list[dict[str, Any]] = []

    for match in re.finditer(r"uses:\s*([a-zA-Z0-9_\-\.\/]+)@([^\s]+)", workflow_yaml):
        action_name = match.group(1)
        version_ref = match.group(2)

        # Ignore local actions
        if action_name.startswith(("./", "docker://")):
            continue

        # SHA is 40 hex chars
        if not re.fullmatch(r"[a-f0-9]{40}", version_ref):
            unpinned.append({
                "action": action_name,
                "ref": version_ref,
                "severity": "medium",
                "recommendation": f"Pin '{action_name}@{version_ref}' to a full commit SHA for supply-chain security.",
            })

    return {
        "status": "ok",
        "total_actions_found": len(unpinned),
        "unpinned_count": len(unpinned),
        "pinned_securely": len(unpinned) == 0,
        "unpinned_actions": unpinned,
    }
