"""Context commands — pure async command handlers for AST context compilation and prompt pruning.

Provides headless execution of 3-tier AST reachability compilation, Ebbinghaus
channel decay, deterministic prompt pruning, and code skeletonization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

import structlog

# Ensure workspace root is in sys.path for plugins package import
_ws_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_ws_root) not in sys.path:
    sys.path.insert(0, str(_ws_root))

from plugins.memory_and_epistemics.context_compiler.compiler_core import (
    ContextCompiler,
    skeletonize_source,
)
from plugins.memory_and_epistemics.unified_context_pipeline import (
    PipelineMessage,
    UnifiedContextPipeline,
    UnifiedPipelineResult,
)

logger = structlog.get_logger()


@dataclass
class ContextCompileResult:
    """Result of compiling 3-tier AST context from a target file."""

    target_file: str
    tier1_files: int
    tier2_files: int
    tier3_excluded_files: int
    naive_dump_tokens: int
    compiled_tokens: int
    reduction_pct: float
    build_ms: float
    assembled_prompt: str
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file": self.target_file,
            "tier1_files": self.tier1_files,
            "tier2_files": self.tier2_files,
            "tier3_excluded_files": self.tier3_excluded_files,
            "naive_dump_tokens": self.naive_dump_tokens,
            "compiled_tokens": self.compiled_tokens,
            "reduction_pct": self.reduction_pct,
            "build_ms": self.build_ms,
            "assembled_prompt": self.assembled_prompt,
            "diagnostics": self.diagnostics,
        }


@dataclass
class ContextOptimizeResult:
    """Result of running the unified context optimization pipeline."""

    session_id: str
    input_messages: int
    decay_evicted: int
    pruner_removed: int
    final_messages: int
    tokens_raw: int
    tokens_optimized: int
    token_savings_pct: float
    elapsed_ms: float
    assembled_prompt: str
    code_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "input_messages": self.input_messages,
            "decay_evicted": self.decay_evicted,
            "pruner_removed": self.pruner_removed,
            "final_messages": self.final_messages,
            "tokens_raw": self.tokens_raw,
            "tokens_optimized": self.tokens_optimized,
            "token_savings_pct": self.token_savings_pct,
            "elapsed_ms": self.elapsed_ms,
            "assembled_prompt": self.assembled_prompt,
            "code_context": self.code_context,
        }


@dataclass
class CodeSkeletonResult:
    """Result of skeletonizing a Python source file or snippet."""

    functions_stripped: int
    tokens_raw: int
    tokens_skeleton: int
    reduction_pct: float
    skeleton_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "functions_stripped": self.functions_stripped,
            "tokens_raw": self.tokens_raw,
            "tokens_skeleton": self.tokens_skeleton,
            "reduction_pct": self.reduction_pct,
            "skeleton_code": self.skeleton_code,
        }


async def compile_context_cmd(
    target_file: str | Path,
    repo_root: str | Path | None = None,
    max_hops: int = 2,
) -> ContextCompileResult:
    """Compile 3-tier AST context starting outward from a target file."""
    t_path = Path(target_file).resolve()
    if not t_path.exists():
        raise FileNotFoundError(f"Target file not found: {target_file}")

    root = Path(repo_root).resolve() if repo_root else t_path.parent
    compiler = ContextCompiler(root, max_hops=max_hops)
    compiled = compiler.compile(t_path)
    data = compiled.to_dict()

    return ContextCompileResult(
        target_file=str(t_path),
        tier1_files=data.get("tier1_files", 1),
        tier2_files=data.get("tier2_files", 0),
        tier3_excluded_files=data.get("tier3_excluded_files", 0),
        naive_dump_tokens=data.get("naive_dump_tokens", 0),
        compiled_tokens=data.get("compiled_tokens", 0),
        reduction_pct=data.get("reduction_pct", 0.0),
        build_ms=data.get("build_ms", 0.0),
        assembled_prompt=compiled.to_prompt_string(),
        diagnostics=data.get("diagnostics") or {},
    )


async def optimize_context_cmd(
    session_id: str,
    messages: list[dict[str, Any] | PipelineMessage],
    target_repo: str | Path | None = None,
    target_file: str | Path | None = None,
    code_tier_limit: int = 3,
    advance_turn: bool = True,
) -> ContextOptimizeResult:
    """Run full unified context optimization pipeline (decay + 3-pass pruning + AST compilation)."""
    pipeline = UnifiedContextPipeline()
    res: UnifiedPipelineResult = pipeline.process(
        session_id=session_id,
        messages=messages,
        target_repo_path=str(target_repo) if target_repo else None,
        target_file_path=str(target_file) if target_file else None,
        code_tier_limit=code_tier_limit,
        advance_turn=advance_turn,
    )
    return ContextOptimizeResult(
        session_id=res.session_id,
        input_messages=res.input_messages_count,
        decay_evicted=res.decay_evicted_count,
        pruner_removed=res.pruner_removed_count,
        final_messages=res.final_messages_count,
        tokens_raw=res.tokens_raw,
        tokens_optimized=res.tokens_optimized,
        token_savings_pct=res.token_savings_pct,
        elapsed_ms=res.elapsed_ms,
        assembled_prompt=res.assembled_prompt,
        code_context=res.code_context,
    )


async def skeletonize_code_cmd(source_or_file: str | Path) -> CodeSkeletonResult:
    """Skeletonize Python code stripping function bodies and leaving structural outline."""
    source = str(source_or_file)
    if "\n" not in source and len(source) < 4096:
        try:
            p = Path(source)
            if p.exists() and p.is_file():
                source = p.read_text(encoding="utf-8")
        except OSError:
            pass

    skeleton, stripped = skeletonize_source(source)
    raw_tokens = max(1, len(source) // 4)
    skel_tokens = max(1, len(skeleton) // 4)
    savings = 100.0 * (1.0 - (skel_tokens / raw_tokens)) if raw_tokens > 0 else 0.0

    return CodeSkeletonResult(
        functions_stripped=stripped,
        tokens_raw=raw_tokens,
        tokens_skeleton=skel_tokens,
        reduction_pct=round(savings, 2),
        skeleton_code=skeleton,
    )


# --- Codebase Context Architecture (Micro-Kernel Seams: Rule 49 & Rule 57) ---
from harness.services.codebase_context import (
    ContextGovernanceReport,
    ContextLintReport,
    SyncResult,
    resolve_codebase_context,
)


async def lint_codebase_context_cmd(root: str | Path = ".") -> ContextLintReport:
    """Execute 4-check context file linting on the target repository."""
    service = resolve_codebase_context(root=root)
    return service.lint()


async def sync_codebase_context_cmd(root: str | Path = ".", source: str = "AGENTS.md", dry_run: bool = False) -> SyncResult:
    """Synchronize downstream context files against canonical source."""
    service = resolve_codebase_context(root=root)
    return service.sync(source_rel=source, dry_run=dry_run)


async def govern_codebase_context_cmd(
    root: str | Path = ".",
    target_file: str | Path | None = None,
    complexity_score: float = 0.5,
) -> ContextGovernanceReport:
    """Execute full 5-stage context governance pipeline on the target repository."""
    service = resolve_codebase_context(root=root)
    return service.govern(root=root, target_file=target_file, complexity_score=complexity_score)


# --- Click CLI adapters ---
import json as _json
import click
from harness.commands._utils import _run_async


@click.group("context")
def context_group() -> None:
    """Manage 3-tier AST reachability compilation and context optimization."""


@context_group.command("compile")
@click.argument("target_file", type=click.Path(exists=True))
@click.option("--repo-root", "-r", default=None, type=click.Path(exists=True), help="Root directory of the repository")
@click.option("--max-hops", "-h", default=2, type=int, help="Maximum reachability hop depth")
def context_compile(target_file: str, repo_root: str | None, max_hops: int) -> None:
    """Compile 3-tier AST reachability context starting from a target file."""
    res = _run_async(compile_context_cmd(target_file, repo_root=repo_root, max_hops=max_hops))
    click.echo(f"\n3-Tier AST Compilation: {res.target_file}")
    click.echo("━" * 60)
    click.echo(f"Tier 1 (Target Full Source): {res.tier1_files} file")
    click.echo(f"Tier 2 (Skeletonized):       {res.tier2_files} file(s)")
    click.echo(f"Tier 3 (Excluded):           {res.tier3_excluded_files} file(s)")
    click.echo(f"Naive Token Dump:            {res.naive_dump_tokens} tokens")
    click.echo(f"Compiled Token Size:         {res.compiled_tokens} tokens")
    click.echo(f"Token Reduction:             {res.reduction_pct:.1f}%")
    click.echo(f"Build Duration:              {res.build_ms:.2f} ms")
    click.echo()


@context_group.command("skeletonize")
@click.argument("target_file", type=click.Path(exists=True))
def context_skeletonize(target_file: str) -> None:
    """Extract structural interface skeleton from Python source file."""
    res = _run_async(skeletonize_code_cmd(target_file))
    click.echo(f"\nSkeletonized: {target_file}")
    click.echo("━" * 60)
    click.echo(f"Functions Stripped: {res.functions_stripped}")
    click.echo(f"Token Reduction:    {res.reduction_pct:.1f}% ({res.tokens_raw} -> {res.tokens_skeleton} tokens)")
    click.echo("\nSkeleton Source Preview:")
    click.echo("─" * 60)
    click.echo(res.skeleton_code[:1500])
    if len(res.skeleton_code) > 1500:
        click.echo("... [truncated preview]")
    click.echo()


@context_group.command("lint")
@click.option("--root", "-r", default=".", help="Repository root path")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--silent", is_flag=True, help="Suppress output on pass")
def context_lint(root: str, as_json: bool, silent: bool) -> None:
    """Verify repository context files across 4 quality dimensions."""
    report = _run_async(lint_codebase_context_cmd(root=root))
    if as_json:
        click.echo(_json.dumps(report.to_dict(), indent=2))
        sys.exit(0 if report.passed else 1)

    if report.passed:
        if not silent:
            click.echo(f"[PASS] Context files healthy across {report.checks_count} checks at: {root}")
        sys.exit(0)

    click.echo(f"[FAIL] Context file linter detected {report.problems_count} problem(s):", err=True)
    for p in report.problems:
        d = p.to_dict()
        click.echo(f"  - [{d['check']}] {p.message}", err=True)
    sys.exit(1)


@context_group.command("sync")
@click.option("--root", "-r", default=".", help="Repository root path")
@click.option("--source", "-s", default="AGENTS.md", help="Canonical source filename")
@click.option("--dry-run", is_flag=True, help="Check for drift without writing changes")
@click.option("--silent", is_flag=True, help="Suppress output on success")
def context_sync(root: str, source: str, dry_run: bool, silent: bool) -> None:
    """Synchronize downstream vendor files against canonical source."""
    result = _run_async(sync_codebase_context_cmd(root=root, source=source, dry_run=dry_run))
    if not silent or not result.in_sync:
        for action in result.actions:
            click.echo(action, err=(not result.in_sync and dry_run))

    if dry_run and not result.in_sync:
        sys.exit(1)
    sys.exit(0)


@context_group.command("govern")
@click.option("--root", "-r", default=".", help="Repository root path")
@click.option("--complexity", "-c", default=0.5, type=float, help="5D complexity score (0.0 to 1.0)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--silent", is_flag=True, help="Suppress output on pass")
def context_govern(root: str, complexity: float, as_json: bool, silent: bool) -> None:
    """Execute complete 5-stage context governance audit and compute tier assessment."""
    report = _run_async(govern_codebase_context_cmd(root=root, complexity_score=complexity))
    if as_json:
        click.echo(_json.dumps(report.to_dict(), indent=2))
        sys.exit(0 if report.passed else 1)

    if report.passed:
        if not silent:
            click.echo(f"\n[PASS] Context Governance Audit Passed ({report.passed_stages_count}/{report.total_stages} stages)")
            click.echo("━" * 60)
            click.echo(f"Recommended Compute Tier: {report.recommended_tier}")
            for st in report.stages:
                click.echo(f"  Stage {st.stage_num} [{st.stage_name}]: {st.message} ({st.duration_ms:.1f}ms)")
            click.echo()
        sys.exit(0)

    click.echo("\n[FAIL] Context Governance Violations Detected:", err=True)
    for st in report.stages:
        if not st.passed:
            click.echo(f"  - [Stage {st.stage_num}: {st.stage_name}] {st.message}", err=True)
    for v in report.violations:
        click.echo(f"  - [{v.rule_name}] {v.file_path}:{v.line_number}: {v.message}", err=True)
    sys.exit(1)


# --- Provenance & Context Type System CLI Seams ---
@context_group.command("add")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--type", "-t", "context_type", required=True, type=click.Choice(["instruction", "memory", "evidence", "tool_output"]), help="Semantic channel context type")
@click.option("--content", "-c", required=True, help="Content text")
@click.option("--source", default=None, help="Origin source identifier")
@click.option("--priority", "-p", default=0, type=int, help="Priority score")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def context_add_cmd(session: str, context_type: str, content: str, source: str | None, priority: int, as_json: bool) -> None:
    """Register a typed context item into session origin ledger."""
    from plugins.memory_and_epistemics.context_type_system.main import context_add
    res = context_add(session_id=session, context_type=context_type, content=content, source=source, priority=priority)
    if as_json:
        click.echo(_json.dumps(res, indent=2))
        return
    if res.get("status") == "ok":
        item = res.get("item") or {}
        click.secho(f"[OK] Added context item '{item.get('request_id')}' ({item.get('context_type')}) in session '{session}'", fg="green")
    else:
        click.secho(f"[ERROR] Failed to add context: {res.get('error')}", fg="red", err=True)
        sys.exit(1)


@context_group.command("transform")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--id", "request_id", required=True, help="Target item request ID")
@click.option("--to-type", required=True, type=click.Choice(["instruction", "memory", "evidence", "tool_output"]), help="Target context type")
@click.option("--source", default=None, help="Source identifier")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def context_transform_cmd(session: str, request_id: str, to_type: str, source: str | None, as_json: bool) -> None:
    """Explicitly transition a context item across permitted policy boundaries."""
    from plugins.memory_and_epistemics.context_type_system.main import context_transform
    res = context_transform(session_id=session, request_id=request_id, to_type=to_type, source=source)
    if as_json:
        click.echo(_json.dumps(res, indent=2))
        return
    if res.get("status") == "ok":
        item = res.get("item") or {}
        click.secho(f"[OK] Transformed item '{request_id}' -> '{item.get('context_type')}' in session '{session}'", fg="green")
    else:
        click.secho(f"[ERROR] Transform rejected: {res.get('error')}", fg="red", err=True)
        sys.exit(1)


@context_group.command("validate-tool")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--id", "request_id", default=None, help="Existing tool_output item request ID")
@click.option("--tool-name", default="tool", help="Tool name if creating new tool_output item")
@click.option("--output-json", default=None, help="Raw tool output payload if creating new item")
@click.option("--strict", is_flag=True, help="Enforce strict validation")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def context_validate_tool_cmd(session: str, request_id: str | None, tool_name: str, output_json: str | None, strict: bool, as_json: bool) -> None:
    """Validate tool output and promote to verified evidence."""
    from plugins.memory_and_epistemics.context_type_system.main import (
        context_add,
        context_validate_tool_output,
    )
    if not request_id:
        if not output_json:
            click.secho("[ERROR] Must provide either --id or --output-json", fg="red", err=True)
            sys.exit(1)
        add_res = context_add(session_id=session, context_type="tool_output", content=output_json, source=tool_name)
        if add_res.get("status") != "ok" or not add_res.get("item"):
            click.secho(f"[ERROR] Failed to stage tool output: {add_res.get('error')}", fg="red", err=True)
            sys.exit(1)
        request_id = add_res["item"]["request_id"]

    res = context_validate_tool_output(session_id=session, tool_request_id=request_id, strict_mode=strict)
    if as_json:
        click.echo(_json.dumps(res, indent=2))
        return
    if res.get("status") == "ok":
        item = res.get("item") or {}
        click.secho(f"[OK] Validated and elevated '{request_id}' to evidence in session '{session}' (New ID: {item.get('request_id')})", fg="green")
    else:
        click.secho(f"[ERROR] Tool validation failed: {res.get('error')}", fg="red", err=True)
        sys.exit(1)


@context_group.command("assemble")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--budget-tokens", default=4000, type=int, help="Maximum token budget for assembled prompt")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def context_assemble_cmd(session: str, budget_tokens: int, as_json: bool) -> None:
    """Render structured prompt partitioned by typed semantic channels."""
    from plugins.memory_and_epistemics.context_type_system.main import context_assemble_prompt
    res = context_assemble_prompt(session_id=session, max_tokens=budget_tokens)
    if as_json:
        click.echo(_json.dumps(res, indent=2))
        return
    click.secho(f"\nAssembled Context Prompt ({session})", fg="cyan", bold=True)
    click.echo("━" * 60)
    click.echo(f"Items Rendered:  {res.get('item_count')}")
    click.echo(f"Items Dropped:   {res.get('dropped_items_count')}")
    click.echo(f"Used Tokens:     {res.get('used_tokens')}/{budget_tokens}")
    click.echo(f"Channel Split:   {res.get('channel_breakdown')}")
    click.echo("\nPrompt Preview:")
    click.echo("─" * 60)
    click.echo(res.get("prompt", "")[:1000])
    if len(res.get("prompt", "")) > 1000:
        click.echo("... [truncated]")


@context_group.command("ledger")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--id", "request_id", default=None, help="Inspect specific item derivation lineage")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def context_ledger_cmd(session: str, request_id: str | None, as_json: bool) -> None:
    """Audit origin ledger or trace multi-hop Isnad lineage for a session."""
    from plugins.memory_and_epistemics.context_type_system.main import (
        context_get_lineage,
        context_inspect_ledger,
    )
    if request_id:
        res = context_get_lineage(session_id=session, request_id=request_id)
        if as_json:
            click.echo(_json.dumps(res, indent=2))
            return
        if res.get("status") == "ok":
            click.secho(f"\nLineage Audit for Item '{request_id}' (Hops: {res.get('hops')})", fg="cyan", bold=True)
            for hop in res.get("lineage", []):
                click.echo(f"  • [{hop.get('context_type')}] {hop.get('request_id')} (from {hop.get('source') or 'unknown'})")
        else:
            click.secho(f"[ERROR] Lineage trace failed: {res.get('error')}", fg="red", err=True)
            sys.exit(1)
    else:
        res = context_inspect_ledger(session_id=session)
        if as_json:
            click.echo(_json.dumps(res, indent=2))
            return
        click.secho(f"\nContext Provenance Ledger ({session})", fg="cyan", bold=True)
        click.echo("━" * 60)
        click.echo(f"Total Active Items: {res.get('total_items')}")
        for rec in res.get("ledger", []):
            click.echo(f"  • {rec.get('origin_id')}: type={rec.get('origin_type')} key={rec.get('key')}")


@context_group.command("snapshot")
@click.option("--session", "-s", default="default", help="Session identifier")
@click.option("--export", "export_path", default=None, type=click.Path(), help="File path to export snapshot JSON")
@click.option("--import", "import_path", default=None, type=click.Path(exists=True), help="File path to import snapshot JSON")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output")
def context_snapshot_cmd(session: str, export_path: str | None, import_path: str | None, as_json: bool) -> None:
    """Export or restore a context session snapshot."""
    from plugins.memory_and_epistemics.context_type_system.main import (
        context_export_session,
        context_import_session,
    )
    if import_path:
        data = _json.loads(Path(import_path).read_text(encoding="utf-8"))
        res = context_import_session(session_id=session, data=data)
        if as_json:
            click.echo(_json.dumps(res, indent=2))
            return
        if res.get("status") == "ok":
            click.secho(f"[OK] Restored session '{session}' from {import_path}", fg="green")
        else:
            click.secho(f"[ERROR] Import failed: {res.get('error')}", fg="red", err=True)
            sys.exit(1)
    elif export_path:
        res = context_export_session(session_id=session)
        if res.get("status") == "ok":
            Path(export_path).write_text(_json.dumps(res.get("data", {}), indent=2), encoding="utf-8")
            if as_json:
                click.echo(_json.dumps(res, indent=2))
            else:
                click.secho(f"[OK] Exported session '{session}' snapshot to {export_path}", fg="green")
        else:
            click.secho(f"[ERROR] Export failed: {res.get('error')}", fg="red", err=True)
            sys.exit(1)
    else:
        res = context_export_session(session_id=session)
        click.echo(_json.dumps(res, indent=2))


__all__ = [
    "CodeSkeletonResult",
    "ContextCompileResult",
    "ContextOptimizeResult",
    "compile_context_cmd",
    "context_group",
    "govern_codebase_context_cmd",
    "lint_codebase_context_cmd",
    "optimize_context_cmd",
    "skeletonize_code_cmd",
    "sync_codebase_context_cmd",
]

