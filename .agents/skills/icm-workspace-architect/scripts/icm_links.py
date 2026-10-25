# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""List every relative link and input path that does not resolve. Exit 1 if there are any.

Usage:
    python icm_links.py [ROOT] [--skip FOLDER ...] [--graph FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify ICM workspace relative links and inputs.")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to check")
    parser.add_argument("--skip", action="append", default=[], help="Folders to skip")
    parser.add_argument("--graph", default=None, help="Output path for JSONL graph")
    args = parser.parse_args()

    # Prepend workspace src to sys.path if needed
    src_dir = Path(__file__).resolve().parents[4] / "src"
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from harness.services.icm_architect import DefaultIcmArchitectService

    svc = DefaultIcmArchitectService()
    report = svc.verify_links(root=args.root, skip_folders=args.skip, graph_file=args.graph)

    print(f"Scanned {report.total_links} links, {report.resolved_links} resolved cleanly.")
    if report.broken_links:
        print(f"FAILED: {len(report.broken_links)} broken links found:", file=sys.stderr)
        for b in report.broken_links:
            print(f"  - {b.get('file')}: {b.get('link')} ({b.get('type')})", file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: Zero broken links found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
