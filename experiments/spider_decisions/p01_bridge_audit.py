"""Phase 1.1-1.2: Audit all bridges_to_harness assertions and generate human label sheet."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import SNAPSHOTS, VAULT, bootstrap, write_json, write_md  # noqa: E402

bootstrap()

TARGET_SNAPSHOTS = ("google_portfolio_root", "grm", "gvisor", "airllm", "airllm_plus")

GENERIC_UNIT_NAMES = frozenset(
    {
        "python",
        "tests",
        "scripts",
        "test",
        "go",
        "js",
        "pkg",
        "tools",
        "docs",
        "examples",
        "bench",
        "images",
        "website",
        "protos",
        "data",
        "eval",
        "training",
        "runtime",
    }
)


def _load_vault_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        dir_id = meta_path.parent.name
        index[dir_id] = data
        index[dir_id.replace("-", "_")] = data
        for key in ("id", "ki_id"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                cleaned = val.strip()
                index[cleaned] = data
                index[cleaned.replace("-", "_")] = data
    return index


def _extract_source_strings(meta: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for key in ("source_target", "source_uri", "source_repo"):
        val = meta.get(key)
        if isinstance(val, str) and val.strip():
            fields.append(val)
    isnad = meta.get("isnad")
    if isinstance(isnad, dict):
        repo = isnad.get("source_repo")
        if isinstance(repo, str) and repo.strip():
            fields.append(repo)
    for src in meta.get("sources") or []:
        if isinstance(src, dict):
            for key in ("repo", "path", "uri", "url"):
                val = src.get(key)
                if isinstance(val, str) and val.strip():
                    fields.append(val)
    return fields


def _norm_token(text: str) -> str:
    return text.strip().lower().replace("-", "_")


def _draft_label(raw_name: str, ki_id: str, meta: dict[str, Any]) -> str:
    norm = _norm_token(raw_name)
    raw_lower = raw_name.strip().lower()
    if not norm:
        return "unsure"

    # Full segment match inside KI id
    ki_segments = [s for s in re.split(r"[_-]+", ki_id.lower()) if s]
    norm_parts = [s for s in norm.split("_") if s]
    id_hit = False
    if norm in ki_segments:
        id_hit = True
    elif len(norm_parts) > 1 and norm in ki_id.lower().replace("-", "_"):
        # Ensure boundary alignment across segments
        for i in range(len(ki_segments) - len(norm_parts) + 1):
            if ki_segments[i : i + len(norm_parts)] == norm_parts:
                id_hit = True
                break

    src_strings = _extract_source_strings(meta)
    src_hit = any(norm in _norm_token(s) or raw_lower in s.lower() for s in src_strings)

    if id_hit or src_hit:
        return "likely_true"

    tags = [str(t).strip() for t in (meta.get("tags") or []) if str(t).strip()]
    tag_norms = {_norm_token(t) for t in tags}
    tag_hit = norm in tag_norms or raw_lower in {t.lower() for t in tags}

    if tag_hit and (norm in GENERIC_UNIT_NAMES or len(norm) <= 4):
        return "likely_false"
    return "unsure"


def _escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    from ontology_spider.api import load_model

    vault_index = _load_vault_index()
    rows: list[dict[str, Any]] = []

    for snap_name in TARGET_SNAPSHOTS:
        model = load_model(SNAPSHOTS / f"{snap_name}.json")
        bridges = [a for a in model.assertions.values() if a.relation.predicate == "bridges_to_harness"]
        bridges.sort(key=lambda a: (a.relation.subject, a.relation.object))
        for asrt in bridges:
            subj = asrt.relation.subject
            ki_id = asrt.relation.object
            ent = model.entities.get(subj)
            attrs = dict(getattr(ent, "attributes", {}) or {})
            raw_name = str(attrs.get("raw_name") or subj)
            meta = vault_index.get(ki_id, {})
            title = str(meta.get("title") or "")
            tags = list(meta.get("tags") or [])
            source_target = meta.get("source_target")
            draft = _draft_label(raw_name, ki_id, meta)
            rows.append(
                {
                    "snapshot": snap_name,
                    "subject": subj,
                    "object": ki_id,
                    "raw_name": raw_name,
                    "relative_path": attrs.get("relative_path"),
                    "ki_title": title,
                    "tags": tags,
                    "source_target": source_target,
                    "draft_label": draft,
                }
            )

    json_path = write_json(1, "bridges_before", rows)

    md_lines = [
        "# Phase 1 — Bridges Before Fix (Human Label Sheet)",
        "",
        "Fill the `FINAL (fill: T/F)` column with `T` (true bridge) or `F` (false positive bridge).",
        "",
        "| # | snapshot | unit | ki_id | ki_title | draft_label | FINAL (fill: T/F) |",
        "|---:|---|---|---|---|---|---|",
    ]
    for idx, row in enumerate(rows, start=1):
        md_lines.append(
            f"| {idx} | {_escape_md(row['snapshot'])} | {_escape_md(row['raw_name'])} "
            f"| {_escape_md(row['object'])} | {_escape_md(row['ki_title'])} "
            f"| {row['draft_label']} |  |"
        )
    md_lines.append("")
    md_path = write_md(1, "bridges_label_sheet", "\n".join(md_lines))

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["draft_label"]] = counts.get(row["draft_label"], 0) + 1
    print(f"Collected {len(rows)} bridges_to_harness assertions: {counts}")
    print(f"JSON: {json_path}")
    print(f"Markdown sheet: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
