"""Main entrypoint and typed tool registrations for Context Compiler plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceKey
from plugins.memory_and_epistemics.context_compiler.compiler_core import (
    ContextCompiler,
    SymbolResolver,
    estimate_tokens,
    skeletonize_source,
)

logger = structlog.get_logger()


def compile_context(repo_root: str, target_file: str, max_hops: int = 2) -> dict[str, Any]:
    """Compile a 3-tier token-efficient context window for a target file in a repository.

    Args:
        repo_root: Root directory of the repository.
        target_file: Path to the file actively being targeted or edited.
        max_hops: Maximum call and import hops outward to include in Tier 2.

    Returns:
        Structured compiled context dictionary including prompt string and token diagnostics.
    """
    root_path = Path(repo_root)
    if not root_path.exists() or not root_path.is_dir():
        return {"status": "error", "error": f"Repository root directory not found: {repo_root}"}

    file_path = Path(target_file)
    if not file_path.is_absolute():
        file_path = (root_path / target_file).resolve()

    if not file_path.exists() or not file_path.is_file():
        return {"status": "error", "error": f"Target file not found: {target_file}"}

    try:
        compiler = ContextCompiler(root_path, max_hops=max_hops)
        compiled = compiler.compile(file_path)
        return {
            "status": "ok",
            "prompt_text": compiled.to_prompt_string(),
            "target_file": str(compiled.target_file),
            "total_repo_files": compiled.total_repo_files,
            "tier1_count": 1,
            "tier2_count": sum(1 for e in compiled.entries if e.tier == 2),
            "tier3_excluded_count": compiled.excluded_count,
            "naive_dump_tokens": compiled.naive_dump_tokens,
            "compiled_tokens": compiled.compiled_tokens,
            "reduction_pct": round(compiled.reduction_pct(), 2),
            "build_ms": round(compiled.build_seconds * 1000, 2),
            "diagnostics": compiled.diagnostics.to_dict() if compiled.diagnostics else None,
            "summary": compiled.summary(),
        }
    except Exception as e:
        logger.error("context_compiler_failed", error=str(e), repo=repo_root, target=target_file)
        return {"status": "error", "error": str(e)}


def skeletonize_code(source_code: str) -> dict[str, Any]:
    """Strip function and method bodies from Python source, preserving signatures and docstrings.

    Args:
        source_code: Raw Python code string to skeletonize.

    Returns:
        Skeletonized code string, function count stripped, and token reduction metrics.
    """
    if not source_code.strip():
        return {
            "status": "ok",
            "skeleton_code": "",
            "functions_stripped": 0,
            "original_tokens": 0,
            "skeleton_tokens": 0,
            "reduction_pct": 0.0,
        }

    try:
        skeleton, count = skeletonize_source(source_code)
        orig_tokens = estimate_tokens(source_code)
        skel_tokens = estimate_tokens(skeleton)
        reduction = round(100.0 * (1.0 - (skel_tokens / orig_tokens)), 2) if orig_tokens else 0.0
        return {
            "status": "ok",
            "skeleton_code": skeleton,
            "functions_stripped": count,
            "original_tokens": orig_tokens,
            "skeleton_tokens": skel_tokens,
            "reduction_pct": reduction,
        }
    except Exception as e:
        logger.error("skeletonize_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def resolve_reachability(repo_root: str, target_file: str, max_hops: int = 2) -> dict[str, Any]:
    """Perform multi-hop AST symbol and import reachability analysis from a target file.

    Args:
        repo_root: Root directory of the repository.
        target_file: Target file to begin reachability traversal from.
        max_hops: Maximum call/import distance hops outward.

    Returns:
        Reachable file map with hop distances, unresolved calls, dynamic dispatch warnings, and collision notes.
    """
    root_path = Path(repo_root)
    if not root_path.exists() or not root_path.is_dir():
        return {"status": "error", "error": f"Repository root directory not found: {repo_root}"}

    file_path = Path(target_file)
    if not file_path.is_absolute():
        file_path = (root_path / target_file).resolve()

    if not file_path.exists() or not file_path.is_file():
        return {"status": "error", "error": f"Target file not found: {target_file}"}

    try:
        resolver = SymbolResolver(root_path, max_hops=max_hops)
        res = resolver.resolve(file_path)
        return {
            "status": "ok",
            "target_file": str(file_path),
            "max_hops": max_hops,
            "reachability": res.to_dict(),
            "reachable_file_count": len(res.reachable),
        }
    except Exception as e:
        logger.error("reachability_resolution_failed", error=str(e), repo=repo_root, target=target_file)
        return {"status": "error", "error": str(e)}


def estimate_token_reduction(repo_root: str, target_file: str, max_hops: int = 2) -> dict[str, Any]:
    """Calculate potential token savings of compiled 3-tier context versus a naive repository dump.

    Args:
        repo_root: Root directory of the repository.
        target_file: Target file to analyze.
        max_hops: Maximum call hops outward.

    Returns:
        Comparative token counts, reduction percentages, and file tier distributions.
    """
    root_path = Path(repo_root)
    if not root_path.exists() or not root_path.is_dir():
        return {"status": "error", "error": f"Repository root directory not found: {repo_root}"}

    file_path = Path(target_file)
    if not file_path.is_absolute():
        file_path = (root_path / target_file).resolve()

    if not file_path.exists() or not file_path.is_file():
        return {"status": "error", "error": f"Target file not found: {target_file}"}

    try:
        compiler = ContextCompiler(root_path, max_hops=max_hops)
        compiled = compiler.compile(file_path)
        return {
            "status": "ok",
            "target_file": str(compiled.target_file),
            "naive_dump_tokens": compiled.naive_dump_tokens,
            "compiled_tokens": compiled.compiled_tokens,
            "tokens_saved": max(0, compiled.naive_dump_tokens - compiled.compiled_tokens),
            "reduction_pct": round(compiled.reduction_pct(), 2),
            "total_repo_files": compiled.total_repo_files,
            "tier1_files": 1,
            "tier2_files": sum(1 for e in compiled.entries if e.tier == 2),
            "tier3_excluded_files": compiled.excluded_count,
            "build_ms": round(compiled.build_seconds * 1000, 2),
        }
    except Exception as e:
        logger.error("estimate_token_reduction_failed", error=str(e), repo=repo_root, target=target_file)
        return {"status": "error", "error": str(e)}


class ContextCompilerService:
    """Service provider for 3-tier AST context compilation."""

    def compile(self, repo_root: str, target_file: str, max_hops: int = 2) -> dict[str, Any]:
        return compile_context(repo_root, target_file, max_hops=max_hops)

    def skeletonize(self, source_code: str) -> dict[str, Any]:
        return skeletonize_code(source_code)

    def resolve(self, repo_root: str, target_file: str, max_hops: int = 2) -> dict[str, Any]:
        return resolve_reachability(repo_root, target_file, max_hops=max_hops)

    def estimate_reduction(self, repo_root: str, target_file: str, max_hops: int = 2) -> dict[str, Any]:
        return estimate_token_reduction(repo_root, target_file, max_hops=max_hops)


CONTEXT_COMPILER_SERVICE_KEY = ServiceKey[ContextCompilerService]("domain.context_compiler")
