"""Three-tier AST context compilation engine orchestrator."""

from __future__ import annotations

from pathlib import Path
import time

from plugins.memory_and_epistemics.context_compiler.compiler_core.constants import estimate_tokens
from plugins.memory_and_epistemics.context_compiler.compiler_core.models import (
    CompiledContext,
    TierEntry,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.skeletonizer import SkeletonizerRegistry
from plugins.memory_and_epistemics.context_compiler.compiler_core.symbol_resolver import SymbolResolver


class ContextCompiler:
    """Orchestrates 3-tier AST context compilation for agent workflows."""

    def __init__(self, repo_root: str | Path, max_hops: int = 2) -> None:
        self.root = Path(repo_root).resolve()
        self.max_hops = max_hops
        self.resolver = SymbolResolver(self.root, max_hops=max_hops)

    def compile(self, target_file: str | Path) -> CompiledContext:
        """Compile a 3-tier bounded context representation for target file."""
        start = time.perf_counter()
        target_path = Path(target_file).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Target file does not exist: {target_path}")

        target_source = target_path.read_text(encoding="utf-8")
        reachability = self.resolver.resolve(target_path)

        entries = [
            TierEntry(
                path=target_path,
                tier=1,
                content=target_source,
                tokens=estimate_tokens(target_source),
                hop_distance=0,
            )
        ]

        for dep_path, hop in sorted(reachability.reachable.items(), key=lambda kv: kv[1]):
            try:
                source = dep_path.read_text(encoding="utf-8", errors="replace")
                skeleton, _ = SkeletonizerRegistry.skeletonize(dep_path, source)
            except Exception:
                continue
            entries.append(
                TierEntry(
                    path=dep_path,
                    tier=2,
                    content=skeleton,
                    tokens=estimate_tokens(skeleton),
                    hop_distance=hop,
                )
            )

        all_py_files = list(self.resolver.index.path_to_module.keys())
        included_paths = {e.path for e in entries}
        excluded_count = max(0, len(all_py_files) - len(included_paths))

        naive_dump_tokens = 0
        for path in all_py_files:
            try:
                naive_dump_tokens += estimate_tokens(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue

        compiled_tokens = sum(e.tokens for e in entries)

        return CompiledContext(
            target_file=target_path,
            entries=entries,
            excluded_count=excluded_count,
            total_repo_files=len(all_py_files),
            naive_dump_tokens=naive_dump_tokens,
            compiled_tokens=compiled_tokens,
            build_seconds=time.perf_counter() - start,
            diagnostics=reachability,
        )
