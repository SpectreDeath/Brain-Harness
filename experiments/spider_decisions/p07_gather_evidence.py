"""Phase 7.1: Gather verified and unverified vault evidence for Q1 and Q2 design questions."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import VAULT, bootstrap, load_vault_model, write_json  # noqa: E402
from retrieval import retrieve_kis  # noqa: E402

bootstrap()

Q1_QUESTION = "What eviction/prefetch policy should Brain Harness use for lazily-staged plugin artifacts?"
Q2_QUESTION = "How should uncertainty_guard decide to abstain or escalate to a human?"

Q1_EXPECTED = (
    "ki_airllm_plus_superblock_prefetch_runtime",
    "ki_airllm_layerwise_streaming_and_moe_expert_offload",
)
Q1_TAG_KEYWORDS = frozenset({"prefetch", "cache", "lru", "streaming"})

Q2_EXPECTED = (
    "ki_google_research_aspest_active_selective_prediction",
    "ki_google_research_uq_benchmark_2019_calibration_shift",
    "ki_google_research_cisc_confidence_voting",
)


def _load_vault_index() -> dict[str, tuple[dict[str, Any], str]]:
    idx: dict[str, tuple[dict[str, Any], str]] = {}
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta, dict):
            continue
        sum_path = meta_path.parent / "summary.md"
        sum_txt = sum_path.read_text(encoding="utf-8", errors="ignore") if sum_path.is_file() else ""
        for key in (meta_path.parent.name, str(meta.get("id") or ""), str(meta.get("ki_id") or "")):
            if key:
                idx[key] = (meta, sum_txt)
                idx[key.replace("-", "_")] = (meta, sum_txt)
    return idx


def _extract_ki_record(
    ki_id: str,
    source_tag: str,
    vault_model: Any,
    idx: dict[str, tuple[dict[str, Any], str]],
) -> dict[str, Any]:
    safe_id = ki_id.replace("-", "_")
    ent = vault_model.entities.get(safe_id) or vault_model.entities.get(ki_id)
    ent_attrs = dict(getattr(ent, "attributes", {}) or {})
    meta, sum_txt = idx.get(ki_id, idx.get(safe_id, ({}, "")))
    isnad_verified = bool(ent_attrs.get("isnad_verified"))
    isnad = meta.get("isnad") if isinstance(meta.get("isnad"), dict) else {}

    raw_claims = isnad.get("claims") or []
    claims: list[dict[str, Any]] = []
    for cl in raw_claims:
        if not isinstance(cl, dict):
            continue
        claims.append(
            {
                "assertion": str(cl.get("assertion") or "").strip(),
                "file": str(cl.get("file") or cl.get("source_file") or ""),
                "lines": str(cl.get("lines") or ""),
                "verified": bool(cl.get("verified")),
            }
        )

    return {
        "ki_id": str(meta.get("id") or ki_id),
        "title": str(meta.get("title") or ent_attrs.get("title") or ""),
        "category": str(meta.get("category") or ent_attrs.get("category") or ""),
        "tags": list(meta.get("tags") or []),
        "discovery_source": source_tag,
        "isnad_verified": isnad_verified,
        "claim_count": len(claims),
        "verified_claim_count": sum(1 for c in claims if c["verified"]),
        "claims": claims,
        "distilled_learning": str(ent_attrs.get("distilled_learning") or meta.get("summary") or "")[:400],
        "summary_excerpt": sum_txt[:600],
    }


def _tag_matches_q1(tags: list[str]) -> bool:
    for t in tags:
        parts = set(re.split(r"[-_\s]+", str(t).strip().lower()))
        if parts & Q1_TAG_KEYWORDS:
            return True
    return False


def main() -> int:
    vault = load_vault_model()
    idx = _load_vault_index()

    # Question 1: expected + tag search for prefetch/cache/lru/streaming
    q1_sources: dict[str, list[str]] = {}
    for k in Q1_EXPECTED:
        q1_sources.setdefault(k, []).append("expected")
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta, dict):
            continue
        kid = str(meta.get("id") or meta_path.parent.name)
        tags = [str(t) for t in (meta.get("tags") or [])]
        if _tag_matches_q1(tags):
            q1_sources.setdefault(kid, []).append("tag_search")

    q1_evidence = [
        _extract_ki_record(kid, "+".join(sorted(set(srcs))), vault, idx) for kid, srcs in sorted(q1_sources.items())
    ]

    # Question 2: expected + retrieve_kis("harness.services.uncertainty_guard", hops=1)
    q2_sources: dict[str, list[str]] = {}
    for k in Q2_EXPECTED:
        q2_sources.setdefault(k, []).append("expected")
    for kid, hop, via in retrieve_kis(vault, "harness.services.uncertainty_guard", hops=1):
        q2_sources.setdefault(kid, []).append(f"retrieve_hop{hop}:{via}")

    q2_evidence = [
        _extract_ki_record(kid, "+".join(sorted(set(srcs))), vault, idx) for kid, srcs in sorted(q2_sources.items())
    ]

    p1 = write_json(7, "evidence_q1", {"question": Q1_QUESTION, "kis": q1_evidence})
    p2 = write_json(7, "evidence_q2", {"question": Q2_QUESTION, "kis": q2_evidence})
    print(f"Q1 evidence ({len(q1_evidence)} KIs): {p1}")
    for item in q1_evidence:
        print(
            f"  - {item['ki_id']}: verified={item['isnad_verified']}, "
            f"claims={item['verified_claim_count']}/{item['claim_count']}, via={item['discovery_source']}"
        )
    print(f"Q2 evidence ({len(q2_evidence)} KIs): {p2}")
    for item in q2_evidence:
        print(
            f"  - {item['ki_id']}: verified={item['isnad_verified']}, "
            f"claims={item['verified_claim_count']}/{item['claim_count']}, via={item['discovery_source']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
