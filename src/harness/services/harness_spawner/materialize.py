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

from ._doc_templates import BlueprintLike
from .diff_review import compute_tree_sha256
from .doc_bundle import (
    TRACKED_DOC_PATHS,
    build_harness_docs,
    compute_docs_sha256,
    fallback_doc_context,
)

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
            },
            "audit-docs": {
                "description": "Verify 7-part documentation bundle, companion CARD.md files, and relative links.",
                "write_path": False,
                "steps": [
                    {
                        "command": f"{_python_invocation()} _tools/audit_docs.py",
                        "workdir": ".",
                        "expected_output": "DOCS_AUDIT_OK",
                    }
                ],
            },
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
    blueprint: BlueprintLike | None = None,
    prime_commit: str = "",
    spawn_id: str = "",
    skills_root: Path | str = ".agents/skills",
) -> dict[str, Any]:
    """Validate, build 7-part docs + ICM layout, write spawn tree + `dock.yaml`, and link dock."""
    tree_dict = dict(tree)
    guards.assert_tree_clean(tree_dict)
    census = surface_ops.validate(surface, tree_dict)

    repo_dir = Path(target_dir).resolve()
    doc_ctx: BlueprintLike = (
        blueprint if blueprint is not None else fallback_doc_context(name, description, surface, tree_dict)
    )
    doc_info = build_harness_docs(
        doc_ctx,
        repo_dir=repo_dir,
        prime_commit=prime_commit,
        spawn_id=spawn_id,
        skills_root=skills_root,
    )
    surface_ops.write_tree(surface, tree_dict, repo_dir)

    dock_payload = build_spawn_dock_yaml(name=name, description=description, surface=surface, tree=tree_dict)
    (repo_dir / "dock.yaml").write_text(yaml.safe_dump(dock_payload, sort_keys=False), encoding="utf-8")

    tree_sha256 = compute_tree_sha256(tree_dict)
    docs_sha256 = compute_docs_sha256(repo_dir, TRACKED_DOC_PATHS)
    digest_path = repo_dir / _TREE_DIGEST_REL
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        json.dumps(
            {
                "name": name,
                "tree_sha256": tree_sha256,
                "docs_sha256": docs_sha256,
                "tracked_docs": list(TRACKED_DOC_PATHS),
                "icm_form": doc_info["icm_form"],
                "surface": surface.name,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    dock = dock_service if dock_service is not None else DefaultDockService()
    link_rec: DockLinkRecord = dock.link(repo_dir, name=name, approve=approve)
    return {
        "repo_dir": str(repo_dir),
        "dock_name": link_rec.dock_name,
        "manifest_sha256": link_rec.manifest_sha256,
        "approved": link_rec.approved,
        "approved_sha256": link_rec.approved_sha256,
        "tree_sha256": tree_sha256,
        "docs_sha256": docs_sha256,
        "tracked_docs": list(TRACKED_DOC_PATHS),
        "icm_form": doc_info["icm_form"],
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
    """Detect manifest, editable tree, or documentation digest drift on a materialized repo."""
    repo_dir = Path(target_dir).resolve()
    digest_file = repo_dir / _TREE_DIGEST_REL
    digest_data: dict[str, Any] = {}
    if digest_file.is_file():
        digest_data = json.loads(digest_file.read_text(encoding="utf-8"))
    recorded_sha = expected_tree_sha256 or str(digest_data.get("tree_sha256") or "")
    recorded_docs_sha = str(digest_data.get("docs_sha256") or "")
    tracked_docs = [str(p) for p in (digest_data.get("tracked_docs") or TRACKED_DOC_PATHS)]

    live_tree = surface_ops.read_tree(surface, repo_dir)
    live_tree_sha = compute_tree_sha256(live_tree)
    tree_drifted = bool(recorded_sha and live_tree_sha != recorded_sha)
    live_docs_sha = compute_docs_sha256(repo_dir, tracked_docs) if recorded_docs_sha else ""
    docs_drifted = bool(recorded_docs_sha and live_docs_sha != recorded_docs_sha)

    dock = dock_service if dock_service is not None else DefaultDockService()
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
        "expected_docs_sha256": recorded_docs_sha,
        "live_docs_sha256": live_docs_sha,
        "tree_drifted": tree_drifted,
        "docs_drifted": docs_drifted,
        "manifest_drifted": manifest_drifted,
        "drifted": tree_drifted or manifest_drifted or docs_drifted,
    }


__all__ = [
    "build_spawn_dock_yaml",
    "check_materialized_drift",
    "materialize_spawn_as_dock",
]
