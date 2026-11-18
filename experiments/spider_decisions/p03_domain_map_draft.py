"""Phase 3.1-3.2: Draft mapping from Knowledge Vault categories to repository domain classes."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import SNAPSHOTS, VAULT, bootstrap, project_entities, write_json, write_md  # noqa: E402

bootstrap()

REPO_SNAPSHOTS = ("grm", "google_portfolio_root", "gvisor", "airllm", "airllm_plus")
OPT_TAGS = frozenset({"vector", "vector_search", "search", "quantization", "compression", "pruning", "sparsity", "vq"})


def _draft_map_category(category: str) -> str:
    cat = category.strip().lower()
    if not cat:
        return "unmapped"
    if any(tok in cat for tok in ("security", "forensic", "privacy", "safety", "alignment")):
        return "privacy_fairness_safety_project"
    if any(tok in cat for tok in ("nlp", "llm", "language")):
        return "nlp_and_llm_project"
    if any(tok in cat for tok in ("vision", "multimodal", "3d", "image")):
        return "vision_and_3d_project"
    if any(tok in cat for tok in ("speech", "audio", "music")):
        return "speech_and_audio_project"
    if any(tok in cat for tok in ("graph", "knowledge_graph", "ontology", "program")):
        return "graph_and_program_project"
    if any(tok in cat for tok in ("bio", "science", "chem", "physics", "quantum", "medical")):
        return "science_and_bio_project"
    if any(tok in cat for tok in ("rl", "reinforcement", "control", "robotics")):
        return "rl_and_control_project"
    if any(tok in cat for tok in ("optim", "quantiz", "compress", "prun")):
        return "optimization_and_compression_project"
    if "machine_learning" in cat or cat == "ml":
        return "general_ml_project"
    if any(tok in cat for tok in ("infrastructure", "runtime", "system", "sandbox", "cloud")):
        return "systems_and_runtime_project"
    if "agent" in cat:
        return "agent_orchestration_project"
    return "unmapped"


def main() -> int:
    from ontology_spider.api import load_model

    cat_counts: Counter[str] = Counter()
    data_eng_opt_split: Counter[str] = Counter()
    vault_items: list[dict[str, Any]] = []

    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        cat = str(data.get("category") or "").strip() or "(empty)"
        tags = {str(t).strip().lower() for t in (data.get("tags") or []) if str(t).strip()}
        cat_counts[cat] += 1
        if "data_engineering" in cat.lower():
            if tags & OPT_TAGS:
                data_eng_opt_split["optimization_and_compression_project"] += 1
            else:
                data_eng_opt_split["unmapped"] += 1
        vault_items.append({"id": data.get("id") or meta_path.parent.name, "category": cat, "tags": sorted(tags)})

    domain_counts: Counter[str] = Counter()
    per_snapshot_domains: dict[str, dict[str, int]] = {}
    for snap in REPO_SNAPSHOTS:
        model = load_model(SNAPSHOTS / f"{snap}.json")
        ents = project_entities(model)
        snap_counter: Counter[str] = Counter()
        for attrs in ents.values():
            dc = str(attrs.get("domain_class") or "general_ml_project")
            domain_counts[dc] += 1
            snap_counter[dc] += 1
        per_snapshot_domains[snap] = dict(sorted(snap_counter.items()))

    category_rows: list[dict[str, Any]] = []
    for cat, count in sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if "data_engineering" in cat.lower():
            mapped = "conditional:optimization_and_compression_project"
        else:
            mapped = _draft_map_category(cat)
        category_rows.append(
            {
                "vault_category": cat,
                "vault_count": count,
                "draft_domain_class": mapped,
                "notes": (
                    f"tag-split opt={data_eng_opt_split['optimization_and_compression_project']}, "
                    f"unmapped={data_eng_opt_split['unmapped']}"
                    if "data_engineering" in cat.lower()
                    else ""
                ),
            }
        )

    payload = {
        "vault_categories": dict(sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "repo_domain_classes": dict(sorted(domain_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "per_snapshot_domains": per_snapshot_domains,
        "data_engineering_tag_split": dict(data_eng_opt_split),
        "draft_mapping": category_rows,
    }
    json_path = write_json(3, "domain_map_draft", payload)

    md_lines = [
        "# Phase 3 — Vault Category to Repo Domain-Class Mapping Review",
        "",
        "Please review or edit the `FINAL_DOMAIN_CLASS` column below (or confirm ``ok`` / ``proceed``).",
        "",
        "## Repo `domain_class` Distribution (5 Snapshots)",
        "",
        "| Repo `domain_class` | Unit Count |",
        "|---|---:|",
    ]
    for dc, cnt in sorted(domain_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        md_lines.append(f"| `{dc}` | {cnt} |")

    md_lines.extend(
        [
            "",
            "## Draft Mapping (`vault_category` -> `domain_class`)",
            "",
            "| # | Vault `category` | KI Count | Draft `domain_class` | Notes | FINAL_DOMAIN_CLASS |",
            "|---:|---|---:|---|---|---|",
        ]
    )
    for idx, row in enumerate(category_rows, start=1):
        md_lines.append(
            f"| {idx} | `{row['vault_category']}` | {row['vault_count']} | `{row['draft_domain_class']}` "
            f"| {row['notes']} | `{row['draft_domain_class']}` |"
        )
    md_lines.append("")
    md_path = write_md(3, "domain_map_review", "\n".join(md_lines))

    print(f"Distinct vault categories={len(cat_counts)}, distinct repo domain_classes={len(domain_counts)}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
