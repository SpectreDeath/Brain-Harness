"""Human-readable diff review and digest approval guard for proposed spawn trees (Rules 12, 43)."""

from __future__ import annotations

import difflib
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.models import SurfaceSpec


@dataclass(slots=True, frozen=True)
class TreeDiffReview:
    """Auditable diff and SHA-256 approval summary across proposed tree edits."""

    tree_sha256: str
    base_sha256: str
    added: tuple[str, ...]
    modified: tuple[str, ...]
    removed: tuple[str, ...]
    unified_diff: str
    approved: bool = False
    approved_digest: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "tree_sha256": self.tree_sha256,
            "base_sha256": self.base_sha256,
            "added": list(self.added),
            "modified": list(self.modified),
            "removed": list(self.removed),
            "unified_diff": self.unified_diff,
            "approved": self.approved,
            "approved_digest": self.approved_digest,
        }


def compute_tree_sha256(tree: Mapping[str, str]) -> str:
    """Compute a deterministic canonical SHA-256 digest over normalized relative tree entries."""
    normalized = {surface_ops.normalize_rel(str(k)): str(v) for k, v in sorted(tree.items())}
    canonical = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_tree_diff_review(
    surface: SurfaceSpec,
    base_tree: Mapping[str, str],
    proposed_tree: Mapping[str, str],
    *,
    approved_digest: str | None = None,
) -> TreeDiffReview:
    """Build a human-readable unified diff and canonical digest review for a proposed tree."""
    diff = surface_ops.diff_summary(surface, base_tree, proposed_tree)
    all_paths = sorted(set(base_tree) | set(proposed_tree))
    chunks: list[str] = []
    for rel in all_paths:
        old_lines = base_tree.get(rel, "").splitlines(keepends=True)
        new_lines = proposed_tree.get(rel, "").splitlines(keepends=True)
        if old_lines == new_lines:
            continue
        chunks.extend(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{rel}" if rel in base_tree else "/dev/null",
                tofile=f"b/{rel}" if rel in proposed_tree else "/dev/null",
            )
        )
    tree_sha = compute_tree_sha256(proposed_tree)
    base_sha = compute_tree_sha256(base_tree)
    normalized_approval = (approved_digest or "").strip().lower()
    return TreeDiffReview(
        tree_sha256=tree_sha,
        base_sha256=base_sha,
        added=tuple(diff["added"]),
        modified=tuple(diff["modified"]),
        removed=tuple(diff["removed"]),
        unified_diff="".join(chunks),
        approved=bool(normalized_approval and normalized_approval == tree_sha),
        approved_digest=normalized_approval,
    )


def verify_diff_approval(proposed_tree: Mapping[str, str], *, approved_digest: str | None) -> str:
    """Fail-closed trust-boundary check requiring an explicit matching digest before write-enabled spawn."""
    live_sha = compute_tree_sha256(proposed_tree)
    supplied = (approved_digest or "").strip().lower()
    if not supplied:
        raise ValueError(f"Write-permitted spawn requires approved_tree_digest matching live tree digest {live_sha}")
    if supplied != live_sha:
        raise ValueError(
            f"Proposed tree digest drift: approved_tree_digest={supplied} does not match live tree={live_sha}"
        )
    return live_sha


__all__ = [
    "TreeDiffReview",
    "build_tree_diff_review",
    "compute_tree_sha256",
    "verify_diff_approval",
]
