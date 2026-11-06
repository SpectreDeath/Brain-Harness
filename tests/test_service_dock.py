"""Unit and contract tests for Agent Dock service, models, and boundaries."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import pytest

from harness.services.dock import (
    DefaultDockService,
    DockApprovalDriftError,
    DockBoundaries,
    DockBoundaryViolationError,
    DockError,
    DockLinkRecord,
    DockManifest,
    DockManifestError,
    DockNotFoundError,
    DockPermissionError,
    DockPermissions,
    DockProcedure,
    DockProcedureCycleError,
    DockRunResult,
    DockStep,
    DockStepResult,
    build_generic_dock_manifest,
    check_command_safety,
    load_dock_manifest,
)


def test_slotted_frozen_dataclasses_immutability() -> None:
    """Assert immutability of slotted/frozen dock models per Rule 12 & Rule 43."""
    perms = DockPermissions(read=True, run=True, write=False, push=False)
    with pytest.raises((AttributeError, TypeError)):
        perms.write = True  # type: ignore

    bounds = DockBoundaries(paths=(".git/",), operations=("git push --force",))
    with pytest.raises((AttributeError, TypeError)):
        bounds.paths = ()  # type: ignore

    step = DockStep(command="echo hello", workdir=".")
    with pytest.raises((AttributeError, TypeError)):
        step.command = "other"  # type: ignore

    proc = DockProcedure(name="p", steps=(step,))
    with pytest.raises((AttributeError, TypeError)):
        proc.name = "other"  # type: ignore

    manifest = DockManifest(
        name="test",
        description="desc",
        declared=True,
        manifest_path=None,
        sha256="abc",
        entrypoints={"p": proc},
        tools=("tool1",),
        permissions=perms,
        boundaries=bounds,
    )
    with pytest.raises((AttributeError, TypeError)):
        manifest.name = "changed"  # type: ignore


def test_dock_step_validation() -> None:
    """DockStep must define exactly one of 'command' or 'call_procedure'."""
    with pytest.raises(ValueError, match="exactly one of"):
        DockStep()  # Neither

    with pytest.raises(ValueError, match="exactly one of"):
        DockStep(command="echo hi", call_procedure="other")  # Both

    s1 = DockStep(command="echo hi")
    assert s1.command == "echo hi"
    assert s1.call_procedure is None

    s2 = DockStep(call_procedure="other")
    assert s2.call_procedure == "other"
    assert s2.command == ""


def test_load_real_dock_manifest() -> None:
    """Test loading repo-root dock.yaml for brain-harness."""
    repo_root = Path(__file__).resolve().parent.parent
    manifest = load_dock_manifest(repo_root)

    assert manifest.declared is True
    assert manifest.name == "brain-harness"
    assert len(manifest.sha256) == 64
    assert manifest.permissions.read is True
    assert manifest.permissions.run is True
    assert ".git/" in manifest.boundaries.paths
    assert "git push --force" in manifest.boundaries.operations
    assert "vault-stats" in manifest.entrypoints
    assert "verify-core" in manifest.entrypoints
    assert "sync-context" in manifest.entrypoints
    assert manifest.entrypoints["sync-context"].write_path is True
    vault_step = manifest.entrypoints["vault-stats"].steps[0]
    assert vault_step.command == "python -m harness.cli knowledge stats"
    assert vault_step.expected_output == "Knowledge Graph Census Statistics"
    sync_step = manifest.entrypoints["sync-context"].steps[0]
    assert sync_step.command == "python -m harness.cli context lint --root ."


def test_load_dock_manifest_malformed(tmp_path: Path) -> None:
    """Malformed YAML raises DockManifestError."""
    bad_yaml = tmp_path / "dock.yaml"
    bad_yaml.write_text("name: test\n  bad_indent: [", encoding="utf-8")
    with pytest.raises(DockManifestError, match="Malformed YAML"):
        load_dock_manifest(tmp_path)


def test_load_dock_manifest_missing_required(tmp_path: Path) -> None:
    """Missing name or description raises DockManifestError."""
    f = tmp_path / "dock.yaml"
    f.write_text("description: only desc", encoding="utf-8")
    with pytest.raises(DockManifestError, match="Missing required field 'name'"):
        load_dock_manifest(tmp_path)

    f.write_text("name: only name", encoding="utf-8")
    with pytest.raises(DockManifestError, match="Missing required field 'description'"):
        load_dock_manifest(tmp_path)


def test_generic_dock_manifest_synthesis(tmp_path: Path) -> None:
    """Generic dock fallback provides safe defaults and auto-detected procedures."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='toy'", encoding="utf-8")
    manifest = build_generic_dock_manifest(tmp_path)

    assert manifest.declared is False
    assert len(manifest.sha256) == 64
    assert manifest.sha256 != ""
    assert manifest.permissions.read is True
    assert manifest.permissions.run is True
    assert manifest.permissions.write is False
    assert manifest.permissions.push is False
    assert "test" in manifest.entrypoints
    assert "status" in manifest.entrypoints
    assert ".git/" in manifest.boundaries.paths


