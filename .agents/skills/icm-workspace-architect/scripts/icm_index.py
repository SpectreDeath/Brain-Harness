# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Write _index.md in each folder named: one line per note, built from the note itself.

Usage:
    python icm_index.py FOLDER [FOLDER ...] [--root ROOT]
"""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Rebuild _index.md files across shelves.")
    parser.add_argument("folders", nargs="+", help="Folders to index")
    parser.add_argument("--root", default=".", help="Root workspace directory")
    args = parser.parse_args()

    src_dir = Path(__file__).resolve().parents[4] / "src"
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from harness.services.icm_architect import DefaultIcmArchitectService

    svc = DefaultIcmArchitectService()
    report = svc.rebuild_index(folders=args.folders, root=args.root)

    print(f"Indexed {report.total_notes} notes across {len(report.folders_indexed)} folders.")
    for idx_file in report.index_files_written:
        print(f"  + Wrote {idx_file}")


if __name__ == "__main__":
    main()
