"""Agent Dock Service — repository-level declarative workstation dock.

Enables agents to plug into a repository, inspect its capabilities, and drive it
via declared procedures, permission gates, and boundary enforcement.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import asdict, dataclass, field
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Protocol, runtime_checkable

import structlog
import yaml

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.filesystem_git import DefaultFilesystemGitService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = structlog.get_logger(__name__)


# -----------------------------------------------------------------------------
# Slotted & Frozen Dataclasses (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class DockPermissions:
    """Capability permissions declared in dock manifest (Rule 12)."""

    read: bool = True
    run: bool = True
    write: bool = False
    push: bool = False


@dataclass(slots=True, frozen=True)
class DockBoundaries:
    """Path and operation boundaries that cannot be crossed (Rule 12)."""

    paths: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class DockStep:
    """Individual sequential execution step within a procedure (Rule 12)."""

    command: str = ""
    workdir: str = "."
    expected_output: str = ""
    call_procedure: str | None = None

    def __post_init__(self) -> None:
        has_cmd = bool(self.command and self.command.strip())
        has_call = bool(self.call_procedure and self.call_procedure.strip())
        if has_cmd == has_call:
            raise ValueError(
                "DockStep must define exactly one of 'command' or 'call_procedure'"
            )


@dataclass(slots=True, frozen=True)
class DockProcedure:
    """Named executable procedure containing sequential steps (Rule 12)."""

    name: str
    description: str = ""
    steps: tuple[DockStep, ...] = ()
    write_path: bool = False


@dataclass(slots=True, frozen=True)
class DockManifest:
    """Repository-level declarative dock specification (Rule 12)."""

    name: str
    description: str
    declared: bool
    manifest_path: str | None
    sha256: str
    entrypoints: dict[str, DockProcedure]
    tools: tuple[str, ...]
    permissions: DockPermissions
    boundaries: DockBoundaries
    warnings: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class DockLinkRecord:
    """Persistent ledger record of a linked agent dock (Rule 12)."""

    dock_name: str
    repo_source: str
    repo_path: str
    transport: str
    declared: bool
    manifest_sha256: str
    approved: bool
    approved_sha256: str
    linked_at: str


@dataclass(slots=True, frozen=True)
class DockStepResult:
    """Result of executing an individual procedure step (Rule 12)."""

    step_index: int
    command: str
    workdir: str
    returncode: int
    stdout: str
    stderr: str
    success: bool
    duration_seconds: float = 0.0
    called_procedure: str | None = None


@dataclass(slots=True, frozen=True)
class DockRunResult:
    """Aggregated outcome of executing a procedure on a dock (Rule 12)."""

    dock_name: str
    procedure_name: str
    success: bool
    steps: tuple[DockStepResult, ...] = ()
    error: str | None = None
    failed_step_index: int | None = None
    failed_step_command: str | None = None
    dry_run: bool = False
    total_duration_seconds: float = 0.0


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class DockError(Exception):
    """Base exception for all agent dock operations."""


class DockManifestError(DockError):
    """Raised when dock manifest is malformed, missing required fields, or unparseable."""

    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = str(path)
        self.reason = reason
        super().__init__(f"Dock manifest error in '{path}': {reason}")


class DockApprovalDriftError(DockError):
    """Raised when live dock.yaml sha256 does not match approved_sha256."""

    def __init__(self, dock_name: str, live_sha: str, approved_sha: str) -> None:
        self.dock_name = dock_name
        self.live_sha = live_sha
        self.approved_sha = approved_sha
        super().__init__(
            f"Approval drift detected for dock '{dock_name}'. "
            f"Live manifest SHA ({live_sha[:12] if live_sha else 'empty'}) differs from approved SHA ({approved_sha[:12] if approved_sha else 'none'}). "
            f"Re-link with 'harness dock link <repo> --approve' to proceed."
        )


class DockBoundaryViolationError(DockError):
    """Raised when a procedure step violates boundary paths, operations, or workdir confinement."""


class DockPermissionError(DockError):
    """Raised when a requested action or procedure exceeds declared/approved permissions."""


class DockProcedureCycleError(DockError):
    """Raised when circular procedure composition is detected."""


class DockNotFoundError(DockError):
    """Raised when a named dock is not found in linked records."""


# -----------------------------------------------------------------------------
# Dangerous Command & Credential Patterns
# -----------------------------------------------------------------------------

_CATASTROPHIC_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+-[rR]f\s+(?:/|/\*|~|\$HOME)", "Filesystem root deletion"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\s+", "Filesystem format"),
    (r"\bdd\s+if=.*of=/dev/[sh]d", "Direct disk overwrite"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb DoS"),
    (r"\b(?:curl|wget|fetch)\b.*\|\s*(?:bash|sh|zsh|python|perl|powershell)", "Unchecked remote script execution"),
    (r"\bgit\s+push\s+.*--force\b", "Prohibited git push --force"),
    (r"\bgit\s+push\s+.*-f\b", "Prohibited git push -f"),
    (r"\bgit\s+reset\s+--hard\b", "Prohibited git reset --hard"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "Prohibited git clean -f"),
    (r"\bshutdown\b", "System shutdown"),
    (r"\breboot\b", "System reboot"),
]

_CREDENTIAL_ACCESS_PATTERNS: list[tuple[str, str]] = [
    (r"\b(?:cat|type|more|less|head|tail)\s+.*\.env\b", "Attempted .env file read"),
    (r"\b(?:cat|type)\s+.*\.git-credentials\b", "Attempted .git-credentials read"),
    (r"\bprintenv\b", "Attempted environment variable dump"),
    (r"\b(?:get-childitem|gci)\s+env:\b", "Attempted PowerShell env dump"),
]


def check_command_safety(
    command: str,
    boundaries: DockBoundaries,
) -> tuple[bool, str]:
    """Check command string against catastrophic patterns, credentials, and boundaries."""
    clean_cmd = command.strip()
    if not clean_cmd:
        return True, ""

    # 1. Catastrophic patterns
    for pat, desc in _CATASTROPHIC_PATTERNS:
        if re.search(pat, clean_cmd, re.IGNORECASE):
            return False, f"Triggered catastrophic security rule: {desc}"

    # 2. Credential access patterns
    for pat, desc in _CREDENTIAL_ACCESS_PATTERNS:
        if re.search(pat, clean_cmd, re.IGNORECASE):
            return False, f"Prohibited credential inspection: {desc}"

    # 3. Manifest operation boundaries
    for op in boundaries.operations:
        op_clean = op.strip()
        if op_clean and op_clean.lower() in clean_cmd.lower():
            return False, f"Command matches prohibited boundary operation: '{op_clean}'"

    # 4. Manifest path boundaries
    for bp in boundaries.paths:
        bp_clean = bp.strip().replace("\\", "/").rstrip("/")
        if not bp_clean:
            continue
        # Check if boundary path token appears in command
        cmd_normalized = clean_cmd.replace("\\", "/")
        if re.search(rf"(?:^|[\s\"'/]){re.escape(bp_clean)}(?:$|[\s\"'/])", cmd_normalized, re.IGNORECASE):
            return False, f"Command references prohibited boundary path: '{bp_clean}'"

    return True, ""


# -----------------------------------------------------------------------------
# Manifest Loading & Synthesis (Rule 33)
# -----------------------------------------------------------------------------


def load_dock_manifest(repo_root: Path) -> DockManifest:
    """Load and parse repository dock manifest (pure read, zero code execution)."""
    manifest_file = repo_root / "dock.yaml"
    warnings: list[str] = []

    # Check for mislocated manifest in .harness/dock.yaml
    alt_file = repo_root / ".harness" / "dock.yaml"
    if not manifest_file.exists():
        if alt_file.exists():
            warnings.append(
                "Found .harness/dock.yaml, but only repo-root 'dock.yaml' is supported."
            )
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


# -----------------------------------------------------------------------------
# DockService Protocol & Implementation (Rule 1, Rule 2, Rule 49)
# -----------------------------------------------------------------------------


@runtime_checkable
class DockService(Protocol):
    """Protocol for Agent Dock inspection, linking, and procedure execution."""

    def inspect(self, repo_or_path: str | Path) -> DockManifest:
        """Inspect repository dock manifest without linking or state changes."""
        ...

    def link(
        self,
        repo_or_path: str | Path,
        name: str | None = None,
        approve: bool = False,
    ) -> DockLinkRecord:
        """Link an agent dock and record approval digest."""
        ...

    def list_docks(self) -> list[dict[str, Any]]:
        """List all linked docks and evaluate approval drift."""
        ...

    def tools(self, dock_name: str) -> list[str]:
        """List tools exposed by the dock."""
        ...

    async def run_async(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Execute declared procedure on a linked dock asynchronously."""
        ...

    def run(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Synchronous wrapper for procedure execution."""
        ...


DOCK_SERVICE_KEY: ServiceKey[DockService] = ServiceKey("service.dock")


class DefaultDockService:
    """Standard micro-kernel implementation of DockService."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        state_file: Path | None = None,
    ) -> None:
        self._workspace_root = (workspace_root or Path.cwd()).resolve()
        env_state = os.environ.get("HARNESS_DOCKS_STATE_FILE")
        if state_file is not None:
            self._state_file = Path(state_file).resolve()
        elif env_state:
            self._state_file = Path(env_state).resolve()
        else:
            self._state_file = (
                self._workspace_root / ".harness" / "docks.json"
            ).resolve()
        self._git_service = DefaultFilesystemGitService()

    @property
    def state_file(self) -> Path:
        return self._state_file

    def _load_records(self) -> dict[str, dict[str, Any]]:
        if not self._state_file.exists():
            return {}
        try:
            return json.loads(self._state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_records(self, records: dict[str, dict[str, Any]]) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def _resolve_repo_path(self, repo_or_path: str | Path) -> tuple[Path, str, str]:
        """Resolve local path or remote repository. Returns (path, transport, source)."""
        raw_str = str(repo_or_path).strip()
        candidate_path = Path(raw_str).resolve()
        if candidate_path.is_dir():
            return candidate_path, "local", str(candidate_path)

        # Parse via universal ingestion resolver
        from harness.ingestion.providers import parse_repo_source

        parsed = parse_repo_source(raw_str)
        if parsed is None:
            # Check relative to workspace root
            rel_candidate = (self._workspace_root / raw_str).resolve()
            if rel_candidate.is_dir():
                return rel_candidate, "local", str(rel_candidate)
            raise DockError(f"Cannot resolve repository source or directory '{raw_str}'")

        target_dir = Path.home() / ".harness" / "docks" / f"{parsed.owner}__{parsed.repo}"
        clone_url = parsed.clone_url or f"https://github.com/{parsed.owner}/{parsed.repo}.git"

        if not target_dir.exists():
            git_bin = shutil.which("git")
            if not git_bin:
                raise DockError("git executable not found on PATH for remote dock cloning")
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            res = subprocess.run(
                [git_bin, "clone", "--depth", "1", clone_url, str(target_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                raise DockError(f"Failed to clone remote dock repository: {res.stderr}")

        return target_dir, "git", clone_url

    def inspect(self, repo_or_path: str | Path) -> DockManifest:
        """Inspect dock manifest without state modification."""
        repo_path, _, _ = self._resolve_repo_path(repo_or_path)
        manifest_file = repo_path / "dock.yaml"
        if manifest_file.exists():
            return load_dock_manifest(repo_path)
        return build_generic_dock_manifest(repo_path)

    def link(
        self,
        repo_or_path: str | Path,
        name: str | None = None,
        approve: bool = False,
    ) -> DockLinkRecord:
        """Link repository dock and record approval digest."""
        repo_path, transport, source = self._resolve_repo_path(repo_or_path)
        manifest = self.inspect(repo_path)

        dock_name = (name or manifest.name).strip()
        live_sha = manifest.sha256
        approved_sha = live_sha if approve else ""

        record = DockLinkRecord(
            dock_name=dock_name,
            repo_source=source,
            repo_path=str(repo_path),
            transport=transport,
            declared=manifest.declared,
            manifest_sha256=live_sha,
            approved=approve,
            approved_sha256=approved_sha,
            linked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        records = self._load_records()
        records[dock_name] = asdict(record)
        self._save_records(records)
        return record

    def list_docks(self) -> list[dict[str, Any]]:
        """List all linked docks and evaluate live approval status."""
        records = self._load_records()
        results: list[dict[str, Any]] = []

        for name, data in records.items():
            repo_path = Path(data.get("repo_path", ""))
            approved = bool(data.get("approved", False))
            approved_sha = data.get("approved_sha256", "")

            # Check live manifest (inspect computes live_sha for both declared and generic docks)
            try:
                manifest = self.inspect(repo_path)
                live_sha = manifest.sha256
                declared = manifest.declared
            except Exception:
                live_sha = ""
                declared = bool(data.get("declared", False))

            status = "unapproved"
            if approved:
                if live_sha and live_sha == approved_sha:
                    status = "approved"
                else:
                    status = "manifest_changed"

            results.append({
                "dock_name": name,
                "status": status,
                "declared": declared,
                "repo_path": str(repo_path),
                "transport": data.get("transport", "local"),
                "approved": approved,
                "manifest_sha256": live_sha,
                "approved_sha256": approved_sha,
                "linked_at": data.get("linked_at", ""),
            })

        return sorted(results, key=lambda x: x["dock_name"])

    def tools(self, dock_name: str) -> list[str]:
        """List tools declared or synthesized for dock."""
        records = self._load_records()
        if dock_name not in records:
            raise DockNotFoundError(f"Dock '{dock_name}' is not linked.")

        repo_path = Path(records[dock_name]["repo_path"])
        manifest = self.inspect(repo_path)
        return list(manifest.tools)

    def run(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Synchronous procedure execution."""
        return self._run_procedure(dock_name, procedure_name, dry_run=dry_run)

    async def run_async(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Asynchronous procedure execution."""
        return self._run_procedure(dock_name, procedure_name, dry_run=dry_run)

    def _run_procedure(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Execute declared procedure on a linked dock."""
        start_time = time.monotonic()
        records = self._load_records()
        if dock_name not in records:
            raise DockNotFoundError(f"Dock '{dock_name}' is not linked. Run 'harness dock link' first.")

        dock_data = records[dock_name]
        repo_path = Path(dock_data["repo_path"]).resolve()
        if not repo_path.is_dir():
            raise DockError(f"Dock directory '{repo_path}' does not exist.")

        manifest = self.inspect(repo_path)
        approved = bool(dock_data.get("approved", False))
        approved_sha = dock_data.get("approved_sha256", "")

        # 1. Approval Gate (Uniform drift protection across declared and generic docks)
        if not approved:
            raise DockApprovalDriftError(dock_name, manifest.sha256, "")
        if manifest.sha256 != approved_sha:
            raise DockApprovalDriftError(dock_name, manifest.sha256, approved_sha)

        # 2. Permission Gate (Run)
        if not manifest.permissions.run:
            raise DockPermissionError(f"Dock '{dock_name}' permissions do not permit running procedures.")

        if procedure_name not in manifest.entrypoints:
            available = ", ".join(manifest.entrypoints.keys()) or "none"
            raise DockError(
                f"Procedure '{procedure_name}' not found on dock '{dock_name}'. "
                f"Available entrypoints: {available}"
            )

        target_proc = manifest.entrypoints[procedure_name]

        # 3. Permission Gate (Write)
        if target_proc.write_path and not manifest.permissions.write:
            raise DockPermissionError(
                f"Procedure '{procedure_name}' is marked write_path=true but dock permissions do not allow write."
            )

        # Check git clean state before starting write_path procedure (Rule 8)
        initial_clean = False
        if target_proc.write_path and (repo_path / ".git").is_dir():
            status_res = self._git_service.git_status(str(repo_path))
            if status_res.status == "ok" and not status_res.dirty:
                initial_clean = True

        # Expand steps handling procedure composition (cycle-safe, max depth 5)
        flattened_steps: list[tuple[int, DockStep, str | None]] = []
        call_stack: list[str] = [procedure_name]

        def _expand_proc(proc: DockProcedure, parent_name: str | None = None) -> None:
            for s in proc.steps:
                if s.call_procedure:
                    sub_name = s.call_procedure.strip()
                    if sub_name in call_stack:
                        cycle_path = " -> ".join(call_stack + [sub_name])
                        raise DockProcedureCycleError(f"Procedure cycle detected: {cycle_path}")
                    if len(call_stack) >= 5:
                        raise DockProcedureCycleError(
                            f"Procedure call recursion exceeded max depth 5: {' -> '.join(call_stack)}"
                        )
                    if sub_name not in manifest.entrypoints:
                        raise DockError(f"Composed procedure '{sub_name}' not declared in manifest.")

                    sub_proc = manifest.entrypoints[sub_name]
                    if sub_proc.write_path and not manifest.permissions.write:
                        raise DockPermissionError(
                            f"Composed procedure '{sub_name}' is marked write_path=true but dock permissions do not allow write."
                        )
                    call_stack.append(sub_name)
                    _expand_proc(sub_proc, parent_name=sub_name)
                    call_stack.pop()
                else:
                    flattened_steps.append((len(flattened_steps) + 1, s, parent_name))

        _expand_proc(target_proc)

        # Pre-validate all steps against boundaries before executing any step
        for idx, step, _ in flattened_steps:
            # Workdir confinement
            step_workdir = (repo_path / step.workdir).resolve()
            if not step_workdir.is_relative_to(repo_path):
                raise DockBoundaryViolationError(
                    f"Step {idx} working directory '{step.workdir}' escapes repository root '{repo_path}'"
                )

            # Command safety & boundary checks
            safe, reason = check_command_safety(step.command, manifest.boundaries)
            if not safe:
                raise DockBoundaryViolationError(f"Step {idx} boundary violation: {reason}")

            # Check push permission if git push present
            if re.search(r"\bgit\s+push\b", step.command) and not manifest.permissions.push:
                raise DockPermissionError(
                    f"Step {idx} contains 'git push' but dock permissions do not allow push."
                )

        step_results: list[DockStepResult] = []

        # Execute steps sequentially
        for idx, step, called_proc in flattened_steps:
            step_workdir = (repo_path / step.workdir).resolve()
            step_start = time.monotonic()

            if dry_run:
                step_results.append(
                    DockStepResult(
                        step_index=idx,
                        command=step.command,
                        workdir=str(step.workdir),
                        returncode=0,
                        stdout=f"[dry-run] Would execute: {step.command}",
                        stderr="",
                        success=True,
                        duration_seconds=0.0,
                        called_procedure=called_proc,
                    )
                )
                continue

            # Prepare scrubbed environment (Rule 15 & Rule 23)
            env = dict(os.environ)
            for k in list(env.keys()):
                ku = k.upper()
                if (
                    "TOKEN" in ku
                    or "SECRET" in ku
                    or "PASSWORD" in ku
                    or ("KEY" in ku and "PATH" not in ku)
                ):
                    env.pop(k, None)
            env["PYTHONIOENCODING"] = "utf-8"

            # Execute subprocess with Rule 14 & Rule 53 guarantees
            stderr_ring: deque[str] = deque(maxlen=50)
            try:
                sub_res = subprocess.run(
                    step.command,
                    shell=True,
                    cwd=str(step_workdir),
                    capture_output=True,
                    text=True,
                    env=env,
                    check=False,
                )
                code = sub_res.returncode
                stdout_str = sub_res.stdout
                stderr_str = sub_res.stderr
                for line in stderr_str.splitlines(keepends=True):
                    stderr_ring.append(line)
            except Exception as exc:
                code = 1
                stdout_str = ""
                stderr_str = f"Subprocess execution error: {exc}"
                stderr_ring.append(stderr_str)

            duration = time.monotonic() - step_start
            success = (code == 0)

            # Check expected output if specified
            if success and step.expected_output:
                if step.expected_output not in stdout_str:
                    success = False
                    code = 1
                    stderr_str += f"\nExpected output '{step.expected_output}' not found in stdout."

            step_res = DockStepResult(
                step_index=idx,
                command=step.command,
                workdir=str(step.workdir),
                returncode=code,
                stdout=stdout_str,
                stderr=stderr_str,
                success=success,
                duration_seconds=duration,
                called_procedure=called_proc,
            )
            step_results.append(step_res)

            if not success:
                # Rule 8: Rollback transaction if write_path step failed on clean repo
                if initial_clean and (repo_path / ".git").is_dir():
                    logger.warning("Rolling back workspace changes after failed step", step_index=idx)
                    self._git_service.rollback_transaction(str(repo_path))

                total_dur = time.monotonic() - start_time
                return DockRunResult(
                    dock_name=dock_name,
                    procedure_name=procedure_name,
                    success=False,
                    steps=tuple(step_results),
                    error=f"Step {idx} ('{step.command}') failed with code {code}: {stderr_str.strip()[:200]}",
                    failed_step_index=idx,
                    failed_step_command=step.command,
                    dry_run=dry_run,
                    total_duration_seconds=total_dur,
                )

        total_dur = time.monotonic() - start_time
        return DockRunResult(
            dock_name=dock_name,
            procedure_name=procedure_name,
            success=True,
            steps=tuple(step_results),
            dry_run=dry_run,
            total_duration_seconds=total_dur,
        )


def resolve_dock_service(context: ServiceContext | None = None) -> DockService:
    """Resolve DockService from context or return DefaultDockService."""
    if context is not None:
        svc = context.optional(DOCK_SERVICE_KEY)
        if svc is not None:
            return svc
    return DefaultDockService()


__all__ = [
    "DOCK_SERVICE_KEY",
    "DockApprovalDriftError",
    "DockBoundaries",
    "DockBoundaryViolationError",
    "DockError",
    "DockLinkRecord",
    "DockManifest",
    "DockManifestError",
    "DockNotFoundError",
    "DockPermissionError",
    "DockPermissions",
    "DockProcedure",
    "DockProcedureCycleError",
    "DockRunResult",
    "DockService",
    "DockStep",
    "DockStepResult",
    "DefaultDockService",
    "build_generic_dock_manifest",
    "check_command_safety",
    "load_dock_manifest",
    "resolve_dock_service",
]