def test_check_command_safety() -> None:
    """Verify danger patterns and boundary violations."""
    bounds = DockBoundaries(
        paths=(".git/", ".env", "src/harness/ui/static/"),
        operations=("git push --force", "git reset --hard", "git clean -fd"),
    )

    # Safe commands
    safe, _ = check_command_safety("pytest -q", bounds)
    assert safe is True

    safe, _ = check_command_safety("git status --short", bounds)
    assert safe is True

    # Catastrophic deletion
    safe, msg = check_command_safety("rm -rf /", bounds)
    assert safe is False
    assert "Catastrophic" in msg or "deletion" in msg

    # Destructive git
    safe, msg = check_command_safety("git push --force origin main", bounds)
    assert safe is False

    safe, msg = check_command_safety("git reset --hard HEAD~1", bounds)
    assert safe is False

    # Prohibited boundary paths
    safe, msg = check_command_safety("cp foo .env", bounds)
    assert safe is False
    assert ".env" in msg

    safe, msg = check_command_safety("cat .git/config", bounds)
    assert safe is False

    # Credential dump
    safe, msg = check_command_safety("printenv", bounds)
    assert safe is False
    assert "credential" in msg or "environment" in msg


def test_dock_service_link_and_drift(tmp_path: Path) -> None:
    """Test link record creation, approval status, and approval drift detection."""
    dock_yaml = tmp_path / "dock.yaml"
    dock_yaml.write_text(
        "name: toy-dock\ndescription: Toy repo\nentrypoints:\n  echo:\n    steps:\n      - command: echo 123\n",
        encoding="utf-8",
    )

    state_file = tmp_path / "docks_state.json"
    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)

    # 1. Link without approve
    rec_unapproved = service.link(tmp_path, name="toy", approve=False)
    assert rec_unapproved.approved is False
    assert rec_unapproved.approved_sha256 == ""

    # Attempt to run while unapproved raises DockApprovalDriftError
    with pytest.raises(DockApprovalDriftError):
        service.run("toy", "echo")

    # 2. Link with approve
    rec_approved = service.link(tmp_path, name="toy", approve=True)
    assert rec_approved.approved is True
    assert len(rec_approved.approved_sha256) == 64

    # Run works
    res = service.run("toy", "echo")
    assert res.success is True
    assert "123" in res.steps[0].stdout

    # 3. Modify dock.yaml -> drift detected
    dock_yaml.write_text(
        "name: toy-dock\ndescription: Toy repo modified\nentrypoints:\n  echo:\n    steps:\n      - command: echo 456\n",
        encoding="utf-8",
    )
    with pytest.raises(DockApprovalDriftError, match="Approval drift detected"):
        service.run("toy", "echo")


def test_dock_service_workdir_confinement(tmp_path: Path) -> None:
    """Escaping repo root via ../ is prohibited."""
    dock_yaml = tmp_path / "dock.yaml"
    dock_yaml.write_text(
        "name: escape-dock\ndescription: Escape test\nentrypoints:\n  escape:\n    steps:\n      - command: dir\n        workdir: ../../\n",
        encoding="utf-8",
    )
    state_file = tmp_path / "docks_state.json"
    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(tmp_path, name="escape", approve=True)

    with pytest.raises(DockBoundaryViolationError, match="escapes repository root"):
        service.run("escape", "escape")


