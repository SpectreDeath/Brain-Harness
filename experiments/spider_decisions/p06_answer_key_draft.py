"""Phase 6.1: Draft candidate KI answer key per Brain Harness module via vault substring search."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import VAULT, bootstrap, write_json, write_md  # noqa: E402

bootstrap()

TARGET_MODULES: tuple[str, ...] = (
    "harness.services.vector_index",
    "harness.services.uncertainty_guard",
    "harness.agent.swarm.consensus",
    "harness.services.ontology_spider",
    "harness.services.deep_auditor",
)


def _escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _load_vault_docs() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            meta_raw = meta_path.read_text(encoding="utf-8")
            meta_obj = json.loads(meta_raw)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta_obj, dict):
            continue
        ki_id = str(meta_obj.get("id") or meta_obj.get("ki_id") or meta_path.parent.name)
        title = str(meta_obj.get("title") or "")
        sum_path = meta_path.parent / "summary.md"
        sum_raw = sum_path.read_text(encoding="utf-8", errors="ignore") if sum_path.is_file() else ""
        docs.append(
            {
                "ki_id": ki_id,
                "ki_title": title,
                "meta_lower": meta_raw.lower(),
                "summary_lower": sum_raw.lower(),
            }
        )
    return docs


def main() -> int:
    docs = _load_vault_docs()
    rows: list[dict[str, Any]] = []
    counts_per_module: dict[str, int] = {}

    for mod in TARGET_MODULES:
        last_seg = mod.rsplit(".", 1)[-1].lower()
        dotted_low = mod.lower()
        mod_count = 0
        for d in docs:
            in_meta = dotted_low in d["meta_lower"] or last_seg in d["meta_lower"]
            in_sum = dotted_low in d["summary_lower"] or last_seg in d["summary_lower"]
            if not (in_meta or in_sum):
                continue
            where_parts: list[str] = []
            if in_meta:
                where_parts.append("metadata.json")
            if in_sum:
                where_parts.append("summary.md")
            mod_count += 1
            rows.append(
                {
                    "module": mod,
                    "ki_id": d["ki_id"],
                    "ki_title": d["ki_title"],
                    "where_mentioned": "+".join(where_parts),
                }
            )
        counts_per_module[mod] = mod_count

    json_path = write_json(6, "answer_key_draft", {"counts": counts_per_module, "rows": rows})

    md_lines = [
        "# Phase 6 — Module-to-KI Retrieval Answer Key Review Sheet",
        "",
        "Fill the `RELEVANT (Y/N)` column for each `(module, ki_id)` row. "
        "Add any missing relevant KIs at the bottom if needed.",
        "",
        "| module | ki_id | ki_title | where_mentioned | RELEVANT (Y/N) |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        md_lines.append(
            f"| `{r['module']}` | `{_escape_md(r['ki_id'])}` | {_escape_md(r['ki_title'])[:80]} "
            f"| {r['where_mentioned']} |  |"
        )
    md_lines.append("")
    md_path = write_md(6, "answer_key_sheet", "\n".join(md_lines))

    print(f"Draft answer key hits ({len(rows)} total): {counts_per_module}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
