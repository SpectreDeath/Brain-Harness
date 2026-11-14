"""KI emission and child ServiceContext disposal helpers for Harness Spawner."""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext
from harness.services.recursive_harnessing.library import ExperienceLibrary

from .models import (
    SpawnLifecycleState,
    SpawnSpec,
    SpawnTrialResult,
    SpawnedHarnessRecord,
    _RuntimeHandle,
)


logger = structlog.get_logger(__name__)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower()).strip("-")
    return cleaned or "spawn"


def _write_ki_dual_file(
    ki_dir: Path,
    *,
    ki_id: str,
    title: str,
    domain: str,
    spawn_id: str,
    task_id: str,
    proposal_id: str,
    cue: str,
    lesson: str,
    evidence: str,
    why: str,
    status: str,
) -> None:
    """Write a canonical dual-file Knowledge Item directory (Rule 40)."""
    ki_dir.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()
    metadata = {
        "id": ki_id,
        "title": title,
        "summary": f"{cue} -> {lesson}",
        "domain": domain,
        "status": status,
        "tags": ["spawn", _slugify(domain)],
        "created_at": now_iso,
        "updated_at": now_iso,
        "source_spawn_id": spawn_id,
        "source_proposal_id": proposal_id,
        "task_id": task_id,
        "isnad_claim": {
            "cue": cue,
            "lesson": lesson,
            "evidence": evidence,
        },
    }
    (ki_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    md_lines = [
        f"# {title}",
        "",
        f"- **KI ID**: `{ki_id}`",
        f"- **Domain**: `{domain}`",
        f"- **Status**: `{status}`",
        f"- **Source Spawn**: `{spawn_id}` (`{task_id}`)",
        f"- **Proposal ID**: `{proposal_id}`",
        "",
        "## Transferable Claim",
        f"- **Cue**: {cue}",
        f"- **Lesson**: {lesson}",
        f"- **Evidence**: {evidence}",
    ]
    if why.strip():
        md_lines.extend(["", "## Rationale", why.strip()])
    (ki_dir / "summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


async def _dispose_contexts_async(contexts: tuple[ServiceContext, ...]) -> None:
    for ctx in reversed(contexts):
        try:
            await ctx.dispose()
        except Exception as exc:
            logger.warning("child_context_dispose_error", error=str(exc))


def _dispose_contexts_sync(contexts: tuple[ServiceContext, ...]) -> None:
    """Dispose a child context stack cleanly from sync or async call sites."""
    if not contexts:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_dispose_contexts_async(contexts))
        return

    if loop.is_running():
        # Clear local registrations & run sync inverses immediately, and schedule full async dispose.
        for ctx in reversed(contexts):
            with ctx._mutation_lock:
                stack = list(ctx._dispose_stack)
                ctx._dispose_stack.clear()
                async_inverses = []
                for inv in reversed(stack):
                    try:
                        if inspect.iscoroutinefunction(inv):
                            async_inverses.append(inv)
                        else:
                            res = inv()
                            if inspect.isawaitable(res):
                                async_inverses.append(lambda r=res: r)
                    except Exception as exc:
                        logger.warning("sync_context_inverse_error", error=str(exc))
            if async_inverses:

                async def _drain(items: list[Any] = async_inverses) -> None:
                    for item in items:
                        try:
                            res = item()
                            if inspect.isawaitable(res):
                                await res
                        except Exception:
                            pass

                loop.create_task(_drain())


def _build_spawn_record_and_handle(
    *,
    spawn_id: str,
    spec: SpawnSpec,
    state: SpawnLifecycleState,
    child_depth: int,
    effective_max_depth: int,
    session_id: str,
    node_id: str,
    fingerprint: str,
    child_save_dir: Path,
    probe_tokens: int,
    has_probe: bool,
    trial: SpawnTrialResult,
    error: str,
    child_scopes: tuple[ServiceContext, ...],
    child_library: ExperienceLibrary,
    disposed: bool,
) -> tuple[SpawnedHarnessRecord, _RuntimeHandle]:
    """Build paired SpawnedHarnessRecord and _RuntimeHandle cleanly without duplication."""
    rec = SpawnedHarnessRecord(
        spawn_id=spawn_id,
        name=spec.name,
        domain=spec.domain,
        task=spec.task,
        state=state,
        depth=child_depth,
        max_spawn_depth=effective_max_depth,
        parent_spawn_id=spec.parent_spawn_id,
        parent_session_id=spec.parent_session_id,
        session_id=session_id,
        node_id=node_id,
        fingerprint=fingerprint,
        save_dir=str(child_save_dir),
        tokens_used=probe_tokens,
        rollouts_used=1 if has_probe else 0,
        sessions_used=1,
        budget=spec.budget,
        lifetime=spec.lifetime,
        trial=trial,
        error=error,
    )
    handle = _RuntimeHandle(
        contexts=child_scopes,
        library=child_library,
        surface=spec.surface,
        tree=dict(spec.tree),
        disposed=disposed,
    )
    return rec, handle


__all__ = [
    "logger",
    "_slugify",
    "_write_ki_dual_file",
    "_dispose_contexts_async",
    "_dispose_contexts_sync",
    "_build_spawn_record_and_handle",
]
