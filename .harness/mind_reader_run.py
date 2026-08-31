#!/usr/bin/env python
"""Mind Reader: 4-Axis Introspection for antigravity brain."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\GitHub\projects\Brain Harness")

from plugins.memory_and_epistemics.brain_bridge.main import (
    brain_attach,
    brain_detach,
    brain_list_attached,
    brain_query,
)

BRAIN_PATH = r"C:\Users\spectre\.gemini\antigravity-ide\brain"
ALIAS = "antigravity_core"
OUTPUT_PATH = Path(r"D:\GitHub\projects\Brain Harness\.harness\mind-reader-results.json")

QUERIES = {
    "axis1_architectural": (
        "Why was this architecture, service key, or module design chosen? "
        "What trade-offs were made?"
    ),
    "axis2_errors": (
        "What commands, tests, or approaches failed and how were they debugged or corrected?"
    ),
    "axis3_epistemic": (
        "What verification standards, test markings, or coding guidelines were consistently applied?"
    ),
    "axis4_delta": (
        "What techniques or insights are unique, unexpected, or counter-intuitive?"
    ),
}


def main() -> int:
    print("[1] Attaching brain...")
    attach_res = brain_attach(
        folder_path=BRAIN_PATH,
        alias=ALIAS,
        read_transcripts=True,
        attach_mode="lens",
    )
    print(f"    status={attach_res['status']} format={attach_res['detected_format']}")
    print(f"    chunks={attach_res['summary']['total_chunks']} transcripts={attach_res['summary']['transcript_chunks']}")

    if attach_res["status"] != "ok":
        print("ATTACH_FAILED")
        return 1

    print("[2] Running 4-axis introspection...")
    results: dict[str, object] = {}
    for axis, query in QUERIES.items():
        res = brain_query(
            query=query,
            brain_alias=ALIAS,
            include_trajectories=True,
            top_k=10,
        )
        results[axis] = res
        print(f"    {axis}: {res['results_count']} results")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "attach": attach_res,
                "queries": results,
                "attached_brains": brain_list_attached(),
            },
            f,
            indent=2,
        )
    print(f"[3] Results written to {OUTPUT_PATH}")

    brain_detach(ALIAS)
    print("[4] Detached.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
