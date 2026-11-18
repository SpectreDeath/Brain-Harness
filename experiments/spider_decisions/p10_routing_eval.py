"""Phase 10.3-10.4: Evaluate BuiltinSkillRegistryService route_intent vs Spider-assisted vs Hybrid."""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, WORKSPACE, bootstrap, load_vault_model, write_json, write_md  # noqa: E402

bootstrap()

STOPWORDS = frozenset(
    {
        "this",
        "that",
        "with",
        "from",
        "into",
        "using",
        "across",
        "under",
        "before",
        "after",
        "when",
        "what",
        "next",
        "build",
        "make",
        "code",
    }
)

GENERIC_SUFFIX_TOKENS = frozenset(
    {
        "architect",
        "engine",
        "manager",
        "governor",
        "pipeline",
        "runner",
        "viewer",
        "assistant",
        "tooling",
        "framework",
        "system",
        "service",
        "module",
        "layer",
    }
)


def _parse_task_sheet(sheet_path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for line in sheet_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in s.strip("|").split("|")]
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        tasks.append(
            {
                "id": int(cells[0]),
                "task_intent": cells[1],
                "expected_skill": cells[2],
                "domain_note": cells[3],
                "approved_skill": cells[4] or cells[2],
            }
        )
    return tasks


def _tokenize(text: str, *, min_len: int = 3) -> set[str]:
    tokens = {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) >= min_len}
    return tokens - STOPWORDS


def _token_matches(query_tok: str, candidate_toks: set[str]) -> bool:
    if query_tok in candidate_toks:
        return True
    if len(query_tok) >= 5:
        pref = query_tok[:5]
        return any(ct.startswith(pref) or (len(ct) >= 5 and query_tok.startswith(ct[:5])) for ct in candidate_toks)
    return False


def _extract_vault_ki_index(vault_model: Any) -> list[dict[str, Any]]:
    edge_targets_by_ki: dict[str, set[str]] = {}
    for asrt in vault_model.assertions.values():
        pred = asrt.relation.predicate
        if pred in ("became_skill", "became_plugin", "references_code"):
            subj = str(asrt.relation.subject)
            obj = str(asrt.relation.object)
            edge_targets_by_ki.setdefault(subj, set()).update(_tokenize(obj, min_len=3))

    kis: list[dict[str, Any]] = []
    for eid, ent in vault_model.entities.items():
        attrs = dict(getattr(ent, "attributes", {}) or {})
        if not (str(eid).startswith("ki") and ("tags" in attrs or "title" in attrs)):
            continue
        tags_toks: set[str] = set()
        for t in attrs.get("tags") or []:
            tags_toks |= _tokenize(str(t), min_len=3)
        title_toks = _tokenize(str(attrs.get("title") or ""), min_len=3)
        id_toks = _tokenize(str(attrs.get("raw_id") or eid), min_len=3)
        cat_toks = _tokenize(str(attrs.get("category") or ""), min_len=3)

        query_surface = tags_toks | id_toks | title_toks
        assoc_tokens = edge_targets_by_ki.get(str(eid), set()) | tags_toks | cat_toks | id_toks
        kis.append(
            {
                "ki_id": str(attrs.get("raw_id") or eid),
                "query_surface": query_surface,
                "assoc_tokens": assoc_tokens,
            }
        )
    return kis


