"""Phase 2.3: Detect candidate duplicate KI pairs vs intentional siblings in the vault."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import VAULT, bootstrap, load_vault_model, write_json, write_md  # noqa: E402

bootstrap()


def _normalize_source_target(raw: Any) -> str:
    if not isinstance(raw, str):
        return ""
    s = raw.strip().lower()
    for prefix in ("https://github.com/", "http://github.com/", "external/"):
        if s.startswith(prefix):
            s = s[len(prefix) :]
    return s.rstrip("/")


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _load_all_metadata() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        raw_id = str(data.get("id") or data.get("ki_id") or meta_path.parent.name)
        tags = {str(t).strip().lower() for t in (data.get("tags") or []) if str(t).strip()}
        norm_src = _normalize_source_target(data.get("source_target"))
        records.append(
            {
                "dir_name": meta_path.parent.name,
                "raw_id": raw_id,
                "safe_id": raw_id.replace("-", "_"),
                "title": str(data.get("title") or ""),
                "category": str(data.get("category") or ""),
                "source_target": str(data.get("source_target") or ""),
                "norm_source": norm_src,
                "tags": tags,
            }
        )
    return records


def main() -> int:
    model = load_vault_model()
    sibling_edges: dict[tuple[str, str], str] = {}
    for asrt in model.assertions.values():
        pred = asrt.relation.predicate
        if pred in ("same_domain", "related_to"):
            s, o = asrt.relation.subject, asrt.relation.object
            sibling_edges[(s, o)] = pred
            sibling_edges[(o, s)] = pred

    records = _load_all_metadata()
    candidates: list[dict[str, Any]] = []
    intentional_siblings: list[dict[str, Any]] = []

    n = len(records)
    for i in range(n):
        a = records[i]
        for j in range(i + 1, n):
            b = records[j]
            jac = _jaccard(a["tags"], b["tags"])
            same_src = bool(a["norm_source"] and a["norm_source"] == b["norm_source"])
            cond_a = same_src and jac >= 0.5
            cond_b = len(a["tags"]) >= 3 and len(b["tags"]) >= 3 and jac >= 0.7
            if not (cond_a or cond_b):
                continue

            edge_pred = sibling_edges.get((a["safe_id"], b["safe_id"])) or sibling_edges.get((a["raw_id"], b["raw_id"]))
            entry = {
                "ki_a": a["raw_id"],
                "ki_b": b["raw_id"],
                "title_a": a["title"],
                "title_b": b["title"],
                "norm_source_a": a["norm_source"],
                "norm_source_b": b["norm_source"],
                "same_source": same_src,
                "tag_jaccard": round(jac, 4),
                "shared_tags": sorted(a["tags"] & b["tags"]),
                "matched_rule": "source+tags>=0.5"
                if cond_a and not cond_b
                else "tags>=0.7"
                if cond_b and not cond_a
                else "both",
                "sibling_edge": edge_pred,
            }
            if edge_pred is not None:
                intentional_siblings.append(entry)
            else:
                candidates.append(entry)

    candidates.sort(key=lambda r: (-r["tag_jaccard"], r["ki_a"], r["ki_b"]))
    intentional_siblings.sort(key=lambda r: (-r["tag_jaccard"], r["ki_a"], r["ki_b"]))

    payload = {
        "total_kis_scanned": n,
        "candidate_count": len(candidates),
        "intentional_siblings_count": len(intentional_siblings),
        "candidates": candidates,
        "intentional_siblings": intentional_siblings,
    }
    json_path = write_json(2, "duplicate_candidates", payload)

    md_lines = [
        "# Phase 2 — Duplicate KI Candidate Review Sheet",
        "",
        f"Scanned **{n}** KIs: **{len(candidates)}** candidate duplicate pair(s) and "
        f"**{len(intentional_siblings)}** intentional sibling pair(s) (connected via `same_domain` / `related_to`).",
        "",
        "## Candidate Duplicate Pairs",
        "",
        "| # | KI A | KI B | Same Source? | Jaccard | Rule | Shared Tags | DECISION (merge / keep / supersede) |",
        "|---:|---|---|---|---:|---|---|---|",
    ]
    for idx, c in enumerate(candidates, start=1):
        shared = ", ".join(c["shared_tags"][:6])
        md_lines.append(
            f"| {idx} | `{_escape_md(c['ki_a'])}` | `{_escape_md(c['ki_b'])}` "
            f"| {c['same_source']} | {c['tag_jaccard']:.2f} | {c['matched_rule']} | {_escape_md(shared)} |  |"
        )
    if not candidates:
        md_lines.append("| — | *(none)* | — | — | — | — | — | — |")

    md_lines.extend(
        [
            "",
            "## Intentional Siblings (Excluded via `same_domain` / `related_to`)",
            "",
            "| # | KI A | KI B | Edge | Jaccard | Shared Tags |",
            "|---:|---|---|---|---:|---|",
        ]
    )
    for idx, s in enumerate(intentional_siblings, start=1):
        shared = ", ".join(s["shared_tags"][:6])
        md_lines.append(
            f"| {idx} | `{_escape_md(s['ki_a'])}` | `{_escape_md(s['ki_b'])}` "
            f"| `{s['sibling_edge']}` | {s['tag_jaccard']:.2f} | {_escape_md(shared)} |"
        )
    md_lines.append("")
    md_path = write_md(2, "duplicate_review_sheet", "\n".join(md_lines))

    print(f"Scanned {n} KIs: candidates={len(candidates)}, intentional_siblings={len(intentional_siblings)}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
