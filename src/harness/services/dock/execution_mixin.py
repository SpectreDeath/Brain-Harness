"""Procedure execution mixin for DefaultDockService."""

from __future__ import annotations

import re
import subprocess
import time
from collections import deque
from pathlib import Path

from .models import (
    DockApprovalDriftError,
    DockBoundaryViolationError,
    DockError,
    DockNotFoundError,
    DockPermissionError,
    DockProcedure,
    DockProcedureCycleError,
    DockRunResult,
    DockStep,
    DockStepResult,
)
from .protocols import logger
from .safety import (
    _build_scrubbed_env,
    check_command_safety,
)


class _DockExecutionMixin:
    """Mixin implementing procedure expansion, boundary gating, and execution."""

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
                f"Procedure '{procedure_name}' not found on dock '{dock_name}'. Available entrypoints: {available}"
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
                raise DockPermissionError(f"Step {idx} contains 'git push' but dock permissions do not allow push.")

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

            env = _build_scrubbed_env(repo_path)

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
            success = code == 0

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


__all__ = ["_DockExecutionMixin"]
