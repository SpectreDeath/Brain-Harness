"""Tree filesystem I/O, diff summarization, and candidate diversity measurement.

Distilled from google-research/harness2 `core.tree`.
"""

from __future__ import annotations

from pathlib import Path

from harness.services.recursive_harnessing.guards import iter_files
from harness.services.recursive_harnessing.models import SurfaceSpec, Tree

_READ_DEPTH = 12


def read_tree(
    spec: SurfaceSpec,
    d: Path | str,
    *,
    rejected: list[str] | None = None,
    is_allowed_fn=None,
) -> Tree:
    """rel -> content for every file on the editable surface; off-surface paths go to `rejected`."""
    from harness.services.recursive_harnessing.surface import is_allowed

    allowed = is_allowed_fn or (lambda rel: is_allowed(spec, rel))
    root, out = Path(d), {}
    if not root.is_dir():
        return out
    for p in iter_files(root, max_depth=_READ_DEPTH):
        rel = p.relative_to(root).as_posix()
        if not allowed(rel):
            if rejected is not None:
                rejected.append(rel)
            continue
        out[rel] = p.read_text(encoding="utf-8", errors="replace")
    return out


def write_tree(
    spec: SurfaceSpec,
    tree: Tree,
    dest: Path | str,
    *,
    is_allowed_fn=None,
    normalize_fn=None,
) -> Path:
    """Materialise an exact editable tree; files outside the editable surface are preserved."""
    from harness.services.recursive_harnessing.surface import is_allowed, normalize_rel

    allowed = is_allowed_fn or (lambda rel: is_allowed(spec, rel))
    norm = normalize_fn or normalize_rel

    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)
    for p in list(iter_files(root, max_depth=_READ_DEPTH)):
        if allowed(p.relative_to(root).as_posix()):
            p.unlink()
    for a in spec.always_on:
        if a not in tree and not (root / a).exists():
            (root / a).parent.mkdir(parents=True, exist_ok=True)
            (root / a).write_text("", encoding="utf-8")
    for rel, content in tree.items():
        target = root / norm(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def diff_summary(spec: SurfaceSpec, before: Tree, after: Tree) -> dict:
    from harness.services.recursive_harnessing.surface import always_on_text

    return {
        "added": sorted(set(after) - set(before)),
        "removed": sorted(set(before) - set(after)),
        "modified": sorted(r for r in set(before) & set(after) if before[r] != after[r]),
        "always_on_char_delta": len(always_on_text(spec, after)) - len(always_on_text(spec, before)),
    }


def diversity(trees: dict[str, Tree]) -> dict:
    """Pairwise line-Jaccard over candidate trees, so collapse to one body is visible."""
    names = sorted(trees)
    if len(names) < 2:
        return {"n": len(names), "n_distinct": len(names), "mean_line_jaccard": 1.0}
    sets = {n: {f"{r}:{ln}" for r, c in trees[n].items() for ln in c.splitlines() if ln.strip()} for n in names}
    sims = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            u = sets[a] | sets[b]
            sims.append(len(sets[a] & sets[b]) / len(u) if u else 1.0)
    distinct = len({tuple(sorted(t.items())) for t in trees.values()})
    return {"n": len(names), "n_distinct": distinct, "mean_line_jaccard": round(sum(sims) / len(sims), 4)}

