"""Materialize validated spawn trees as durable dock-linked repositories with drift checks (Step 3)."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

import yaml

from harness.services.dock import DefaultDockService, DockLinkRecord
from harness.services.recursive_harnessing import guards, surface as surface_ops
from harness.services.recursive_harnessing.models import SurfaceSpec

from .diff_review import compute_tree_sha256

_TREE_DIGEST_REL = ".harness/spawn_tree_digest.json"


def _python_invocation() -> str:
    """Return a shell-safe interpreter invocation that does not rely on a bare `python` on PATH."""
    exe = sys.executable or "python3"
    if os.name == "nt":
        return f'"{exe}"'
    return shlex.quote(exe)


def build_spawn_dock_yaml(
    *,
    name: str,
    description: str,
    surface: SurfaceSpec,
    tree: Mapping[str, str],
) -> dict[str, Any]:
    """Build a declarative `dock.yaml` mapping for a materialized domain harness."""
    skills = surface_ops.skill_names(surface, dict(tree))
    always_on_entry = surface.always_on[0] if surface.always_on else "AGENTS.md"
    return {
        "name": name,
        "description": description or f"Materialized domain harness: {name}",
        "version": "1.0",
        "permissions": {
            "read": True,
            "run": True,
            "write": False,
            "push": False,
        },
        "boundaries": {
            "paths": [".env", ".git-credentials"],
            "operations": ["git push --force", "rm -rf"],
        },
        "tools": skills,
        "entrypoints": {
            "validate": {
                "description": "Verify materialized harness always-on file exists.",
                "write_path": False,
                "steps": [
                    {
                        "command": (
                            f'{_python_invocation()} -c "import os; assert os.path.isfile({always_on_entry!r}); '
                            "print('DOCK_HARNESS_OK')\""
                        ),
                        "workdir": ".",
                        "expected_output": "DOCK_HARNESS_OK",
                    }
                ],
            }
        },
    }


def materialize_spawn_as_dock(
    surface: SurfaceSpec,
    tree: Mapping[str, str],
    target_dir: Path | str,
    *,
    name: str,
    description: str,
    dock_service: DefaultDockService | None = None,
    approve: bool = False,
) -> dict[str, Any]:
    """Validate, write a spawn tree + `dock.yaml`, record tree digest, and link via `DefaultDockService`."""
    tree_dict = dict(tree)
    guards.assert_tree_clean(tree_dict)
    census = surface_ops.validate(surface, tree_dict)

    repo_dir = Path(target_dir).resolve()
    surface_ops.write_tree(surface, tree_dict, repo_dir)

    dock_payload = build_spawn_dock_yaml(name=name, description=description, surface=surface, tree=tree_dict)
    (repo_dir / "dock.yaml").write_text(yaml.safe_dump(dock_payload, sort_keys=False), encoding="utf-8")

    tree_sha256 = compute_tree_sha256(tree_dict)
    digest_path = repo_dir / _TREE_DIGEST_REL
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        json.dumps({"name": name, "tree_sha256": tree_sha256, "surface": surface.name}, indent=2) + "\n",
        encoding="utf-8",
    )

    dock = dock_service if dock_service is not None else DefaultDockService(workspace_root=repo_dir)
    link_rec: DockLinkRecord = dock.link(repo_dir, name=name, approve=approve)
    return {
        "repo_dir": str(repo_dir),
        "dock_name": link_rec.dock_name,
        "manifest_sha256": link_rec.manifest_sha256,
        "approved": link_rec.approved,
        "approved_sha256": link_rec.approved_sha256,
        "tree_sha256": tree_sha256,
        "census": census,
    }


def check_materialized_drift(
    target_dir: Path | str,
    surface: SurfaceSpec,
    *,
    expected_tree_sha256: str | None = None,
    dock_service: DefaultDockService | None = None,
    dock_name: str | None = None,
) -> dict[str, Any]:
    """Detect manifest approval drift (`list_docks`) or editable tree digest drift on a materialized repo."""
    repo_dir = Path(target_dir).resolve()
    digest_file = repo_dir / _TREE_DIGEST_REL
    recorded_sha = expected_tree_sha256 or ""
    if not recorded_sha and digest_file.is_file():
        recorded_sha = str(json.loads(digest_file.read_text(encoding="utf-8")).get("tree_sha256") or "")

    live_tree = surface_ops.read_tree(surface, repo_dir)
    live_tree_sha = compute_tree_sha256(live_tree)
    tree_drifted = bool(recorded_sha and live_tree_sha != recorded_sha)

    dock = dock_service if dock_service is not None else DefaultDockService(workspace_root=repo_dir)
    dock_status = "unlinked"
    for entry in dock.list_docks():
        if (dock_name and entry.get("dock_name") == dock_name) or (
            Path(str(entry.get("repo_path") or "")).resolve() == repo_dir
        ):
            dock_status = str(entry.get("status") or "unknown")
            break

    manifest_drifted = dock_status == "manifest_changed"
    return {
        "repo_dir": str(repo_dir),
        "dock_status": dock_status,
        "expected_tree_sha256": recorded_sha,
        "live_tree_sha256": live_tree_sha,
        "tree_drifted": tree_drifted,
        "manifest_drifted": manifest_drifted,
        "drifted": tree_drifted or manifest_drifted,
    }


__all__ = [
    "build_spawn_dock_yaml",
    "check_materialized_drift",
    "materialize_spawn_as_dock",
]
