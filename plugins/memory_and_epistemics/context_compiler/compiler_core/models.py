"""Slotted domain models and container representations for context compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FileSymbols:
    """Symbols and AST features discovered within a single source file."""

    imported_modules: set[str] = field(default_factory=set)
    called_names: set[str] = field(default_factory=set)
    defined_names: set[str] = field(default_factory=set)
    uses_dynamic_dispatch: bool = False
    uses_decorators: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ReachabilityResult:
    """Graph traversal reachability and symbol resolution diagnostics."""

    reachable: dict[Path, int] = field(default_factory=dict)  # path -> hop distance
    unresolved_calls: set[str] = field(default_factory=set)
    dynamic_dispatch_files: set[Path] = field(default_factory=set)
    decorator_hint_files: dict[Path, set[str]] = field(default_factory=dict)
    name_collisions: dict[str, list[Path]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert reachability diagnostics to serialized dictionary."""
        return {
            "reachable_files": {str(k): v for k, v in self.reachable.items()},
            "unresolved_calls": sorted(self.unresolved_calls),
            "dynamic_dispatch_files": [str(p) for p in self.dynamic_dispatch_files],
            "decorator_hint_files": {str(k): sorted(v) for k, v in self.decorator_hint_files.items()},
            "name_collisions": {k: [str(p) for p in v] for k, v in self.name_collisions.items()},
        }


@dataclass(slots=True, frozen=True)
class TierEntry:
    """Immutable entry in a multi-tier compiled context window."""

    path: Path
    tier: int
    content: str
    tokens: int
    hop_distance: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize tier entry to dictionary."""
        return {
            "path": str(self.path),
            "tier": self.tier,
            "tokens": self.tokens,
            "hop_distance": self.hop_distance,
        }


@dataclass(slots=True)
class CompiledContext:
    """Orchestrated compilation output containing multi-tier prompt and diagnostics."""

    target_file: Path
    entries: list[TierEntry] = field(default_factory=list)
    excluded_count: int = 0
    total_repo_files: int = 0
    naive_dump_tokens: int = 0
    compiled_tokens: int = 0
    build_seconds: float = 0.0
    diagnostics: ReachabilityResult | None = None

    def to_prompt_string(self) -> str:
        """Render tiered prompt payload for model ingestion."""
        parts = []
        for entry in self.entries:
            label = "FULL SOURCE" if entry.tier == 1 else "SKELETON"
            parts.append(f"# ---- [{label}] {entry.path} ----\n{entry.content}")
        return "\n\n".join(parts)

    def reduction_pct(self) -> float:
        """Calculate token reduction percentage relative to naive full dump."""
        if self.naive_dump_tokens == 0:
            return 0.0
        return 100.0 * (1.0 - (self.compiled_tokens / self.naive_dump_tokens))

    def summary(self) -> str:
        """Generate human-readable summary of compiled context."""
        tier2 = sum(1 for e in self.entries if e.tier == 2)
        lines = [
            f"Target file: {self.target_file}",
            f"Repo files scanned: {self.total_repo_files}",
            "Tier 1 (full source): 1 file",
            f"Tier 2 (skeletonized): {tier2} files",
            f"Tier 3 (excluded): {self.excluded_count} files",
            f"Naive full-dump estimate: {self.naive_dump_tokens} tokens",
            f"Compiled context: {self.compiled_tokens} tokens",
            f"Reduction: {self.reduction_pct():.1f}%",
            f"Build time: {self.build_seconds * 1000:.2f} ms",
        ]
        if self.diagnostics:
            if self.diagnostics.dynamic_dispatch_files:
                lines.append(
                    f"Warning: {len(self.diagnostics.dynamic_dispatch_files)} file(s) use "
                    f"getattr()-based dynamic dispatch — targets may be missing from tier 2."
                )
            if self.diagnostics.decorator_hint_files:
                lines.append(
                    f"Warning: {len(self.diagnostics.decorator_hint_files)} file(s) use "
                    f"event-style decorators — handlers may be missing from tier 2."
                )
            if self.diagnostics.name_collisions:
                lines.append(
                    f"Note: {len(self.diagnostics.name_collisions)} call name(s) resolved to "
                    f"more than one file — tier 2 may include false positives."
                )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert complete compilation payload to dictionary."""
        return {
            "target_file": str(self.target_file),
            "total_repo_files": self.total_repo_files,
            "tier1_files": 1,
            "tier2_files": sum(1 for e in self.entries if e.tier == 2),
            "tier3_excluded_files": self.excluded_count,
            "naive_dump_tokens": self.naive_dump_tokens,
            "compiled_tokens": self.compiled_tokens,
            "reduction_pct": round(self.reduction_pct(), 2),
            "build_ms": round(self.build_seconds * 1000, 2),
            "entries": [e.to_dict() for e in self.entries],
            "diagnostics": self.diagnostics.to_dict() if self.diagnostics else None,
            "summary": self.summary(),
        }