def test_dock_service_permission_enforcement(tmp_path: Path) -> None:
    """write_path requires permissions.write=True, and push requires permissions.push=True."""
    dock_yaml = tmp_path / "dock.yaml"
    dock_yaml.write_text(
        "name: perm-dock\ndescription: Perm test\npermissions:\n  write: false\n  push: false\nentrypoints:\n  write-op:\n    write_path: true\n    steps:\n      - command: echo write\n  push-op:\n    steps:\n      - command: git push origin main\n",
        encoding="utf-8",
    )
    state_file = tmp_path / "docks_state.json"
    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(tmp_path, name="perm", approve=True)

    with pytest.raises(DockPermissionError, match="do not allow write"):
        service.run("perm", "write-op")

    with pytest.raises(DockPermissionError, match="do not allow push"):
        service.run("perm", "push-op")


def test_dock_service_procedure_composition_and_cycle(tmp_path: Path) -> None:
    """Procedure composition via call_procedure, with cycle detection."""
    dock_yaml = tmp_path / "dock.yaml"
    dock_yaml.write_text(
        """name: compose-dock
description: Composition test
entrypoints:
  step-a:
    steps:
      - command: echo A
  step-b:
    steps:
      - call_procedure: step-a
      - command: echo B
  cycle-a:
    steps:
      - call_procedure: cycle-b
  cycle-b:
    steps:
      - call_procedure: cycle-a
""",
        encoding="utf-8",
    )
    state_file = tmp_path / "docks_state.json"
    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(tmp_path, name="compose", approve=True)

    # Valid composition
    res = service.run("compose", "step-b")
    assert res.success is True
    assert len(res.steps) == 2
    assert "A" in res.steps[0].stdout
    assert "B" in res.steps[1].stdout
    assert res.steps[0].called_procedure == "step-a"

    # Cycle detection
    with pytest.raises(DockProcedureCycleError, match="cycle detected"):
        service.run("compose", "cycle-a")


def test_dock_service_dry_run(tmp_path: Path) -> None:
    """Dry run reports planned steps without executing them."""
    dock_yaml = tmp_path / "dock.yaml"
    dock_yaml.write_text(
        "name: dry-dock\ndescription: Dry run\nentrypoints:\n  hello:\n    steps:\n      - command: echo hello\n",
        encoding="utf-8",
    )
    state_file = tmp_path / "docks_state.json"
    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(tmp_path, name="dry", approve=True)

    res = service.run("dry", "hello", dry_run=True)
    assert res.success is True
    assert res.dry_run is True
    assert "[dry-run]" in res.steps[0].stdout


def test_generic_dock_drift_protection(tmp_path: Path) -> None:
    """Generic dock fallback computes deterministic SHA and catches structural drift."""
    toy_repo = tmp_path / "generic_repo"
    toy_repo.mkdir()
    state_file = tmp_path / "test_docks_state.json"
    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)

    # 1. Inspect without test files -> only status procedure
    m1 = service.inspect(toy_repo)
    assert "test" not in m1.entrypoints
    assert "status" in m1.entrypoints
    sha1 = m1.sha256
    assert len(sha1) == 64

    # Link with approve
    rec = service.link(toy_repo, name="gen-dock", approve=True)
    assert rec.approved_sha256 == sha1

    # 2. Add pyproject.toml -> structural drift in generic procedures (adds test procedure)
    (toy_repo / "pyproject.toml").write_text("[project]\nname='toy'\n", encoding="utf-8")
    m2 = service.inspect(toy_repo)
    assert "test" in m2.entrypoints
    sha2 = m2.sha256
    assert sha1 != sha2

    # list_docks must detect manifest_changed on generic dock
    docks = service.list_docks()
    gen_docks = [d for d in docks if d["dock_name"] == "gen-dock"]
    assert len(gen_docks) == 1
    assert gen_docks[0]["status"] == "manifest_changed"

    # Execution blocked by drift error
    with pytest.raises(DockApprovalDriftError):
        service.run("gen-dock", "status")
