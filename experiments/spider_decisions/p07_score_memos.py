"""Phase 7.3: Score design memos by cited claim verification rate, distinct KIs, and conflicts."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, VAULT, bootstrap, write_json, write_md  # noqa: E402

bootstrap()

KI_TOKEN_RE = re.compile(r"\b(ki[-_][a-zA-Z0-9_-]+)\b")


def _all_vault_ki_ids() -> set[str]:
    ids: set[str] = set()
    for p in VAULT.glob("*/metadata.json"):
        ids.add(p.parent.name)
        ids.add(p.parent.name.replace("-", "_"))
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            for k in ("id", "ki_id"):
                val = data.get(k)
                if isinstance(val, str) and val.strip():
                    ids.add(val.strip())
                    ids.add(val.strip().replace("-", "_"))
    return ids


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip('"').strip("'")).lower()


def _score_memo(memo_path: Path, evidence_path: Path, vault_ids: set[str]) -> dict[str, Any]:
    memo_text = memo_path.read_text(encoding="utf-8")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    ev_by_id: dict[str, dict[str, Any]] = {}
    claim_lookup: dict[tuple[str, str], bool] = {}
    for item in evidence["kis"]:
        kid = item["ki_id"]
        ev_by_id[kid] = item
        ev_by_id[kid.replace("-", "_")] = item
        for cl in item.get("claims") or []:
            norm_a = _normalize(cl.get("assertion") or "")
            if norm_a:
                claim_lookup[(kid, norm_a)] = bool(cl.get("verified"))
                claim_lookup[(kid.replace("-", "_"), norm_a)] = bool(cl.get("verified"))

    cited_ki_ids = sorted(set(KI_TOKEN_RE.findall(memo_text)))
    invalid_kis = [k for k in cited_ki_ids if k not in vault_ids]

    # Parse claim rows from the "## Supporting Claims Cited" Markdown table
    in_claims_table = False
    cited_claims: list[dict[str, Any]] = []
    for line in memo_text.splitlines():
        s = line.strip()
        if s.startswith("## Supporting Claims Cited"):
            in_claims_table = True
            continue
        if in_claims_table and s.startswith("## "):
            in_claims_table = False
            continue
        if not in_claims_table or not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in ("KI ID", "---") or set(cells[0]) == {"-"}:
            continue
        kid = cells[0].strip("`")
        claim_txt = cells[1].strip().strip('"')
        norm_c = _normalize(claim_txt)
        verified_in_ev = claim_lookup.get((kid, norm_c))
        if verified_in_ev is None and kid in ev_by_id:
            # Fallback prefix match against evidence assertions for this KI
            for cl in ev_by_id[kid].get("claims") or []:
                ev_norm = _normalize(cl.get("assertion") or "")
                if ev_norm and (norm_c in ev_norm or ev_norm in norm_c):
                    verified_in_ev = bool(cl.get("verified"))
                    break
        if verified_in_ev is None:
            # Summary-derived verified KI claims vs explicit UNVERIFIED tag
            marked_verified = "VERIFIED" in cells[3].upper() and "UNVERIFIED" not in cells[3].upper()
            ki_verified = bool(ev_by_id.get(kid, {}).get("isnad_verified"))
            verified_in_ev = marked_verified and ki_verified
        cited_claims.append(
            {
                "ki_id": kid,
                "claim_excerpt": claim_txt[:90],
                "verified_in_evidence": bool(verified_in_ev),
            }
        )

    # Count conflicts flagged in ## Conflicts & Gaps section
    in_conflicts = False
    conflicts_flagged = 0
    gaps_flagged = 0
    for line in memo_text.splitlines():
        s = line.strip()
        if s.startswith("## Conflicts"):
            in_conflicts = True
            continue
        if in_conflicts and s.startswith("## "):
            break
        if in_conflicts:
            if "[CONFLICT]" in s:
                conflicts_flagged += 1
            elif "[GAP]" in s:
                gaps_flagged += 1

    total_claims = len(cited_claims)
    verified_claims = sum(1 for c in cited_claims if c["verified_in_evidence"])
    pct_verified = round(100.0 * verified_claims / total_claims, 2) if total_claims else 0.0

    return {
        "memo_file": str(memo_path),
        "cited_ki_ids": cited_ki_ids,
        "distinct_kis_cited": len(cited_ki_ids),
        "invalid_vault_ki_ids": invalid_kis,
        "all_cited_kis_in_vault": len(invalid_kis) == 0,
        "cited_claims_total": total_claims,
        "cited_claims_verified": verified_claims,
        "pct_cited_claims_verified": pct_verified,
        "conflicts_flagged": conflicts_flagged,
        "gaps_flagged": gaps_flagged,
        "cited_claims": cited_claims,
    }


def main() -> int:
    p07_dir = RESULTS / "p07"
    vault_ids = _all_vault_ki_ids()
    q1 = _score_memo(p07_dir / "memo_q1.md", p07_dir / "evidence_q1.json", vault_ids)
    q2 = _score_memo(p07_dir / "memo_q2.md", p07_dir / "evidence_q2.json", vault_ids)

    payload = {"q1": q1, "q2": q2}
    json_path = write_json(7, "memo_scores", payload)

    md_lines = [
        "# Phase 7 — Design Memo Automated Citation & Verification Scores",
        "",
        "| Memo | Distinct KIs Cited | All Valid in Vault | Cited Claims | Verified Claims | % Claims Verified | Conflicts Flagged | Gaps Flagged |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for label, res in (("memo_q1", q1), ("memo_q2", q2)):
        md_lines.append(
            f"| `{label}` | {res['distinct_kis_cited']} | {res['all_cited_kis_in_vault']} "
            f"| {res['cited_claims_total']} | {res['cited_claims_verified']} "
            f"| {res['pct_cited_claims_verified']:.1f}% | {res['conflicts_flagged']} | {res['gaps_flagged']} |"
        )
    md_lines.append("")
    md_path = write_md(7, "memo_scores", "\n".join(md_lines))

    print(
        f"Q1: KIs={q1['distinct_kis_cited']}, verified={q1['pct_cited_claims_verified']:.1f}%, conflicts={q1['conflicts_flagged']}"
    )
    print(
        f"Q2: KIs={q2['distinct_kis_cited']}, verified={q2['pct_cited_claims_verified']:.1f}%, conflicts={q2['conflicts_flagged']}"
    )
    print(f"JSON: {json_path}")
    print(f"MD: {md_path}")
    return 0 if (q1["all_cited_kis_in_vault"] and q2["all_cited_kis_in_vault"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
