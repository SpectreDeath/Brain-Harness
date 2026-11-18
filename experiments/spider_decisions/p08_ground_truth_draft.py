"""Phase 8.1: Draft Plugin vs KI-Only vs Skip ground truth sheet for Google and AIRLLM repos."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import (  # noqa: E402
    AIRLLM_ROOT,
    SNAPSHOTS,
    VAULT,
    WORKSPACE,
    bootstrap,
    load_vault_model,
    project_entities,
    write_json,
    write_md,
)

bootstrap()


def _normalize_token(raw_name: str) -> str:
    s = raw_name.strip().lower()
    for suf in ("-main", "_main", "-master", "_master"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s.replace("-", "_")


def _find_matching_plugins(raw_name: str) -> list[str]:
    norm = _normalize_token(raw_name)
    tokens = {norm}
    if norm == "earthengine_api":
        tokens.add("earth_engine")
    if norm.startswith("adk_"):
        tokens.add(f"google_{norm}")
    if norm in ("tunix", "styleguide"):
        tokens.add(f"google_{norm}")

    matched: list[str] = []
    plugins_root = WORKSPACE / "plugins"
    for pdir in sorted(plugins_root.glob("*/*")):
        if not pdir.is_dir() or pdir.name == "__pycache__":
            continue
        pname = pdir.name.lower()
        hit = any(tok in pname for tok in tokens)
        if not hit:
            pj = pdir / "plugin.json"
            if pj.is_file():
                txt = pj.read_text(encoding="utf-8", errors="ignore").lower()
                if f"/{raw_name.lower()}" in txt or f"google/{norm}" in txt:
                    hit = True
        if hit:
            matched.append(f"{pdir.parent.name}/{pdir.name}")
    return matched


def _find_vault_bridges(raw_name: str, vault_model: Any, child_snap_kis: set[str]) -> list[str]:
    norm = _normalize_token(raw_name)
    slugs = {raw_name.lower(), norm, norm.replace("_", "-")}
    hits = set(child_snap_kis)

    for asrt in vault_model.assertions.values():
        if asrt.relation.predicate == "became_plugin":
            continue
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        kid = str(data.get("id") or data.get("ki_id") or meta_path.parent.name)
        src_fields = [
            str(data.get("source_target") or ""),
            str(data.get("source_uri") or ""),
            str((data.get("isnad") or {}).get("source_repo") or ""),
        ]
        for s in data.get("sources") or []:
            if isinstance(s, dict):
                src_fields.extend([str(s.get("repo") or ""), str(s.get("path") or "")])
        joined = " ".join(src_fields).lower()
        if any(sl in joined for sl in slugs):
            hits.add(kid)
    return sorted(hits)


def main() -> int:
    from ontology_spider.api import load_model

    groot_model = load_model(SNAPSHOTS / "google_portfolio_root.json")
    grm_model = load_model(SNAPSHOTS / "grm.json")
    gvisor_model = load_model(SNAPSHOTS / "gvisor.json")
    airllm_model = load_model(SNAPSHOTS / "airllm.json")
    airllm_plus_model = load_model(SNAPSHOTS / "airllm_plus.json")
    vault_model = load_vault_model()

    became_plugin_kis = {
        (str(a.relation.subject), str(a.relation.object))
        for a in vault_model.assertions.values()
        if a.relation.predicate == "became_plugin"
    }

    child_bridges_map: dict[str, set[str]] = {
        "google-research-master": {
            a.relation.object for a in grm_model.assertions.values() if a.relation.predicate == "bridges_to_harness"
        },
        "gvisor": {
            a.relation.object for a in gvisor_model.assertions.values() if a.relation.predicate == "bridges_to_harness"
        },
        "airllm": {
            a.relation.object for a in airllm_model.assertions.values() if a.relation.predicate == "bridges_to_harness"
        },
        "airllm-plus": {
            a.relation.object
            for a in airllm_plus_model.assertions.values()
            if a.relation.predicate == "bridges_to_harness"
        },
    }

    repo_list: list[tuple[str, str, str | None]] = []
    for eid, attrs in sorted(project_entities(groot_model).items(), key=lambda kv: str(kv[1]["raw_name"])):
        repo_list.append(("Google", str(attrs["raw_name"]), str(attrs.get("learned_ki_id") or "") or None))
    for child in sorted(AIRLLM_ROOT.iterdir(), key=lambda p: p.name):
        if child.is_dir() and not child.name.startswith("."):
            repo_list.append(("AIRLLM_SUITE", child.name, None))

    rows: list[dict[str, Any]] = []
    for parent, raw_name, root_ki in repo_list:
        plugins = _find_matching_plugins(raw_name)
        norm = _normalize_token(raw_name)
        edge_plugins = sorted(
            f"{subj}->{obj}" for subj, obj in became_plugin_kis if norm in obj.lower() or (root_ki and subj == root_ki)
        )
        child_kis = set(child_bridges_map.get(raw_name, set()))
        if root_ki:
            child_kis.add(root_ki)
        ki_hits = _find_vault_bridges(raw_name, vault_model, child_kis)

        if plugins or edge_plugins:
            draft = "plugin"
            evidence = ", ".join(plugins[:3] or edge_plugins[:3])
        elif ki_hits:
            draft = "ki_only"
            evidence = ", ".join(ki_hits[:3]) + (f" (+{len(ki_hits) - 3})" if len(ki_hits) > 3 else "")
        else:
            draft = "skip"
            evidence = "(none)"

        rows.append(
            {
                "portfolio": parent,
                "repo": raw_name,
                "draft_outcome": draft,
                "plugins_found": plugins,
                "became_plugin_edges": edge_plugins,
                "ki_count": len(ki_hits),
                "evidence_summary": evidence,
            }
        )

    json_path = write_json(8, "ground_truth_draft", rows)

    md_lines = [
        "# Phase 8 — Repo Handling Ground Truth Review Sheet (`plugin` / `ki_only` / `skip`)",
        "",
        "Review and confirm or edit the `FINAL` column (`plugin`, `ki_only`, or `skip`).",
        "",
        "| # | Portfolio | Repo | Draft Outcome | Evidence | FINAL |",
        "|---:|---|---|---|---|---|",
    ]
    for idx, r in enumerate(rows, start=1):
        md_lines.append(
            f"| {idx} | {r['portfolio']} | `{r['repo']}` | `{r['draft_outcome']}` "
            f"| {r['evidence_summary']} | `{r['draft_outcome']}` |"
        )
    md_lines.append("")
    md_path = write_md(8, "ground_truth_sheet", "\n".join(md_lines))

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["draft_outcome"]] = counts.get(r["draft_outcome"], 0) + 1
    print(f"Drafted {len(rows)} repos: {counts}")
    print(f"JSON: {json_path}")
    print(f"Sheet: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
