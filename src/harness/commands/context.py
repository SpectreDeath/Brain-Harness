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
    p = Path(str(source_or_file))
    if p.exists() and p.is_file():
        source = p.read_text(encoding="utf-8")
    else:
        source = str(source_or_file)

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


# --- Codebase Context Architecture (Headless Seams) ---
_engine_dir = _ws_root / ".agents" / "skills" / "codebase-context-architect" / "scripts"
if str(_engine_dir) not in sys.path:
    sys.path.insert(0, str(_engine_dir))

try:
    from engine import CodebaseContextEngine, ContextLintReport, SyncResult
except ImportError:
    CodebaseContextEngine = None  # type: ignore
    ContextLintReport = None  # type: ignore
    SyncResult = None  # type: ignore


async def lint_codebase_context_cmd(root: str | Path = ".") -> Any:
    """Execute 4-check context file linting on the target repository."""
    if CodebaseContextEngine is None:
        raise RuntimeError("CodebaseContextEngine could not be imported")
    engine = CodebaseContextEngine(root=root)
    return engine.lint()


async def sync_codebase_context_cmd(root: str | Path = ".", source: str = "AGENTS.md", dry_run: bool = False) -> Any:
    """Synchronize downstream context files against canonical source."""
    if CodebaseContextEngine is None:
        raise RuntimeError("CodebaseContextEngine could not be imported")
    engine = CodebaseContextEngine(root=root)
    return engine.sync(source_rel=source, dry_run=dry_run)


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


__all__ = [
    "CodeSkeletonResult",
    "ContextCompileResult",
    "ContextOptimizeResult",
    "compile_context_cmd",
    "context_group",
    "lint_codebase_context_cmd",
    "optimize_context_cmd",
    "skeletonize_code_cmd",
    "sync_codebase_context_cmd",
]

