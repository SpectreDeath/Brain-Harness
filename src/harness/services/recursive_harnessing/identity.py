"""Trial identity: was this rollout finished, and by this exact configuration?

Distilled from google/harness2 `core.runmark`. Completion is recorded explicitly by the code
that observed the run return -- presence of output is never evidence of completion. The marker
fingerprints the harness that produced the rollout and, optionally, the task inputs it
answered, so a rollout from a different configuration is never reused.

Improvements over the source: paths are hashed in POSIX form (identical digests on Windows and
Linux), files are hashed in bounded chunks, a corrupt marker is logged rather than swallowed
(Rule 32), and traversal is depth-bounded and pruned (Rule 52).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections.abc import Mapping
from pathlib import Path

import structlog

from harness.services.recursive_harnessing.guards import iter_files

logger = structlog.get_logger(__name__)

MARK = ".refine_complete"
VERSION = 1
_HASH_DEPTH = 16
_CHUNK = 1024 * 1024


def _ignored(p: Path) -> bool:
    """Byproducts that are not part of the harness and must not change its identity."""
    return "__pycache__" in p.parts or p.suffix == ".pyc" or p.name in (".DS_Store", MARK)


def _feed_file(h: "hashlib._Hash", path: Path) -> None:
    try:
        with path.open("rb") as fh:
            while chunk := fh.read(_CHUNK):
                h.update(chunk)
    except OSError as exc:
        logger.warning("fingerprint_unreadable", path=str(path), error=str(exc))
        h.update(b"<unreadable>")


def _feed_dir(h: "hashlib._Hash", root: Path) -> None:
    for p in iter_files(root, max_depth=_HASH_DEPTH):
        if _ignored(p):
            continue
        h.update(p.relative_to(root).as_posix().encode())
        h.update(b"\0")
        _feed_file(h, p)
        h.update(b"\0")


def fingerprint_dir(harness_dir: Path | str | None) -> str:
    """Stable digest of the harness directory that produced a rollout.

    `None` is a rollout on the inherited base harness and digests to the shared value
    "base"; a missing directory digests to "absent".
    """
    if harness_dir is None:
        return "base"
    root = Path(harness_dir)
    if not root.is_dir():
        return "absent"
    h = hashlib.sha1()
    _feed_dir(h, root)
    return h.hexdigest()[:16]


def fingerprint_tree(tree: Mapping[str, str]) -> str:
    """Stable digest of an in-memory harness tree (order-independent)."""
    h = hashlib.sha1()
    for rel in sorted(tree):
        h.update(rel.replace("\\", "/").encode())
        h.update(b"\0")
        h.update(str(tree[rel]).encode("utf-8", errors="replace"))
        h.update(b"\0")
    return h.hexdigest()[:16]


def inputs_fingerprint(task_prompt: str, files_dir: Path | str | None) -> str:
    """Digest of what the agent was asked and what it was given (prompt text + source files)."""
    h = hashlib.sha1()
    h.update(b"prompt\0" + str(task_prompt).encode() + b"\0")
    if files_dir is not None and Path(files_dir).is_dir():
        _feed_dir(h, Path(files_dir))
    return h.hexdigest()[:16]


def call_fingerprint(label: str, mission: str, system: str, context_dir: Path | str | None) -> str:
    """Content-address one proposer session, including its evidence and workspace path.

    The resolved path is part of the key: two recursion modes may have byte-identical evidence
    and must still be independent draws.
    """
    h = hashlib.sha256()
    for value in (label, mission, system):
        h.update(value.encode("utf-8", errors="replace") + b"\0")
    if context_dir:
        root = Path(context_dir)
        h.update(str(root.resolve()).encode("utf-8", errors="replace") + b"\0")
        if root.is_dir():
            _feed_dir(h, root)
    return h.hexdigest()[:16]


def mark_complete(
    where: Path | str,
    *,
    run_id: str,
    harness_dir: Path | str | None = None,
    inputs: str | None = None,
    extra: Mapping[str, object] | None = None,
) -> Path:
    """Atomically record that `run_id` finished. Call only after the runner returned normally."""
    d = Path(where)
    d.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "version": VERSION,
        "run_id": run_id,
        "at": time.time(),
        "harness": fingerprint_dir(harness_dir),
        **dict(extra or {}),
    }
    if inputs is not None:
        payload["inputs"] = inputs
    tmp = d / f"{MARK}.{os.getpid()}.{threading.get_ident()}.tmp"
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    final = d / MARK
    os.replace(tmp, final)
    return final


def read_mark(where: Path | str) -> dict | None:
    """The marker dict, or None when absent/corrupt (corruption is logged)."""
    path = Path(where) / MARK
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("trial_marker_corrupt", path=str(path), error=str(exc))
        return None
    return data if isinstance(data, dict) else None


def _inputs_match(mark: Mapping[str, object], inputs: str | None) -> bool:
    """Legacy markers carry no input identity and are not invalidated by its arrival."""
    recorded = mark.get("inputs")
    return recorded is None or inputs is None or recorded == inputs


def is_complete(
    where: Path | str,
    *,
    harness_dir: Path | str | None = None,
    match_harness: bool = True,
    inputs: str | None = None,
) -> bool:
    """Whether artifacts at `where` may be reused: a current marker naming the same harness
    and task inputs, unless either comparison is switched off."""
    mark = read_mark(where)
    if not mark or mark.get("version") != VERSION:
        return False
    if not _inputs_match(mark, inputs):
        return False
    return (not match_harness) or mark.get("harness") == fingerprint_dir(harness_dir)


def why_not(where: Path | str, *, harness_dir: Path | str | None = None, inputs: str | None = None) -> str:
    """A sentence for a log line explaining why `where` is or is not reusable."""
    mark = read_mark(where)
    if not mark:
        return f"no {MARK} -- never finished, corrupt, or finished before completion was recorded"
    if mark.get("version") != VERSION:
        return f"marker version {mark.get('version')} != {VERSION}"
    if not _inputs_match(mark, inputs):
        return f"task inputs {mark.get('inputs')} != {inputs} -- the task changed since this rollout"
    want, got = fingerprint_dir(harness_dir), mark.get("harness")
    if want != got:
        return f"harness fingerprint {got} != {want} -- produced by a different configuration"
    return "reusable"