def _score_spider_skills(
    task_intent: str,
    vault_kis: list[dict[str, Any]],
    skill_names: list[str],
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    task_toks = {t for t in _tokenize(task_intent, min_len=4)}
    matched_kis = [ki for ki in vault_kis if any(_token_matches(qt, ki["query_surface"]) for qt in task_toks)]

    support_counts: dict[str, int] = {}
    ranked: list[dict[str, Any]] = []
    for sname in skill_names:
        sname_toks = {t for t in sname.lower().split("-") if len(t) >= 3}
        domain_toks = sname_toks - GENERIC_SUFFIX_TOKENS

        supporting_kis = 0
        weighted_overlap = 0
        for ki in matched_kis:
            assoc = ki["assoc_tokens"]
            non_generic_hits = {dt for dt in domain_toks if _token_matches(dt, assoc)}
            all_hits = {st for st in sname_toks if _token_matches(st, assoc)}
            if len(non_generic_hits) >= 1 or len(all_hits) >= 2:
                supporting_kis += 1
                weighted_overlap += len(non_generic_hits) + len(all_hits)

        support_counts[sname] = supporting_kis
        direct_overlap = sum(1 for dt in domain_toks if _token_matches(dt, task_toks))
        ranked.append(
            {
                "skill_name": sname,
                "supporting_kis": supporting_kis,
                "weighted_overlap": weighted_overlap,
                "direct_task_overlap": direct_overlap,
            }
        )

    ranked.sort(
        key=lambda r: (
            -r["supporting_kis"],
            -r["weighted_overlap"],
            -r["direct_task_overlap"],
            r["skill_name"],
        )
    )
    return support_counts, ranked


def _eval_hits(ranked_lists: list[list[str]], expected_list: list[str]) -> dict[str, Any]:
    n = len(expected_list)
    h1 = sum(1 for r, e in zip(ranked_lists, expected_list, strict=True) if r and r[0] == e)
    h3 = sum(1 for r, e in zip(ranked_lists, expected_list, strict=True) if e in r[:3])
    return {
        "hit_at_1_count": h1,
        "hit_at_1": round(h1 / n, 4) if n else 0.0,
        "hit_at_3_count": h3,
        "hit_at_3": round(h3 / n, 4) if n else 0.0,
    }


def main() -> int:
    from harness.services.skill_graph import BuiltinSkillRegistryService

    p10_dir = RESULTS / "p10"
    tasks = _parse_task_sheet(p10_dir / "task_set_sheet.md")
    ts_path = write_json(10, "task_set", tasks)

    svc = BuiltinSkillRegistryService()
    svc.discover_all(str(WORKSPACE))
    vault_model = load_vault_model()
    vault_kis = _extract_vault_ki_index(vault_model)
    skill_names = sorted(d.name for d in (WORKSPACE / ".agents" / "skills").iterdir() if d.is_dir())

    per_task: list[dict[str, Any]] = []
    base_lists: list[list[str]] = []
    spider_lists: list[list[str]] = []
    hybrid_lists: list[list[str]] = []
    union_lists: list[list[str]] = []
    expected_list: list[str] = []

    for task in tasks:
        tid = task["id"]
        intent = task["task_intent"]
        expected = task["approved_skill"]
        expected_list.append(expected)

        res = svc.route_intent(intent, top_k=3)
        raw_matches = res.get("matches") or []
        base_top3 = [str(m.get("skill_name") or m.get("name") or "") for m in raw_matches[:3]]

        support_counts, spider_ranked = _score_spider_skills(intent, vault_kis, skill_names)
        spider_top3 = [r["skill_name"] for r in spider_ranked[:3]]

        # Hybrid: baseline top-3 re-ranked by adding +1 per supporting KI
        hybrid_scored: list[tuple[float, int, str]] = []
        for idx, m in enumerate(raw_matches[:3]):
            sname = str(m.get("skill_name") or m.get("name") or "")
            base_score = float(m.get("raw_score") or m.get("confidence") or 0.0)
            supp = support_counts.get(sname, 0)
            hybrid_scored.append((base_score + 1.0 * supp, -idx, sname))
        hybrid_scored.sort(reverse=True)
        hybrid_top3 = [item[2] for item in hybrid_scored]

        # Hybrid Union diagnostic: merge baseline top-3 and spider top-3
        base_score_map = {
            str(m.get("skill_name") or m.get("name") or ""): float(m.get("raw_score") or m.get("confidence") or 0.0)
            for m in raw_matches[:3]
        }
        union_pool = list(dict.fromkeys(base_top3 + spider_top3))
        union_scored = [(base_score_map.get(s, 0.0) + 1.0 * support_counts.get(s, 0), s) for s in union_pool]
        union_scored.sort(key=lambda x: (-x[0], x[1]))
        union_top3 = [item[1] for item in union_scored[:3]]

        base_lists.append(base_top3)
        spider_lists.append(spider_top3)
        hybrid_lists.append(hybrid_top3)
        union_lists.append(union_top3)

        per_task.append(
            {
                "id": tid,
                "task_intent": intent,
                "expected_skill": expected,
                "baseline_top3": base_top3,
                "spider_top3": spider_top3,
                "hybrid_top3": hybrid_top3,
                "hybrid_union_top3": union_top3,
                "expected_supporting_kis": support_counts.get(expected, 0),
                "hits_at_1": {
                    "baseline": bool(base_top3 and base_top3[0] == expected),
                    "spider": bool(spider_top3 and spider_top3[0] == expected),
                    "hybrid": bool(hybrid_top3 and hybrid_top3[0] == expected),
                    "hybrid_union": bool(union_top3 and union_top3[0] == expected),
                },
                "hits_at_3": {
                    "baseline": expected in base_top3,
                    "spider": expected in spider_top3,
                    "hybrid": expected in hybrid_top3,
                    "hybrid_union": expected in union_top3,
                },
            }
        )

    summary_metrics = {
        "baseline_route_intent": _eval_hits(base_lists, expected_list),
        "spider_assisted": _eval_hits(spider_lists, expected_list),
        "hybrid_rerank_top3": _eval_hits(hybrid_lists, expected_list),
        "hybrid_union_top3": _eval_hits(union_lists, expected_list),
    }

    unique_wins = {
        "baseline_only_at_1": [
            r["id"] for r in per_task if r["hits_at_1"]["baseline"] and not r["hits_at_1"]["spider"]
        ],
        "spider_only_at_1": [r["id"] for r in per_task if r["hits_at_1"]["spider"] and not r["hits_at_1"]["baseline"]],
        "union_gains_over_baseline_at_3": [
            r["id"] for r in per_task if r["hits_at_3"]["hybrid_union"] and not r["hits_at_3"]["baseline"]
        ],
    }

    payload = {
        "task_count": len(tasks),
        "indexed_skills_count": len(skill_names),
        "vault_kis_scanned": len(vault_kis),
        "summary_metrics": summary_metrics,
        "unique_wins": unique_wins,
        "per_task": per_task,
    }
    res_path = write_json(10, "results", payload)

    md_lines = [
        "# Phase 10 — Skill Routing Evaluation Summary (`route_intent` vs Spider vs Hybrid)",
        "",
        f"Evaluated **{len(tasks)}** task intents across **{len(skill_names)}** `.agents/skills/` targets and **{len(vault_kis)}** vault KIs.",
        "",
        "## Hit@1 and Hit@3 Comparison",
        "",
        "| Method | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, key in (
        ("Baseline (`route_intent`)", "baseline_route_intent"),
        ("Spider-assisted (vault tags + edges)", "spider_assisted"),
        ("Hybrid (baseline top-3 re-ranked)", "hybrid_rerank_top3"),
        ("Hybrid Union (baseline ∪ spider top-3)", "hybrid_union_top3"),
    ):
        m = summary_metrics[key]
        md_lines.append(
            f"| {label} | {m['hit_at_1_count']}/{len(tasks)} | {100.0 * m['hit_at_1']:.1f}% "
            f"| {m['hit_at_3_count']}/{len(tasks)} | {100.0 * m['hit_at_3']:.1f}% |"
        )

    md_lines.extend(
        [
            "",
            "## Unique Wins",
            f"- **Baseline `@1` only (missed by Spider `@1`):** `{unique_wins['baseline_only_at_1']}`",
            f"- **Spider `@1` only (missed by Baseline `@1`):** `{unique_wins['spider_only_at_1']}`",
            f"- **Hybrid Union `@3` gains over Baseline `@3`:** `{unique_wins['union_gains_over_baseline_at_3']}`",
            "",
            "## Per-Task Outcomes",
            "",
            "| # | Expected | Baseline Top-1 | Spider Top-1 | Hybrid Top-1 | Union Top-1 | B@3 | S@3 | H@3 | U@3 |",
            "|---:|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for r in per_task:
        h3 = r["hits_at_3"]
        md_lines.append(
            f"| {r['id']} | `{r['expected_skill']}` | `{r['baseline_top3'][0] if r['baseline_top3'] else ''}` "
            f"| `{r['spider_top3'][0] if r['spider_top3'] else ''}` "
            f"| `{r['hybrid_top3'][0] if r['hybrid_top3'] else ''}` "
            f"| `{r['hybrid_union_top3'][0] if r['hybrid_union_top3'] else ''}` "
            f"| {h3['baseline']} | {h3['spider']} | {h3['hybrid']} | {h3['hybrid_union']} |"
        )
    md_lines.append("")
    md_path = write_md(10, "summary", "\n".join(md_lines))

    print(f"Task set saved: {ts_path}")
    print(f"Metrics: {summary_metrics}")
    print(f"Unique wins: {unique_wins}")
    print(f"Results: {res_path}")
    print(f"Summary: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
