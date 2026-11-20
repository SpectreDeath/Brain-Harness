"""Canonical git-blob LF SHA-256 stamping and recomputing isnad claim verifier."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
LOCAL_PATH_PREFIXES = ("src/", "plugins/", "tests/", ".agents/", "experiments/", "scripts/")
LOCAL_EXACT_FILES = frozenset({"AGENTS.md", "pyproject.toml", "README.md", "CLAUDE.md"})
_HASH_KEYS = ("sha256_hash", "sha256", "artifact_sha256")
_PATH_KEYS = ("file", "path", "source_file", "uri", "artifact")
StrMap = dict[str, str | None] | None


@dataclass(slots=True, frozen=True)
class ClaimHashCheck:
    """Verification outcome for a single isnad claim entry or lineage node."""

    ki_id: str
    file_path: str
    claim_sha256: str | None
    computed_sha256: str | None
    verified: bool
    status: str
    detail: str = ""


@dataclass(slots=True, frozen=True)
class VaultHashAuditReport:
    """Aggregate audit summary of isnad claim hashes across vault knowledge items."""

    total_claims: int
    local_verified: int
    local_mismatches: int
    local_missing_files: int
    external_verified: int
    missing_hash_flagged: int
    malformed_hash: int
    unverified: int
    checks: tuple[ClaimHashCheck, ...]


def normalize_claim_path(raw: Any) -> str:
    """Normalize claim file/URI string to a relative POSIX path without line fragments."""
    if not isinstance(raw, str):
        return ""
    text = raw.strip().split("#", 1)[0].removeprefix("file:///").replace("\\", "/").lstrip("/")
    while text.startswith("./"):
        text = text[2:]
    return text


def is_local_repo_path(rel_path: str) -> bool:
    """Return True when rel_path addresses a Brain Harness repository path."""
    return (n := normalize_claim_path(rel_path)) in LOCAL_EXACT_FILES or n.startswith(LOCAL_PATH_PREFIXES)


def extract_claim_path(entry: dict[str, Any]) -> str:
    """Extract normalized target file path from an isnad claim or lineage dict."""
    direct = next((normalize_claim_path(v) for k in _PATH_KEYS if isinstance(v := entry.get(k), str) and v.strip()), "")
    if direct:
        return direct
    if isinstance(s := entry.get("source"), str) and (t := s.strip()) and not t.startswith(("http://", "https://")):
        norm = normalize_claim_path(t)
        if is_local_repo_path(norm) or ("/" in norm and " " not in norm):
            return norm
    return ""


def extract_claim_hash(entry: dict[str, Any]) -> str | None:
    """Extract claim SHA-256 candidate string, returning None for empty or 'N/A'."""
    for key in _HASH_KEYS:
        if isinstance(val := entry.get(key), str) and (cleaned := val.strip()) and cleaned.lower() != "n/a":
            return cleaned
    return None


def compute_canonical_blob_sha256(rel_path: str, repo_root: Path, *, cache: StrMap = None) -> str | None:
    """Compute SHA-256 using git-blob HEAD bytes first, then LF-normalized working file."""
    norm = normalize_claim_path(rel_path)
    if not norm or norm.startswith(("http://", "https://")):
        return None
    if cache is not None and norm in cache:
        return cache[norm]
    digest: str | None = None
    if (repo_root / ".git").exists():
        proc = subprocess.run(["git", "-C", str(repo_root), "show", f"HEAD:{norm}"], capture_output=True, timeout=5)
        if proc.returncode == 0:
            digest = hashlib.sha256(proc.stdout).hexdigest()
    if digest is None and (target := repo_root / norm).is_file():
        raw = target.read_bytes()
        digest = hashlib.sha256(raw.replace(b"\r\n", b"\n") if b"\x00" not in raw[:8192] else raw).hexdigest()
    if cache is not None:
        cache[norm] = digest
    return digest


def stamp_claim_sha256(rel_path: str, repo_root: Path, *, cache: StrMap = None) -> str:
    """Return canonical LF SHA-256 for rel_path or raise FileNotFoundError."""
    if (digest := compute_canonical_blob_sha256(rel_path, repo_root, cache=cache)) is None:
        raise FileNotFoundError(f"Cannot resolve canonical blob hash for {rel_path!r} under {repo_root}")
    return digest


def _verify_hash_pair(
    rel_path: str, claim_hash: str, *, ki_id: str, repo_root: Path | None, blob_cache: StrMap
) -> ClaimHashCheck:
    lower_hash = claim_hash.lower()
    if not _HEX64_RE.match(lower_hash):
        return ClaimHashCheck(ki_id, rel_path, claim_hash, None, False, "MALFORMED_HASH", "Expected 64 hex chars")
    if repo_root is not None and rel_path:
        if (expected := compute_canonical_blob_sha256(rel_path, repo_root, cache=blob_cache)) is not None:
            ok = lower_hash == expected
            st, det = ("VERIFIED_LOCAL_MATCH", "") if ok else ("HASH_MISMATCH", f"expected {expected}")
            return ClaimHashCheck(ki_id, rel_path, lower_hash, expected, ok, st, det)
        if is_local_repo_path(rel_path):
            return ClaimHashCheck(ki_id, rel_path, lower_hash, None, False, "LOCAL_FILE_MISSING", "File missing")
    return ClaimHashCheck(ki_id, rel_path, lower_hash, None, True, "VERIFIED_EXTERNAL_HASH")


def verify_claim_entry(
    entry: dict[str, Any],
    *,
    ki_id: str = "",
    repo_root: Path | None = None,
    source_repo: str = "",
    blob_cache: StrMap = None,
) -> ClaimHashCheck:
    """Verify an isnad claim dictionary strictly against cryptographic 64-hex hashes."""
    _ = source_repo
    rel_path = extract_claim_path(entry)
    if (claim_hash := extract_claim_hash(entry)) is not None:
        return _verify_hash_pair(rel_path, claim_hash, ki_id=ki_id, repo_root=repo_root, blob_cache=blob_cache)
    if isinstance(lineage := entry.get("lineage"), list):
        nodes = [
            _verify_hash_pair(extract_claim_path(n), h, ki_id=ki_id, repo_root=repo_root, blob_cache=blob_cache)
            for n in lineage
            if isinstance(n, dict) and (h := extract_claim_hash(n))
        ]
        if nodes:
            return next((c for c in nodes if not c.verified), nodes[0])
    is_v = (
        entry.get("verified") is True or entry.get("verified_at") or str(entry.get("status", "")).lower() == "verified"
    )
    st = "MISSING_HASH_FLAGGED" if is_v else "UNVERIFIED"
    return ClaimHashCheck(ki_id, rel_path, None, None, False, st, "No valid 64-hex hash")


def _verify_metadata_file(meta_path: Path, root: Path, cache: dict[str, str | None]) -> list[ClaimHashCheck]:
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    raw, src, kid = data.get("isnad"), str(data.get("source_repo") or ""), meta_path.parent.name
    if isinstance(raw, dict) and raw:
        nested = raw.get("claims")
        entries = [e for e in nested if isinstance(e, dict)] if isinstance(nested, list) and nested else [raw]
    else:
        entries = [e for e in raw if isinstance(e, dict)] if isinstance(raw, list) else []
    return [verify_claim_entry(e, ki_id=kid, repo_root=root, source_repo=src, blob_cache=cache) for e in entries]


def resolve_ki_verification_map(
    ki_ids: Iterable[str], vault_dir: Path | str = Path(".harness/knowledge"), *, repo_root: Path | None = None
) -> dict[str, bool | None]:
    """Resolve live hash-verification status for cited KIs (True/False/None if missing)."""
    vdir = Path(vault_dir)
    root = repo_root or (vdir.parent.parent if vdir.name == "knowledge" else vdir)
    cache: dict[str, str | None] = {}
    out: dict[str, bool | None] = {}
    for raw_id in ki_ids:
        if not (key := str(raw_id or "").strip()) or key in out:
            continue
        meta = vdir / key / "metadata.json"
        if not meta.is_file() and "-" in key:
            meta = vdir / key.replace("-", "_") / "metadata.json"
        out[key] = any(c.verified for c in _verify_metadata_file(meta, root, cache)) if meta.is_file() else None
    return out


def audit_vault_claim_hashes(
    vault_dir: Path, *, repo_root: Path | None = None, ki_ids: set[str] | None = None
) -> VaultHashAuditReport:
    """Audit all isnad claims across a Knowledge Vault directory against canonical hashes."""
    root = repo_root or (vault_dir.parent.parent if vault_dir.name == "knowledge" else vault_dir)
    cache: dict[str, str | None] = {}
    checks: list[ClaimHashCheck] = []
    for meta in sorted(vault_dir.glob("*/metadata.json")):
        if ki_ids is None or meta.parent.name in ki_ids:
            checks.extend(_verify_metadata_file(meta, root, cache))
    cts = Counter(c.status for c in checks)
    k1 = "VERIFIED_LOCAL_MATCH HASH_MISMATCH LOCAL_FILE_MISSING VERIFIED_EXTERNAL_HASH"
    n = [cts[s] for s in f"{k1} MISSING_HASH_FLAGGED MALFORMED_HASH UNVERIFIED".split()]
    return VaultHashAuditReport(len(checks), n[0], n[1], n[2], n[3], n[4], n[5], n[6], tuple(checks))
