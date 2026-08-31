#!/usr/bin/env python
"""Validate all Knowledge Items (KIs) in .harness/knowledge for schema and Isnad integrity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

KNOWLEDGE_ROOT = Path(r"D:\GitHub\projects\Brain Harness\.harness\knowledge")

REQUIRED_METADATA_FIELDS = {
    "id",
    "title",
    "detected_format",
    "isnad",
    "tags",
    "context",
    "distilled_learning",
}


def validate_all_knowledge_items() -> int:
    if not KNOWLEDGE_ROOT.exists():
        print(f"[ERROR] Knowledge directory not found: {KNOWLEDGE_ROOT}")
        return 1

    ki_dirs = [d for d in KNOWLEDGE_ROOT.iterdir() if d.is_dir()]
    print(f"[*] Found {len(ki_dirs)} Knowledge Items in {KNOWLEDGE_ROOT}")

    errors: list[str] = []

    for ki_dir in sorted(ki_dirs):
        ki_id = ki_dir.name
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"

        if not meta_file.exists():
            errors.append(f"[{ki_id}] Missing metadata.json")
            continue

        if not summary_file.exists():
            errors.append(f"[{ki_id}] Missing summary.md")

        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"[{ki_id}] metadata.json JSON parsing failed: {e}")
            continue

        # Check required fields
        for field in REQUIRED_METADATA_FIELDS:
            if field not in meta:
                errors.append(f"[{ki_id}] Missing metadata field: '{field}'")

        # Check Isnad block
        isnad = meta.get("isnad", {})
        if not isinstance(isnad, dict):
            errors.append(f"[{ki_id}] 'isnad' must be a dictionary")
        else:
            has_status = "status" in isnad or "verified" in isnad
            if not has_status:
                errors.append(f"[{ki_id}] 'isnad' must have 'status' or 'verified'")
            if "claims" not in isnad and "primary_source" not in isnad:
                errors.append(f"[{ki_id}] 'isnad' must contain 'claims' or 'primary_source'")

        # Check summary.md content
        if summary_file.exists():
            summary_content = summary_file.read_text(encoding="utf-8")
            if not summary_content.strip():
                errors.append(f"[{ki_id}] summary.md is empty")

    if errors:
        print(f"\n[FAIL] Found {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"\n[PASS] All {len(ki_dirs)} Knowledge Items validated successfully with full Isnad schema compliance.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_all_knowledge_items())
