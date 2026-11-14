"""DefaultDockService and ServiceContext resolution factory."""

from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.filesystem_git import DefaultFilesystemGitService

from .execution_mixin import _DockExecutionMixin
from .manifest import (
    build_generic_dock_manifest,
    load_dock_manifest,
)
from .models import (
    DockError,
    DockLinkRecord,
    DockManifest,
    DockNotFoundError,
    DockRunResult,
)
from .protocols import (
    DOCK_SERVICE_KEY,
    DockService,
    logger,
)
from .store import _DockStoreMixin


class DefaultDockService(_DockExecutionMixin, _DockStoreMixin):
    """Default filesystem and Git-guarded Repository Dock implementation."""

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
            self._state_file = (self._workspace_root / ".harness" / "docks.json").resolve()
        self._git_service = DefaultFilesystemGitService()

    @property
    def state_file(self) -> Path:
        return self._state_file

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

            results.append(
                {
                    "dock_name": name,
                    "status": status,
                    "declared": declared,
                    "repo_path": str(repo_path),
                    "transport": data.get("transport", "local"),
                    "approved": approved,
                    "manifest_sha256": live_sha,
                    "approved_sha256": approved_sha,
                    "linked_at": data.get("linked_at", ""),
                }
            )

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


def resolve_dock_service(context: ServiceContext | None = None) -> DockService:
    """Resolve DockService from context or return DefaultDockService."""
    if context is not None:
        svc = context.optional(DOCK_SERVICE_KEY)
        if svc is not None:
            return svc
    return DefaultDockService()


__all__ = ["DefaultDockService", "resolve_dock_service"]
