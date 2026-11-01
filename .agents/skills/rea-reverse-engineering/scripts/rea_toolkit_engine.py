"""Stand-alone runner script for REA reverse-engineering skill operations."""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23 & Rule 50)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# SysPath Precedence Invariant (Rule 50)
workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root / "src"))
sys.path.insert(0, str(workspace_root))

from harness.services.rea_toolkit import StandardReaToolkitService


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python rea_toolkit_engine.py <inspect|signatures|providers|list> [target]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    service = StandardReaToolkitService()

    if cmd == "list":
        from harness.services.rea_toolkit import ARTIFACT_KIND_TOOLS
        print(json.dumps(ARTIFACT_KIND_TOOLS, indent=2))
        return

    if cmd == "providers":
        provs = service.providers()
        print(json.dumps({k: v.to_dict() for k, v in provs.items()}, indent=2))
        return

    if len(sys.argv) < 3:
        print(f"Error: Command '{cmd}' requires a target argument.")
        sys.exit(1)

    target = sys.argv[2]
    if cmd == "inspect":
        envelope = service.dissect(target)
        print(json.dumps(envelope.to_dict(), indent=2, ensure_ascii=False))
    elif cmd == "signatures":
        sigs = service.signatures(target)
        print(json.dumps([s.to_dict() for s in sigs], indent=2, ensure_ascii=False))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()

