"""Evidence-isolation tripwires: no oracle may reach a model that is adapting a harness.

Distilled from google/harness2 `core.context`. Hardened relative to the source: traversal is
depth-bounded and noise-pruned (Rule 52) and *fails closed* when it cannot look everywhere;
content scans are chunked (bounded memory) with boundary overlap so a marker straddling two
chunks is still found; unreadable files are logged, never silently skipped (Rule 32).
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

GRADER_VERDICT_MARKERS: tuple[str, ...] = (
    "deterministic_eval_summary",
    "deterministic_eval_result",
    "judge_scope_and_deterministic_status",
    "Judge findings on the rendered result",
    '"passed_count"',
    '"pass_rate"',
    '"test_pass_rate"',
)

SCAN_SUFFIXES = frozenset(
    {
        ".md",
        ".txt",
        ".json",
        ".csv",
        ".tsv",
        ".yaml",
        ".yml",
        ".html",
        ".htm",
        ".log",
        ".py",
        ".js",
        ".sh",
        ".xml",
        ".ini",
        ".toml",
        ".patch",
        ".diff",
        "",
    }
)
PRUNE_DIRS = frozenset({".git", "node_modules", ".venv", "__pycache__", "target", "dist", ".gemini"})
DEFAULT_MAX_DEPTH = 8
CHUNK_CHARS = 1024 * 1024

SCRUB_ENV = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "SLACK_BOT_TOKEN",
        "SLACK_WEBHOOK_URL",
        "JIRA_API_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_BEARER_TOKEN_BEDROCK",
        "HF_TOKEN",
        "HARNESS_JUDGE_API_KEY",
        "HARNESS_BRIDGE_KEY",
    }
)


class EvidenceLeakError(ValueError):
    """An oracle (answer key or grader verdict) would have entered model context."""


class TraversalDepthError(EvidenceLeakError):
    """A bounded walk met a tree deeper than allowed and refuses to certify the remainder."""


def iter_files(root: Path | str, *, max_depth: int = DEFAULT_MAX_DEPTH) -> Iterator[Path]:
    """Yield files under `root`, pruning noise dirs; raise if the tree is deeper than allowed.

    Raising (rather than silently stopping) keeps a tripwire from reporting "clean" about
    a region it never inspected.
    """
    base = Path(root)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in PRUNE_DIRS)
        depth = len(Path(dirpath).relative_to(base).parts)
        if depth >= max_depth and dirnames:
            raise TraversalDepthError(
                f"evidence tree under {base} is deeper than max_depth={max_depth}; "
                f"refusing to certify it clean without scanning it"
            )
        for name in sorted(filenames):
            yield Path(dirpath) / name


def assert_no_leak_paths(root: Path | str, patterns: Sequence[str], *, max_depth: int = DEFAULT_MAX_DEPTH) -> None:
    """Reject benchmark-declared answer-key paths before a context reaches a model."""
    base = Path(root)
    if not patterns or not base.is_dir():
        return
    pats = [str(p).replace("\\", "/").lstrip("./") for p in patterns]
    hits = []
    for p in iter_files(base, max_depth=max_depth):
        rel = p.relative_to(base).as_posix()
        if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, f"*/{pat}") for pat in pats):
            hits.append(rel)
    if hits:
        raise EvidenceLeakError("answer-key path(s) would enter model context: " + ", ".join(sorted(hits)[:8]))


def _find_marker(path: Path, markers: Sequence[str]) -> tuple[str, int] | None:
    """Chunked substring scan returning (marker, char offset) of the first hit, if any."""
    keep = max(len(m) for m in markers) - 1
    tail, offset = "", 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        while chunk := fh.read(CHUNK_CHARS):
            buf = tail + chunk
            for marker in markers:
                idx = buf.find(marker)
                if idx >= 0:
                    return marker, offset - len(tail) + idx
            tail = buf[-keep:] if keep > 0 else ""
            offset += len(chunk)
    return None


def assert_no_verdicts(
    root: Path | str,
    markers: Sequence[str] = GRADER_VERDICT_MARKERS,
    *,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> None:
    """Refuse a context tree containing grader output, by file name and by content.

    A tripwire on the adapters' read boundary, not the defence itself: when it fires, find
    the read path that produced the match instead of widening the marker list.
    """
    base = Path(root)
    if not markers or not base.is_dir():
        return
    for p in iter_files(base, max_depth=max_depth):
        rel = p.relative_to(base).as_posix()
        for m in markers:
            if m in rel:
                raise EvidenceLeakError(
                    f"grader verdict would enter model context: {rel!r} matched marker "
                    f"{m!r} in its NAME. This is a leak, not a false positive to widen around."
                )
        if p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            hit = _find_marker(p, markers)
        except OSError as exc:
            logger.warning("verdict_scan_unreadable", path=rel, error=str(exc))
            raise EvidenceLeakError(f"cannot certify {rel!r} clean: unreadable ({exc})") from exc
        if hit:
            raise EvidenceLeakError(
                f"grader verdict would enter model context: {rel!r} contains marker "
                f"{hit[0]!r} at offset {hit[1]}. This is a leak, not a false positive."
            )


def assert_tree_clean(tree: Mapping[str, str], markers: Sequence[str] = GRADER_VERDICT_MARKERS) -> None:
    """The same tripwire on an agent-authored harness tree (rel -> body), before it is stored."""
    for rel in sorted(tree):
        for m in markers:
            if m in rel:
                raise EvidenceLeakError(f"harness file {rel!r} has grader-verdict marker {m!r} in its NAME; rename it")
        if Path(rel).suffix.lower() not in SCAN_SUFFIXES:
            continue
        body = str(tree[rel])
        for m in markers:
            if m in body:
                at = body.index(m)
                raise EvidenceLeakError(
                    f"harness file {rel!r} contains grader-verdict marker {m!r} at offset {at} "
                    f"({body[max(0, at - 40) : at + 80]!r}); remove it"
                )


def scrub_env(base_env: Mapping[str, str] | None = None, *, keep: Iterable[str] = ()) -> dict[str, str]:
    """Copy `base_env` (default `os.environ`) with runner and host secrets removed."""
    src = os.environ if base_env is None else base_env
    drop = SCRUB_ENV - set(keep)
    return {k: v for k, v in src.items() if k not in drop}
