# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check that quoted lines appear word for word in raw sources and enforce keep-outs.

Usage:
    python icm_quotes.py [ROOT] [--show-cuts]
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
    parser = argparse.ArgumentParser(description="Verify ICM quote provenance and keep-outs.")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to check")
    parser.add_argument("--show-cuts", action="store_true", help="Show text dropped by cuts")
    args = parser.parse_args()

    src_dir = Path(__file__).resolve().parents[4] / "src"
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from harness.services.icm_architect import DefaultIcmArchitectService

    svc = DefaultIcmArchitectService()
    report = svc.verify_quotes(root=args.root, show_cuts=args.show_cuts)

    print(f"Scanned {report.total_quotes} quotes, {report.verified_quotes} verified cleanly.")
    if report.broken_quotes or report.keep_out_violations:
        if report.broken_quotes:
            print(f"FAILED: {len(report.broken_quotes)} broken quotes found:", file=sys.stderr)
            for b in report.broken_quotes:
                print(f"  - {b.get('file')}: \"{b.get('quote')}\" ({b.get('reason')})", file=sys.stderr)
        if report.keep_out_violations:
            print(f"FAILED: {len(report.keep_out_violations)} keep-out violations found:", file=sys.stderr)
            for k in report.keep_out_violations:
                print(f"  - {k}", file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: All quotes verified and zero keep-out violations detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
