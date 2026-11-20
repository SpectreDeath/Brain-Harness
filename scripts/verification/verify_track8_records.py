"""Live verification for Track 8.2 (Phase 4 records + 103-claim vault hash audit + PLAN ticks)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from harness.services.storage.isnad_hash import audit_vault_claim_hashes  # noqa: E402


def main() -> None:
    comp = (ROOT / "experiments" / "spider_decisions" / "results" / "p04" / "comparison.md").read_text(encoding="utf-8")
    rep = (ROOT / "experiments" / "spider_decisions" / "REPORT.md").read_text(encoding="utf-8")
    plan_txt = (ROOT / "experiments" / "spider_decisions" / "PLAN.md").read_text(encoding="utf-8")

    assert "ceiling: 2" in comp and "unconfirmed" in comp and "seed `2026111841`" in comp
    assert "ceiling: `2`" in rep or "ceiling: 2" in rep
    assert "unconfirmed" in rep
    assert "one per domain group, together covering all domains" in plan_txt

    checked = len(re.findall(r"^- \[x\]", plan_txt, flags=re.M))
    unchecked = len(re.findall(r"^- \[ \]", plan_txt, flags=re.M))
    print(f"PLAN.md checkboxes: checked={checked}, unchecked={unchecked}")
    assert checked == 81 and unchecked == 0

    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", "--name-only", "--pretty=", "120c201", "757bc2e", "2edb03d"],
        capture_output=True,
        text=True,
        check=True,
    )
    touched = {
        line.split("/")[2]
        for line in proc.stdout.splitlines()
        if line.startswith(".harness/knowledge/") and len(line.split("/")) >= 3
    }
    report = audit_vault_claim_hashes(ROOT / ".harness" / "knowledge", repo_root=ROOT, ki_ids=touched)
    unverified_kis = sorted({c.ki_id for c in report.checks if c.status == "UNVERIFIED"})
    accounted = (
        report.local_verified
        + report.local_mismatches
        + report.local_missing_files
        + report.external_verified
        + report.missing_hash_flagged
        + report.malformed_hash
        + report.unverified
    )
    print(
        f"28-KI Vault Hash Recompute: touched={len(touched)} total_claims={report.total_claims} "
        f"local_verified={report.local_verified} external_verified={report.external_verified} "
        f"missing_hash_flagged={report.missing_hash_flagged} unverified={report.unverified} "
        f"local_mismatches={report.local_mismatches} malformed={report.malformed_hash}"
    )
    print(f"UNVERIFIED KIs ({len(unverified_kis)}): {unverified_kis}")

    assert len(touched) == 28
    assert accounted == report.total_claims == 103
    assert report.local_verified == 22
    assert report.external_verified == 16
    assert report.missing_hash_flagged == 62
    assert report.unverified == 3
    assert report.local_mismatches == 0
    assert report.local_missing_files == 0
    assert report.malformed_hash == 0


if __name__ == "__main__":
    main()
