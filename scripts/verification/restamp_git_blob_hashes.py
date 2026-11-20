"""Idempotent git-blob LF SHA-256 restamping and vault claim hash audit."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).resolve().parents[2]
VAULT = WORKSPACE / ".harness" / "knowledge"

if str(WORKSPACE / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE / "src"))
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from harness.services.storage.isnad_hash import (  # noqa: E402
    VaultHashAuditReport,
    audit_vault_claim_hashes,
    is_local_repo_path,
    stamp_claim_sha256,
)
from plugins.memory_and_epistemics.ontology_spider.adapter import HarnessVaultModelSource  # noqa: E402

PHASE5_VERIFIED_KIS = (
    "ki_20261014_70_cycle_deepening_corpus",
    "ki_agent_skills_progressive_disclosure",
    "ki_google_repos_bridge",
    "ki_njoku_uncertainty_aware_systems",
    "ki_self_20260907_02",
    "ki_self_20260907_03",
    "ki_solla_dikw_data_asset_continuum",
    "ki_solla_dmbok_governance_decision_rights",
)

PROVENANCE_NOTE = (
    "Hashes computed over canonical git-blob (LF) bytes via "
    "harness.services.storage.isnad_hash.stamp_claim_sha256 (never raw working-tree CRLF)."
)


def _touched_28_kis() -> set[str]:
    proc = subprocess.run(
        ["git", "-C", str(WORKSPACE), "show", "--name-only", "--pretty=", "120c201", "757bc2e", "2edb03d"],
        capture_output=True,
        text=True,
        check=True,
    )
    kis: set[str] = set()
    for line in proc.stdout.splitlines():
        if line.startswith(".harness/knowledge/"):
            parts = line.split("/")
            if len(parts) >= 3:
                kis.add(parts[2])
    return kis


def _assert_partition_sum(label: str, report: VaultHashAuditReport) -> None:
    accounted = (
        report.local_verified
        + report.local_mismatches
        + report.local_missing_files
        + report.external_verified
        + report.missing_hash_flagged
        + report.malformed_hash
        + report.unverified
    )
    assert accounted == report.total_claims, f"{label}: sum {accounted} != total_claims {report.total_claims}"


def main() -> None:
    cache: dict[str, str | None] = {}
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    restamped_claims = 0

    for ki_id in PHASE5_VERIFIED_KIS:
        meta_path = VAULT / ki_id / "metadata.json"
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        isnad = data.get("isnad")
        assert isinstance(isnad, dict), f"Expected isnad dict in {ki_id}"
        ki_changed = False
        for claim in isnad.get("claims") or []:
            if not isinstance(claim, dict):
                continue
            rel = str(claim.get("file") or "")
            if rel and is_local_repo_path(rel):
                canonical = stamp_claim_sha256(rel, WORKSPACE, cache=cache)
                if claim.get("sha256_hash") != canonical:
                    print(f"Restamping {ki_id} :: {rel}: {claim.get('sha256_hash')} -> {canonical}")
                    claim["sha256_hash"] = canonical
                    restamped_claims += 1
                    ki_changed = True
        if ki_changed or isnad.get("hash_method") != "git_blob_lf_sha256":
            isnad["hash_method"] = "git_blob_lf_sha256"
            isnad["hash_restamped_at"] = now_iso
            isnad["provenance_note"] = PROVENANCE_NOTE
            meta_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"Restamped {restamped_claims} mismatched claim hashes across {len(PHASE5_VERIFIED_KIS)} KIs.")

    touched_28 = _touched_28_kis()
    print(f"Touched KIs across (120c201, 757bc2e, 2edb03d): {len(touched_28)}")
    r28 = audit_vault_claim_hashes(VAULT, repo_root=WORKSPACE, ki_ids=touched_28)
    print(
        f"28-KI Audit: total={r28.total_claims} local_verified={r28.local_verified} "
        f"external_verified={r28.external_verified} missing_hash_flagged={r28.missing_hash_flagged} "
        f"unverified={r28.unverified} local_mismatches={r28.local_mismatches} "
        f"local_missing={r28.local_missing_files} malformed={r28.malformed_hash}"
    )

    _assert_partition_sum("28-KI Audit", r28)
    assert r28.local_mismatches == 0, (
        f"Local mismatches remain: {[c for c in r28.checks if c.status == 'HASH_MISMATCH']}"
    )
    assert r28.local_verified == 22, f"Expected 22 local verified, got {r28.local_verified}"
    assert r28.external_verified == 16, f"Expected 16 external verified, got {r28.external_verified}"

    r_all = audit_vault_claim_hashes(VAULT, repo_root=WORKSPACE)
    print(
        f"Full-Vault Audit: total={r_all.total_claims} local_verified={r_all.local_verified} "
        f"external_verified={r_all.external_verified} missing_hash_flagged={r_all.missing_hash_flagged} "
        f"unverified={r_all.unverified} local_mismatches={r_all.local_mismatches} "
        f"local_missing={r_all.local_missing_files} malformed={r_all.malformed_hash}"
    )
    _assert_partition_sum("Full-Vault Audit", r_all)
    assert r_all.local_mismatches == 0, (
        f"Vault local mismatches: {[c for c in r_all.checks if c.status == 'HASH_MISMATCH']}"
    )

    model = HarnessVaultModelSource(VAULT, repo_root=WORKSPACE).load()
    verified_ents = [e for e in model.entities.values() if e.attributes.get("isnad_verified") is True]
    print(f"Loaded OntologyModel entities={len(model.entities)}, isnad_verified==True: {len(verified_ents)}")


if __name__ == "__main__":
    main()
