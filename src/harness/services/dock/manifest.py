"""Manifest loading and generic dock synthesis."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import yaml

from .models import (
    DockBoundaries,
    DockManifest,
    DockManifestError,
    DockPermissions,
    DockProcedure,
    DockStep,
)


def load_dock_manifest(repo_root: Path) -> DockManifest:
    """Load and parse repository dock manifest (pure read, zero code execution)."""
    manifest_file = repo_root / "dock.yaml"
    warnings: list[str] = []

    # Check for mislocated manifest in .harness/dock.yaml
    alt_file = repo_root / ".harness" / "dock.yaml"
    if not manifest_file.exists():
        if alt_file.exists():
            warnings.append("Found .harness/dock.yaml, but only repo-root 'dock.yaml' is supported.")
        raise DockManifestError(
            manifest_file,
            f"Manifest file 'dock.yaml' not found in repository root '{repo_root}'.",
        )

    try:
        content_bytes = manifest_file.read_bytes()
        sha256 = hashlib.sha256(content_bytes).hexdigest()
        raw = yaml.safe_load(content_bytes)
    except yaml.YAMLError as e:
        raise DockManifestError(manifest_file, f"Malformed YAML: {e}") from e
    except Exception as e:
        raise DockManifestError(manifest_file, f"Failed to read file: {e}") from e

    if not isinstance(raw, dict):
        raise DockManifestError(manifest_file, "Manifest root must be a YAML mapping.")

    # Validate required fields
    name = raw.get("name")
    if not name or not str(name).strip():
        raise DockManifestError(manifest_file, "Missing required field 'name'.")
    name = str(name).strip()

    description = raw.get("description")
    if not description or not str(description).strip():
        raise DockManifestError(manifest_file, "Missing required field 'description'.")
    description = str(description).strip()

    # Rule 33: null-field fallbacks
    perms_raw = raw.get("permissions") or {}
    permissions = DockPermissions(
        read=bool(perms_raw.get("read", True)),
        run=bool(perms_raw.get("run", True)),
        write=bool(perms_raw.get("write", False)),
        push=bool(perms_raw.get("push", False)),
    )

    bounds_raw = raw.get("boundaries") or {}
    b_paths = tuple(str(p) for p in (bounds_raw.get("paths") or ()))
    b_ops = tuple(str(o) for o in (bounds_raw.get("operations") or ()))
    boundaries = DockBoundaries(paths=b_paths, operations=b_ops)

    tools = tuple(str(t) for t in (raw.get("tools") or ()))

    entrypoints_raw = raw.get("entrypoints") or {}
    entrypoints: dict[str, DockProcedure] = {}
    for proc_name, proc_def in entrypoints_raw.items():
        if not isinstance(proc_def, dict):
            continue
        p_name = str(proc_name).strip()
        p_desc = str(proc_def.get("description") or "").strip()
        p_write = bool(proc_def.get("write_path", False))

        steps_raw = proc_def.get("steps") or []
        steps: list[DockStep] = []
        for s_idx, s in enumerate(steps_raw):
            if not isinstance(s, dict):
                continue
            cmd = str(s.get("command") or "").strip()
            workdir = str(s.get("workdir") or ".").strip()
            expected = str(s.get("expected_output") or "").strip()
            call_proc = s.get("call_procedure")
            call_str = str(call_proc).strip() if call_proc else None

            try:
                step = DockStep(
                    command=cmd,
                    workdir=workdir,
                    expected_output=expected,
                    call_procedure=call_str,
                )
                steps.append(step)
            except ValueError as err:
                raise DockManifestError(
                    manifest_file,
                    f"Procedure '{p_name}' step {s_idx + 1} invalid: {err}",
                ) from err

        entrypoints[p_name] = DockProcedure(
            name=p_name,
            description=p_desc,
            steps=tuple(steps),
            write_path=p_write,
        )

    # Check for unknown top-level keys
    known_keys = {"name", "description", "version", "permissions", "boundaries", "tools", "entrypoints"}
    for k in raw:
        if k not in known_keys:
            warnings.append(f"Ignored unknown top-level key: '{k}'")

    return DockManifest(
        name=name,
        description=description,
        declared=True,
        manifest_path=str(manifest_file),
        sha256=sha256,
        entrypoints=entrypoints,
        tools=tools,
        permissions=permissions,
        boundaries=boundaries,
        warnings=tuple(warnings),
    )


def build_generic_dock_manifest(repo_root: Path) -> DockManifest:
    """Synthesize deterministic generic dock manifest for undeclared repositories."""
    repo_name = repo_root.name or "repository"
    procedures: dict[str, DockProcedure] = {}

    # Auto-detect test runner purely by file existence
    if (repo_root / "pyproject.toml").exists() or (repo_root / "tests").is_dir():
        procedures["test"] = DockProcedure(
            name="test",
            description="Run standard pytest test suite",
            steps=(DockStep(command="pytest -q", workdir="."),),
            write_path=False,
        )
    elif (repo_root / "package.json").exists():
        procedures["test"] = DockProcedure(
            name="test",
            description="Run standard npm test script",
            steps=(DockStep(command="npm test", workdir="."),),
            write_path=False,
        )
    elif (repo_root / "Cargo.toml").exists():
        procedures["test"] = DockProcedure(
            name="test",
            description="Run cargo test suite",
            steps=(DockStep(command="cargo test", workdir="."),),
            write_path=False,
        )

    # Always provide status query procedure
    procedures["status"] = DockProcedure(
        name="status",
        description="Inspect git workspace status",
        steps=(DockStep(command="git status --short", workdir="."),),
        write_path=False,
    )

    permissions = DockPermissions(read=True, run=True, write=False, push=False)
    boundaries = DockBoundaries(
        paths=(".git/", ".env", ".pytest_cache/", "src/harness/ui/static/"),
        operations=("git push --force", "git reset --hard", "git clean -fd", "credential_access"),
    )
    tools = ("fs_read_file", "fs_search_text", "fs_list_dir", "git_status", "git_diff", "git_log")

    # Synthesize deterministic SHA-256 digest from the generated structure (Track 5)
    synth_dict = {
        "name": repo_name,
        "declared": False,
        "entrypoints": {
            k: {
                "name": v.name,
                "description": v.description,
                "write_path": v.write_path,
                "steps": [
                    {
                        "command": s.command,
                        "workdir": s.workdir,
                        "expected_output": s.expected_output,
                        "call_procedure": s.call_procedure,
                    }
                    for s in v.steps
                ],
            }
            for k, v in sorted(procedures.items())
        },
        "permissions": asdict(permissions),
        "boundaries": asdict(boundaries),
        "tools": list(tools),
    }
    synth_sha = hashlib.sha256(json.dumps(synth_dict, sort_keys=True).encode("utf-8")).hexdigest()

    return DockManifest(
        name=repo_name,
        description=f"Generic dock fallback for {repo_name}",
        declared=False,
        manifest_path=None,
        sha256=synth_sha,
        entrypoints=procedures,
        tools=tools,
        permissions=permissions,
        boundaries=boundaries,
        warnings=("Undeclared dock: using generic fallback boundaries and procedures.",),
    )


__all__ = ["load_dock_manifest", "build_generic_dock_manifest"]
