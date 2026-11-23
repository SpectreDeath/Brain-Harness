"""`harness spawn` -- headless child-harness spawning, supervision, and reviewed adoption (Rule 10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
from harness.services.harness_spawner import (
    DEFAULT_K,
    DEFAULT_MAX_BLUEPRINT_SKILLS,
    DEFAULT_MAX_ROLLOUTS,
    DEFAULT_MAX_SESSIONS,
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    HARD_MAX_BLUEPRINT_SKILLS,
    HARD_MAX_SPAWN_DEPTH,
    HARNESS_SPAWNER_SERVICE_KEY,
    HarnessBlueprint,
    HarnessSpawnerProtocol,
    SpawnBudgetSpec,
    SpawnLifecycleState,
    SpawnSpec,
    build_blueprint_tree,
    recommend_harness_blueprints,
)
from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.models import BRAIN_SURFACE

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")

logger = structlog.get_logger(__name__)


def get_spawner_service(
    *,
    save_dir: Path | None = None,
    context: ServiceContext | None = None,
) -> HarnessSpawnerProtocol:
    """Resolve the spawner plugin service via IoC context or plugin singleton (Rule 45, 49)."""
    if context is not None:
        svc = context.optional(HARNESS_SPAWNER_SERVICE_KEY)
        if svc is not None:
            return svc

    ws_root = Path(__file__).resolve().parents[3]
    if not (ws_root / "plugins").is_dir():
        ws_root = Path.cwd()
    if str(ws_root) not in sys.path:
        sys.path.insert(0, str(ws_root))
    if str(ws_root / "src") not in sys.path:
        sys.path.insert(0, str(ws_root / "src"))

    state_file = (save_dir / "registry.json") if save_dir is not None else None
    try:
        from plugins.agent_orchestration.harness_spawner.main import (
            plugin as spawner_plugin,
        )

        if state_file is not None:
            return spawner_plugin.for_state_file(state_file)
        return spawner_plugin
    except ImportError as exc:
        logger.warning("harness_spawner_plugin_fallback", error=str(exc))
        from harness.services.harness_spawner import HarnessSpawnerEngine

        return HarnessSpawnerEngine(state_file=state_file)


def _emit(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


def _resolve_proposed_tree(name: str, domain: str, task: str, harness_dir: Path | None) -> dict[str, str]:
    """Build the exact proposed tree `spawn run` would admit (shared so review and run digests agree)."""
    if harness_dir is not None:
        return surface_ops.read_tree(BRAIN_SURFACE, harness_dir)
    return {"AGENTS.md": f"# Spawned Harness: {name}\n\nDomain: {domain}\nTask: {task}\n"}


def _resolve_blueprint_selection(
    blueprint_name: str | None,
    name: str | None,
    domain: str | None,
    task: str,
    harness_dir: Path | None,
    *,
    root_path: Path = Path("."),
    vault_dir: Path = Path(".harness/knowledge"),
) -> tuple[str, str, str, str, dict[str, str], HarnessBlueprint | None]:
    """Resolve target metadata and tree for `--blueprint` or explicit `--name/--domain` callers."""
    if blueprint_name:
        matches = recommend_harness_blueprints(root_path=root_path, vault_dir=vault_dir, name=blueprint_name)
        if not matches:
            raise ValueError(f"Unknown blueprint: {blueprint_name!r}")
        bp = matches[0]
        resolved_name = name or bp.name
        resolved_domain = domain or bp.domain
        resolved_task = bp.mission if task == "spawned_harness" else task
        skills_root = Path(root_path).resolve() / ".agents" / "skills"
        tree = (
            surface_ops.read_tree(BRAIN_SURFACE, harness_dir)
            if harness_dir is not None
            else build_blueprint_tree(bp, skills_root=skills_root)
        )
        return resolved_name, resolved_domain, resolved_task, bp.mission, tree, bp

    if not name or not domain:
        raise ValueError("Specify --blueprint or both --name and --domain")
    return name, domain, task, task, _resolve_proposed_tree(name, domain, task, harness_dir), None


@click.group("spawn")
def spawn_group() -> None:
    """Spawn, inspect, retire, and adopt learnings from isolated child harnesses."""


@spawn_group.command("blueprints")
@click.option(
    "--root",
    "root_path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Workspace root containing .agents/skills/ and skill graph inputs.",
)
@click.option(
    "--vault",
    "vault_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path(".harness/knowledge"),
    show_default=True,
    help="Knowledge Vault directory used for verified KI grounding.",
)
@click.option(
    "--max-skills",
    type=click.IntRange(min=1, max=HARD_MAX_BLUEPRINT_SKILLS),
    default=DEFAULT_MAX_BLUEPRINT_SKILLS,
    show_default=True,
    help="Maximum skills allowed per recommended blueprint.",
)
@click.option(
    "--limit",
    type=click.IntRange(min=1),
    default=22,
    show_default=True,
    help="Maximum number of ranked blueprints to return.",
)
@click.option("--name", default=None, help="Filter to a specific blueprint name.")
@click.option("--json", "as_json", is_flag=True, help="Emit raw JSON payload.")
def blueprints_cmd(
    root_path: Path,
    vault_dir: Path,
    max_skills: int,
    limit: int,
    name: str | None,
    as_json: bool,
) -> None:
    """Recommend prioritized domain harness blueprints from the live skill graph and Knowledge Vault."""
    spawner = get_spawner_service()
    if hasattr(spawner, "recommend_blueprints"):
        bps = spawner.recommend_blueprints(
            root_path=root_path,
            vault_dir=vault_dir,
            max_skills=max_skills,
            limit=limit,
            name=name,
        )
    else:
        bps = recommend_harness_blueprints(
            root_path=root_path,
            vault_dir=vault_dir,
            max_skills=max_skills,
            limit=limit,
            name=name,
        )

    if as_json:
        _emit({"count": len(bps), "blueprints": [bp.to_dict() for bp in bps]})
        return

    if not bps:
        click.echo("No matching harness blueprints found.")
        return

    for idx, bp in enumerate(bps, 1):
        click.echo(
            f"{idx}. {bp.name} (score={bp.score:.2f}, form={bp.icm_form}, "
            f"skills={len(bp.skills)}/{bp.prime_skill_count}, savings={bp.estimated_token_savings_pct:.1f}%, "
            f"verified_kis={len(bp.seeded_kis)}, excluded_unverified={len(bp.excluded_unverified_kis)})"
        )
        click.echo(f"   skills: {', '.join(bp.skills)}")
        click.echo(f"   source: {bp.graph_source}")


@spawn_group.command("run")
@click.option(
    "--blueprint", "blueprint_name", default=None, help="Graph blueprint name from `harness spawn blueprints`."
)
@click.option("--name", default=None, help="Short identifier for the spawned child harness.")
@click.option("--domain", default=None, help="Domain partition for isolated ExperienceLibrary storage.")
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
@click.option(
    "--materialize",
    "materialize_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Optional directory to materialize as a dock-linked repo harness.",
)
@click.option("--approve-dock", is_flag=True, help="Approve the materialized dock.yaml manifest upon linking.")
@click.option("--write-permitted", is_flag=True, help="Require matching --approve-digest before admission.")
@click.option("--approve-digest", default=None, help="Approved SHA-256 digest of the proposed harness tree.")
def run_cmd(
    blueprint_name: str | None,
    name: str | None,
    domain: str | None,
    task: str,
    harness_dir: Path | None,
    max_tokens: int,
    k: int,
    max_depth: int,
    depth: int,
    parent_spawn_id: str | None,
    lifetime: str,
    save_dir: Path,
    materialize_dir: Path | None,
    approve_dock: bool,
    write_permitted: bool,
    approve_digest: str | None,
) -> None:
    """Validate, probe-gate, and spawn an isolated child harness."""
    try:
        resolved_name, resolved_domain, resolved_task, resolved_desc, tree, bp = _resolve_blueprint_selection(
            blueprint_name, name, domain, task, harness_dir
        )
    except (ValueError, FileNotFoundError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc

    spawner = get_spawner_service(save_dir=save_dir)
    try:
        spec = SpawnSpec(
            name=resolved_name,
            domain=resolved_domain,
            task=resolved_task,
            description=resolved_desc,
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
            write_permitted=write_permitted,
            approved_tree_digest=approve_digest,
        )
        rec = spawner.spawn(spec, materialize_dir=materialize_dir, approve_dock=approve_dock, blueprint=bp)
    except (ValueError, KeyError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc

    export = spawner.export_dag()
    payload = rec.to_dict()
    payload["ascii_tree"] = export.formatted_ascii_tree
    _emit(payload)
    if rec.state == SpawnLifecycleState.FAILED:
        raise SystemExit(1)


@spawn_group.command("review")
@click.option(
    "--blueprint", "blueprint_name", default=None, help="Graph blueprint name from `harness spawn blueprints`."
)
@click.option("--name", default=None, help="Short identifier for the proposed child harness.")
@click.option("--domain", default=None, help="Domain partition (used for the default proposed tree).")
@click.option("--task", default="spawned_harness", show_default=True, help="Assigned task summary.")
@click.option(
    "--harness-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Optional harness directory to read the proposed editable tree from.",
)
@click.option(
    "--base-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Optional harness directory to diff against (default: empty base tree).",
)
@click.option(
    "--approve-digest",
    default=None,
    help="Optional digest to check against the proposed tree; exits 1 on mismatch.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the review as JSON instead of human-readable text.")
def review_cmd(
    blueprint_name: str | None,
    name: str | None,
    domain: str | None,
    task: str,
    harness_dir: Path | None,
    base_dir: Path | None,
    approve_digest: str | None,
    as_json: bool,
) -> None:
    """Present the proposed tree diff and its canonical SHA-256 digest for `--approve-digest`."""
    # Pure stateless pre-spawn diff/digest preview: operates directly on tree dicts via
    # `build_tree_diff_review` without instantiating an engine or touching registry state.
    from harness.services.harness_spawner import build_tree_diff_review

    try:
        resolved_name, resolved_domain, _, _, proposed, _ = _resolve_blueprint_selection(
            blueprint_name, name, domain, task, harness_dir
        )
    except (ValueError, FileNotFoundError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc

    base = surface_ops.read_tree(BRAIN_SURFACE, base_dir) if base_dir is not None else {}
    review = build_tree_diff_review(BRAIN_SURFACE, base, proposed, approved_digest=approve_digest)

    if as_json:
        _emit(review.to_dict())
    else:
        click.echo(f"Proposed harness: {resolved_name} (domain={resolved_domain})")
        click.echo(f"Base digest:      {review.base_sha256}")
        click.echo(f"Added:    {', '.join(review.added) or '-'}")
        click.echo(f"Modified: {', '.join(review.modified) or '-'}")
        click.echo(f"Removed:  {', '.join(review.removed) or '-'}")
        click.echo("")
        click.echo(review.unified_diff or "(no changes)")
        click.echo("")
        click.echo(f"Approval digest (pass to `spawn run --write-permitted --approve-digest`): {review.tree_sha256}")
        if approve_digest:
            click.echo(f"Supplied digest matches: {review.approved}")
    if approve_digest and not review.approved:
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
    spawner = get_spawner_service(save_dir=save_dir)
    filter_state = SpawnLifecycleState(state.upper()) if state else None
    records = spawner.list_spawns(state=filter_state)
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

    spawner = get_spawner_service(save_dir=save_dir)
    if retire_all_flag:
        retired = spawner.retire_all()
        _emit({"retired_count": len(retired), "spawns": [r.to_dict() for r in retired]})
        return

    assert spawn_id is not None
    try:
        rec = spawner.retire(spawn_id)
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
    "--kind",
    "proposal_kind",
    type=click.Choice(["ki", "skill", "config"]),
    default="ki",
    show_default=True,
    help="Proposal category allowed under merge-back policy.",
)
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
    proposal_kind: str,
    save_dir: Path,
) -> None:
    """Stage a reviewed learning and dual-file KI draft in the child partition."""
    spawner = get_spawner_service(save_dir=save_dir)
    try:
        proposal = spawner.propose_merge_back(
            spawn_id,
            task_id=task_id,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            ki_id=ki_id,
            proposal_kind=proposal_kind,
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
@click.option("--reviewer", default="human", show_default=True, help="Reviewer identifier.")
@click.option("--note", "review_note", default="", show_default=True, help="Optional review note.")
def adopt_cmd(
    proposal_id: str,
    save_dir: Path,
    library_root: Path,
    knowledge_root: Path,
    reviewer: str,
    review_note: str,
) -> None:
    """Explicitly review and adopt a staged child proposal into parent stores."""
    spawner = get_spawner_service(save_dir=save_dir)
    try:
        result = spawner.adopt_merge_proposal(
            proposal_id,
            parent_library_root=library_root,
            parent_knowledge_root=knowledge_root,
            reviewer=reviewer,
            review_note=review_note,
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc
    _emit(result)


@spawn_group.command("reject")
@click.argument("proposal_id")
@click.option("--reviewer", default="human", show_default=True, help="Reviewer identifier.")
@click.option("--reason", default="", show_default=True, help="Rejection reason.")
@click.option(
    "--save-dir",
    type=click.Path(path_type=Path),
    default=Path(".harness/spawns"),
    show_default=True,
    help="Root directory containing registry state.",
)
def reject_cmd(proposal_id: str, reviewer: str, reason: str, save_dir: Path) -> None:
    """Explicitly reject a staged child proposal (writes nothing to parent stores)."""
    spawner = get_spawner_service(save_dir=save_dir)
    try:
        rejected = spawner.reject_merge_proposal(proposal_id, reviewer=reviewer, reason=reason)
    except (KeyError, ValueError, RuntimeError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(1) from exc
    _emit(rejected.to_dict())


@spawn_group.command("check-drift")
@click.argument("repo_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--expected-digest", default=None, help="Expected canonical SHA-256 tree digest.")
@click.option("--dock-name", default=None, help="Optional dock name to look up.")
def check_drift_cmd(repo_dir: Path, expected_digest: str | None, dock_name: str | None) -> None:
    """Verify a materialized dock repo has not drifted from its approved manifest or tree digest."""
    spawner = get_spawner_service()
    if hasattr(spawner, "check_drift"):
        report = spawner.check_drift(
            repo_dir,
            BRAIN_SURFACE,
            expected_tree_sha256=expected_digest,
            dock_name=dock_name,
        )
    else:
        from harness.services.harness_spawner import check_materialized_drift

        report = check_materialized_drift(
            repo_dir,
            BRAIN_SURFACE,
            expected_tree_sha256=expected_digest,
            dock_name=dock_name,
        )
    _emit(report)
    if report["drifted"]:
        raise SystemExit(1)


@spawn_group.command("cold-walk")
@click.argument("repo_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dock-name", default=None, help="Optional dock name for drift lookup.")
@click.option(
    "--prime-skills-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path(".agents/skills"),
    show_default=True,
    help="Prime skills root used to measure catalog token reduction.",
)
@click.option("--strict", is_flag=True, help="Also exit 1 when human-judged points (#1, #5, #8) are unverified.")
@click.option("--json", "as_json", is_flag=True, help="Emit structured JSON report.")
def cold_walk_cmd(
    repo_dir: Path,
    dock_name: str | None,
    prime_skills_root: Path,
    strict: bool,
    as_json: bool,
) -> None:
    """Run ICM's 8-Point Cold Walk Check on a materialized domain harness."""
    from harness.services.harness_spawner import format_cold_walk_markdown, run_cold_walk

    report = run_cold_walk(
        repo_dir,
        dock_name=dock_name,
        prime_skills_root=prime_skills_root,
    )
    if as_json:
        _emit(report.to_dict())
    else:
        click.echo(format_cold_walk_markdown(report))
    if not report.automated_passed or (strict and not report.overall_passed):
        raise SystemExit(1)
