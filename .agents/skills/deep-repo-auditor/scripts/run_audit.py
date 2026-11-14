"""Standalone CLI runner for the deep-repo-auditor skill (Rules 23, 49, 50)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.is_dir() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from harness.services.deep_auditor import DefaultDeepRepoAuditorService  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Execute 4-axis repository audit and print JSON summary."""
    parser = argparse.ArgumentParser(description="Run 4-axis Deep Repo Auditor inspection.")
    parser.add_argument("repo_path", nargs="?", default=".", help="Path to repository root to audit")
    parser.add_argument("--briefs-dir", default=None, help="Directory where HTML visual briefs will be written")
    parser.add_argument("--no-briefs", action="store_true", help="Skip generating HTML visual briefs")
    args = parser.parse_args(argv)

    service = DefaultDeepRepoAuditorService()
    if args.no_briefs:
        report = service.audit_repo(args.repo_path)
        payload = {"report": report.to_dict(), "ki_candidates": service.extract_ki_candidates(report)}
    else:
        payload = service.run_full_audit(args.repo_path, output_dir=args.briefs_dir)

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
