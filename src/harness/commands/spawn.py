"""`harness spawn` -- headless child-harness spawning, supervision, and reviewed adoption (Rule 10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from harness.services.harness_spawner import (
    DEFAULT_K,
    DEFAULT_MAX_ROLLOUTS,
    DEFAULT_MAX_SESSIONS,
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    HARD_MAX_SPAWN_DEPTH,
    HarnessSpawnerEngine,
    SpawnBudgetSpec,
    SpawnLifecycleState,
    SpawnSpec,
)
from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.models import BRAIN_SURFACE

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")


def _emit(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


@click.group("spawn")
def spawn_group() -> None:
    """Spawn, inspect, retire, and adopt learnings from isolated child harnesses."""


@spawn_group.command("run")
@click.option("--name", required=True, help="Short identifier for the spawned child harness.")
@click.option("--domain", required=True, help="Domain partition for isolated ExperienceLibrary storage.")
@click.option("--task", default="spawned_harness", show_default=True, help="Assigned task summary.")
@click.option(
    "--harness-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Optional harness directory to read initial editable tree from.",
)
@click.option(
    "--max-tokens",
    type=click.IntRange(min=1),
    default=DEFAULT_MAX_TOKENS,
    show_default=True,
    help="Token budget ceiling.",
)
@click.option(
    "--k",
    type=click.IntRange(min=1),
    default=DEFAULT_K,
    show_default=True,
    help="Recursion scale parameter k (R=4k rollouts, P=3k sessions).",
)
@click.option(
    "--max-depth",
    type=click.IntRange(min=1, max=HARD_MAX_SPAWN_DEPTH),
    default=DEFAULT_MAX_SPAWN_DEPTH,
    show_default=True,
    help="Maximum recursion depth allowed (hard cap 3).",
)
@click.option(
    "--depth",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="Caller depth (0 for Prime).",
)
@click.option("--parent-spawn-id", default=None, help="Optional parent spawn ID when nesting.")
@click.option(
    "--lifetime",
    type=click.Choice(["task", "persistent"]),
    default="persistent",
    show_default=True,
    help="Child lifetime policy.",
)
@click.option(
    "--save-dir",
    type=click.Path(path_type=Path),
    default=Path(".harness/spawns"),
    show_default=True,
    help="Root directory for child harness artifacts and registry state.",
)
def run_cmd(
    name: str,
    domain: str,
    task: str,
    harness_dir: Path | None,
    max_tokens: int,
    k: int,
    max_depth: int,
    depth: int,
    parent_spawn_id: str | None,
    lifetime: str,
    save_dir: Path,
) -> None:
    """Validate, probe-gate, and spawn an isolated child harness."""
    if harness_dir is not None:
        tree = surface_ops.read_tree(BRAIN_SURFACE, harness_dir)
    else:
        tree = {
            "AGENTS.md": f"# Spawned Harness: {name}\n\nDomain: {domain}\nTask: {task}\n"
        }

    engine = HarnessSpawnerEngine(state_file=save_dir / "registry.json")
    try:
        spec = SpawnSpec(
            name=name,
            domain=domain,
            task=task,
            tree=tree,
            budget=SpawnBudgetSpec(
                max_tokens=max_tokens,
                k=k,
                max_rollouts=DEFAULT_MAX_ROLLOUTS * k,
                max_sessions=DEFAULT_MAX_SESSIONS * k,
            ),
            save_dir=save_dir,
            parent_spawn_id=parent_spawn_id,
            current_depth=depth,
            max_spawn_depth=max_depth,
            lifetime=lifetime,
        )
        rec = engine.spawn(spec)
    except (ValueError, KeyError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc

    export = engine.export_dag()
    payload = rec.to_dict()
    payload["ascii_tree"] = export.formatted_ascii_tree
    _emit(payload)
    if rec.state == SpawnLifecycleState.FAILED:
        raise SystemExit(1)


@spawn_group.command("list")
@click.option(
    "--save-dir",
    type=click.Path(path_type=Path),
    default=Path(".harness/spawns"),
    show_default=True,
    help="Root directory containing registry state.",
)
@click.option(
    "--state",
    type=click.Choice([s.value for s in SpawnLifecycleState], case_sensitive=False),
    default=None,
    help="Filter records by lifecycle state.",
)
def list_cmd(save_dir: Path, state: str | None) -> None:
    """List registered child harnesses and their lifecycle state / budget usage."""
    engine = HarnessSpawnerEngine(state_file=save_dir / "registry.json")
    filter_state = SpawnLifecycleState(state.upper()) if state else None
    records = engine.list_spawns(state=filter_state)
    _emit({"count": len(records), "spawns": [r.to_dict() for r in records]})


@spawn_group.command("retire")
@click.argument("spawn_id", required=False)
@click.option("--all", "retire_all_flag", is_flag=True, help="Retire all active child harnesses.")
@click.option(
    "--save-dir",
    type=click.Path(path_type=Path),
    default=Path(".harness/spawns"),
    show_default=True,
    help="Root directory containing registry state.",
)
def retire_cmd(spawn_id: str | None, retire_all_flag: bool, save_dir: Path) -> None:
    """Retire a spawned child harness (or all active ones) and close its DAG edge."""
    if not retire_all_flag and not spawn_id:
        _emit({"status": "error", "error": "Specify SPAWN_ID or --all"})
        raise SystemExit(1)

    engine = HarnessSpawnerEngine(state_file=save_dir / "registry.json")
    if retire_all_flag:
        retired = engine.retire_all()
        _emit({"retired_count": len(retired), "spawns": [r.to_dict() for r in retired]})
        return

    assert spawn_id is not None
    try:
        rec = engine.retire(spawn_id)
    except KeyError as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc
    _emit(rec.to_dict())


@spawn_group.command("propose")
@click.argument("spawn_id")
@click.option("--task-id", required=True, help="Task identifier associated with the lesson.")
@click.option("--cue", required=True, help="Transferable cue triggering this lesson.")
@click.option("--lesson", required=True, help="Distilled transferable lesson.")
@click.option("--evidence", required=True, help="Supporting empirical evidence.")
@click.option("--why", default="", show_default=True, help="Rationale for adoption review.")
@click.option("--ki-id", default="", show_default=True, help="Optional KI slug identifier.")
@click.option(
    "--save-dir",
    type=click.Path(path_type=Path),
    default=Path(".harness/spawns"),
    show_default=True,
    help="Root directory containing registry state.",
)
def propose_cmd(
    spawn_id: str,
    task_id: str,
    cue: str,
    lesson: str,
    evidence: str,
    why: str,
    ki_id: str,
    save_dir: Path,
) -> None:
    """Stage a reviewed learning and dual-file KI draft in the child partition."""
    engine = HarnessSpawnerEngine(state_file=save_dir / "registry.json")
    try:
        proposal = engine.propose_merge_back(
            spawn_id,
            task_id=task_id,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            ki_id=ki_id,
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc
    _emit(proposal.to_dict())


@spawn_group.command("adopt")
@click.argument("proposal_id")
@click.option(
    "--save-dir",
    type=click.Path(path_type=Path),
    default=Path(".harness/spawns"),
    show_default=True,
    help="Root directory containing registry state.",
)
@click.option(
    "--library-root",
    type=click.Path(path_type=Path),
    default=Path(".harness/experience"),
    show_default=True,
    help="Parent ExperienceLibrary root to adopt into.",
)
@click.option(
    "--knowledge-root",
    type=click.Path(path_type=Path),
    default=Path(".harness/knowledge"),
    show_default=True,
    help="Parent Knowledge Vault root to adopt the dual-file KI into.",
)
def adopt_cmd(
    proposal_id: str,
    save_dir: Path,
    library_root: Path,
    knowledge_root: Path,
) -> None:
    """Explicitly review and adopt a staged child proposal into parent stores."""
    engine = HarnessSpawnerEngine(state_file=save_dir / "registry.json")
    try:
        result = engine.adopt_merge_proposal(
            proposal_id,
            parent_library_root=library_root,
            parent_knowledge_root=knowledge_root,
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc
    _emit(result)
